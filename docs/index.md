---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "Cost Cutter"
  #   text: "A kill-switch for AWS"
  tagline: "A kill-switch for AWS"
  actions:
    - theme: brand
      text: What is CostCutter?
      link: /guide/what-is-costcutter
    - theme: alt
      text: Configure It
      link: /guide/config-reference
    - theme: alt
      text: GitHub
      link: https://github.com/HYP3R00T/costcutter

features:
  - icon: ⚡
    title: Fast AWS Resource Cleanup
    details: Scan and clean up EC2 instances, Lambda functions, and more with a single command. Supports dry-run mode for safe testing.
  - icon: 🛠️
    title: Layered Configuration
    details: Merge defaults, home overrides, explicit files, environment variables, and CLI flags without boilerplate.
  - icon: 📊
    title: Live Terminal View
    details: Watch events stream in through a Rich powered table and review a summary once orchestration completes.
  - icon: 🔒
    title: Credential Flexibility
    details: Reuse profiles, shared credential files, or explicit keys while keeping secrets out of the repository.
---
