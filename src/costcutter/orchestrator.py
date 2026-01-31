import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from graphlib import TopologicalSorter
from typing import Any

from boto3.session import Session
from pydantic import BaseModel

from costcutter.config import load_config
from costcutter.core.session_helper import create_aws_session
from costcutter.dependencies import RESOURCE_DEPENDENCIES, get_all_resources
from costcutter.reporter import get_reporter
from costcutter.services.ec2 import cleanup_ec2
from costcutter.services.ec2 import get_handler_for_resource as get_ec2_handler
from costcutter.services.elasticbeanstalk import (
    cleanup_elasticbeanstalk,
)
from costcutter.services.elasticbeanstalk import (
    get_handler_for_resource as get_eb_handler,
)
from costcutter.services.s3 import cleanup_s3
from costcutter.services.s3 import get_handler_for_resource as get_s3_handler

logger = logging.getLogger(__name__)


def _get_config_value(obj: BaseModel | dict[str, Any] | Any, key: str, default: Any = None) -> Any:
    """Get a value from BaseModel, dict, or object with attribute access."""
    if isinstance(obj, BaseModel):
        return getattr(obj, key, default)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


SERVICE_HANDLERS = {
    # Service-level handlers (used for non-DAG execution path)
    "ec2": cleanup_ec2,
    "elasticbeanstalk": cleanup_elasticbeanstalk,
    "s3": cleanup_s3,
}

# Resource-level handler getters for DAG-based execution
RESOURCE_HANDLER_GETTERS: dict[str, Callable[[str], Callable | None]] = {
    "ec2": get_ec2_handler,
    "elasticbeanstalk": get_eb_handler,
    "s3": get_s3_handler,
}


def _service_supported_in_region(available_regions_map: dict[str, set[str]], service_key: str, region: str) -> bool:
    """Check if a service is supported in a given region."""
    regions = available_regions_map.get(service_key)
    # If mapping unknown, default to allowed to avoid over-blocking
    return True if regions is None else region in regions


def _get_resource_handler(service: str, resource_type: str) -> Callable | None:
    """Get the handler function for a specific service resource type.

    Args:
        service: Service name (ec2, elasticbeanstalk, s3)
        resource_type: Resource type within the service

    Returns:
        Handler function or None if not found
    """
    getter = RESOURCE_HANDLER_GETTERS.get(service)
    if getter is None:
        return None
    return getter(resource_type)


def _process_single_resource(
    session: Session,
    service: str,
    resource_type: str,
    region: str,
    dry_run: bool,
    resource_max_workers: int = 10,
) -> dict[str, Any]:
    """Execute deletion for a single service/resource/region combination.

    Args:
        session: AWS session
        service: Service name (e.g., 'ec2')
        resource_type: Resource type (e.g., 'instances')
        region: AWS region
        dry_run: Whether to perform dry run
        resource_max_workers: Max concurrent workers for resource handler (e.g., parallel instance deletions)

    Returns:
        Dict with execution details (succeeded, failed, etc.)
    """
    handler = _get_resource_handler(service, resource_type)
    if handler is None:
        logger.warning("[%s][%s][%s] No handler found for resource", region, service, resource_type)
        return {"status": "skipped", "reason": "no_handler"}

    task_id = f"{region}/{service}/{resource_type}"
    logger.info("[%s] Starting deletion", task_id)

    try:
        handler(session=session, region=region, dry_run=dry_run, max_workers=resource_max_workers)
        logger.info("[%s] Completed successfully", task_id)
        return {"status": "succeeded"}
    except Exception as e:
        logger.exception("[%s] Failed with error: %s", task_id, e)
        return {"status": "failed", "error": str(e), "exception_type": type(e).__name__}


def _build_dependency_graph(selected_resources: set[tuple[str, str]], regions: list[str]) -> dict[tuple, list[tuple]]:
    """Build a task dependency graph for topological sorting.

    Args:
        selected_resources: Set of (service, resource_type) tuples to delete
        regions: List of regions to process

    Returns:
        Dict mapping task tuples to lists of task dependencies
    """
    # Task representation: (service, resource_type, region)
    task_dependencies: dict[tuple, list[tuple]] = {}

    for service, resource_type in selected_resources:
        for region in regions:
            task = (service, resource_type, region)
            deps = RESOURCE_DEPENDENCIES.get((service, resource_type), [])

            # Convert resource dependencies to task dependencies (same resource, all regions)
            task_deps: list[tuple] = []
            for dep_service, dep_resource in deps:
                # Dependency must complete in the same region before this task
                dep_task = (dep_service, dep_resource, region)
                task_deps.append(dep_task)

            task_dependencies[task] = task_deps

    return task_dependencies


