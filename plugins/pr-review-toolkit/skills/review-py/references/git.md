# Git Workflows - Code Review

Useful Git commands and workflows for code review. All commands assume you are in the root directory of the repository.

---

## Basic Comparison Commands

### View available branches
```bash
# Current branch
git branch --show-current

# All local branches
git branch

# Remote branches
git branch -r

# All branches (local + remote)
git branch -a
```

---

### Validate if branches exist
```bash
# Check if branch exists
git rev-parse --verify {branch_name}

# Example
git rev-parse --verify main
git rev-parse --verify origin/feature/new-api
```

**Exit code:**
- `0` = branch exists
- `128` = branch does not exist

---

### View commits between branches
```bash
# Lists commits in compare but not in base
git log {base}..{compare} --oneline

# With more details
git log {base}..{compare} --oneline --graph --decorate

# Only commit messages
git log {base}..{compare} --pretty=format:"%s"

# With author and date
git log {base}..{compare} --pretty=format:"%h - %an, %ar : %s"
```

---

## Change Analysis

### General statistics
```bash
# Summary of changes
git diff --stat {base}..{compare}

# Example output:
# src/api/users.py    | 45 ++++++++++++++++++++++-----
# src/models/user.py  | 12 ++++++--
# tests/test_users.py | 23 +++++++++++++++
# 3 files changed, 71 insertions(+), 9 deletions(-)
```

---

### List of modified files
```bash
# Only file names
git diff --name-only {base}..{compare}

# With status (M=Modified, A=Added, D=Deleted, R=Renamed)
git diff --name-status {base}..{compare}

# Example output:
# M	src/api/users.py
# A	src/services/auth.py
# D	src/old_module.py
# R100	src/utils.py	src/helpers/utils.py

# Only Python files
git diff --name-only {base}..{compare} | grep '\.py$'

# Only test files
git diff --name-only {base}..{compare} | grep 'test_.*\.py$'
```

---

### Full diff
```bash
# Diff of all changes
git diff {base}..{compare}

# Diff of specific file
git diff {base}..{compare} -- {path/file.py}

# Diff without whitespace
git diff -w {base}..{compare}

# Diff with extra context (10 lines before and after)
git diff -U10 {base}..{compare}

# Diff showing only names of changed functions
git diff {base}..{compare} --function-context
```

---

### Analysis by file type
```bash
# Count files by extension
git diff --name-only {base}..{compare} | sed 's/.*\.//' | sort | uniq -c | sort -nr

# Example output:
#   12 py
#    3 md
#    2 txt
#    1 toml

# List only modified Python files with statistics
git diff --stat {base}..{compare} -- '*.py'

# List only test files
git diff --stat {base}..{compare} -- 'tests/test_*.py' '**/test_*.py'
```

---

## Detailed File Analysis

### View changes in specific file
```bash
# File diff
git diff {base}..{compare} -- {file}

# With line numbers
git diff -U3 {base}..{compare} -- {file} | cat -n

# View only added lines
git diff {base}..{compare} -- {file} | grep '^+'

# View only removed lines
git diff {base}..{compare} -- {file} | grep '^-'
```

---

### Blame and history
```bash
# View who modified each line (on the compare branch)
git blame {compare} -- {file}

# View commit history that touched the file
git log {base}..{compare} -- {file}

# View diff of each commit that touched the file
git log -p {base}..{compare} -- {file}
```

---

## Author and Activity Analysis

### Change authors
```bash
# List unique authors
git log {base}..{compare} --format='%an' | sort | uniq

# Count by author
git log {base}..{compare} --format='%an' | sort | uniq -c | sort -rn

# Example output:
#   15 Alice Developer
#    8 Bob Engineer
#    3 Charlie Contributor

# Commits by author with messages
git log {base}..{compare} --format='%an: %s' | sort
```

---

### Date and time of changes
```bash
# First and last commit
git log {base}..{compare} --format='%ai %s' | head -1
git log {base}..{compare} --format='%ai %s' | tail -1

# All commits with date
git log {base}..{compare} --format='%ai - %an: %s'
```

---

## Useful Checks

### Detect large added files
```bash
# List added files larger than 1MB
git diff {base}..{compare} --stat | awk '{if ($3 ~ /\+/ && $1 ~ /Bin/) print $0}'

# View size of modified files
git diff {base}..{compare} --stat=200
```

---

### Detect moved or renamed files
```bash
# View moves/renames
git diff {base}..{compare} --name-status | grep '^R'

# With similarity percentage
git diff {base}..{compare} --name-status -M

# Example output:
# R095	src/old_name.py	src/new_name.py
```

---

### Check for merge conflicts
```bash
# Simulate merge to detect conflicts
git merge-tree $(git merge-base {base} {compare}) {base} {compare}

# Simpler (but temporarily modifies working directory)
git checkout {base}
git merge --no-commit --no-ff {compare}
git merge --abort  # undo
```

---

## Content Analysis

### Search for patterns in diff
```bash
# Search for keyword in changes
git diff {base}..{compare} | grep -i "password"
git diff {base}..{compare} | grep -i "api_key"
git diff {base}..{compare} | grep -i "secret"

# Search for added imports
git diff {base}..{compare} | grep '^+import'
git diff {base}..{compare} | grep '^+from .* import'

# Search for added TODOs
git diff {base}..{compare} | grep '^+.*TODO'

# Search for print statements (code smell)
git diff {base}..{compare} | grep '^+.*print('
```

---

