# Architecture Analysis Archive

**Date Archived**: 2025-11-19
**Status**: Converted to official documentation

This directory contains the original architectural analysis documents that were created during the design phase. These documents have been **converted into official documentation** and are preserved here for historical reference only.

## Document Mapping

The following table shows how each analysis document was converted to official documentation:

| Original Analysis | Target Documentation | Type |
|-------------------|---------------------|------|
| `architecture-initial.md` | Multiple documents | Multiple |
| ↳ Vision/Goals | `documentation/prd.rst` | PRD |
| ↳ Components | `documentation/architecture/summary.rst` | Overview |
| ↳ Canister hierarchy | `documentation/architecture/designs/message-abstraction.rst` | Design |
| ↳ Provider patterns | `documentation/architecture/designs/provider-abstraction.rst` | Design |
| `callbacks-vs-events.md` | `documentation/architecture/decisions/001-event-handling-pattern.rst` | ADR |
| `content-storage-analysis.md` | `documentation/architecture/decisions/002-content-storage-strategy.rst` | ADR |
| `ensembles-analysis.md` | `documentation/architecture/decisions/003-tool-organization-with-ensembles.rst` | ADR |
| `deduplicator-analysis.md` | `documentation/architecture/decisions/004-conversation-history-trimming.rst` | ADR |
| `invocations.md` | Multiple documents | Multiple |
| ↳ Tool calling decisions | `documentation/architecture/decisions/005-tool-calling-mvp-scope.rst` | ADR |
| ↳ Invoker/Ensemble design | `documentation/architecture/designs/tool-calling.rst` | Design |
| ↳ MCP integration | `documentation/architecture/designs/mcp-integration.rst` | Design |
| `roles-vs-canisters-analysis.md` | `documentation/architecture/designs/message-abstraction.rst` (Design Rationale) | Design |
| `documentation-conversion-plan.md` | _(Conversion complete)_ | Plan |

## Source of Truth

**The official documentation is now the source of truth.** Do not update these archived files. Any changes to architecture, decisions, or designs should be made in the official documentation:

- **Requirements**: `documentation/prd.rst`
- **Architecture Overview**: `documentation/architecture/summary.rst`
- **Decisions**: `documentation/architecture/decisions/`
- **Designs**: `documentation/architecture/designs/`

## Why Archive?

These files are preserved for:

1. **Historical context**: Understanding the evolution of architectural thinking
2. **Detailed analysis**: Original files contain detailed tradeoff analysis that may be summarized in official docs
3. **Reference**: Useful when revisiting decisions or exploring alternatives
4. **Completeness**: Some clarifications (like roles-vs-canisters) may not have full ADRs but provide valuable context

## Active Development

For current implementation work, see:

- **Implementation Plan**: `.auxiliary/notes/implementation-plan.md`
- **Open Questions**: `.auxiliary/notes/open-questions.md` (if created)
- **TODOs**: `.auxiliary/notes/todo.md` (if created)
