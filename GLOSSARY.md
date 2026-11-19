# Bricksplain

Bricksplain explains an undocumented Databricks notebook to three different audiences, and proves every statement it makes by pointing at the notebook's own lines. It is domain-agnostic: it knows nothing in advance about what any given notebook does.

## Language

**Notebook**:
The Databricks source file the user points the app at. It is the only source of truth about the system being explained.
_Avoid_: Script, file under analysis

**Cell**:
One numbered, separable block of a Notebook, which may hold code, prose, SQL or a run directive.
_Avoid_: Block, section, chunk

**Line Range**:
A span of one or more lines, counted from the top of the Notebook, that lies inside a single Cell.
_Avoid_: Snippet, excerpt

**Audience**:
One of the three kinds of reader a document is written for: non-technical manager, new developer, AI coding agent.
_Avoid_: Persona, role, user type

**Audience Doc**:
The document generated for one Audience about one Notebook.
_Avoid_: Report, output, summary

## Evidence

**Claim**:
A single statement in an Audience Doc about the Notebook. It is either a Fact or a Concern, and both must carry a Citation.
_Avoid_: Statement, assertion, finding

**Fact**:
A Claim about what the Notebook does or contains.
_Avoid_: Observation

**Concern**:
A Claim that something in the Notebook is a risk, oddity or likely mistake, backed by the lines that show it.
_Avoid_: Issue, bug, warning

**Context**:
Generic explanatory framing that is not about this Notebook. It carries no Citation and is visibly marked as not coming from the Notebook.
_Avoid_: Background, filler

**No-findings statement**:
An explicit, uncited line in an Audience Doc saying the risk checklist turned up nothing. It makes no claim about what the Notebook does, so it is neither a Claim nor Context, and is shown as "No findings".
_Avoid_: Empty result, all clear

**Citation**:
A reference from a Claim to a Cell and Line Range, rendered as a link that opens the Source Viewer on those lines.
_Avoid_: Reference, footnote, source link

**Verified Citation**:
A Citation whose Line Range exists in the cited Cell and contains the text the Claim quoted.
_Avoid_: Valid citation, checked link

**Supported Citation**:
A Verified Citation whose quoted text actually backs the Claim that cites it, not merely appears in the Notebook.
_Avoid_: Correct citation, valid claim

**Coverage**:
The share of a Notebook's Cells and lines that at least one Claim in an Audience Doc cites. It shows what a doc leaves out.
_Avoid_: Completeness, score

**Source Viewer**:
The page that shows the Notebook with Cell boundaries and highlights a cited Line Range.
_Avoid_: Code view, preview

## Understanding the Notebook

**Inferred Glossary**:
The set of terms the LLM derives from a given Notebook, each defined and cited. It is output of the app, and is distinct from this file.
_Avoid_: Dictionary, vocabulary

**Eval Case**:
A known, deliberately chosen property of a sample Notebook that the generated docs are expected to surface, such as a specific risk. It is used to judge output quality.
_Avoid_: Test notebook, golden answer

## Relationships

- A **Notebook** is made of ordered **Cells**; each **Audience Doc** is generated from one Notebook for one **Audience**.
- An **Audience Doc** contains **Claims** and **Context**; every **Claim** has at least one **Citation**.
- A **Citation** points to one **Cell** and one **Line Range** and is opened in the **Source Viewer**.
- An **Inferred Glossary** is part of what is generated from a **Notebook**; nothing about a particular Notebook's subject belongs in this file.
