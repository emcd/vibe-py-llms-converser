# Documentation Conversion Plan

**Date**: 2025-11-18
**Purpose**: Convert auxiliary notes into official PRD and architecture documentation

## Executive Summary

This plan outlines the reorganization of ~3,500 lines of substantive architectural analysis from `.auxiliary/notes/` into the official documentation structure under `documentation/`. The conversion will:

1. **Promote mature design documents** from working notes to official record
2. **Separate concerns** between permanent documentation and ephemeral implementation plans
3. **Improve discoverability** for current and future team members
4. **Establish clear document ownership** and maintenance boundaries

**Timeline**: This conversion should happen before significant implementation begins to ensure the official documentation guides development rather than following it.

## Current State Assessment

### Documents to Convert

| File | Lines | Status | Content Type |
|------|-------|--------|--------------|
| architecture-initial.md | 453 | Mature | Overview + core concepts |
| callbacks-vs-events.md | 878 | **Decision made** | Architectural decision |
| content-storage-analysis.md | 429 | **Decision made** | Architectural decision |
| deduplicator-analysis.md | 244 | **Decision made** | Architectural decision |
| ensembles-analysis.md | 263 | **Decision made** | Architectural decision |
| invocations.md | 824 | Comprehensive | Design + decision |
| roles-vs-canisters-analysis.md | 378 | Analysis | Clarification (no decision) |
| **Total** | **3,469** | | |

### Key Observations

1. **Many documents contain DECISIONS**: They have executive summaries, recommendations, and final decisions - these are ADRs, not working notes
2. **High quality content**: Well-structured with pros/cons analysis, examples, and rationale
3. **Proven decisions**: These analyses drove actual architectural choices
4. **Discovery problem**: Critical design rationale is hidden in `.auxiliary/` where new contributors won't find it

## Proposed Documentation Structure

### documentation/prd.rst (Product Requirements Document)

**Source content from**:
- `architecture-initial.md` (lines 1-32: Project Vision, Core Capabilities, Architectural Principles)

**Structure**:
```rst
*******************************************************************************
Product Requirements Document
*******************************************************************************

Vision and Goals
===============================================================================

[Content from architecture-initial.md: Project Vision section]

Core Capabilities
===============================================================================

[From architecture-initial.md: Core Capabilities section]

1. Message Normalization Layer
2. Provider Abstraction
3. Conversation History Management
4. Event-Driven Architecture
5. Tool/Function Calling with MCP Support

User Stories and Acceptance Criteria
===============================================================================

.. todo:: To be developed based on core capabilities

Success Metrics
===============================================================================

.. todo:: To be defined
```

### documentation/architecture/summary.rst (System Overview)

**Source content from**:
- `architecture-initial.md` (lines 33-end: Core Architecture Components)

**Structure**:
```rst
*******************************************************************************
System Overview
*******************************************************************************

High-Level Architecture
===============================================================================

[Narrative overview of the system]

Core Components
===============================================================================

Message Abstraction Layer
-------------------------------------------------------------------------------

[Canister hierarchy, content model from architecture-initial.md]

Provider Abstraction
-------------------------------------------------------------------------------

[Normalization/nativization patterns]

Invocables Framework
-------------------------------------------------------------------------------

[High-level overview, detailed design in separate doc]

Event System
-------------------------------------------------------------------------------

[Callback/event architecture]

Component Relationships
===============================================================================

[Diagram or description of how components interact]
```

### documentation/architecture/decisions/ (ADRs)

Each ADR follows a consistent format (see ADR Format section below).

**Mapping**:

| Source Note | Target ADR | Decision |
|-------------|------------|----------|
| callbacks-vs-events.md | 001-event-handling-pattern.rst | Single callback with pattern matching |
| content-storage-analysis.md | 002-content-storage-strategy.rst | Hybrid inline/hash with size threshold |
| ensembles-analysis.md | 003-invoker-organization.rst | Keep ensembles for MCP lifecycle |
| deduplicator-analysis.md | 004-conversation-trimming.rst | Skip deduplicators for MVP |
| invocations.md (decision sections) | 005-tool-calling-architecture.rst | Core invocables framework |

