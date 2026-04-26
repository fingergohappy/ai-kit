---
name: evaluate
description: Dual-source evidence-based evaluation.
argument-hint: "<要评估的内容>"
disable-model-invocation: true
---

# evaluate

Rigorous evaluation based on dual-source evidence. Every conclusion must have a source and a reasoning chain.

## Core Principles

Evaluation must not rely solely on external search, nor solely on project code. Facts must be collected from both dimensions simultaneously and cross-verified:

- **Project facts**: actual code, dependency versions, configuration, git history, project conventions — representing "what actually is here"
- **External facts**: best practices, official specifications, community consensus, benchmarks — representing "what should be"

Every judgment must be traceable to a specific source. Every reasoning chain must be explicitly shown.

## Execution Steps

### 1. Parse the Evaluation Target

Extract from `$ARGUMENTS` and conversation context:

- **Evaluation subject**: what specifically (library, tool, approach, claim, code pattern, etc.)
- **Evaluation dimensions**: what the user cares about (performance? security? maintainability? accuracy? cost-effectiveness?)
- **Contextual information**: any relevant information already present in the conversation

If the evaluation target is unclear, confirm with the user before proceeding.

### 2. Assess Complexity and Choose Execution Strategy

Judge complexity based on the evaluation subject:

| Complexity | Criteria | Execution Strategy |
|------------|----------|--------------------|
| Simple | Single fact verification, single-file code, single claim | Main agent executes serially, no sub-agents |
| Complex | Tech selection, multi-dimensional comparison, architecture review, batch review verification | Split into sub-agents for parallel fact collection |

Simple evaluation: the main agent reads code + searches on its own, then jumps to step 5.

Complex evaluation: proceed through steps 3-4 using the sub-agent parallel pattern.

### 3. Complex Evaluation: Parallel Sub-Agent Fact Collection

Determine the number of sub-agents based on evaluation complexity. Launch them in parallel using the Agent tool with `run_in_background: true`.

**Sub-agent splitting principles:**

Split by evaluation dimension. Each sub-agent is responsible for one independent fact-collection task. Common splits:

| Evaluation Scenario | Sub-agent Split | Rationale |
|---------------------|-----------------|-----------|
| Tech selection | Project status + one per candidate | Parallel comparison of multiple options |
| Single claim verification | Project facts + external search | The most basic split |
| Batch review verification | One per conclusion | Each verified independently, no dependencies |
| Architecture review | Project architecture status + industry solution search + competitor cases | Three-way parallel |

**Sub-agent task templates:**

Project facts sub-agent:
```
Task: Collect relevant facts about {evaluation subject} within the project
Collection scope:
  - Code facts: read relevant source code, understand implementation, call chains, usage patterns
  - Dependency facts: check package.json / go.mod / Cargo.toml / pyproject.toml to confirm versions
  - Configuration facts: linter, formatter, CI config, CLAUDE.md project conventions
  - History facts: git log / git blame to understand change frequency and decision context
Output format: fact list organized by dimension, each item annotated with file path:line number
```

External facts sub-agent:
```
Task: Search for external facts and best practices about {evaluation subject}
Search strategy:
  - Breadth search: exa + WebSearch + Context7, one round in Chinese and one in English
  - Depth search: search for counter-evidence on controversial points, GitHub issues, competitor comparisons
  - Include version numbers and years in search queries to ensure timeliness
Output format: fact list organized by dimension, each item annotated with source URL
```

Once all sub-agents complete, the main agent aggregates results and proceeds to step 4.

### 4. Cross-Verification

After the main agent receives dual-source results, compare and identify contradictions:

- Discrepancies between the project's actual practices and industry recommendations
- Whether the versions used in the project have known issues
- Whether the project's usage aligns with the library/framework's official recommendations

If gaps requiring additional search are discovered, the main agent searches on its own (no more sub-agents).

### 5. Organize Evidence

Organize dual-source facts by evaluation dimension, annotating source types:

```
## Evidence Summary

### Dimension A: {e.g., Security}

[Project Facts]
- Project uses X v2.3.1, configured with Y (source: package.json:12)
- Unvalidated input exists at Z in the code (source: src/handler.ts:45)

[External Facts]
- X v2.3.1 has known CVE-2025-XXXX (source: url)
- Official documentation recommends using W instead of Y (source: url)

[Contradictions/Gaps]
- Project practice A is inconsistent with official recommendation B, reason is ...
```

### 6. Rigorous Evaluation

Evaluate based on dual-source evidence, following these rules:

