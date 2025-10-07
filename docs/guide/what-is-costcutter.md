# What is CostCutter?

> [!DANGER]
> CostCutter will delete **all resources** in your AWS account, across all configured regions and services, with no discrimination or recovery. Never use it on production.

CostCutter is a powerful AWS cleanup tool designed for aggressive resource deletion. It does **not** monitor usage or costs. When you run CostCutter, it will immediately delete all resources specified in your config file, across all listed regions and services. There is no undo.

You can use CostCutter in two main ways:

- **CLI Mode:** Run `uvx costcutter` to instantly delete resources as configured.
- **Terraform/Lambda Mode:** Integrate with AWS SNS and Lambda. When an alert triggers (e.g., via AWS Budgets), CostCutter runs automatically and deletes everything as specified.

CostCutter is ideal for:

- 🚀 **Students** and experimenters who want a clean slate
- 💼 **Freelancers** who need to wipe test environments
- 🧪 **Homelabbers** and tinkerers
- 🌱 **Startups** building proofs-of-concept
- 🆓 **Free Tier Users** who want to avoid accidental charges

**Warning:** CostCutter is a destructive tool. It does not discriminate between critical and non-critical resources. Use only in non-production accounts where you are certain you want everything deleted.

---

CostCutter: The AWS kill-switch. When you need everything gone, instantly.
