# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please follow these steps:

1. **Do not create a public issue.**
2. Raise an [issue](https://github.com/austinnoronha/etl_with_dagster/issues) in github, with details of the vulnerability.
3. Include as much information as possible to help us understand and address the issue quickly (e.g., steps to reproduce, affected files, potential impact).
4. We will acknowledge receipt within 2 business days and provide a timeline for a fix if appropriate.

## Supported Versions

| Version | Supported          |
| ------- | ----------------- |
| 1.x.x   | :white_check_mark:|

## Security Best Practices
- Do not commit secrets (passwords, API keys, etc.) to the repository.
- Use environment variables and `.env` files (add `.env` to `.gitignore`).
- Keep dependencies up to date and monitor for vulnerabilities (Dependabot is enabled).
- Use branch protection and require PR reviews for all merges.

## Contact
For any security concerns, please contact the maintainer at via [issue](https://github.com/austinnoronha/etl_with_dagster/issues). 