**Transparent reasoning**: show the complete reasoning chain for each conclusion:
```
Conclusion: X outperforms Z in scenario Y
Reasoning:
  1. [Project] Current code uses Z, covering N files (source: git grep)
  2. [External] X's benchmark data is ... (source: url)
  3. [External] Z's data in the same scenario is ... (source: url)
  4. [External] However, X degrades under ... conditions (source: url)
  5. [Inference] In the project's Y scenario, X is superior because ...
```

**Distinguish source types**:
- `[Project]` — statements from project code, configuration, or history
- `[External]` — external facts with clear URLs or document references
- `[Inference]` — reasoning based on facts, with inference basis explained
- `[Uncertain]` — insufficient information to judge, clearly stated

**Counter-evidence must be presented**: if evidence unfavorable to the final conclusion was found during search, it must be listed and an explanation provided for why it was not adopted.

### 7. Output Evaluation Report

Use the following format:

```markdown
# Evaluation: {evaluation subject}

## Conclusion Summary

{one-sentence conclusion, state any prerequisites if applicable}

## Evaluation Dimensions

### {Dimension 1}
- **Rating**: {Excellent / Good / Fair / Poor / Dangerous}
- **Assessment**: {specific explanation}
- **Evidence**:
  - [Project] {in-project fact, with file path or line number}
  - [External] {external fact, with url}
  - [Inference] {reasoning process}

### {Dimension 2}
...

## Controversies and Risks

{contradictions between dual-source evidence, unconfirmed information, potential risks}

## Limitations

{limitations of this evaluation: search coverage, completeness of project facts, timeliness}
```

### 8. Provide Recommendations (if applicable)

If the evaluation reveals issues or room for improvement, provide actionable recommendations:

- Specific modification suggestions with file and line numbers
- Prioritized (what should be changed immediately vs. what can be addressed later)
- Each recommendation accompanied by rationale and source

## When to Stop Searching

Do not judge by search count; judge by evidence sufficiency. Conditions for stopping search:

- Key judgments have at least 2 independent sources corroborating each other
- Counter-evidence has been searched ("X issues", "X defects") and no unaddressed major contradictions were found
- Information gaps do not affect the final conclusion (if they do, continue searching)
- Different sources for the same dimension agree, with no new contradictions emerging

If 3 rounds of searching still reveal new contradictory information, the evaluation is more complex than expected. Inform the user and suggest escalating to a deep evaluation.

## Common Evaluation Scenarios

### Tech Selection Evaluation

- [Project] what is currently used, versions, dependency depth, migration cost
- [External] GitHub activity, download counts, known issues, community feedback, competitor comparisons
- [Trajectory] technology lifecycle assessment: is it growing, stable, or declining? Is the community gathering or dispersing? Is the core team sustainably maintaining it? Is there a clear technical roadmap? Selection cannot be based solely on "good enough now" — evaluate the trajectory over 1-2 years. If a library is being officially replaced (e.g., moment -> dayjs, requests -> httpx), flag the risk even if the current version still works.

### Code Practice Evaluation

- [Project] how the code is actually written, scope of impact, whether test coverage exists
- [External] official documentation recommendations, community consensus, counter-examples, version evolution changes

### Claim Verification

- [Project] how the claim manifests in the project and its context
- [External] original source, credible references, refuting evidence, prerequisites

### Architecture Proposal Evaluation

- [Project] current architecture, module boundaries, dependency direction, change frequency
- [External] industry solutions for similar problems, pros and cons of architecture patterns, large-scale case studies

### Review Conclusion Evaluation

When the user provides a review report path or references a specific review conclusion, verify whether that conclusion holds.

**Identification**: the user says "evaluate this review conclusion", "is this review finding correct", "evaluate review", or provides a report path + line number.

Execution flow:
1. Read the report, locate the specific review conclusion
2. Extract key claims from the conclusion (e.g., "X practice is insecure", "should use Y instead")
3. Read the relevant source code to confirm whether the issue described in the conclusion actually exists (sometimes reports are based on old code that has since been fixed)
4. Search for external evidence to verify whether the conclusion's recommendation aligns with best practices
5. Provide a judgment for each item:

```
### Conclusion #N: {conclusion title}

- **Original judgment**: {what the report says}
- **Project facts**: {actual current code situation, with file:line number}
- **External evidence**: {search results, with sources}
- **Final verdict**: {Valid / Partially Valid / Invalid / Unverifiable}
- **Reasoning**: {reasoning process}
```

Common verdict outcomes:
- **Valid**: project facts confirm the issue exists, external evidence supports the recommendation
- **Partially Valid**: the issue exists but the recommended fix is suboptimal, or prerequisites do not fully apply
- **Invalid**: the issue no longer exists (code has changed), or the recommendation is based on outdated information, or the recommendation does not apply in the current context
- **Unverifiable**: search did not find sufficient evidence; requires human judgment
