# Submission Guidelines

How to submit your contributions.
## Quick Steps

1. Fork the repository
2. Create feature branch: `git checkout -b feat-add-lambda`
3. Make changes following [Code Standards](./code-standards.md)
4. Run quality checks: `mise run fmt`, `mise run lint`, `mise run test`
5. Commit with conventional format: `feat(lambda): add function cleanup`
6. Push and create pull request
## Branch Naming

Format: `<type>-<description>`

Types:
- `feat` : New feature
- `fix` : Bug fix
- `docs` : Documentation
- `test` : Tests
- `refactor` : Code refactoring

Examples:
- `feat-add-lambda-support`
- `fix-volume-deletion-error`
- `docs-update-testing-guide`
## Commit Format

Use Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:

```bash
git commit -m "feat(ec2): add EBS volume cleanup

- Implement catalog_volumes() function
- Implement cleanup_volumes() with parallel execution
- Add comprehensive tests

Resolves #42"
```

```bash
git commit -m "fix(s3): handle versioned bucket deletion

Fixes #56"
```
## Pull Request

**Title:** Same format as commit message

**Description:**
- What you changed
- Why you changed it
- How to test it
- Related issues (Fixes #123)
## Review Process

1. Automated checks run (tests, linting)
2. Maintainer reviews code
3. Address feedback if requested
4. PR merged once approved
## After Merge

Update your fork:
```bash
git checkout main
git pull upstream main
git push origin main
```

Delete feature branch:
```bash
git branch -d feat-add-lambda
git push origin --delete feat-add-lambda
```
## Getting Help

- GitHub Issues for bugs
- GitHub Discussions for questions
- PR comments for review feedback
## Next Steps

- [Adding a Service](./adding-service.md) : Create service handler
- [Adding Subresources](./adding-subresources.md) : Add resources
- [Testing Guide](./testing.md) : Write tests
