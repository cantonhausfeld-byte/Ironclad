# Ironclad

## Operations

### Promote & Smoke
- Manual: **Actions → Promote & Smoke → Run workflow** (fill `RUN_A` baseline and `RUN_B` challenger).
- Artifacts: check the run’s **Artifacts** for `smoke-*.md` and `smoke-*.json`.

### Nightly Smoke
- Runs daily ~2:15am ET on `PROFILE=prod`.
- Posts to Slack if `SLACK_WEBHOOK` is set.
- Artifacts retained for 14 days.

### Local
```bash
make smoke-prod                 # prod end-to-end smoke
PROFILE=prod make nightly-local # same script as nightly job
```