### documentation/architecture/designs/ (Design Documents)

Design documents describe HOW systems work, not WHY decisions were made.

**Mapping**:

| Source Note | Target Design Doc | Content |
|-------------|-------------------|---------|
| architecture-initial.md | message-abstraction.rst | Canister hierarchy, content model, protocols |
| invocations.md | tool-calling.rst | Invoker/Ensemble/InvocationsProcessor implementation |
| invocations.md | mcp-integration.rst | MCP server connection, tool discovery, adapters |
| architecture-initial.md | provider-abstraction.rst | Normalization/nativization patterns |

**Note**: `roles-vs-canisters-analysis.md` doesn't map cleanly because it's a **clarification** (no merge actually happened - we preserved ai-experiments pattern). This content can be:
- Summarized in `message-abstraction.rst` design doc as "Design Rationale"
- Or kept as reference in `.auxiliary/notes/` (archived)

### .auxiliary/notes/ (Implementation Planning)

After conversion, `.auxiliary/notes/` should contain:

- `implementation-plan.md` - Current sprint/iteration work, tactical TODOs
- `open-questions.md` - Unresolved design questions requiring investigation
- `todo.md` - Development task tracking (can be managed via /cs-manage-todos slash command)
- `migration-log.md` - Record of which notes became which official documents

**Lifecycle**: Files here are **ephemeral** - deleted when completed, not maintained long-term.

## Document Format Guidelines

### ADR Format (Architecture Decision Records)

**Template**:
```rst
.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
ADR-NNN: [Decision Title]
*******************************************************************************

:Date: YYYY-MM-DD
:Status: Accepted | Proposed | Superseded
:Deciders: [Who made the decision]

Context and Problem Statement
===============================================================================

[What is the issue we're addressing? What factors are relevant?]

Decision Drivers
===============================================================================

* [Driver 1]
* [Driver 2]
* ...

Considered Options
===============================================================================

Option 1: [Name]
-------------------------------------------------------------------------------

[Description]

**Pros:**

* [Advantage 1]
* [Advantage 2]

**Cons:**

* [Disadvantage 1]
* [Disadvantage 2]

Option 2: [Name]
-------------------------------------------------------------------------------

[Same structure as Option 1]

Decision Outcome
===============================================================================

**Chosen option**: [Option N], because [rationale].

**Consequences:**

* [Positive consequence 1]
* [Negative consequence 1 (tradeoff)]

Implementation Notes
===============================================================================

[Optional: Key implementation considerations, code patterns, migration path]

References
===============================================================================

* [Link 1]
* [Link 2]
```

**Key ADR Principles**:

1. **Immutable after acceptance**: Don't edit accepted ADRs; create new ones that reference/supersede
2. **Context over implementation**: Focus on WHY the decision was made, not HOW to implement
3. **Honest about tradeoffs**: Document negative consequences and alternatives considered
4. **Decision-focused**: Each ADR makes ONE clear decision
5. **Date matters**: Decisions are snapshots in time; capture when and by whom

**Reference**: https://emcd.github.io/python-project-common/stable/sphinx-html/common/architecture.html

### Design Document Format

**Template**:
```rst
.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. [license header - same as ADR]


*******************************************************************************
[Design Name]
*******************************************************************************

:Author: [Name]
:Date: YYYY-MM-DD
:Status: Draft | Active | Deprecated

Overview
===============================================================================

[High-level description of what this design covers]

Goals and Non-Goals
===============================================================================

**Goals:**

* [Goal 1]
* [Goal 2]

**Non-Goals:**

* [What this design explicitly doesn't cover]

Design Details
===============================================================================

[Main content - can have subsections as needed]

Component A
-------------------------------------------------------------------------------

[Description, interfaces, behavior]

Component B
-------------------------------------------------------------------------------

[Description, interfaces, behavior]

Interactions and Data Flow
===============================================================================

[How components work together]

Examples and Usage Patterns
===============================================================================

Example 1: [Scenario]
-------------------------------------------------------------------------------

.. code-block:: python

   # Code example

Alternative Approaches Considered
===============================================================================

[Brief notes on what was considered but not chosen - detailed in ADRs]

Implementation Roadmap
===============================================================================

[Optional: Phasing, dependencies, prerequisites]

References
===============================================================================

* [Related ADRs]
* [External documentation]
```