### Change complexity analysis
```bash
# Added vs removed lines
git diff {base}..{compare} --numstat

# Example output:
# 45	9	src/api/users.py
# 12	3	src/models/user.py
# (45 lines added, 9 removed)

# Total lines changed
git diff {base}..{compare} --shortstat

# Example output:
# 3 files changed, 71 insertions(+), 9 deletions(-)

# By file with change percentage
git diff {base}..{compare} --stat=200 --stat-graph-width=20
```

---

## Advanced Workflows

### Compare with specific version
```bash
# Compare branch with specific commit
git diff {commit_hash}..{compare}

# Compare with tag
git diff v1.0.0..{compare}

# Compare last N commits
git diff HEAD~5..HEAD
```

---

### Ignore specific changes
```bash
# Ignore whitespace changes
git diff -w {base}..{compare}

# Ignore blank line changes
git diff --ignore-blank-lines {base}..{compare}

# Ignore changes in specific files
git diff {base}..{compare} -- . ':(exclude)package-lock.json' ':(exclude)*.min.js'
```

---

### Export diff for analysis
```bash
# Save full diff to file
git diff {base}..{compare} > /tmp/review-diff.txt

# Save only file names
git diff --name-only {base}..{compare} > /tmp/changed-files.txt

# Save statistics
git diff --stat {base}..{compare} > /tmp/diff-stats.txt

# Save diff of each Python file separately
for file in $(git diff --name-only {base}..{compare} | grep '\.py$'); do
    git diff {base}..{compare} -- "$file" > "/tmp/diff-$(basename $file).txt"
done
```

---

## Useful Shortcuts and Aliases

Add to `~/.gitconfig`:
```ini
[alias]
    # Review helpers
    review-files = "!f() { git diff --name-status $1..$2; }; f"
    review-stat = "!f() { git diff --stat $1..$2; }; f"
    review-py = "!f() { git diff --name-only $1..$2 | grep '\\.py$'; }; f"
    review-authors = "!f() { git log $1..$2 --format='%an' | sort | uniq -c | sort -rn; }; f"

    # Detect code smells
    review-todos = "!f() { git diff $1..$2 | grep '^+.*TODO'; }; f"
    review-prints = "!f() { git diff $1..$2 | grep '^+.*print('; }; f"
    review-secrets = "!f() { git diff $1..$2 | grep -iE 'password|secret|api_key|token'; }; f"
```

**Usage:**
```bash
git review-files origin/main feature/new-api
git review-py origin/main HEAD
git review-secrets origin/main feature/new-api
```

---

## Usage Patterns in Review-Py

### Typical workflow
```bash
# 1. Validate branches
git rev-parse --verify {base}
git rev-parse --verify {compare}

# 2. Get general statistics
git diff --stat {base}..{compare}

# 3. List modified Python files
git diff --name-only {base}..{compare} | grep '\.py$'

# 4. For each Python file:
#    a. View diff
git diff {base}..{compare} -- {file}

#    b. Run analysis (Python script)
python scripts/analyze_diff.py --file {file} --base {base} --compare {compare}

# 5. Generate report
python scripts/format_output.py --output review-output.md
```

---

### Quick checks before review
```bash
# Check if there are many changes (>1000 lines)
CHANGES=$(git diff {base}..{compare} --shortstat | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+')
if [ "$CHANGES" -gt 1000 ]; then
    echo "⚠️ Warning: PR too large ($CHANGES lines). Consider splitting."
fi

# Check for non-Python files
NON_PY=$(git diff --name-only {base}..{compare} | grep -v '\.py$' | wc -l)
if [ "$NON_PY" -gt 0 ]; then
    echo "ℹ️ $NON_PY non-Python files modified"
fi

# Check for new files
NEW_FILES=$(git diff --name-status {base}..{compare} | grep '^A' | wc -l)
if [ "$NEW_FILES" -gt 0 ]; then
    echo "✨ $NEW_FILES new files added"
fi
```

---

## Troubleshooting

### Branch not found
```bash
# Fetch latest remote branches
git fetch origin

# Check if branch exists remotely
git ls-remote --heads origin {branch_name}

# Create local tracking branch if needed
git checkout -b {local_name} origin/{remote_name}
```

---

### Very large diff
```bash
# View only statistics without full diff
git diff --stat {base}..{compare}

# View diff of smaller files first
git diff {base}..{compare} --stat | awk '$3 ~ /\+/ {print $3, $1}' | sort -n

# Limit diff to N lines of context
git diff -U1 {base}..{compare}
```

---

### Performance on large repos
```bash
# Use shallow diff (only changed files)
git diff --name-only {base}..{compare}

# Disable rename detection (faster)
git diff --no-renames {base}..{compare}

# Limit log depth
git log {base}..{compare} --oneline -n 100
```

---

## Commands NOT Recommended

**Avoid modifying the repository during review:**
```bash
# ❌ DO NOT DO — checkout modifies working directory
git checkout {compare}

# ❌ DO NOT DO — merge modifies history
git merge {compare}

# ❌ DO NOT DO — rebase rewrites history
git rebase {base}

# ❌ DO NOT DO — reset loses changes
git reset --hard
```

**Review must be read-only!**

---

## References

- Git Diff Documentation: https://git-scm.com/docs/git-diff
- Git Log Documentation: https://git-scm.com/docs/git-log
- Pro Git Book: https://git-scm.com/book/en/v2
- Git Best Practices: https://sethrobertson.github.io/GitBestPractices/

---

## Important Notes

**About branches:**
- Use `origin/{branch}` for remote branches
- Use `{branch}` for local branches
- `HEAD` always references the current commit
- `HEAD~N` references N commits back

**About performance:**
- Large diffs (>1000 files) can be slow
- Use `--stat` for quick overview first
- Consider reviewing in smaller batches

**About security:**
- Git commands in review are read-only
- Never execute commands that modify the repo
- Always validate branches before comparing
