---
name: quality-gates-tests
description: >
  Analiza la calidad de los tests de un repositorio con foco en caminos críticos, flows
  asíncronos y mutation reasoning. Genera reporte JSON (.quality/tests-report.json)
  y muestra el resultado localmente. Usar cuando el usuario pida analizar tests, verificar
  cobertura, auditar calidad de tests, revisar caminos críticos, "analizar tests del repo",
  "reporte de tests", "test quality report", o cualquier análisis profundo de calidad de tests.
argument-hint: "[owner/repo] [--lang <LANGUAGE>] [--full]"
allowed-tools: Agent, Bash, Read, Glob, Grep, Write
autoAccept: true
---

# Quality Gates — Test Quality Analysis

Auditoría profunda de calidad de tests con 2 agentes especializados secuenciales. Produce un
artefacto JSON (`.quality/tests-report.json`), muestra el resultado localmente y **publica los
hallazgos accionables como comentarios en el PR abierto de la rama** (inline review comments
resolubles cuando hay `file:line`; resumen de review para el resto). Ver Phase 4.

## Usage

```
/quality-gates:tests                              # repo local actual (full o incremental)
/quality-gates:tests olimpus-soft/my-service      # repo remoto
/quality-gates:tests --lang Java                  # forzar lenguaje
/quality-gates:tests --full                       # forzar análisis completo
/quality-gates:tests --lang Go olimpus-soft/myapp # combinado
```

---

## Phase 0 — Preflight, Incremental Check, and Context Collection

### 0.0 Verify prerequisites

Before anything else, verify that the `gh` CLI is available and authenticated:

```bash
gh auth status
```

If the command fails, inform the user immediately:
> "`gh` CLI is not authenticated. Run `gh auth login` before continuing."

**Stop here** — do not proceed to 0.1 without confirmed authentication.

### 0.1 Parse arguments and resolve repository

Parse the arguments passed by the user:

- If passed `owner/repo` (e.g.: `olimpus-soft/my-service`): use directly as `$REPO_OWNER/$REPO_NAME`.
- If passed a full GitHub URL: extract owner and repo from it.
- If no argument was passed (or only flags): infer from `git remote -v` in the current directory.
  ```bash
  git remote -v | head -1
  ```
  Extract the owner and repo from the returned URL. Expected format: `origin  https://github.com/OWNER/REPO.git`
- If not possible to determine, ask before proceeding.

If `--lang` was passed, register as `$LANG_OVERRIDE`. Otherwise, `$LANG_OVERRIDE` remains empty.
If `--full` was passed, set `$FORCE_FULL=true`. Otherwise, `$FORCE_FULL=false`.

Save: `$REPO_OWNER`, `$REPO_NAME`, `$LANG_OVERRIDE`, `$FORCE_FULL`.

```bash
# Capture the repo working directory and set up a per-repo work dir for intermediate artifacts.
# All large data (manifests, reference files, agent outputs) goes here — NOT in shell variables.
REPO_DIR="$(pwd)"
WORK_DIR="/tmp/qg-${REPO_NAME}-work"
mkdir -p "$WORK_DIR"
echo "Repo: $REPO_DIR | Work dir: $WORK_DIR"
```

### 0.2 Incremental mode check

```bash
# Get current commit SHA
SHA=$(git -C . rev-parse HEAD 2>/dev/null || echo "unknown")
SHA_SHORT=$(git -C . rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "Current SHA: $SHA"
```

**Check for existing report:**

```bash
if [ -f .quality/tests-report.json ]; then
  LAST_SHA=$(python3 -c "import json; d=json.load(open('.quality/tests-report.json')); print(d.get('metadata',{}).get('commit',''))" 2>/dev/null || echo "")
  echo "Last analyzed SHA: $LAST_SHA"
fi
```

**Determine run mode** (if `$FORCE_FULL=true`, skip to `RUN_MODE=full`):

```bash
if [ "$FORCE_FULL" = "true" ] || [ -z "$LAST_SHA" ] || [ ! -f .quality/tests-report.json ]; then
  RUN_MODE="full"
  CHANGED_FILES=""
else
  CHANGED=$(git diff --name-only "$LAST_SHA"..HEAD 2>/dev/null || echo "")
  RELEVANT=$(echo "$CHANGED" | grep -E '\.(java|go|py|ts|js|kt|rb|rs)$' || true)
  TEST_CHANGES=$(echo "$CHANGED" | grep -iE '(test|spec)' || true)

  RELEVANT_COUNT=$(echo "$RELEVANT" | grep -c . 2>/dev/null || echo 0)

  if [ -z "$RELEVANT" ]; then
    RUN_MODE="skipped"
  elif [ "$RELEVANT_COUNT" -lt 10 ]; then
    RUN_MODE="incremental"
    CHANGED_MODULES="$RELEVANT"
  else
    RUN_MODE="full"
    CHANGED_MODULES=""
  fi
fi

echo "Run mode: $RUN_MODE"
```

**If `RUN_MODE=skipped`:**
- Re-emit the existing `.quality/tests-report.json` content in the terminal (display the report sections from the JSON)
- Print: `> No relevant changes since last analysis (SHA: $LAST_SHA). Re-emitting cached report.`
- **Stop here** — do not proceed further.

Register: `$RUN_MODE`, `$SHA`, `$SHA_SHORT`, `$CHANGED_MODULES`.

### 0.3 Collect repository snapshot

Write all context to `$WORK_DIR` — do NOT load large data into the main context.

```bash
# File tree → file (not stdout — could be 200+ lines)
find . -type f \
  -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/target/*' -not -path '*/vendor/*' \
  -not -path '*/.gradle/*' \
  | sort | head -200 > "$WORK_DIR/file-tree.txt"
echo "File tree: $(wc -l < $WORK_DIR/file-tree.txt) entries → $WORK_DIR/file-tree.txt"
```

```bash
# Count files by extension — small output, keep in context for language detection
find . -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/target/*' \
  | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

```bash
# Dependency manifest files — write to WORK_DIR (do not cat into main context)
for f in pom.xml go.mod requirements.txt package.json build.gradle Gemfile; do
  if [ -f "$f" ]; then
    cp "$f" "$WORK_DIR/dep-$f"
    echo "Staged dep file: $f"
  fi
done
```

```bash
# README → file (not stdout — could be large)
if [ -f README.md ]; then
  cp README.md "$WORK_DIR/readme.md"
  echo "README staged: $WORK_DIR/readme.md"