**Key Design Doc Principles**:

1. **Living documents**: Can be updated as implementation evolves
2. **Implementation-focused**: HOW things work, not WHY decisions were made
3. **Code examples**: Concrete illustrations of usage
4. **Reference ADRs**: Link to decision records for context on WHY
5. **Current state**: Document what IS, not what was considered

## Conversion Mapping

### Detailed Mapping Table

| Source | Type | Lines | Target Document | Section | Notes |
|--------|------|-------|-----------------|---------|-------|
| architecture-initial.md | Overview | 1-32 | prd.rst | Vision, Capabilities, Principles | |
| architecture-initial.md | Design | 33-300 | designs/message-abstraction.rst | Canister hierarchy | |
| architecture-initial.md | Design | 301-453 | designs/provider-abstraction.rst | Normalization patterns | |
| callbacks-vs-events.md | Analysis + Decision | All | decisions/001-event-handling-pattern.rst | Complete ADR | Strong recommendation present |
| content-storage-analysis.md | Analysis + Decision | All | decisions/002-content-storage-strategy.rst | Complete ADR | Stakeholder decision recorded |
| ensembles-analysis.md | Analysis + Decision | All | decisions/003-invoker-organization.rst | Complete ADR | Clear recommendation |
| deduplicator-analysis.md | Analysis + Decision | All | decisions/004-conversation-trimming.rst | Complete ADR | Skip for MVP decision |
| invocations.md | Mixed | 1-100 | prd.rst | Tool calling requirement | Why it's essential |
| invocations.md | Design | 101-600 | designs/tool-calling.rst | Invoker/Ensemble architecture | |
| invocations.md | Design | 601-800 | designs/mcp-integration.rst | MCP server integration | |
| invocations.md | Decision | 709-788 | decisions/005-tool-calling-architecture.rst | Ensemble/Deduplicator decisions | Extract decision sections |
| roles-vs-canisters-analysis.md | Clarification | All | Archive or fold into message-abstraction.rst | No decision to record | |

### Content Requiring Synthesis

Some content needs to be synthesized from multiple sources:

**documentation/architecture/summary.rst**:
- Introduction: New content (narrative overview)
- Components: From architecture-initial.md
- Relationships: New content (how components interact)
- Diagrams: New content (optional, can add later)

**documentation/prd.rst**:
- Vision: From architecture-initial.md
- Core capabilities: From architecture-initial.md
- User stories: New content (to be developed)
- Success metrics: New content (to be defined)

## Conversion Process

### Phase 1: Structure Setup

**Tasks**:
1. Create ADR files (001-005) with proper headers and structure
2. Create design doc files (4 documents) with proper headers
3. Update index files to reference new documents
4. Create migration log template

**Order**: Do this first to establish the target structure

### Phase 2: ADR Conversion

**Priority order**:
1. `002-content-storage-strategy.rst` (from content-storage-analysis.md)
   - Has explicit stakeholder decision
   - Clear recommendation section
   - Well-structured tradeoff analysis

2. `001-event-handling-pattern.rst` (from callbacks-vs-events.md)
   - Largest, most comprehensive
   - Clear executive summary with recommendation
   - Good example of ADR structure

3. `003-invoker-organization.rst` (from ensembles-analysis.md)
   - Clear decision matrix
   - Good pros/cons analysis

4. `004-conversation-trimming.rst` (from deduplicator-analysis.md)
   - Important negative decision (skip for MVP)
   - Good cache vs. trimming tradeoff analysis

5. `005-tool-calling-architecture.rst` (from invocations.md)
   - Extract decision sections only
   - Reference the design docs for implementation

