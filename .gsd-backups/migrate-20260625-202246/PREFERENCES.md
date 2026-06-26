---
version: 1
mode: solo
git:
  isolation: worktree
  main_branch: main
  auto_push: false
parallel:
  enabled: true
  max_workers: 2
  merge_strategy: per-slice
  auto_merge: auto
  worker_model: claude-haiku-4-5
slice_parallel:
  enabled: true
  max_workers: 2
reactive_execution:
  enabled: true
  max_parallel: 3
  isolation_mode: same-tree
verification_commands:
  - npm test
  - npm run build
  - pytest
---
# GSD Skill Preferences

See `~/.gsd/agent/extensions/gsd/docs/preferences-reference.md` for full field documentation and examples.
