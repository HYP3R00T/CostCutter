"""AWS resource dependency graph for safe deletion ordering.

This module defines a directed acyclic graph (DAG) of AWS resources, specifying
which resources must be deleted before others. Used by the orchestrator to
compute a topologically-sorted deletion order that respects AWS constraints.

Dependencies are organized following the 6-phase AWS deletion sequence:
  1. ElasticBeanstalk environments (cascades EC2 instances, security groups, load balancers)
  2. ElasticBeanstalk applications (only after environments deleted)
  3. EC2 instances (terminate first, then other EC2 resources become available)
  4. EBS volumes (require instances terminated; can be deleted in parallel with snapshots)
  5. EBS snapshots (independent; can delete anytime)
  6. Elastic IPs (require instances terminated and disassociation)
  7. EC2 key pairs (independent; no dependencies)
  8. EC2 security groups (require instances/ENIs removed; requires rule cleanup)
  9. S3 buckets (requires objects/versions deleted)

Within-service dependencies:
  - elasticbeanstalk: environments must be terminated before applications deleted
  - ec2: instances first, then volumes/elastic_ips/security_groups in parallel
  - s3: objects must be deleted before bucket

Cross-service dependencies:
  - ec2 security_groups depends on elasticbeanstalk environments (EB auto-deletes SGs)
  - Any EC2 resource region depends on elasticbeanstalk (EB cascade affects EC2)

Format:
  Key: (service, resource_type) tuple
  Value: List of (service, resource_type) tuples that must be deleted first
"""

# Type alias for resources: (service_name, resource_type)
type ResourceKey = tuple[str, str]

# Dependency mapping: resource -> list of dependencies (must be deleted before this resource)
RESOURCE_DEPENDENCIES: dict[ResourceKey, list[ResourceKey]] = {
    # Phase 1: ElasticBeanstalk environments (must come before applications and EC2 resources)
    ("elasticbeanstalk", "environments"): [],  # No dependencies; runs first
    # Phase 2: ElasticBeanstalk applications (depends on environments)
    ("elasticbeanstalk", "applications"): [("elasticbeanstalk", "environments")],
    # Phase 3: EC2 instances (independent; no AWS resource dependencies)
    ("ec2", "instances"): [],
    # Phase 4: EBS volumes (depends on instances being terminated)
    ("ec2", "volumes"): [("ec2", "instances")],
    # Phase 5: EBS snapshots (independent; no dependencies)
    ("ec2", "snapshots"): [],
    # Phase 6: Elastic IPs (depends on instances being terminated to ensure disassociation)
    ("ec2", "elastic_ips"): [("ec2", "instances")],
    # Phase 7: EC2 key pairs (independent; no dependencies)
    ("ec2", "key_pairs"): [],
    # Phase 8: Security groups (depends on instances and EB being removed)
    ("ec2", "security_groups"): [
        ("ec2", "instances"),
        ("elasticbeanstalk", "environments"),  # EB auto-deletes its SGs; we clean up remaining
    ],
    # Phase 9: S3 buckets (depends on objects being deleted)
    ("s3", "buckets"): [],  # Object deletion is internal to bucket cleanup
}


def validate_dependency_graph() -> None:
    """Validate that the dependency graph is acyclic and all dependencies are valid resources.

    Raises:
        ValueError: If a cycle is detected or an invalid resource dependency is found.
    """
    valid_resources = set(RESOURCE_DEPENDENCIES.keys())

    for resource, dependencies in RESOURCE_DEPENDENCIES.items():
        for dep in dependencies:
            if dep not in valid_resources:
                raise ValueError(
                    f"Invalid dependency: {resource} depends on {dep}, "
                    f"but {dep} is not a valid resource in the registry."
                )

    # Check for cycles using a simple DFS (topological sort will also detect this)
    visited: set[ResourceKey] = set()
    rec_stack: set[ResourceKey] = set()

    def has_cycle(node: ResourceKey) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in RESOURCE_DEPENDENCIES.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.discard(node)
        return False

    for resource in valid_resources:
        if resource not in visited and has_cycle(resource):
            raise ValueError(f"Circular dependency detected in resource dependency graph involving {resource}")


def get_resource_dependencies(resource: ResourceKey) -> list[ResourceKey]:
    """Get the list of resources that must be deleted before the given resource.

    Args:
        resource: (service, resource_type) tuple

    Returns:
        List of (service, resource_type) tuples that must be deleted first
    """
    return RESOURCE_DEPENDENCIES.get(resource, [])


def get_all_resources() -> set[ResourceKey]:
    """Get all defined resources in the dependency graph.

    Returns:
        Set of (service, resource_type) tuples
    """
    return set(RESOURCE_DEPENDENCIES.keys())


# Validate graph on module load
try:
    validate_dependency_graph()
except ValueError as e:
    raise RuntimeError(f"Invalid dependency graph configuration: {e}") from e