else
  echo "(no README.md found)" > "$WORK_DIR/readme.md"
fi
```

**Detect primary language** (if `$LANG_OVERRIDE` is empty):
Analyze the extension count from the output above. Mapping:
- `.java`, `.kt` → Java/Kotlin
- `.go` → Go
- `.py` → Python
- `.ts`, `.js` → TypeScript/Node.js
- `.rb` → Ruby
- `.rs` → Rust

Register as `$LANG`. If `$LANG_OVERRIDE` is not empty, use it: `$LANG=$LANG_OVERRIDE`.

**Generate complete, deterministic file manifests — write to files, not shell variables:**

```bash
# Complete source file manifest → $WORK_DIR/source-manifest.txt
find . -type f \
  -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/target/*' -not -path '*/vendor/*' \
  -not -path '*/.gradle/*' -not -path '*/build/*' \
  -not -path '*/dist/*' -not -path '*/__pycache__/*' \
  \( -name '*.java' -o -name '*.kt' -o -name '*.go' -o -name '*.py' \
     -o -name '*.ts' -o -name '*.js' -o -name '*.rb' -o -name '*.rs' \) \
  | sort > "$WORK_DIR/source-manifest.txt"

# Complete test file manifest → $WORK_DIR/test-manifest.txt
find . -type f \
  -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/target/*' -not -path '*/vendor/*' \
  \( -name '*Test.java' -o -name '*Tests.java' -o -name '*Spec.java' \
     -o -name '*_test.go' -o -name 'test_*.py' -o -name '*_test.py' \
     -o -name '*.spec.ts' -o -name '*.test.ts' -o -name '*.spec.js' \
     -o -name '*.test.js' -o -name '*_spec.rb' -o -name '*_test.rs' \) \
  | sort > "$WORK_DIR/test-manifest.txt"

SOURCE_FILE_COUNT=$(wc -l < "$WORK_DIR/source-manifest.txt" | tr -d ' ')
TEST_FILE_COUNT=$(wc -l < "$WORK_DIR/test-manifest.txt" | tr -d ' ')
echo "MANIFEST: $SOURCE_FILE_COUNT source files, $TEST_FILE_COUNT test files → $WORK_DIR"
```

Agents receive **file paths** pointing to `$WORK_DIR`, not content blobs. Large data never enters the main context.

**If `RUN_MODE=incremental`:** still generate the full manifests, but note in agent prompts to focus analysis on `$CHANGED_MODULES` and their test counterparts.

**Check size**: if `SOURCE_FILE_COUNT > 200`, warn:
> "The repository has {N} source files. Analysis may take a few minutes. Continue?"
Wait for confirmation.

---

## Phase 1 — Agent A: Critical Path Mapper

**Skip Agent A entirely if `RUN_MODE=incremental` AND the previous report's `critical_path_coverage` and
`async_testing.flows` can be reused (i.e., no entrypoint/controller/handler files changed). In that case,
reconstruct `$WORK_DIR/paths-map.json` from the existing `.quality/tests-report.json`:

```bash
python3 -c "
import json
report = json.load(open('.quality/tests-report.json'))
paths_map = {
    'critical_paths': [
        {'name': p['name'], 'risk_type': p['risk_type'],
         'entry_point': p['entry_point'], 'flow': p['flow']}
        for p in report.get('critical_path_coverage', [])
    ],
    'async_flows': [
        {'name': f['name'], 'type': f['type'], 'location': f['location']}
        for f in report.get('async_testing', {}).get('flows', [])
    ]
}
import os; os.makedirs('$WORK_DIR', exist_ok=True)
json.dump(paths_map, open('$WORK_DIR/paths-map.json', 'w'), indent=2)
print('Reconstructed paths-map from cached report → $WORK_DIR/paths-map.json')
"
```
**

Otherwise, launch Agent A with the following prompt:

```
You are a senior architect analyzing the critical paths and async flows of a repository.
Your output will be consumed by a test quality analysis agent, so precision is essential.

Context:
- Repository: {owner}/{repo}
- Language: {lang}
- Run mode: {run_mode}
- Work directory (all context files are here): {work_dir}
  - File tree:          read {work_dir}/file-tree.txt
  - README:             read {work_dir}/readme.md
  - Source file manifest ({source_file_count} files): {work_dir}/source-manifest.txt

Use Read, Glob, Grep to read files in the repository at: {repo_dir}

## MANDATORY STEP 0: Exhaustive Entrypoint Discovery

Complete this step in full before any analysis. Sampling is not permitted.

1. Read `{work_dir}/source-manifest.txt`. Count the total files.

2. From the manifest, identify ALL entrypoint files — any file whose name or content matches:
   Controller, Handler, Consumer, Listener, Router, Endpoint, Worker, Job, Cron, Scheduler, Resource
   Use Grep on the repository at `{repo_dir}` for annotations: `@RestController`, `@KafkaListener`,
   `func main()`, `@app.route`, `router.GET`, `@Component`, etc.

3. Use the Read tool to read EVERY entrypoint file identified. No exceptions.

4. For each entrypoint's direct dependencies (services, use cases it calls): Read those files too.

5. Before producing JSON output, state:
   `DISCOVERY COMPLETE: Read [N] entrypoint files, [M] dependency files, from manifest of [T] total.`

DO NOT skip files. DO NOT say "I will focus on the most relevant ones."

## Your Mission

### 1. Identify Critical Paths

A critical path is a business operation flow that:
- Starts at an entrypoint (HTTP controller, gRPC handler, queue consumer, CLI entrypoint)
- Traverses through service/domain/repository layers
- Carries financial, correctness, or security risk

For each critical path, determine:
- **name**: short kebab-case identifier (e.g., "invoice-generation")
- **entry_point**: class.method() where the flow begins
- **flow**: ordered list of class/service names traversed
- **risk_type**: one of "financial" | "correctness" | "security"

Billing/Invoicing heuristics for risk classification:
- `financial`: involves monetary calculation, tax, discount, invoice total, payment processing,
  amount rounding, currency conversion, charge/refund
- `correctness`: status transitions, data integrity, idempotency, external API calls with
  side effects, state machine transitions
- `security`: auth/authz checks, PII access, audit logs, data masking

### 2. Identify Async Flows

An async flow is any operation not triggered by a synchronous HTTP call:
- Queue consumers (Kafka, SQS, RabbitMQ, internal queues)
- Webhook handlers
- Scheduled jobs / cron
- Event listeners
- Background workers

For each async flow:
- **name**: short kebab-case identifier
- **type**: "queue" | "webhook" | "scheduled" | "event"
- **location**: file path and class name

### 3. Output

Write ONLY the following JSON structure to `{work_dir}/paths-map.json` using the Write tool.
Do not print it to stdout. After writing, output exactly one line:
`PATHS_MAP_WRITTEN: {work_dir}/paths-map.json`

```json
{
  "critical_paths": [
    {
      "name": "invoice-generation",
      "risk_type": "financial",
      "entry_point": "InvoiceController.generate()",
      "flow": ["InvoiceService", "TaxCalculator", "PdfGenerator", "InvoiceRepository"]
    }
  ],
  "async_flows": [
    {
      "name": "payment-event-consumer",
      "type": "queue",
      "location": "src/main/java/com/example/PaymentEventListener.java"
    }
  ]
}
```

Be exhaustive — identify ALL critical paths and async flows present in the codebase.
For Billing/Invoicing systems, prioritize: invoice creation, tax calculation, payment processing,
refunds, chargebacks, status transitions, and any async financial event processing.
```

After Agent A completes, verify the output file exists:

```bash
if [ ! -f "$WORK_DIR/paths-map.json" ]; then
  echo "ERROR: Agent A did not write paths-map.json — aborting."
  exit 1
fi
python3 -c "
import json
d = json.load(open('$WORK_DIR/paths-map.json'))
print(f'Agent A complete: {len(d[\"critical_paths\"])} critical paths, {len(d[\"async_flows\"])} async flows → $WORK_DIR/paths-map.json')
"
```

---

## Phase 2 — Agent B: Test Quality Analyzer

Launch Agent B with the following prompt. If `RUN_MODE=incremental`, scope analysis to changed modules only.

```
You are a test quality expert analyzing a repository with ZERO tolerance for production failures.

Context:
- Repository: {owner}/{repo}
- Language: {lang}
- Run mode: {run_mode}
- Work directory: {work_dir}
- Repository root: {repo_dir}
- Critical paths and async flows: read {work_dir}/paths-map.json
- Source file manifest ({source_file_count} files): {work_dir}/source-manifest.txt
- Test file manifest ({test_file_count} files): {work_dir}/test-manifest.txt
{if incremental: "- Changed modules to focus on: {changed_modules}"}

Use Read, Glob, Grep to read files in the repository at: {repo_dir}

## MANDATORY STEP 0: File Reading Protocol

Complete ALL steps below before scoring. Read files on demand using Read tool — do not expect content
to be pre-loaded. Sampling invalidates the analysis.

### Step 0.0 — Reference knowledge
Apply the following testing standards from your training knowledge:
1. Testing best practices (Maurício Aniche — *Effective Software Testing*)
2. 19 test smell patterns (testsmells.org)
3. The output JSON must follow the structure defined in the Output Format section below

### Step 0.1 — Read ALL test files
The manifest `{work_dir}/test-manifest.txt` is authoritative (generated by bash find — covers every test file).

1. Read `{work_dir}/test-manifest.txt` to get the full path list.
2. Use the Read tool to read EVERY file in the list, in order. No sampling.
3. Log progress: `Reading test file [N]/[M]: <path>`

After Step 0.1, state:
`TEST FILES COMPLETE: Read [N]/[M]. Skipped: [list paths or 'none'].`

### Step 0.2 — Read critical path source files (priority)
From `{work_dir}/paths-map.json`, extract all files referenced in `critical_paths[].flow` and
`async_flows[].location`. Use Read to read each in full.

After Step 0.2, state:
`CRITICAL PATH FILES COMPLETE: Read [N] source files for [M] critical paths.`

### Step 0.3 — Read ALL remaining source files
After Step 0.2, read every source file in `{work_dir}/source-manifest.txt` NOT already read in Step 0.2.
Critical paths have priority in analysis weight, but ALL files must be read to ensure exhaustive
anti-pattern detection and coverage completeness.

After Step 0.3, state:
`ALL SOURCE FILES COMPLETE: Read [N] source files total from manifest of [T].`

DO NOT sample. DO NOT say "I'll focus on the most important ones."

Use the best practices reference above as the evaluation standard. When identifying gaps,
cross-reference against the anti-patterns documented there (ad-hoc tests, magic numbers,
multiple scenarios per method, structural-only coverage, mocking the class under test, etc.).
When suggesting fixes, model them after the ✅ examples in the guide.

## Scoring Dimensions (0-100, higher = better)

For each dimension, you will produce a score 0-100 and the evidence behind it.

### 1. critical_path_coverage (weight: 20%)
For each critical path in PATHS_MAP.critical_paths, assess:
- **happy path**: is there a test exercising the full successful flow?
- **failure path**: is there a test for the primary failure mode (external dep failure, validation error)?
- **boundary testing**: are boundary conditions (min/max, null, zero, off-by-one) tested?
- Score = 100 × (covered_aspects / total_aspects_across_all_paths)
- Each missing aspect → `assessment` field in the path entry

### 2. test_anti_patterns (weight: 15%)
Penalize tests that match these anti-patterns:
- `thread_sleep` — Thread.sleep() / time.sleep() used for synchronization
- `no_assertion_tests` — test methods with zero asserts or only assertTrue(true)
- `over_mocking` — mocking the class under test, or > 5 mocks per test
- `trivial_assertions` — only assertNotNull / assertEquals("", "") / assertTrue(result != null)
- `magic_values` — hardcoded literals without named constants or explanation
- `implementation_detail_testing` — tests that break if internal implementation changes but behavior stays the same
- Score = 100 × (clean_tests / total_tests_examined)
- Each occurrence → entry in `anti_patterns` array

### 3. mutation_readiness (weight: 25%)
For each block of critical business logic (conditionals, calculations, validations, status transitions):
- Imagine mutating: invert condition, swap operator (+/-/*/÷), remove null check, return constant, off-by-one
- If NO test would catch the mutation → contributes to estimated kill rate miss
- Score = overall estimated kill rate (0-100) — weighted average across all tiers
- Group findings into 3 tiers:
  - `high_resilience`: logic blocks where 85-100% of mutations would be caught (e.g. table-driven tests with boundary cases)
  - `medium_resilience`: logic blocks where 50-84% of mutations would be caught (e.g. tests cover happy path but not all conditions)
  - `low_resilience`: logic blocks where < 50% of mutations would survive (e.g. only assertNotNull, no real value checks)
