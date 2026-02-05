# Caveats / Known Design Decisions

- In an included `mkdocs.yml`, you cannot have `!include`. It is only supported in the root `mkdocs.yml`

- **Anchor-based inclusion alias collision risk**: When using anchor syntax (`!include path/to/mkdocs.yml#SectionName`), the generated alias follows the pattern `{site_name}-{SectionName}`. This can create a collision if you also include a separate `mkdocs.yml` file whose `site_name` exactly matches this generated alias.

  **Example collision scenario:**
  ```yaml
  # File A: docs/team-a/mkdocs.yml
  site_name: MyDocs
  nav:
    - Guides:
      - Getting Started: getting-started.md

  # File B: docs/team-b/mkdocs.yml
  site_name: MyDocs-Guides
  nav:
    - Overview: overview.md

  # Root mkdocs.yml - This will cause a collision!
  nav:
    - Team A Guides: "!include docs/team-a/mkdocs.yml#Guides"  # alias: "MyDocs-Guides"
    - Team B: "!include docs/team-b/mkdocs.yml"                # alias: "MyDocs-Guides"
  ```

  **Workaround:** Ensure your `site_name` values don't match the pattern `{OtherSiteName}-{SectionName}` when using anchor-based includes. The collision will be detected at build time with a clear error message listing all registered aliases.
