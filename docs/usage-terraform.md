# Usage (Terraform)

CostCutter ships as a Python package and does not include a Terraform module. You can still orchestrate cleanups from Terraform by invoking the CLI from Terraform resources.

## Current Status

- No managed Terraform module or Lambda deployment is bundled with this repository
- All automation relies on the same CLI options documented in [CostCutter CLI](/usage-cli.md)

## Triggering the CLI from Terraform

### Example `null_resource`

```hcl
resource "null_resource" "costcutter_cleanup" {
	provisioner "local-exec" {
		command = "uvx costcutter --no-dry-run --config ${path.module}/costcutter.yaml"
		environment = {
			COSTCUTTER_LOGGING__LEVEL = "INFO"
		}
	}
}
```

Key points:

- Package installation is your responsibility (for example via `uv tool install costcutter` or a virtual environment)
- Provide an explicit config file that lives alongside your Terraform code
- Use `--dry-run` while validating infrastructure changes and switch to `--no-dry-run` only when you intend to delete resources

## Managing Configuration Files

- Commit a baseline YAML, TOML, or JSON file to your Terraform module
- Populate secrets or overrides with Terraform variables and render them using the [`templatefile`](https://developer.hashicorp.com/terraform/language/functions/templatefile) function when required
- Keep the file path stable so the CLI can be invoked in plan and apply stages consistently

## Monitoring and Logs

- CLI executions write logs to the directory configured in `logging.dir`
- Rich output appears in the Terraform apply log; capture it for later review if you use automation
- CSV exports are saved to the path configured under `reporting.csv.path`

## Troubleshooting Terraform Automations

- Ensure the environment running Terraform has AWS credentials usable by CostCutter
- Surface CLI failures by checking Terraform provisioner exit codes and logs
- Run the same command locally to reproduce issues, then consult [Troubleshooting](/guide/troubleshooting.md) for deeper diagnostics
