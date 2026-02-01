# Quick Start

Get from zero to your first dry-run in under 2 minutes.

## 1. Set AWS Credentials

CostCutter needs access to your AWS account. Choose one method:

=== "AWS Profile"

    ```bash
    export AWS_PROFILE=dev
    ```

=== "Access Keys"

    ```bash
    export AWS_ACCESS_KEY_ID=AKIA...
    export AWS_SECRET_ACCESS_KEY=...
    ```

## 2. Run a Dry-Run

Preview what would be deleted **without making any changes**:

```bash
costcutter --dry-run
```

CostCutter scans your configured regions and services, showing a live table of discovered resources.

## 3. Review the Output

**CostCutter - Summary (DRY-RUN)**

| Service | Resource | Action | Count |
|---------|----------|--------|-------|
| ec2 | instance | catalog | 3 |
| ec2 | volume | catalog | 5 |
| s3 | bucket | catalog | 2 |

## 4. Execute (When Ready)

Once you've reviewed and are confident:

```bash
costcutter --no-dry-run
```

!!! danger "This is Irreversible"

    Running without `--dry-run` **permanently deletes resources**. There is no undo.

## Common Options

### Target Specific Regions

```bash
costcutter --dry-run --regions us-east-1,eu-west-1
```

### Target Specific Services

```bash
costcutter --dry-run --services ec2,s3
```

### Use a Config File

```bash
costcutter --config costcutter.yaml
```

## What's Next?

| Topic | Description |
|-------|-------------|
| [Configuration](../configuration/index.md) | Customize behavior with config files |
| [Services](../services/index.md) | See what resources each service deletes |
| [How It Works](../concepts/how-it-works.md) | Understand the deletion order and safety mechanisms |