- Record per tier: `detail` (which code/blocks), `estimated_kill_rate`
- Record: `tested_logic_blocks`, `total_logic_blocks`, `unkilled_mutant_examples` (top 3-5 worst cases)

### 4. async_flow_testing (weight: 10%)
For each async flow in PATHS_MAP.async_flows:
- Is there at least one test (unit or integration) exercising that flow?
- Does the test use proper async patterns (no Thread.sleep; use Awaitility, WireMock, etc.)?
- Score = 100 × (properly_tested_async_flows / total_async_flows)
- Record per-flow: `name`, `type`, `tested` (true/false), `uses_proper_patterns` (true/false), `risk_level`

### 5. coverage_completeness (weight: 20%)
Assess coverage completeness by layer:
- `controllers`: HTTP/gRPC handlers and request validation
- `use_cases` / `services`: business logic and domain services
- `repositories`: data access and persistence
- `infrastructure`: external integrations, queue consumers, clients
- Score = 100 × (layers_with_adequate_coverage / total_layers_identified)
- Record per-layer: `layer`, `coverage_level` ("full"|"partial"|"none"), `missing_scenarios`

### 6. test_pyramid_health (weight: 10%)
Count tests by category and compare to recommended ratios:
- `unit`: isolated tests with mocked dependencies (~70% recommended)
- `integration`: tests that span 2+ components or use real DB/queue (~20% recommended)
- `functional` / `e2e`: end-to-end tests (~10% recommended)
- Score = 100 × (1 - deviation_from_recommended_ratios)
- Record: `unit_count`, `integration_count`, `functional_count`, `unit_pct`, `integration_pct`, `functional_pct`, `assessment`
- **`unit_pct`, `integration_pct`, `functional_pct` must be integers** — use `round()` (e.g. `round(unit_count / total * 100)`). The server rejects floats.

