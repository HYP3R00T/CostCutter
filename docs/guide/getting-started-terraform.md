# Getting Started (Terraform)

There is no Terraform module packaged with CostCutter today. Instead, you can call the CLI from Terraform to run a cleanup as part of a workflow. This guide walks through a minimal setup.

## Prerequisites

- Terraform 1.6 or newer installed locally
- Access to AWS credentials compatible with the CostCutter CLI
- A CostCutter configuration file committed alongside your Terraform code

## 1. Prepare the configuration file

Copy the YAML snippet from [Getting Started](/guide/getting-started.md) into your Terraform module directory (for example `config/costcutter.yaml`). Ensure the regions and services match the AWS account you plan to clean up.

## 2. Install the CLI in your automation environment

The machine that runs `terraform apply` must also have the `costcutter` command available. Using uv:

```sh
uv tool install costcutter
```

Include this step in your CI setup script if you run Terraform from a pipeline.

## 3. Wire CostCutter into Terraform

Add a `null_resource` with a `local-exec` provisioner to call the CLI:

```hcl
resource "null_resource" "costcutter_cleanup" {
  provisioner "local-exec" {
    command = "uvx costcutter --dry-run --config ${path.module}/config/costcutter.yaml"
  }
}
```

Tips:

- Keep the command in dry run mode until you review the output
- Inject overrides with environment variables if you need per-environment tweaks (example: `COSTCUTTER_AWS__PROFILE`)
- Use Terraform variables to control whether the provisioner runs during a particular apply

## 4. Promote to destructive mode

After validating the dry run output, change the command to use `--no-dry-run`. You may also want to add safeguards such as confirmation variables or pipeline approvals.

## 5. Observe the run

Terraform will stream the Rich output into its own logs. Capture the output for audit purposes and collect the CSV report from the path defined in your configuration.

## Troubleshooting

- If the provisioner fails, re-run the same command outside Terraform to inspect the error directly
- Verify that the AWS credentials visible to Terraform also allow the CostCutter CLI to list and delete resources
- Review [Usage (Terraform)](/usage-terraform.md) and [Troubleshooting](/guide/troubleshooting.md) for additional integration pointers