**Process for each ADR**:
1. Create RST file with proper header
2. Extract decision from source markdown
3. Reformat to ADR template structure
4. Add to decisions/index.rst toctree
5. Update migration log

**Markdown to RST conversion notes**:
- Headings: `##` → underline with `=`, `###` → underline with `-`
- Code blocks: Triple backticks → `.. code-block:: python`
- Bold: `**text**` → `**text**` (same)
- Lists: `- item` → `* item` (mostly same, watch indentation)
- Links: `[text](url)` → `` `text <url>`_ ``
- Internal refs: Use RST cross-references: `:doc:`path/to/doc``

### Phase 3: Design Document Conversion

**Priority order**:
1. `message-abstraction.rst` (from architecture-initial.md)
   - Foundation for everything else
   - Canister hierarchy is core abstraction

2. `provider-abstraction.rst` (from architecture-initial.md)
   - Normalization/nativization patterns
   - Provider interface design

3. `tool-calling.rst` (from invocations.md)
   - Comprehensive implementation details
   - Invoker/Ensemble/InvocationsProcessor

4. `mcp-integration.rst` (from invocations.md)
   - MCP server connection patterns
   - Tool discovery and execution

**Process for each design doc**:
1. Create RST file with proper header
2. Extract relevant sections from source(s)
3. Reorganize into design doc structure
4. Add code examples (convert markdown to RST)
5. Add cross-references to related ADRs
6. Add to designs/index.rst toctree
7. Update migration log

### Phase 4: PRD and Summary Updates

**PRD (documentation/prd.rst)**:
1. Extract vision and goals from architecture-initial.md
2. List core capabilities with brief descriptions
3. Add TODO markers for user stories and metrics
4. Reference ADRs where decisions affect requirements

**Summary (documentation/architecture/summary.rst)**:
1. Write narrative overview of system
2. Extract component descriptions from architecture-initial.md
3. Describe component interactions
4. Add cross-references to detailed design docs

### Phase 5: Cleanup and Verification

**Tasks**:
1. Create `.auxiliary/notes/implementation-plan.md` template
2. Create `.auxiliary/notes/open-questions.md` if needed
3. Update `.auxiliary/notes/migration-log.md` with complete mapping
4. Archive or delete converted notes from `.auxiliary/notes/`
5. Update CLAUDE.md context section if needed
6. Build Sphinx docs to verify all cross-references work

**Verification checklist**:
- [ ] All toctrees updated
- [ ] All cross-references resolve
- [ ] All code blocks have proper syntax highlighting
- [ ] All ADRs have dates and status
- [ ] All design docs reference relevant ADRs
- [ ] Migration log is complete
- [ ] Sphinx build succeeds without warnings

## Migration Log Template

Create `.auxiliary/notes/migration-log.md`:

```markdown
# Documentation Migration Log

**Date**: 2025-11-18

## Mapping: Notes → Official Documentation

### ADRs Created

| ADR File | Source Note | Conversion Date | Converter |
|----------|-------------|-----------------|-----------|
| 001-event-handling-pattern.rst | callbacks-vs-events.md | YYYY-MM-DD | [Name] |
| 002-content-storage-strategy.rst | content-storage-analysis.md | YYYY-MM-DD | [Name] |
| 003-invoker-organization.rst | ensembles-analysis.md | YYYY-MM-DD | [Name] |
| 004-conversation-trimming.rst | deduplicator-analysis.md | YYYY-MM-DD | [Name] |
| 005-tool-calling-architecture.rst | invocations.md (sections) | YYYY-MM-DD | [Name] |

### Design Docs Created

| Design Doc | Source Note(s) | Conversion Date | Converter |
|------------|----------------|-----------------|-----------|
| message-abstraction.rst | architecture-initial.md | YYYY-MM-DD | [Name] |
| provider-abstraction.rst | architecture-initial.md | YYYY-MM-DD | [Name] |
| tool-calling.rst | invocations.md | YYYY-MM-DD | [Name] |
| mcp-integration.rst | invocations.md | YYYY-MM-DD | [Name] |

### Other Documentation Updates

| Document | Source Content | Update Date | Updater |
|----------|----------------|-------------|---------|
| prd.rst | architecture-initial.md (vision) | YYYY-MM-DD | [Name] |
| architecture/summary.rst | architecture-initial.md (components) | YYYY-MM-DD | [Name] |

### Original Notes Status

| Original Note | Status | Archive Location |
|---------------|--------|------------------|
| architecture-initial.md | Converted | Deleted (content in multiple docs) |
| callbacks-vs-events.md | Converted | Deleted (→ ADR-001) |
| content-storage-analysis.md | Converted | Deleted (→ ADR-002) |
| ensembles-analysis.md | Converted | Deleted (→ ADR-003) |
| deduplicator-analysis.md | Converted | Deleted (→ ADR-004) |
| invocations.md | Converted | Deleted (→ ADR-005 + designs) |
| roles-vs-canisters-analysis.md | Archived | .auxiliary/notes/archive/ (clarification, no decision) |

## Notes

[Any issues encountered, special considerations, or future work needed]
```