## Anti-Pattern Classification

For every anti-pattern found, classify it as one of:
1. `thread_sleep` — Thread.sleep / time.sleep used for timing synchronization
2. `no_assertion_tests` — test methods with zero meaningful asserts
3. `over_mocking` — mocking the class under test or excessive mock count
4. `trivial_assertions` — asserts that don't validate business-critical data
5. `magic_values` — unexplained hardcoded literals in test data
6. `implementation_detail_testing` — tests coupled to internal implementation
7. `missing_failure_path` — external dep failure not tested
8. `untested_critical_module` — entire class/module in critical path has zero tests
9. `missing_async_test` — async flow (queue/webhook/scheduler) has no tests
10. `assertion_roulette` — multiple asserts in one test without failure messages; on failure, impossible to know which one failed
11. `conditional_test_logic` — if/switch/for/while inside test method; assertion may never execute, hiding real bugs
12. `empty_test` — test method with no executable statements (empty body or all lines commented out); always passes vacuously
13. `ignored_test` — @Ignore/@Disabled without a linked tracking issue; test silently rots as production code evolves
14. `mystery_guest` — test depends on external file, database, or network resource not set up within the test; causes non-deterministic CI failures

## Output Format

Output ONLY the following JSON structure, with no additional text before or after:

{
  "scores": {
    "critical_path_coverage": <0-100>,
    "test_anti_patterns": <0-100>,
    "mutation_readiness": <0-100>,
    "async_flow_testing": <0-100>,
    "coverage_completeness": <0-100>,
    "test_pyramid_health": <0-100>
  },
  "grades": {
    "overall": "<A+|A|A-|B+|B|B-|C+|C|C-|D|F>",
    "critical_path_coverage": "<letter grade>",
    "test_anti_patterns": "<letter grade>",
    "mutation_readiness": "<letter grade>",
    "async_flow_testing": "<letter grade>",
    "coverage_completeness": "<letter grade>",
    "test_pyramid_health": "<letter grade>"
  },
  "verdict": "<one sentence NL summary: what this test suite does well and its primary gap>",
  "test_distribution": {
    "unit_count": <N>,
    "integration_count": <N>,
    "functional_count": <N>,
    "unit_pct": <integer 0-100, use round()>,
    "integration_pct": <integer 0-100, use round()>,
    "functional_pct": <integer 0-100, use round()>,
    "assessment": "healthy|inverted|weak"
  },
  "critical_path_coverage": [
    {
      "name": "<from PATHS_MAP>",
      "risk_type": "<from PATHS_MAP>",
      "entry_point": "<from PATHS_MAP>",
      "flow": ["<from PATHS_MAP>"],
      "test_count": <N>,
      "assessment": "full|partial|none",
      "gaps": ["<specific gap description>"]
    }
  ],
  "anti_patterns": [
    {
      "type": "<one of the 14 patterns>",
      "severity": "CRITICAL|HIGH|MEDIUM",
      "file": "<source file path>",
      "lines": "<line range e.g. 45-67 or null>",
      "description": "<specific description with financial/correctness impact>",
      "suggested_fix": "<brief description of the fix>"
    }
  ],
  "mutation_readiness": {
    "estimated_kill_rate": <0-100>,
    "tested_logic_blocks": <N>,
    "total_logic_blocks": <N>,
    "resilience_tiers": [
      {
        "tier": "high_resilience|medium_resilience|low_resilience",
        "detail": "<which code/blocks fall here and why>",
        "estimated_kill_rate": <0-100>
      }
    ],
    "unkilled_mutant_examples": [
      {
        "file": "<file path>",
        "lines": "<line range>",
        "mutation": "<description of the mutation that would survive>",
        "risk": "financial|correctness|security"
      }
    ]
  },
  "async_testing": {
    "total_flows": <N>,
    "tested_flows": <N>,
    "flows": [
      {
        "name": "<from PATHS_MAP>",
        "type": "<from PATHS_MAP>",
        "location": "<from PATHS_MAP>",
        "tested": <true|false>,
        "uses_proper_patterns": <true|false>,
        "risk_level": "CRITICAL|HIGH|MEDIUM"
      }
    ]
  },
  "coverage_gaps": {
    "layers": [
      {
        "layer": "controllers|use_cases|repositories|infrastructure",
        "coverage_level": "full|partial|none",
        "missing_scenarios": ["<scenario description>"]
      }
    ]
  },
  "recommendations": {
    "tier1_this_week": [
      {
        "action": "<concrete P0/P1 action>",
        "urgency": "P0|P1",
        "owner": "<team/module>",
        "risk_justification": "<why this matters in financial/billing context>"
      }
    ],
    "tier2_this_month": [
      {
        "action": "<concrete P2 action>",
        "urgency": "P2",
        "owner": "<team/module>",
        "risk_justification": "<why this matters>"
      }
    ],
    "tier3_backlog": [
      {
        "action": "<improvement action>",
        "urgency": "P3",
        "owner": "<team/module>",
        "risk_justification": "<why this matters>"
      }
    ]
  },
  "untested_units": [
    {
      "unit": "<class/package/module path>",
      "reason": "<why it has no tests — e.g. 'main entry point', 'interface definitions only', 'wire/DI setup'>",
      "risk": "low|medium|high"
    }
  ],
  "ai_coverage_pct": <estimated 0-100 or null if not determinable>
}
```

For `ai_coverage_pct`: count the non-trivial source files (exclude config, DI wiring, interfaces/DTOs)
that have at least one corresponding test exercising their main logic, divided by total non-trivial
source files, ×100. Report null only if the codebase structure makes this impossible to estimate.

Write the JSON to `{work_dir}/agent-b-output.json` using the Write tool. Do not print it to stdout.
After writing, output exactly two lines:
```
AGENT_B_WRITTEN: {work_dir}/agent-b-output.json
ai_coverage_pct: <the value you computed, or null>
```

After Agent B completes, verify and extract the coverage metric:

```bash
if [ ! -f "$WORK_DIR/agent-b-output.json" ]; then
  echo "ERROR: Agent B did not write agent-b-output.json — aborting."
  exit 1
