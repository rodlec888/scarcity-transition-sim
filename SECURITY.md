# Security policy

## Reporting a vulnerability

Please do not report security vulnerabilities in public issues.

Report them privately through GitHub: open the repository's **Security** tab and choose
**Report a vulnerability**, or go directly to
[the private reporting form](https://github.com/rodlec888/scarcity-transition-sim/security/advisories/new).
Only the maintainer can read the report.

Please include:

- what the vulnerability is and where it is (file, function or dependency);
- the steps or input that trigger it;
- what an attacker could achieve with it.

You can expect an acknowledgement within 7 days. Once a fix is available, the report is
published as a GitHub security advisory, with credit to the reporter unless they prefer
otherwise.

## Supported versions

This is a research codebase with no tagged releases. Security fixes are made on the `main`
branch only.

## Scope

In scope:

- the code in this repository, in particular the handling of the xAI API key (read from a
  local `.env` file, never committed) and the parsing of model responses into the fixed
  action vocabulary;
- the pinned dependency versions in `uv.lock`;
- the GitHub Actions workflows in `.github/workflows/`.

Out of scope: vulnerabilities in the xAI API itself or in third-party packages. Please
report those to their maintainers. Known vulnerabilities in this repository's dependencies
are tracked through Dependabot security updates.