## RST Conversion Reference

### Common Markdown → RST Patterns

**Headings**:
```markdown
# Level 1
## Level 2
### Level 3
```
→
```rst
*******************************************************************************
Level 1
*******************************************************************************

Level 2
===============================================================================

Level 3
-------------------------------------------------------------------------------
```

**Code blocks**:
```markdown
​```python
def foo():
    pass
​```
```
→
```rst
.. code-block:: python

   def foo():
       pass
```

**Lists**:
```markdown
- Item 1
- Item 2
  - Nested
```
→
```rst
* Item 1
* Item 2

  * Nested
```

**Links**:
```markdown
[Text](https://example.com)
```
→
```rst
`Text <https://example.com>`_
```

**Internal references**:
```rst
See :doc:`../decisions/001-event-handling-pattern` for details.

:ref:`section-label` for cross-references within same doc
```

**Emphasis**:
```markdown
**bold** and *italic*
```
→
```rst
**bold** and *italic*
```
(Same syntax, but RST uses single `*` for emphasis)

**Notes/Warnings**:
```rst
.. note::
   This is a note.

.. warning::
   This is a warning.

.. important::
   This is important.
```

**TODOs**:
```rst
.. todo:: Complete this section
```

### Semi-Automated Conversion

**Tools that can help**:
- `pandoc`: Can convert markdown → RST, though manual cleanup usually needed
  ```bash
  pandoc -f markdown -t rst input.md -o output.rst
  ```
- Manual editing: Given the document size and need for restructuring, manual conversion may be clearer

**Recommended approach**:
1. Use pandoc for initial conversion of large sections
2. Manually restructure to fit ADR/design doc templates
3. Clean up formatting issues
4. Add RST-specific directives (notes, code blocks with proper highlighting)

## Quality Checklist

Before marking conversion complete, verify:

### Content Quality
- [ ] All decisions from notes are captured in ADRs
- [ ] All design information is captured in design docs
- [ ] No important content was lost in conversion
- [ ] Cross-references between docs are complete
- [ ] Code examples are accurate and tested
- [ ] Tradeoffs and alternatives are documented

### Format Quality
- [ ] All RST files have proper license headers
- [ ] All ADRs follow the ADR template structure
- [ ] All design docs follow the design doc template
- [ ] Heading levels are consistent
- [ ] Code blocks have correct language highlighting
- [ ] Lists are properly formatted
- [ ] Links and cross-references work

### Structure Quality
- [ ] All new docs are in toctrees
- [ ] Index files are updated
- [ ] Document organization is logical
- [ ] Related docs cross-reference each other
- [ ] Navigation makes sense

### Technical Quality
- [ ] Sphinx builds without errors
- [ ] Sphinx builds without warnings
- [ ] All cross-references resolve
- [ ] Generated HTML looks correct
- [ ] Code examples have proper syntax highlighting

### Maintenance Quality
- [ ] Migration log is complete
- [ ] Original notes are archived or deleted
- [ ] Implementation plan template created
- [ ] Clear boundary between official docs and working notes
- [ ] CLAUDE.md updated if needed

## Additional Thoughts and Recommendations

### 1. ADR Numbering Strategy

**Recommendation**: Use 3-digit zero-padded numbers (001, 002, ...)
- Sorts correctly in file listings
- Allows up to 999 ADRs (sufficient)
- Standard practice in many projects

### 2. When to Create New ADRs vs. Update Design Docs

**Create new ADR when**:
- Making a NEW architectural decision
- Superseding a previous decision
- Choosing between significant alternatives

**Update design doc when**:
- Implementation details change
- Adding examples or clarifications
- Fixing errors or updating for current state
- No decision is being made, just documenting reality

### 3. Dating and Versioning

**ADRs**:
- Date = when decision was made
- Status = Accepted (for decisions already implemented)
- Never modify accepted ADRs (create new one that supersedes)

**Design docs**:
- Date = last significant update
- Status = Active (for current implementation)
- Can be freely updated as implementation evolves

### 4. Cross-Referencing Strategy

Create a web of references:
- ADRs reference the design docs they affect
- Design docs reference the ADRs that explain their decisions
- PRD references ADRs for major architectural choices
- Summary references design docs for implementation details

Example:
```rst
.. In ADR-002 (content storage):
   See :doc:`../designs/message-abstraction` for implementation details.

