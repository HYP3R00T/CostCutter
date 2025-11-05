# What is CostCutter?

> [!DANGER]
> CostCutter deletes resources. Always start with a dry run and restrict usage to disposable AWS accounts.

CostCutter is a Python-based CLI for reclaiming AWS spend quickly. It enumerates the services you enable, records what it finds in a Rich-powered table, and deletes every matching resource when you opt out of dry run mode.

## Why people use it

- 🚀 **Students and tinkerers** who want a clean slate after labs or experiments
- 💼 **Consultants and freelancers** who reset test environments between engagements
- 🌱 **Startups** protecting free-tier budgets by purging unused infrastructure
- 🧪 **Engineering teams** who need a repeatable teardown tool for pre-production accounts

## How it runs

- **One CLI:** invoke `costcutter` (or `uvx costcutter`) from your shell or automation.
- **Layered configuration:** defaults, home overrides, explicit files, environment variables, and CLI flags merge into a single runtime config.
- **Threaded orchestration:** `(region, service)` pairs fan out in a thread pool so large accounts finish faster.

## Safety model

- Dry run is enabled by default. Handlers either set `DryRun=True` on AWS APIs or short-circuit before deletion.
- Verbose reporting streams to the terminal and can optionally be written to CSV for auditing.
- Disabling dry run (`--no-dry-run`) irrevocably deletes the resources targeted by the handlers. There is no undo.

Ready to try it? Continue with the [Getting Started](./getting-started.md) guide and review [Supported Services & Resources](./supported-services.md) for the latest coverage.
