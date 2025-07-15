
# Releasing

This document outlines the process for creating new releases.

## Tagging & Release Workflow

- **Tag Pattern**: Tags MUST follow the `v<MAJOR>.<MINOR>.<PATCH>` pattern (e.g., `v1.3.1`). We use [Semantic Versioning](https://semver.org/).

- **GitHub Release**: For every new version tag, a corresponding GitHub Release MUST be created. The release notes SHOULD include a changelog section detailing the changes in that release.

- **Stable Tag (Optional)**: A lightweight `stable` tag MAY be used to point to the latest stable release. This tag is updated to point to the new version with each release.

- **Automation**: The GitHub CLI (`gh`) can be used to automate this process:

  ```bash
  # Example: Create a new release
  gh release create v1.3.1 --title "v1.3.1" --notes-file docs/CHANGELOG_SEGMENT.md

  # Example: Update the optional stable tag
  git tag -f stable v1.3.1
  git push origin stable --force
  ```

- **CI/CD**: CI/CD pipelines SHOULD be configured to trigger on the creation of new version tags. It is recommended to use annotated tags (`git tag -a`) for releases to include metadata, which can be useful for CI/CD workflows.
