# Architecture

Understanding how CostCutter components work together.

---

_[Architectural diagram placeholder - will be added as SVG/PNG]_

---

## Core Components

### 1. Configuration Management (`conf/`)

**What it does:**
- Reads `config.yaml` for default settings
- Overrides with environment variables
- Validates settings using Pydantic models
- Provides configuration to all components

**Key file:** `conf/config.py`

**Important:** Uses Pydantic's `ConfigDict` for validation. All settings are type-checked.

---

### 2. Service Registry (`services/`)

**What it does:**
- Each AWS service (EC2, S3, Lambda) is a directory
- Contains subresource handlers (e.g., `ec2/instances.py`, `ec2/volumes.py`)
- All handlers follow the **three-function pattern** (mandatory)

**The Three-Function Pattern:**

```python
def catalog_<resource>(session, region, reporter):
    """List available resources."""
    # Returns list of resource IDs or names

def cleanup_<resource>(session, region, resource_id, reporter, dry_run):
    """Delete single resource."""
    # Handles single resource deletion

def cleanup_<resources>(session, region, reporter, dry_run=True):
    """Batch delete with parallel execution."""
    # Uses ThreadPoolExecutor for parallel cleanup
```

**Registration in `__init__.py`:**

```python
SERVICE_REGISTRY["ec2"] = {
    "instances": {"catalog": catalog_instances, "cleanup": cleanup_instances},
    "volumes": {"catalog": catalog_volumes, "cleanup": cleanup_volumes},
    # ... more subresources
}
```

**Execution order matters:** Subresources are executed in the order they appear in `SERVICE_REGISTRY`. For EC2, instances must be deleted before volumes.

---

### 3. Orchestrator (`orchestrator.py`)

**What it does:**
- Reads configuration and determines which services/regions to process
- Creates AWS sessions with credentials
- Spawns worker threads for parallel execution
- Calls service handlers for each (region, service) pair
- Aggregates results from all threads

**Key insight:** Uses `ThreadPoolExecutor` to run multiple services/regions in parallel for speed.

---

### 4. Reporter (`reporter.py`)

**What it does:**
- Thread-safe event tracking (uses locks)
- Records every cleanup action: service, region, resource type, resource ID, status
- Provides real-time events to CLI for display
- Exports all events to CSV report

**Thread safety is critical:** Multiple handlers run in parallel and all record events simultaneously. Reporter uses `threading.Lock()` to prevent race conditions.

---

### 5. Logger (`logger.py`)

**What it does:**
- File-based structured logging to `logs/costcutter.log`
- Log rotation (10MB max per file, 5 backup files)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Used by all components for debugging

**Not for events:** Logger is for debugging/diagnostics. Events go through Reporter for user-facing display.

---

### 6. CLI (`cli.py`)

**What it does:**
- Typer-based command-line interface
- Rich library for live terminal UI with event tables
- Shows last 10 events in real-time
- Displays summary statistics
- Exports CSV report at end

---

## Execution Flow

1. **User runs CLI command:**
   ```bash
   costcutter destroy --region us-east-1 --service ec2
   ```

2. **CLI validates arguments** and calls `main.py`

3. **Main entry point:**
   - Loads configuration from `config.yaml`
   - Overrides with CLI arguments
   - Creates AWS session
   - Calls orchestrator

4. **Orchestrator:**
   - Resolves which services and regions to process
   - Spawns worker threads for each (region, service)
   - Each thread calls the service handler (e.g., `cleanup_ec2()`)

5. **Service handler (e.g., `cleanup_ec2()`):**
   - Iterates through registered subresources in order
   - For each subresource:
     - Calls `catalog_<resource>()` to list resources
     - Calls `cleanup_<resources>()` to delete in parallel
   - Each deletion records an event via Reporter

6. **Reporter:**
   - Collects events from all threads
   - Provides events to CLI for live display
   - Exports to CSV at end

7. **CLI displays:**
   - Live event table (updates in real-time)
   - Summary statistics (resources deleted, failed, skipped)
   - CSV export location

---

## Key Design Patterns

### Service Auto-Discovery

Services are discovered automatically from `SERVICE_REGISTRY`. No hardcoding in orchestrator.

### Convention Over Configuration

Subresources don't need config entries. If registered in `SERVICE_REGISTRY`, they run when the parent service is enabled.

### Parallel Execution at Two Levels

1. **Service/Region level:** Orchestrator runs multiple (region, service) combinations in parallel
2. **Resource level:** Each subresource handler uses `ThreadPoolExecutor` to delete multiple resources in parallel

### Thread-Safe Reporter

All handlers call `reporter.record()` from different threads. Reporter uses locks to prevent data corruption.

---

## Important Implementation Details

### Execution Order in Services

**EC2 example:** Must delete instances before volumes (volumes are attached to instances).

In `services/ec2/__init__.py`:
```python
SERVICE_REGISTRY["ec2"] = {
    "instances": {...},      # First
    "volumes": {...},        # Second
    "snapshots": {...},      # Third
    # Order matters!
}
```

### Dry-Run Mode

All cleanup functions accept `dry_run` parameter:
- `True` (default): Catalog only, no deletion
- `False`: Actually delete resources

Reporter marks dry-run events differently for display.

### Error Handling

Handlers should catch exceptions and report failures via Reporter. Orchestrator continues even if one handler fails.

---

## Component Dependencies

- **Configuration** → Used by Orchestrator and all handlers
- **Orchestrator** → Calls Service Handlers
- **Service Handlers** → Call Resource Handlers, use Reporter and Logger
- **Resource Handlers** → Use Reporter for events, Logger for debugging
- **Reporter** → Standalone, thread-safe
- **Logger** → Standalone, file-based
- **CLI** → Calls Orchestrator, displays Reporter events

---

## Next Steps

- [Code Structure](./code-structure.md) : Detailed file organization
- [Adding a Service](./adding-service.md) : Create new service handlers
- [Adding Subresources](./adding-subresources.md) : Add resources to existing services
