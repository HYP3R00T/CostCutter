# Getting Started (Terraform)

This guide will help you deploy CostCutter using the Terraform solution for automated AWS cost control.

## Prerequisites

- AWS account with permissions for Budget, SNS, Lambda, IAM
- Terraform installed ([Download](https://www.terraform.io/downloads.html))
- Git installed

## Steps

1. **Clone the Terraform repository:**
   ```sh
   git clone https://github.com/HYP3R00T/aws-costcutter.git
   cd aws-costcutter
   ```
2. **Edit the configuration file:**
   - Open `lambda/config.yaml` and adjust settings for your environment (regions, budget thresholds, notification emails, etc).
3. **Initialize Terraform:**
   ```sh
   terraform init
   ```
4. **Apply the infrastructure:**
   ```sh
   terraform apply
   ```
   - Review the plan and confirm to proceed.
5. **What gets created?**
   - AWS Budget with alert
   - SNS topic for notifications
   - Lambda function for automated actions
   - IAM roles and permissions

## Next Steps

- Monitor your AWS account for alerts and automated actions
- Update config and re-apply as needed

For advanced usage, see the [Usage (Terraform)](/usage-terraform) page.