fi
AI_COVERAGE_PCT=$(python3 -c "
import json
d = json.load(open('$WORK_DIR/agent-b-output.json'))
print(d.get('ai_coverage_pct', 'null'))
" 2>/dev/null || echo null)
echo "Agent B complete. ai_coverage_pct=$AI_COVERAGE_PCT"
```

**Validate Agent B output against the JSON Schema (hard stop — no fallback):**

```bash
pip3 install jsonschema --break-system-packages -q 2>/dev/null || true
```

```bash
python3 - << PYEOF
import json, sys
import jsonschema

schema   = json.load(open('$WORK_DIR/output-schema.json'))
data     = json.load(open('$WORK_DIR/agent-b-output.json'))

# Agent B output does not yet contain metadata/run_mode/summary — validate its sub-sections
AGENT_B_REQUIRED = [
    "scores", "grades", "verdict", "test_distribution",
    "critical_path_coverage", "anti_patterns", "mutation_readiness",
    "async_testing", "coverage_gaps", "untested_units", "recommendations"
]

missing = [k for k in AGENT_B_REQUIRED if k not in data]
if missing:
    print(f"AGENT_B_VALIDATION_FAILED: missing top-level keys: {missing}")
    sys.exit(1)

for key in AGENT_B_REQUIRED:
    fragment_schema = {
        "\$schema": schema["\$schema"],
        "\$defs": schema["\$defs"],
        **schema["properties"][key]
    }
    try:
        jsonschema.validate(data[key], fragment_schema)
    except jsonschema.ValidationError as e:
        print(f"AGENT_B_VALIDATION_FAILED in '{key}': {e.message} at {list(e.absolute_path)}")
        sys.exit(1)

print("Agent B output valid — proceeding to Phase 3")
PYEOF
```

**If validation exits with code 1**, re-invoke Agent B exactly once with this appended instruction:

```
Your previous output failed JSON Schema validation with this error: {error message}.
The required schema is at: $WORK_DIR/output-schema.json
The canonical example is at: $WORK_DIR/output-example.json
Re-write the COMPLETE JSON to $WORK_DIR/agent-b-output.json — do not omit any key, do not rename fields, do not add extra keys.
```

**If the retry also fails: STOP.** Print the validation error, do not write any file, do not send to the endpoint. Surface the error clearly to the user so they can re-run.

---

## Phase 3 — Score Calculation and Output

### 3.1 Compute overall score and risk level

```python
import json, math

# Read Agent B output from file — never hold the full JSON in a shell variable
data = json.load(open(f"{WORK_DIR}/agent-b-output.json"))
scores = data["scores"]

# Weighted average
weights = {
    "mutation_readiness": 0.25,
    "critical_path_coverage": 0.20,
    "coverage_completeness": 0.20,
    "test_anti_patterns": 0.15,
    "async_flow_testing": 0.10,
    "test_pyramid_health": 0.10,
}

overall = sum(scores[dim] * weights[dim] for dim in weights)
overall = round(overall)

# Risk level
if overall <= 30:
    risk_level = "CRITICAL"
elif overall <= 50:
    risk_level = "HIGH"
elif overall <= 70:
    risk_level = "MEDIUM"
else:
    risk_level = "LOW"
```

### 3.2 Compute summary statistics

From Agent B output, compute:
- `total_anti_patterns` = `len(anti_patterns)`
- `critical_anti_patterns` = count of anti_patterns with severity = "CRITICAL"
- `high_anti_patterns` = count of anti_patterns with severity = "HIGH"
- `medium_anti_patterns` = count of anti_patterns with severity = "MEDIUM"
- `critical_paths_total` = `len(critical_path_coverage)`
- `critical_paths_covered` = count where `assessment = "full"`
- `async_flows_total` = `async_testing.total_flows`
- `async_flows_covered` = `async_testing.tested_flows`
- `untested_units_count` = `len(untested_units)`
- `all_tests_passing` = run the language-appropriate test command and infer true/false; set `null` if tests cannot be run locally
- `statement_coverage_pct` = run tests with coverage enabled and parse the generated report (see language-specific commands below); set `null` if tests cannot run
- `ai_coverage_pct` = already extracted as `$AI_COVERAGE_PCT` after Agent B completed

**Language-specific coverage execution:**

```bash
echo "Running tests to measure actual coverage..."
STATEMENT_COVERAGE_PCT=null
ALL_TESTS_PASSING=null

if [ "$LANG" = "Java" ] || [ "$LANG" = "Kotlin" ]; then
  if [ -f "gradlew" ]; then
    ./gradlew test jacocoTestReport -q 2>&1 | tail -3
    TEST_EXIT=$?
    [ $TEST_EXIT -eq 0 ] && ALL_TESTS_PASSING=true || ALL_TESTS_PASSING=false
    STATEMENT_COVERAGE_PCT=$(python3 -c "
import xml.etree.ElementTree as ET, glob
files = glob.glob('build/reports/jacoco/**/*.xml', recursive=True)
if files:
    root = ET.parse(files[0]).getroot()
    for c in root.findall('.//counter'):
        if c.get('type') == 'INSTRUCTION':
            covered = int(c.get('covered', 0))
            missed = int(c.get('missed', 0))
            total = covered + missed
            print(round(covered/total*100, 1) if total > 0 else 'null')
            break
    else:
        print('null')
else:
    print('null')
" 2>/dev/null || echo null)
  elif [ -f "pom.xml" ]; then
    mvn test jacoco:report -q 2>&1 | tail -3
    TEST_EXIT=$?
    [ $TEST_EXIT -eq 0 ] && ALL_TESTS_PASSING=true || ALL_TESTS_PASSING=false
    STATEMENT_COVERAGE_PCT=$(python3 -c "
import xml.etree.ElementTree as ET, glob
files = glob.glob('target/site/jacoco/*.xml')
if files:
    root = ET.parse(files[0]).getroot()
    for c in root.findall('.//counter'):
        if c.get('type') == 'INSTRUCTION':
            covered = int(c.get('covered', 0))
            missed = int(c.get('missed', 0))
            total = covered + missed
            print(round(covered/total*100, 1) if total > 0 else 'null')
            break
    else:
        print('null')
else:
    print('null')
" 2>/dev/null || echo null)
  fi
elif [ "$LANG" = "Go" ]; then
  go test ./... -coverprofile=coverage.out 2>&1 | tail -3
  TEST_EXIT=$?
  [ $TEST_EXIT -eq 0 ] && ALL_TESTS_PASSING=true || ALL_TESTS_PASSING=false
  STATEMENT_COVERAGE_PCT=$(go tool cover -func=coverage.out 2>/dev/null | tail -1 | awk '{gsub(/%/,"",$3); print $3}' || echo null)
elif [ "$LANG" = "Python" ]; then
  python -m pytest --cov --cov-report=xml -q 2>&1 | tail -3
  TEST_EXIT=$?
  [ $TEST_EXIT -eq 0 ] && ALL_TESTS_PASSING=true || ALL_TESTS_PASSING=false
  STATEMENT_COVERAGE_PCT=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    root = ET.parse('coverage.xml').getroot()
    print(round(float(root.get('line-rate', 0)) * 100, 1))
except:
    print('null')
" 2>/dev/null || echo null)
elif echo "$LANG" | grep -qiE 'node|typescript|javascript'; then
  npm test -- --coverage --coverageReporters=json-summary 2>&1 | tail -3
  TEST_EXIT=$?
  [ $TEST_EXIT -eq 0 ] && ALL_TESTS_PASSING=true || ALL_TESTS_PASSING=false
  STATEMENT_COVERAGE_PCT=$(python3 -c "
import json
try:
    d = json.load(open('coverage/coverage-summary.json'))
    pct = d.get('total', {}).get('lines', {}).get('pct')
    print(pct if pct is not None else 'null')
except:
    print('null')
" 2>/dev/null || echo null)
fi

echo "Tests passing: $ALL_TESTS_PASSING | Tool-measured coverage: ${STATEMENT_COVERAGE_PCT}%"
```

### 3.3 Build and write the JSON report

Ensure the `.quality/` directory exists:

```bash
mkdir -p .quality
```

Build the complete JSON artifact using Python (read Agent B output from file) and write it to `.quality/tests-report.json`.
Use the Write tool with the assembled JSON content. The structure must conform to the schema at `$WORK_DIR/output-schema.json`.

```json
{
  "schema_version": 1,
  "metadata": {
    "repository": "{owner}/{repo}",
    "analysis_date": "{ISO8601 timestamp}",
    "commit": "{SHA}",
    "language": "{LANG}",
    "branch": "{git branch name}",
    "framework": "{detected test framework e.g. JUnit5, testify, pytest}",
    "source_files": {N},
    "test_files": {N},
    "test_methods": {N},
    "test_to_source_ratio": {float}
  },

  "run_mode": "{RUN_MODE}",
  "risk_level": "{risk_level}",

  "scores": {
    "overall": {overall},
    "critical_path_coverage": {scores.critical_path_coverage},
    "test_anti_patterns": {scores.test_anti_patterns},
    "mutation_readiness": {scores.mutation_readiness},
    "async_flow_testing": {scores.async_flow_testing},
    "coverage_completeness": {scores.coverage_completeness},
    "test_pyramid_health": {scores.test_pyramid_health}
  },

  "grades": {from Agent B output},
  "verdict": "{from Agent B output — one sentence NL summary}",

  "test_distribution": {from Agent B output},
  "critical_path_coverage": [{from Agent B output}],
  "anti_patterns": [{from Agent B output}],
  "mutation_readiness": {from Agent B output},
  "async_testing": {from Agent B output},
  "coverage_gaps": {from Agent B output},
  "untested_units": [{from Agent B output}],
  "recommendations": {from Agent B output},

  "summary": {
    "overall_grade": "{grades.overall}",
    "verdict": "{same as top-level verdict}",
    "all_tests_passing": {ALL_TESTS_PASSING},
    "statement_coverage_pct": {STATEMENT_COVERAGE_PCT — from running tests, or null},
    "ai_coverage_pct": {ai_coverage_pct from Agent B output, or null},
    "total_anti_patterns": {N},
    "critical_anti_patterns": {N},
    "high_anti_patterns": {N},
    "medium_anti_patterns": {N},
    "critical_paths_total": {N},
    "critical_paths_covered": {N},
    "async_flows_total": {N},
    "async_flows_covered": {N},
    "untested_units_count": {N}
  }
}
```

Write using the Write tool to `.quality/tests-report.json`.

Validate the written JSON against the full schema — **hard stop if invalid**:

```bash
python3 - << PYEOF
import json, sys
import jsonschema

schema = json.load(open('$WORK_DIR/output-schema.json'))
report = json.load(open('.quality/tests-report.json'))

errors = list(jsonschema.Draft202012Validator(schema).iter_errors(report))
if errors:
    print(f"FINAL_SCHEMA_VALIDATION_FAILED — {len(errors)} error(s):")
    for e in errors:
        print(f"  • {e.message} (at {list(e.absolute_path)})")
    sys.exit(1)
else:
    print(f"Schema v{report['schema_version']} validated — report is conformant")
PYEOF
```

**If this exits with code 1: STOP. Do not send the report to the endpoint.** Print the validation errors and ask the user to re-run.

### 3.4 Display terminal report

Display the following formatted report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧬 TEST QUALITY — {owner}/{repo}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: {run_mode} | Commit: {sha_short} | Language: {lang}

### Overall Score: {overall}/100 ({overall_grade}) — {risk_emoji} {risk_level}
> {verdict}

| Dimension                | Score | Grade | Status |
|--------------------------|-------|-------|--------|
| Critical path coverage   | {N}   | {X}   | {emoji}|
| Test anti-patterns       | {N}   | {X}   | {emoji}|
| Mutation readiness       | {N}   | {X}   | {emoji}|
| Async flow testing       | {N}   | {X}   | {emoji}|
| Coverage completeness    | {N}   | {X}   | {emoji}|
| Test pyramid health      | {N}   | {X}   | {emoji}|

Score emoji key: 0-30 → 🔴 | 31-50 → ⚠️ | 51-70 → 💡 | 71-100 → ✅

### Coverage Metrics
| Metric                                 | Value                            |
|----------------------------------------|----------------------------------|
| AI-identified (files with test logic)  | {ai_coverage_pct}% or N/A        |
| Tool-measured (statement coverage)     | {statement_coverage_pct}% or N/A |

{If both values are non-null and |ai_coverage_pct - statement_coverage_pct| > 20:}
⚠️  Delta of {delta}% between AI-estimated and tool-measured coverage.
    Possible cause: excessive exclusions in coverage config (jacoco.xml, .nycrc, .coveragerc, etc.)
    Check for excluded packages/files that inflate the tool's reported percentage.

### Critical Path Coverage ({critical_paths_total} paths)
| Path                | Assessment | Test Count | Gaps |
|---------------------|------------|------------|------|
| {path.name}         | full/partial/none | {N} | {gap count} |

### Async Flows ({async_flows_total} flows, {async_flows_covered} tested)
{For each async flow: emoji + name (type) — "TESTED (proper patterns)" or "TESTED (Thread.sleep ⚠️)" or "NO TESTS"}

### Top Anti-Patterns ({total_anti_patterns} total: {critical_anti_patterns} 🔴, {high_anti_patterns} ⚠️, {medium_anti_patterns} 💡)
{Show all CRITICAL anti-patterns, then first 5 HIGH anti-patterns}
For each: severity_emoji [type] file:lines — description
           → {suggested_fix}

### Untested Units ({untested_units_count} units, all low-risk acceptable)
{For each untested_unit with risk = "medium" or "high": ⚠️ {unit} — {reason}}
{For low-risk units: just the count, no listing}

### Recommendations
{For tier1_this_week items (P0/P1), sorted by urgency:}
[{urgency}] {owner} — {action}
  Risk: {risk_justification}
{If tier2_this_month is non-empty:}
P2 backlog: {N} items — run with --full to see all

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Report saved: .quality/tests-report.json
```

Use these emoji for risk levels in score column:
- 0-30: 🔴
- 31-50: ⚠️
- 51-70: 💡
- 71-100: ✅

---

## Phase 4 — Publish findings as PR comments (mandatory)

The report must not live only in `.quality/tests-report.json`. Every actionable finding is published as a
comment on the open PR for the current branch, so it enters the standard respond-and-resolve cycle.
Anti-patterns (which carry `file` + `lines`) are posted as **inline review comments** → resolvable threads.
Findings without a precise location (critical-path gaps, untested async flows, P0/P1 recommendations) and any
anti-pattern whose line is not part of the PR diff are collected into a single summary review comment.

### 4.1 Resolve the open PR for the current branch

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")
if [ -z "$PR_NUMBER" ]; then
  PR_NUMBER=$(gh pr list --head "$BRANCH" --state open --json number --jq '.[0].number' 2>/dev/null || echo "")
fi
HEAD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
echo "PR=$PR_NUMBER | branch=$BRANCH | head=$HEAD_SHA"
```

**If `PR_NUMBER` is empty:** there is no open PR yet. Skip publishing, but print:
> "⚠️ No open PR for branch `$BRANCH` — quality-test findings were NOT published. Open the PR and re-run `/quality-test`, or publish manually. Merge is blocked until findings are posted and resolved."
Do not fail the skill; the local report is still saved.

### 4.2 Publish findings (idempotent)

All comments are prefixed with the marker `<!-- quality-test -->` so re-runs can detect and skip duplicates
instead of spamming the PR. Build and post with Python:

```bash
python3 - "$PR_NUMBER" "$HEAD_SHA" "$REPO_OWNER" "$REPO_NAME" << 'PYEOF'
import json, subprocess, sys, re

pr, head_sha, owner, repo = sys.argv[1:5]
if not pr:
    print("No PR — skipping publish.")
    sys.exit(0)

report = json.load(open(".quality/tests-report.json"))
MARK = "<!-- quality-test -->"

def gh_api(args, payload=None):
    cmd = ["gh", "api"] + args
    if payload is not None:
        cmd += ["--input", "-"]
        return subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True)
    return subprocess.run(cmd, capture_output=True, text=True)

# Existing quality-test comments → (path, line) set, to dedup on re-run
existing = set()
r = gh_api(["-X", "GET", f"repos/{owner}/{repo}/pulls/{pr}/comments", "--paginate"])
if r.returncode == 0:
    try:
        for c in json.loads(r.stdout):
            if MARK in (c.get("body") or ""):
                existing.add((c.get("path"), c.get("line") or c.get("original_line")))
    except Exception:
        pass

def first_line(lines):
    if not lines:
        return None
    m = re.search(r"\d+", str(lines))
    return int(m.group()) if m else None

sev_emoji = {"CRITICAL": "🔴", "HIGH": "⚠️", "MEDIUM": "💡"}
posted_inline, fallback = 0, []

for ap in report.get("anti_patterns", []):
    path, line = ap.get("file"), first_line(ap.get("lines"))
    body = (f"{MARK}\n{sev_emoji.get(ap.get('severity'),'')} **quality-test · {ap.get('type')}** "
            f"({ap.get('severity')})\n\n{ap.get('description','')}\n\n"
            f"**Suggested fix:** {ap.get('suggested_fix','—')}")
    if path and line is not None:
        if (path, line) in existing:
            continue
        res = gh_api(["-X", "POST", f"repos/{owner}/{repo}/pulls/{pr}/comments"],
                     {"body": body, "commit_id": head_sha, "path": path, "line": line, "side": "RIGHT"})
        if res.returncode == 0:
            posted_inline += 1
            continue
        # Line not in diff (422) or other error → fall back to summary
    fallback.append(f"- {sev_emoji.get(ap.get('severity'),'')} **{ap.get('type')}** ({ap.get('severity')}) "
                    f"`{path or '?'}:{ap.get('lines') or '?'}` — {ap.get('description','')} "
                    f"→ _{ap.get('suggested_fix','—')}_")

# Build summary review body (always) with non-localized findings
lines_out = [MARK, f"## 🧬 quality-test findings — overall {report.get('scores',{}).get('overall','?')}/100 "
             f"({report.get('grades',{}).get('overall','?')}) · risk {report.get('risk_level','?')}",
             f"> {report.get('verdict','')}", ""]

cp_gaps = [p for p in report.get("critical_path_coverage", []) if p.get("assessment") != "full"]
if cp_gaps:
    lines_out.append("### Critical-path gaps")
    for p in cp_gaps:
        lines_out.append(f"- **{p.get('name')}** ({p.get('risk_type')}, {p.get('assessment')}): "
                         + "; ".join(p.get("gaps", []) or ["—"]))
    lines_out.append("")

async_untested = [f for f in report.get("async_testing", {}).get("flows", []) if not f.get("tested")]
if async_untested:
    lines_out.append("### Untested async flows")
    for f in async_untested:
        lines_out.append(f"- **{f.get('name')}** ({f.get('type')}, {f.get('risk_level')}) — `{f.get('location')}`")
    lines_out.append("")

tier1 = report.get("recommendations", {}).get("tier1_this_week", [])
if tier1:
    lines_out.append("### Recommended this week (P0/P1)")
    for rec in tier1:
        lines_out.append(f"- [{rec.get('urgency')}] {rec.get('action')} — _{rec.get('risk_justification','')}_")
    lines_out.append("")

if fallback:
    lines_out.append("### Anti-patterns (no diff line — resolve below)")
    lines_out += fallback
    lines_out.append("")

lines_out.append("---\n_Posted by `/quality-test`. Respond to and resolve every thread before merge._")
summary = "\n".join(lines_out)

# Post summary as a PR review (event=COMMENT) so it shows in the review timeline
res = gh_api(["-X", "POST", f"repos/{owner}/{repo}/pulls/{pr}/reviews"],
             {"commit_id": head_sha, "event": "COMMENT", "body": summary})
summary_ok = res.returncode == 0
if not summary_ok:
    # Fallback to a plain issue comment so findings are never lost
    subprocess.run(["gh", "pr", "comment", pr, "--body", summary], capture_output=True, text=True)

print(f"PUBLISHED: {posted_inline} inline review comment(s), "
      f"{len(fallback)} finding(s) in summary, summary_posted={summary_ok or 'as-issue-comment'}")
PYEOF
```

### 4.3 Confirm

Print:
```
💬 Findings published to PR #{PR_NUMBER}. Resolve every thread before merge.
```

If `PR_NUMBER` was empty, instead remind the user that publishing was skipped and merge is blocked until done.

---

## Notes

### Output language

Always write the report and JSON artifact in **English**, regardless of the language used to invoke
the skill. Gap descriptions, action plan items, and all user-facing output must be in English.

### Language detection
| Extension | Language | Extra focus |
|-----------|----------|------------|
| `.java`, `.kt` | Java/Kotlin | Checked exceptions, Optional, streams, concurrency, @Transactional |
| `.go` | Go | Explicit error handling, goroutines, defer/panic/recover, channels |
| `.py` | Python | Type hints, context managers, GIL, generators, async/await |
| `.ts`, `.js` | TypeScript/Node.js | Promise/async-await, null coalescing, strict types, decorators |
| `.rb` | Ruby | Blocks/procs, metaprogramming, frozen strings, ActiveRecord |
| `.rs` | Rust | Ownership, lifetimes, unwrap without handling, async runtimes |

### Billing/Invoicing context

This skill is specifically tuned for Billing and Invoicing repositories where silent test failures
carry direct financial risk. Prioritize gaps that could cause:
- Incorrect invoice amounts or tax calculations
- Double charges or missing charges
- Failed idempotency (duplicate processing)
- Undetected payment processing errors
- Incorrect status transitions in financial workflows

### When in doubt, flag it

In a financial/billing context, **false positives are preferable to silent bugs**.
If something looks suspicious but is not clearly wrong, mark it as HIGH severity and explain
the potential impact.

### Incremental mode scope

When `RUN_MODE=incremental`:
- Agent A: reuse `critical_path_coverage` and `async_testing.flows` from previous report if no entrypoint files changed
- Agent B: scope anti-pattern and gap analysis to `$CHANGED_MODULES` and their test counterparts
- Score calculation: for unchanged paths, carry forward scores from the previous report
- The `run_mode` field in the output will be `"incremental"` to indicate partial analysis

### BigQuery compatibility

The JSON schema maps directly to BigQuery:
- Scalar fields: `metadata.*`, `run_mode`, `risk_level`, `verdict`, all `scores.*`, all `grades.*`, all `summary.*`
- Nested objects: `test_distribution`, `mutation_readiness`, `async_testing`, `coverage_gaps`
- Repeated records: `critical_path_coverage[]`, `anti_patterns[]`, `untested_units[]`,
  `recommendations.tier1_this_week[]`, `recommendations.tier2_this_month[]`, `recommendations.tier3_backlog[]`

Sample BigQuery queries:
```sql
-- Anti-pattern frequency by type and severity
SELECT metadata.repository, ap.type, ap.severity, COUNT(*) as count
FROM quality_tests_reports, UNNEST(anti_patterns) as ap
GROUP BY 1, 2, 3
ORDER BY count DESC

-- Grade distribution across repos
SELECT grades.overall, COUNT(*) as repos
FROM quality_tests_reports
WHERE summary.all_tests_passing = true
GROUP BY 1 ORDER BY 1
```
