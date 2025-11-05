# Supported Services

CostCutter is built to handle multiple AWS services. The `aws.services` list in your configuration controls which handlers run, and contributors can extend the catalog by registering additional cleanup functions.

## Current coverage

### EC2 (Elastic Compute Cloud)

| Resource type | What the handler does | Why it matters |
| ------------- | --------------------- | -------------- |
| Instances | Terminates all instances in the configured regions. | Stops ongoing compute charges. |
| Volumes | Deletes unattached EBS volumes. | Removes storage fees from orphaned disks. |
| Snapshots | Deletes snapshots owned by the account. | Shrinks long term backup costs. |
| Elastic IPs | Releases Elastic IP allocations (disassociates first when needed). | Avoids idle address charges. |
| Key pairs | Deletes EC2 key pairs. | Removes unused credentials. |
| Security groups | Deletes non-default security groups. | Keeps the account tidy after tearing down instances. |

Execution order: instances → volumes → snapshots → elastic IPs → key pairs → security groups. The sequence avoids dependency issues during teardown.

### S3 (Simple Storage Service)

| Resource type | What the handler does |
| ------------- | --------------------- |
| Buckets | Empties all objects, aborts multipart uploads, and deletes the bucket. |

Versioned buckets are supported. Every object and delete marker is removed before the bucket itself is deleted when dry run is disabled.

## Extending coverage

- Register new services by adding `cleanup_<service>` functions to `SERVICE_HANDLERS` in `src/costcutter/orchestrator.py`
- Follow the [Adding a Service](../contributing/adding-service.md) and [Adding Subresources](../contributing/adding-subresources.md) guides for implementation details
- Update your configuration to include the new service name once the handler exists

Candidate services on the roadmap include Lambda, RDS, DynamoDB, CloudWatch, and more. Contributions are welcome—CostCutter is intentionally modular so the list above can keep growing.

## Verifying coverage

Run a dry run to see what would be deleted:

```sh
costcutter --dry-run --config ./costcutter.yaml
```

Every discovered resource is recorded in the live table, the summary, and the optional CSV report. Review the output before disabling dry run.

## Region selection

Regions are controlled through the configuration:

```yaml
aws:
  region:
    - us-east-1
    - eu-west-1
```

Use the special value `all` to expand to every region supported by the selected services:

```yaml
aws:
  region:
    - all
```

The CLI also accepts environment variables such as `COSTCUTTER_AWS__REGION="[us-east-1, eu-west-1]"` if you prefer not to edit files.

## Next steps

- Learn how orchestration ties these handlers together in [How It Works](./how-it-works.md)
- Review the configuration schema in [Configuration Reference](./config-reference.md)
- Contribute additional handlers by following [Adding a Service](../contributing/adding-service.md)
