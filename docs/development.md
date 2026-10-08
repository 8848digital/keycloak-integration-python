<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Development setup

This app follows the 8848 custom app setup
([project_base_template/custom_app_setup.md](https://github.com/8848digital/skills/blob/8848-skills/project_base_template/custom_app_setup.md)
in the skills repo). This page tells you how to work on the app with that setup.

## What the app contains

| File / folder | Purpose | Setup section |
| ------------- | ------- | ------------- |
| `pyproject.toml` | flit build data and the shared black / isort / ruff settings. | §2 |
| `.pre-commit-config.yaml` | Hooks: whitespace, YAML/JSON/TOML/AST checks, black, prettier, eslint, isort, flake8, max lines. | §3, §4.1 |
| `scripts/check_max_lines.py` | Fails a Python file with more than 250 lines. | §4.2 |
| `.eslintrc`, `.flake8` | JavaScript and Python lint rules. | §4.3, §4.4 |
| `commitlint.config.js` | Conventional Commits (`feat:`, `fix:`, `docs:` …). | §4.5 |
| `.editorconfig` | Tabs for Python/JS, 2 spaces for JSON, LF line ends. | §4.6 |
| `keycloak/commands/` | `bench --site <site> 8848-export-fixtures` (reads `custom_fixtures`). | §4.7 |
| `keycloak/utils/api_handlers/` | Standard API envelope, wired as `after_request` in `hooks.py`. | §4.9 |
| `.claude/skills/`, `CLAUDE.md`, `scripts/sync_skills.sh` | Agent skills and coding rules. | §4.10 |
| `.github/workflows/linters.yml` | CI: commit lint, pre-commit, Frappe semgrep rules, pip-audit. | §5 (version B) |
| `.semgrepignore` | Keeps repo tooling and the synced template out of semgrep. | — |

## 1. Get a bench with the app

```shell
bench init frappe-bench --frappe-branch version-15
cd frappe-bench
bench get-app erpnext --branch version-15
bench get-app keycloak https://github.com/8848digital/keycloak-integration-python
bench new-site keycloak.localhost --install-app erpnext
bench --site keycloak.localhost install-app keycloak
source env/bin/activate
```

## 2. Turn on pre-commit

In the app folder (`apps/keycloak`):

```shell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The hook runs on every commit. To check only some files:

```shell
git ls-files -- keycloak/keycloak_integration/sync/* | xargs pre-commit run --files
```

## 3. Run the tests

Use a separate test site; tests change data.

```shell
bench new-site keycloak-test.localhost --install-app erpnext
bench --site keycloak-test.localhost install-app keycloak
bench --site keycloak-test.localhost set-config allow_tests true
bench --site keycloak-test.localhost execute erpnext.setup.utils.before_tests   # once
bench --site keycloak-test.localhost run-tests --app keycloak
```

| Tests | Location |
| ----- | -------- |
| Login, SSO callback, logout, Admin API helpers | `keycloak/tests/test_sso_and_login.py` |
| Real-time events from the listener | `keycloak/tests/test_keycloak_events.py` |
| Role sync from login claims | `keycloak/tests/test_role_claims.py` |
| API entry point and security | `keycloak/tests/test_sdk_api.py` |
| Role Profile / Social Login Key / User Permission hooks | `keycloak/tests/test_customizations.py` |
| DocType behaviour | `keycloak/keycloak_integration/doctype/*/test_*.py` |

For an end-to-end check with a real Keycloak, follow
[keycloak-setup.md](./keycloak-setup.md) and
[erpnext-keycloak-setup.md](./erpnext-keycloak-setup.md), then run
`scripts/create-demo-data.py`.

## 4. Run the CI checks locally

```shell
pip install semgrep pip-audit
git clone --depth 1 https://github.com/frappe/semgrep-rules.git /tmp/frappe-semgrep-rules
semgrep scan --config /tmp/frappe-semgrep-rules/rules --config r/python.lang.correctness
pip-audit --desc on .
```

A `# nosemgrep` comment needs a "Reviewed:" comment above it that says why.

## 5. Work rules

- Raise a GitHub issue first; branch, commit with `Refs #<issue>`, open a
  PR that starts with `Closes #<issue>` (see `CLAUDE.md`).
- Commit messages follow Conventional Commits.
- Bump `__version__` in `keycloak/__init__.py`: minor for a database change
  (DocType, field, patch), patch for anything else.
- Every `.py`, `.js` and `.md` file starts with the copyright header.

## 6. Keep the skills up to date

```shell
scripts/sync_skills.sh --dry-run
scripts/sync_skills.sh
```

It updates `.claude/skills/`, `CLAUDE.md`, `keycloak/commands/` and
`keycloak/utils/api_handlers/`. It does not change `hooks.py` and does not commit.

## 7. CodeGraph (optional, per machine)

```shell
npm install -g @colbymchenry/codegraph
codegraph install      # in apps/keycloak; creates .codegraph/ (git-ignored)
```
