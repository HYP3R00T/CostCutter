# Usage (Terraform)

How to operate and manage CostCutter after deploying with Terraform.

## Editing Configuration

- Update `lambda/config.yaml` to change budget thresholds, regions, or notification settings
- Run `terraform apply` again to update AWS resources

## Monitoring

- AWS Budget alerts trigger notifications via SNS
- Lambda executes automated cleanup or notifications as configured
- Check Lambda logs in AWS Console > Lambda > Monitor > Logs

## Common Operations

- **Change budget threshold:** Edit config and re-apply
- **Add/remove regions:** Update config and re-apply
- **Update notification emails:** Edit config and re-apply

## Troubleshooting

- Ensure IAM permissions are correct for Terraform and Lambda
- Check Terraform output for errors
- Review Lambda logs for execution issues

For more details, see [Troubleshooting & FAQ](/guide/troubleshooting).