.. In message-abstraction.rst design doc:
   The content storage strategy is explained in :doc:`../decisions/002-content-storage-strategy`.
```

### 5. Future Document Creation

As the project evolves, maintain the pattern:

**New decision needed?** → Create ADR in `decisions/`
- File name: `NNN-short-description.rst`
- Follow ADR template
- Link from related design docs

**New system component?** → Create design doc in `designs/`
- File name: `component-name.rst`
- Follow design doc template
- Link from summary.rst
- Link to related ADRs

**Implementation work?** → Update `.auxiliary/notes/implementation-plan.md`
- Ephemeral, deleted when done
- Not part of official documentation

### 6. Handling Clarifications

`roles-vs-canisters-analysis.md` is a **clarification**, not a decision (no merge happened, we preserved ai-experiments pattern).

**Options**:
1. Fold into `message-abstraction.rst` as "Design Rationale" section
2. Archive in `.auxiliary/notes/archive/` for historical reference
3. Delete (information is implicit in the design)

**Recommendation**: Option 1 - add a "Design Rationale" section to `message-abstraction.rst` explaining why we use distinct types rather than a single Canister class.

### 7. Sphinx Build Integration

Add a documentation build check to CI/CD:
```bash
# In .github/workflows or similar
sphinx-build -W -b html documentation documentation/_build/html
```

The `-W` flag treats warnings as errors, ensuring clean documentation.

### 8. Documentation Review Process

Establish a lightweight review process:
1. New ADRs: Stakeholder review before marking "Accepted"
2. Design docs: Technical review for accuracy
3. Implementation plans: No formal review (working documents)

This ensures documentation quality without bureaucracy.

## Conclusion

This conversion will transform ~3,500 lines of hidden analysis into discoverable, structured, and maintainable official documentation. The separation between official docs (permanent, immutable ADRs and living design docs) and working notes (ephemeral implementation plans) will clarify the project's architectural foundation while preserving flexibility for active development.

**Key Success Factor**: Complete this conversion BEFORE major implementation work begins. Once code is being written, the official documentation should be the source of truth, not auxiliary notes.

**Estimated Effort**:
- Phase 1 (Structure): 1-2 hours
- Phase 2 (ADRs): 4-6 hours (5 ADRs × ~1 hour each)
- Phase 3 (Design Docs): 6-8 hours (4 docs × 1.5-2 hours each)
- Phase 4 (PRD/Summary): 2-3 hours
- Phase 5 (Cleanup): 1-2 hours
- **Total**: 14-21 hours

This is a significant but worthwhile investment that will pay dividends in project clarity, onboarding efficiency, and long-term maintainability.