def _execute_with_topological_sort(
    session: Session,
    selected_resources: set[tuple[str, str]],
    regions: list[str],
    available_regions_map: dict[str, set[str]],
    dry_run: bool,
    max_workers: int,
    resource_max_workers: int = 10,
) -> dict[str, Any]:
    """Execute resource deletion using topological sort for dependency ordering.

    Args:
        session: AWS session
        selected_resources: Set of (service, resource_type) tuples to delete
        regions: List of AWS regions
        available_regions_map: Map of service -> available regions
        dry_run: Whether to perform dry run
        max_workers: Max concurrent tasks (stage-level parallelism)
        resource_max_workers: Max concurrent workers per resource handler

    Returns:
        Summary dict with execution statistics
    """
    # Build task graph and filter by supported regions
    task_dependencies = _build_dependency_graph(selected_resources, regions)
    tasks = {
        task: deps
        for task, deps in task_dependencies.items()
        if _service_supported_in_region(available_regions_map, task[0], task[2])
    }

    if not tasks:
        logger.warning("No valid tasks to execute after filtering by supported regions")
        return {"processed": 0, "skipped": 0, "failed": 0, "events": [], "stages": []}

    # Compute topological order using graphlib
    sorter = TopologicalSorter(tasks)
    try:
        sorted_tasks = tuple(sorter.static_order())
    except Exception as e:
        logger.error("Failed to compute topological sort: %s", e)
        raise RuntimeError(f"Dependency graph has cycles or invalid structure: {e}") from e

    logger.info(
        "Computed deletion order: %d tasks across %d resources and %d regions",
        len(sorted_tasks),
        len(selected_resources),
        len(regions),
    )

    # Group tasks into stages using TopologicalSorter's built-in stage detection
    # This is O(n) compared to the manual O(n²) approach
    sorter = TopologicalSorter(tasks)
    sorter.prepare()

    stages: list[list[tuple]] = []
    while sorter.is_active():
        # get_ready() returns all tasks whose dependencies are satisfied
        ready_tasks = sorter.get_ready()
        if ready_tasks:
            stage = list(ready_tasks)
            stages.append(stage)
            # Mark all tasks in this stage as done
            for task in stage:
                sorter.done(task)

    logger.info("Created %d execution stages (optimized grouping)", len(stages))

    # Execute stages sequentially, with parallelism within each stage
    succeeded = 0
    failed = 0
    deferred: list[tuple] = []
    stage_results: list[dict] = []

    for stage_num, stage_tasks in enumerate(stages, 1):
        logger.info("[Stage %d/%d] Executing %d tasks", stage_num, len(stages), len(stage_tasks))
        stage_summary: dict[str, Any] = {
            "stage": stage_num,
            "total": len(stage_tasks),
            "succeeded": 0,
            "failed": 0,
            "tasks": [],
        }

        with ThreadPoolExecutor(max_workers=min(max_workers, len(stage_tasks))) as executor:
            future_map: dict[Any, tuple] = {}
            for task in stage_tasks:
                service, resource_type, region = task
                fut = executor.submit(
                    _process_single_resource, session, service, resource_type, region, dry_run, resource_max_workers
                )
                future_map[fut] = task

            for future in as_completed(future_map):
                task = future_map[future]
                service, resource_type, region = task

                try:
                    result = future.result()
                    if result["status"] == "succeeded":
                        succeeded += 1
                        stage_summary["succeeded"] += 1
                        stage_summary["tasks"].append({
                            "task": f"{region}/{service}/{resource_type}",
                            "status": "succeeded",
                        })
                    elif result["status"] == "failed":
                        failed += 1
                        stage_summary["failed"] += 1
                        deferred.append(task)
                        stage_summary["tasks"].append({
                            "task": f"{region}/{service}/{resource_type}",
                            "status": "failed",
                            "reason": result.get("reason"),
                        })
                except Exception as e:
                    failed += 1
                    stage_summary["failed"] += 1
                    deferred.append(task)
                    stage_summary["tasks"].append({
                        "task": f"{region}/{service}/{resource_type}",
                        "status": "failed",
                        "reason": str(e),
                    })

        stage_results.append(stage_summary)

    # Attempt retry of deferred tasks once
    if deferred:
        logger.info("[Deferred Retry] Attempting %d previously failed tasks", len(deferred))
        deferred_summary: dict[str, Any] = {
            "stage": "deferred_retry",
            "total": len(deferred),
            "succeeded": 0,
            "failed": 0,
            "tasks": [],
        }

        with ThreadPoolExecutor(max_workers=min(max_workers, len(deferred))) as executor:
            future_map = {}
            for task in deferred:
                service, resource_type, region = task
                fut = executor.submit(
                    _process_single_resource, session, service, resource_type, region, dry_run, resource_max_workers
                )
                future_map[fut] = task

            for future in as_completed(future_map):
                task = future_map[future]
                service, resource_type, region = task

                try:
                    result = future.result()
                    if result["status"] == "succeeded":
                        succeeded += 1
                        deferred_summary["succeeded"] += 1
                        failed -= 1
                        deferred_summary["tasks"].append({
                            "task": f"{region}/{service}/{resource_type}",
                            "status": "succeeded",
                        })
                    else:
                        deferred_summary["failed"] += 1
                        deferred_summary["tasks"].append({
                            "task": f"{region}/{service}/{resource_type}",
                            "status": "failed",
                            "reason": result.get("reason"),
                        })
                except Exception as e:
                    deferred_summary["failed"] += 1
                    deferred_summary["tasks"].append({
                        "task": f"{region}/{service}/{resource_type}",
                        "status": "failed",
                        "reason": str(e),
                    })

        stage_results.append(deferred_summary)

    # After all work is finished, gather recorded events from the global reporter
    reporter = get_reporter()
    events = reporter.to_dicts()

    return {
        "processed": succeeded,
        "skipped": len(tasks),  # skipped by filtering, not explicitly tracked
        "failed": failed,
        "events": events,
        "stages": stage_results,
    }


