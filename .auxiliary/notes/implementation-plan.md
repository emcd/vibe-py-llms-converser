# Implementation Plan

**Status**: Active
**Last Updated**: 2025-11-19

This document tracks tactical implementation work for the current development phase. Unlike the official architecture documentation, this file is **ephemeral** and should be updated frequently as tasks are completed or priorities change.

## Current Phase: Phase 1 (MVP)

### Core Foundations

#### Base Protocols
- [ ] Canister hierarchy protocols (all 6 types)
  - [ ] UserCanister, AssistantCanister, SupervisorCanister
  - [ ] DocumentCanister, InvocationCanister, ResultCanister
- [ ] Content protocols (Text, Image designed; Audio/Video deferred)
  - [ ] TextualContent with MIME type support
  - [ ] ImageContent with hash-based storage
- [ ] Provider/Client/Model protocols
- [ ] Event definitions (MessageStartedEvent, MessageProgressEvent, etc.)

#### Storage Layer
- [ ] JSONL message serialization
- [ ] TOML metadata handling
- [ ] Hybrid content storage (inline + hash)
  - [ ] Size-based threshold logic (1KB cutoff)
  - [ ] Hash-based content addressing (SHA-256)
  - [ ] Content deduplication
- [ ] Conversation forking support

#### Message Events
- [ ] Single callback with pattern matching
- [ ] Event hierarchy implementation
- [ ] Provider event emission

#### Tool Calling
- [ ] Invoker core abstraction
- [ ] Ensemble for grouping
- [ ] InvocationsProcessor protocol
- [ ] MCP server tool discovery/invocation
- [ ] Configuration loading from TOML
- [ ] Fail-fast error handling

#### Provider Implementation
- [ ] Anthropic provider
  - [ ] MessagesProcessor (normalization/nativization)
  - [ ] ControlsProcessor
  - [ ] InvocationsProcessor
  - [ ] ConversationTokenizer
- [ ] Streaming and non-streaming modes
- [ ] Tool calling integration

#### CLI Interface
- [ ] Basic commands (chat, list, show)
- [ ] Provider selection
- [ ] Conversation management

## Implementation Notes

### Current Focus
[Add current sprint/iteration focus here]

### Blockers
[Track any blockers or dependencies here]

### Technical Debt
[Track technical debt items that should be addressed]

## Phase 2 (Future)

Deferred items from ADR-005 and other decisions:

- Additional providers (OpenAI, Ollama/VLLM)
- Deduplicators (if conversations approach context limits)
- Tool result caching
- Permission/sandbox system for tools
- Wrapping converser as MCP server
- Conversation import/export
- AudioContent and VideoContent implementations

## References

- Architecture Summary: `documentation/architecture/summary.rst`
- ADRs: `documentation/architecture/decisions/`
- Design Docs: `documentation/architecture/designs/`
- Archived Analysis: `.auxiliary/notes/architecture-initial/`
