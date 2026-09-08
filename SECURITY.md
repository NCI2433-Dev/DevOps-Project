## Reporting security issues

If you discover a security vulnerability in this project, please report it privately so it can be addressed.

Preferred steps:

1. Do not create a public issue with sensitive data.
2. Email the repository owner with reproduction steps and any proof-of-concept.

## Secret scanning and rotation

Before publishing this repository, run a repo-history secret scan and remove sensitive files:

Recommended tools:

- gitleaks: https://github.com/zricethezav/gitleaks
- truffleHog: https://github.com/trufflesecurity/truffleHog
- git-secrets: https://github.com/awslabs/git-secrets

Example gitleaks command:

```bash
gitleaks detect --source . --report-path gitleaks-report.json
```

If you find secrets in the history, rotate them immediately and remove them from history using `git filter-repo` or BFG.

## Local cleanup steps

Before pushing to GitHub, run the following to avoid committing local environments and DB files:

```bash
git rm --cached db.sqlite3 || true
rm -f db.sqlite3
git rm -r --cached venv .venv || true
echo ".venv/\nvenv/\ndb.sqlite3\n.env\n.env.*" >> .gitignore
git add .gitignore
git commit -m "Ignore local env and DB files"
```
