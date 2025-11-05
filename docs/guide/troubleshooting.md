# Troubleshooting and FAQ

Common issues encountered when running CostCutter and how to resolve them.

## Common issues

### Permission errors

**Symptoms:** AWS responses such as `AccessDenied`, `UnauthorizedOperation`, or `OperationNotPermitted`.

**Fixes:**

- Ensure the credentials cover the AWS APIs used by the enabled services (for example, `ec2:Describe*`/`ec2:Delete*` for EC2, `s3:List*`/`s3:Delete*` for S3, and the equivalent actions for any additional handlers you add)
- Grant permissions on the account or resource scope that matches your cleanup target
- Capture the failing API call from the log file to build a least-privilege policy for future runs

### Missing credentials

**Symptoms:** `NoCredentialsError`, `Unable to locate credentials`, or authentication prompts from boto3.

**Fixes:**

1. Populate the AWS section of the configuration file:

   ```yaml
   aws:
     profile: cleanup
     credential_file_path: ~/.aws/credentials
   ```

2. Override via environment variables before invoking the CLI:

   ```sh
   export COSTCUTTER_AWS__PROFILE=cleanup
   export COSTCUTTER_AWS__CREDENTIAL_FILE_PATH=~/.aws/credentials
   costcutter --dry-run
   ```

3. Fall back to standard environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) if you prefer ephemeral credentials

### No resources discovered

**Symptoms:** Live table and summary remain empty during a dry run.

**Fixes:**

- Confirm the regions listed under `aws.region` actually contain the resources you expect
- Make sure `aws.services` includes the service identifiers you want to process; the CLI logs and skips names without registered handlers
- Check the log file for authentication or throttling errors that prevented enumeration

### Rate limiting

**Symptoms:** `ThrottlingException` or `RequestLimitExceeded` messages in the log.

**Fixes:**

- Reduce concurrency by lowering `aws.max_workers`
- Limit the number of regions or services per run
- Re-run the command after a short pause to allow AWS rate limits to reset

### Volumes still in use

**Symptoms:** EC2 volume deletions fail with `VolumeInUse`.

**Fixes:**

- Verify that the corresponding instance termination succeeded during the same run
- Re-run CostCutter; once instances vanish the volumes become available and the handler removes them
- As a last resort, detach the volume manually (`aws ec2 detach-volume --volume-id vol-123`) and run CostCutter again

### Buckets not empty

**Symptoms:** S3 bucket deletions fail because the bucket still contains objects.

**Fixes:**

- Ensure the credentials allow `s3:DeleteObjectVersion` for versioned buckets
- Re-run CostCutter so it can resume deletion from the point it stopped; the reporter keeps track of progress
- Inspect CloudTrail or S3 access logs to confirm no other process is adding new objects during the cleanup

### Dry run shows no events

**Symptoms:** Dry run completes without listing resources even though they exist.

**Fixes:**

- Verify that dry run was not disabled unintentionally; destructive runs remove resources so subsequent dry runs find nothing
- Check the log file for errors encountered while cataloguing resources
- Confirm the reporter CSV (if enabled) to ensure events are not being recorded under unexpected service or region names

## Frequently asked questions

### Can I undo deletions?

No. When you run with `--no-dry-run` the resources are deleted permanently. Always perform a dry run first:

```sh
costcutter --dry-run --config ./costcutter.yaml
```

### How do I target multiple regions?

Add them to the configuration file:

```yaml
aws:
  region:
    - us-east-1
    - eu-west-1
```

Or supply an environment variable on the fly:

```sh
export COSTCUTTER_AWS__REGION="[us-east-1, eu-west-1]"
costcutter --dry-run
```

### Can I exclude specific resources?

Not today. CostCutter deletes every resource of the enabled types. To scope work:

1. Limit the regions or services in the configuration
2. Fork the repository and add filtering logic inside the relevant handler

### How long does a run take?

It depends on resource count and network latency. Rough estimates from testing:

- Small dev account (dozens of resources): under a minute
- High volume EBS or S3 cleanups: several minutes while AWS processes deletions

### What happens when a handler fails?

The orchestrator records the failure, logs the exception, and continues processing other tasks. Re-running CostCutter after fixing the underlying issue is safe; skipped resources are re-evaluated.

### Does CostCutter work across multiple AWS accounts?

Each run operates on one account. To clean multiple accounts, invoke the CLI separately with different profiles or credentials. Automation scripts can loop through accounts by updating `COSTCUTTER_AWS__PROFILE` before each invocation.

### Can I schedule runs?

Yes. Examples:

- `cron`: `0 2 * * * /usr/local/bin/costcutter --no-dry-run --config /etc/costcutter.yaml`
- CI/CD: call the CLI from pipelines after validation
- Terraform: see [Usage (Terraform)](/usage-terraform.md)

Always keep dry run enabled for scheduled jobs unless you have tight safeguards.

### How can I debug stubborn issues?

1. Enable debug logging:

   ```yaml
   logging:
     level: DEBUG
   ```

2. Inspect the latest log file in `logging.dir`

3. Open the CSV report to see the recorded status of each resource

4. Use AWS CloudTrail to confirm which API calls succeeded or failed

### How do I contribute new handlers?

Follow [Adding a Service](../contributing/adding-service.md) and [Adding Subresources](../contributing/adding-subresources.md). The orchestrator picks up new entries from `SERVICE_HANDLERS` automatically.

## Getting help

- Report bugs or feature requests on [GitHub Issues](https://github.com/HYP3R00T/costcutter/issues)
- Ask questions or share ideas on [GitHub Discussions](https://github.com/HYP3R00T/costcutter/discussions)
- Keep exploring the docs: [How It Works](./how-it-works.md), [Supported Services](./supported-services.md), and [Configuration Reference](./config-reference.md)
