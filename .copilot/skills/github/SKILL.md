---
name: github
description: "Explore GitHub repositories and safely create or manage GitHub Issues, pull requests, labels, milestones, and branches with gh. Use when: inspect a repository, search GitHub code or issues, understand a remote project, create an issue, comment on an issue or PR, create a PR, manage labels or milestones, or inspect remote branches."
argument-hint: "Describe the repository operation and target repository"
user-invocable: true
---

# GitHub

Use this skill for repository-agnostic GitHub work. Follow repository-local
instructions for account, branch, issue-template, and project-board rules.

## Preconditions

1. Confirm the GitHub CLI is available and authenticated:

   ```bash
   gh auth status
   gh api user --jq .login
   ```

2. Resolve the target repository before reading or writing. Prefer an explicit
   `OWNER/REPO`; otherwise inspect the current remote:

   ```bash
   gh repo view --json nameWithOwner,url,defaultBranchRef
   gh repo view OWNER/REPO --json nameWithOwner,url,defaultBranchRef
   ```

3. Pass `--repo OWNER/REPO` for every command when the target is not the current
   repository, or when working from a multi-root workspace.

## Explore Before Changing

Start read-only. Identify existing conventions, duplicate work, and the current
state before creating issues, labels, branches, or pull requests.

```bash
# Repository metadata and default branch
gh repo view OWNER/REPO --json nameWithOwner,description,defaultBranchRef,url

# Open work and labels
gh issue list --repo OWNER/REPO --state open --limit 100
gh label list --repo OWNER/REPO --limit 100

# Search issue and PR text in the target repository
gh search issues "query" --repo OWNER/REPO --limit 100

# Search source code without cloning
gh search code "query" --repo OWNER/REPO --limit 100

# Inspect one item, including discussion and state
gh issue view NUMBER --repo OWNER/REPO --comments
gh pr view NUMBER --repo OWNER/REPO --comments

# Inspect remote branches before branch operations
git ls-remote --heads "$(gh repo view OWNER/REPO --json sshUrl --jq .sshUrl)"
```

Treat search results as leads, not proof. Open the matching issue, pull request,
or source file before deciding the work duplicates an existing effort.

## Create A High-Signal Issue

Create an issue only after searching for duplicates and reading the repository's
issue template and contribution guidance. State observable behavior, constraints,
and validation evidence; avoid implementation guesses presented as requirements.

```bash
gh issue create --repo OWNER/REPO \
  --title "Concise outcome-oriented title" \
  --body-file issue-body.md \
  --label "bug" \
  --assignee "@me"
```

Use a body with this minimum structure when no template exists:

```markdown
## Description

What is true now, what should be true, and why it matters.

## Acceptance Criteria

- [ ] Observable result one
- [ ] Observable result two

## Validation

- Command or manual workflow that proves the result
```

Immediately verify creation and labels:

```bash
gh issue view NUMBER --repo OWNER/REPO --json number,title,state,labels,url
```

## Comments, Labels, And Milestones

Use comments for decisions, blockers, and validation evidence that must remain
with the work. Do not post secrets, personal data, or unverified conclusions.

```bash
gh issue comment NUMBER --repo OWNER/REPO --body "Decision and evidence"
gh issue edit NUMBER --repo OWNER/REPO --add-label "area:backend"
gh issue edit NUMBER --repo OWNER/REPO --milestone "Milestone title"
gh api "repos/OWNER/REPO/milestones" --jq '.[].title'
```

Verify each write with `gh issue view` or `gh api` before reporting success.

## Pull Requests And Branches

Before opening a PR, check the intended base branch, existing PRs for the head
branch, and the final diff. Do not create, rename, delete, force-push, or merge a
branch without explicit user intent and applicable repository rules.

```bash
gh pr list --repo OWNER/REPO --state all --head BRANCH
gh pr create --repo OWNER/REPO --base main --head BRANCH \
  --title "Outcome-oriented title" --body-file pr-body.md
gh pr view NUMBER --repo OWNER/REPO --json url,state,baseRefName,headRefName
```

Use `git push origin <sha>:refs/heads/<branch>` to create a remote branch and
`git push origin --delete <branch>` only after explicit confirmation. Git has no
remote rename operation: create the new ref, verify it, then delete the old ref.

## Failure Handling

- Authentication or scope failure: run `gh auth status`; do not expose tokens.
- `--repo` ambiguity: resolve `OWNER/REPO` explicitly and retry once.
- Permission failure: report the required repository role or token scope; do not
  attempt a workaround that changes ownership or visibility.
- API rate limit: inspect response headers and stop or use an authenticated
  request; do not retry a loop blindly.
- Unexpected write result: inspect the created resource before making another
  mutation.
