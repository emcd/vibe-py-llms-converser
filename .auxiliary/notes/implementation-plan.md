# Implementation Plan

**Status**: Active
**Last Updated**: 2025-11-19

This document tracks tactical implementation work for the current development phase. Unlike the official architecture documentation, this file is **ephemeral** and should be updated frequently as tasks are completed or priorities change.

## Current Phase: Phase 1 (MVP)

### Phase 1.1: Core Protocols

#### Base Protocols
- [x] Canister hierarchy protocols (all 6 types)
  - [x] UserCanister, AssistantCanister, SupervisorCanister
  - [x] DocumentCanister, InvocationCanister, ResultCanister
- [x] Content protocols (Text, Image designed; Audio/Video deferred)
  - [x] TextualContent with MIME type support
  - [x] ImageContent with hash-based storage
- [x] Provider/Client/Model protocols
- [x] Event definitions (MessageStartedEvent, MessageProgressEvent, etc.)
- [x] Tool calling protocols (Invoker, Ensemble, InvokerRegistry)
- [x] Concrete canister implementations (all 6 types with factory methods)

### Phase 1.2: Storage Layer

#### Persistence
- [ ] JSONL message serialization
- [ ] TOML metadata handling
- [ ] Hybrid content storage (inline + hash)
  - [ ] Size-based threshold logic (1KB cutoff)
  - [ ] Hash-based content addressing (SHA-256)
  - [ ] Content deduplication
- [ ] Conversation forking support

### Phase 1.3: Tool Calling Framework

#### Invoker Infrastructure
- [ ] Concrete Invoker implementation
- [ ] Concrete Ensemble implementation
- [ ] InvokerRegistry implementation
- [ ] MCP server tool discovery/invocation
- [ ] Configuration loading from TOML
- [ ] Fail-fast error handling

### Phase 1.4: Provider Implementation

#### Anthropic Provider
- [ ] Anthropic provider
  - [ ] MessagesProcessor (normalization/nativization)
  - [ ] ControlsProcessor
  - [ ] InvocationsProcessor
  - [ ] ConversationTokenizer
- [ ] Streaming and non-streaming modes
- [ ] Tool calling integration
- [ ] Event emission during conversation

### Phase 1.5: CLI Interface

#### User Interface
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

### Official Documentation
- Architecture Summary: `documentation/architecture/summary.rst`
- ADRs: `documentation/architecture/decisions/`
- Design Docs: `documentation/architecture/designs/`
- Archived Analysis: `.auxiliary/notes/architecture-initial/`

### Prior Art (ai-experiments)
The original `ai-experiments` project contains valuable precedent and design decisions:
- Core Messages: https://raw.githubusercontent.com/emcd/ai-experiments/refs/heads/master/sources/aiwb/messages/core.py
- Invocables Core: https://raw.githubusercontent.com/emcd/ai-experiments/refs/heads/master/sources/aiwb/invocables/core.py
- Provider Core: https://raw.githubusercontent.com/emcd/ai-experiments/refs/heads/master/sources/aiwb/providers/core.py
- Provider Interfaces: https://raw.githubusercontent.com/emcd/ai-experiments/refs/heads/master/sources/aiwb/providers/interfaces.py
