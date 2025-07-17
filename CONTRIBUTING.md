# Contributing to etl_with_dagster

Thank you for your interest in contributing! We welcome all contributions that improve the project.

## How to Contribute

1. **Fork the repository** and clone your fork locally.
2. **Create a new branch** for your feature or bugfix:
   ```sh
   git checkout -b my-feature
   ```
3. **Make your changes** and add tests as appropriate.
4. **Run tests locally** to ensure nothing is broken:
   ```sh
   poetry install
   pytest
   ```
5. **Commit your changes** with a clear, descriptive message.
6. **Push to your fork** and open a Pull Request (PR) against the `development` branch.
7. **Describe your changes** in the PR and reference any related issues.
8. **Participate in the review process** and make any requested changes.

## Code Style
- Use [Black](https://black.readthedocs.io/en/stable/) for code formatting.
- Use [isort](https://pycqa.github.io/isort/) for import sorting.
- Lint with [Ruff](https://docs.astral.sh/ruff/).
- Write clear, concise docstrings for all public functions and classes.

## Pull Request Requirements
- All tests must pass (CI will run them automatically).
- New features or fixes should include relevant tests.
- PRs should be focused and not mix unrelated changes.
- At least one review is required before merging.

## Best Practices
- Do not commit secrets or sensitive data.
- Use environment variables for configuration.
- Keep dependencies up to date.
- Document any new features or changes in the README if needed.

## Reporting Issues
- Use the GitHub Issues tab to report bugs or request features.
- Provide as much detail as possible (steps to reproduce, environment, etc.).

## Community
- Be respectful and constructive in all communications.
- We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

Thank you for helping make this project better! 