def orchestrate_services(
    dry_run: bool = False,
) -> dict[str, Any]:
    """Orchestrate resource deletion using topological sort for dependency ordering.

    Retrieves available resources from the dependency registry, builds a task graph
    respecting AWS dependencies, and executes deletion in topologically-sorted order.

    Returns:
        Summary dict with execution statistics and stage-wise results
    """
    config = load_config()

    # Resolve services
    selected_services_raw = list(_get_config_value(config.aws, "services", []) or [])
    if not selected_services_raw:
        raise ValueError("No services configured under aws.services")
    if any(s.lower() == "all" for s in selected_services_raw):
        selected_service_keys = list(SERVICE_HANDLERS.keys())
    else:
        selected_service_keys = [s for s in selected_services_raw if s in SERVICE_HANDLERS]

    if not selected_service_keys:
        raise ValueError("No valid services selected in the configuration.")

    # Create a base AWS session based on config/credentials
    session = create_aws_session(config)

    # Resolve regions
    regions_raw = list(_get_config_value(config.aws, "region", []) or [])
    if not regions_raw:
        raise ValueError("No regions configured under aws.region")

    # Build a map of available regions for each selected service dynamically
    available_regions_map: dict[str, set[str]] = {}
    for svc_key in selected_service_keys:
        try:
            available = session.get_available_regions(svc_key)
        except Exception:
            # If boto3 cannot determine regions for a service key, leave it unknown
            available = []
        available_regions_map[svc_key] = set(available)

    if any(r.lower() == "all" for r in regions_raw):
        # Union of regions supported by selected services (dynamic)
        union: set[str] = set()
        for svc_key in selected_service_keys:
            union.update(available_regions_map.get(svc_key, set()))
        if not union:
            raise ValueError(
                "Unable to resolve regions for selected services. Specify explicit aws.region or ensure AWS SDK can list regions."
            )
        regions = sorted(union)
    else:
        regions = regions_raw

    logger.info("Regions to process: %s", regions)
    logger.info("Selected services: %s", selected_service_keys)

    # Get all defined resources from dependency registry
    all_resources = get_all_resources()

    # Filter to only resources in selected services
    selected_resources = {(svc, res) for svc, res in all_resources if svc in selected_service_keys}

    if not selected_resources:
        raise ValueError("No resources available for selected services")

    logger.info("Selected resources: %s", selected_resources)

    # Allow custom worker count via config, fallback to reasonable default
    max_workers = getattr(getattr(config, "aws", None), "max_workers", None)
    if not isinstance(max_workers, int) or max_workers <= 0:
        max_workers = min(32, len(regions) * len(selected_resources))

    # Get resource-level max workers (controls parallelism within each resource handler)
    resource_max_workers = getattr(getattr(config, "aws", None), "resource_max_workers", 10)
    if not isinstance(resource_max_workers, int) or resource_max_workers <= 0:
        resource_max_workers = 10

    logger.info(
        "Parallelism config: max_workers=%d (stage-level), resource_max_workers=%d (per-resource)",
        max_workers,
        resource_max_workers,
    )

    # Execute using topological sort for dependency-aware ordering
    summary = _execute_with_topological_sort(
        session=session,
        selected_resources=selected_resources,
        regions=regions,
        available_regions_map=available_regions_map,
        dry_run=dry_run,
        max_workers=max_workers,
        resource_max_workers=resource_max_workers,
    )

    return summary
