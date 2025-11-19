# LLM Conversation Architecture - Overview

**Date**: 2025-11-15
**Purpose**: High-level architectural overview and index to detailed design documents

## Project Vision

Build a simpler, focused architecture for LLM conversation management with learnings from the ai-experiments project.

### Core Capabilities

1. **Normalization Layer**: Unified message format across different LLM providers
2. **Provider Abstraction**: "Nativize" normalized messages to provider-specific formats
3. **History Management**: Simple CLI for managing conversation history
4. **Message Events**: Event-driven architecture for provider interactions
5. **Tool Calling**: Function/tool invocation with MCP server support

## Architectural Principles

**Learned from ai-experiments**:
- Full type annotations from start
- Async-first API design
- Configuration-driven provider setup
- Clear separation of concerns via protocols
- Streaming opt-out by default

**New to this project**:
- JSONL for message history (improved readability)
- Single callback with pattern matching (simpler event handling)
- Hybrid content storage (inline + hash-based)
- Multimodal content designed from start

## Core Architecture Components

### 1. Message Abstraction

**Complete canister hierarchy** (preserved from ai-experiments):

```python
Canister (base protocol)
├── UserCanister          # User messages
├── AssistantCanister     # LLM responses
├── SupervisorCanister    # System/supervisor instructions
├── DocumentCanister      # Reference documents
├── InvocationCanister    # Tool invocations
└── ResultCanister        # Tool results
```

**Content model** (multimodal from start):
```python
Content (base protocol)
├── TextualContent        # Text with MIME type support
├── ImageContent          # Images/visual content
├── AudioContent          # Audio (future)
└── VideoContent          # Video (future)
```

**Design rationale**: [roles-vs-canisters-analysis.md](roles-vs-canisters-analysis.md)

### 2. Provider Interface

**Core protocols**:
```python
Provider
├── produce_client() → Client
└── name: str

Client
├── access_model() → Model
└── survey_models() → list[Model]
```

**Provider processors** (all preserved from ai-experiments):
- **ControlsProcessor**: Model parameters
- **MessagesProcessor**: Normalize ↔ native conversion
- **InvocationsProcessor**: Tool invocations
- **ConversationTokenizer**: Token counting

**MVP provider implementations**:
- Anthropic (primary)
- Ollama or VLLM
- OpenAI Conversations API (legacy)
- OpenAI Responses API (new)

### 3. Storage Architecture

**Conversation storage**:
```
conversations/{id}/
├── messages.jsonl        # One message per line
└── metadata.toml         # Name, created, tags, etc.
```

**Content storage** (hybrid approach):
```
content/{hash}/
├── data                  # Binary content
└── metadata.toml         # MIME type, size, etc.
```

**Storage strategy**:
- **Textual content**: Inline by default (fast loading)
- **Large text (>1KB)**: Hash storage (deduplication benefit for forks)
- **System prompts**: Always hash storage (shared across conversations)
- **Non-textual content**: Always hash storage

**Detailed analysis**: [content-storage-analysis.md](content-storage-analysis.md)

### 4. Message Events

**Single callback with pattern matching**:

```python
def handle_message_events(event: MessageEvent) -> None:
    match event:
        case MessageStartedEvent():
            allocate_message_cell()
        case MessageProgressEvent(chunk=chunk):
            append_to_message(chunk)
        case MessageCompletedEvent():
            finalize_message()
        case MessageFailedEvent(error=error):
            show_error(error)
            rollback_changes()
        case _:
            pass  # Ignore unknown events
```

**Event hierarchy**:
- `MessageStartedEvent` - Message allocation begins
- `MessageProgressEvent` - Streaming chunk received
- `MessageUpdatedEvent` - Message content updated
- `MessageCompletedEvent` - Message finalized
- `MessageFailedEvent` - Generation failed

**Design rationale**: [callbacks-vs-events.md](callbacks-vs-events.md)

### 5. Tool/Function Calling

**Core components**:
```python
Invoker              # Wraps tool with schema validation
├── name: str
├── invocable: Callable
├── arguments_schema: dict
└── ensemble: Ensemble

Ensemble             # Groups related invokers
├── name: str
├── invokers: dict[str, Invoker]
├── config: dict     # Server-level configuration
└── connection: Any  # MCP client if applicable
```

**Design decisions**:
- **Keep ensembles**: Essential for MCP server lifecycle management
- **Skip deduplicators** for MVP: Rely on server-side prompt caching

**Detailed analysis**:
- [invocations.md](invocations.md) - Complete tool calling architecture
- [ensembles-analysis.md](ensembles-analysis.md) - Ensemble justification
- [deduplicator-analysis.md](deduplicator-analysis.md) - Deduplicator tradeoffs

## Architecture Decision Records

### ADR-001: Message Storage Format

**Status**: ACCEPTED

**Decision**: JSONL for message history, TOML for metadata

**Rationale**:
- JSONL: One message per line enables incremental append, better readability
- TOML: Human-readable metadata and configuration
- Universal tooling support

**Note**: JSONL is for persistent storage, not streaming responses during active conversation.

### ADR-002: Provider Plugin System

**Status**: ACCEPTED

**Decision**: Config-driven virtual plugin architecture from day one

**Implementation**: Librovore-style dynamic loading (NOT entry points)

```toml
# Configuration-driven provider registry
[providers]
anthropic = { module = "vibe_llms.providers.anthropic" }
ollama = { module = "vibe_llms.providers.ollama" }
```

```python
# Self-registration pattern
from vibe_llms.providers.core import register
from .client import AnthropicProvider

register("anthropic", AnthropicProvider)
```

**Benefits**:
- No entry point pollution
- Runtime flexibility
- Uniform provider access (built-in and external identical)
- Lazy installation of external providers

### ADR-003: Message Event Handling

**Status**: ACCEPTED

**Decision**: Single callback with pattern matching

**Provider signature**:
```python
class Provider:
    def __init__(self, event_handler: Callable[[MessageEvent], None]):
        self.event_handler = event_handler
```

**Rationale**:
- Simpler interface (one parameter vs multiple callbacks)
- Python 3.10+ pattern matching provides clean dispatch
- Extensible (new events = new case branches)
- Extension-friendly (unknown events ignored in `case _`)

**Detailed comparison**: [callbacks-vs-events.md](callbacks-vs-events.md)

### ADR-004: Tool Calling in MVP

**Status**: ACCEPTED

**Decision**: Tool/function calling is **required** for MVP

**Scope**:
- Invoker/Ensemble architecture
- InvocationsProcessor required from start
- MCP server tool calling (NOT wrapping as MCP server)
- Invocation/Result canisters

**Rationale**: Without function calling, the tool is nearly worthless for intended use cases.

**Details**: [invocations.md](invocations.md)

### ADR-005: Multimodal Content

**Status**: ACCEPTED

**Decision**: Design for multimodal from start with separate content types

**Implementation**:
- `TextualContent`, `ImageContent` designed immediately
- `AudioContent`, `VideoContent` designed but implementation deferred
- Each modality has its own type (not generic `MultimodalContent`)

**Rationale**: Architectural decision cannot be retrofitted; primary requirement for reimplementation.

### ADR-006: Type Annotations

**Status**: ACCEPTED

**Decision**: Full type annotations required from day one

**Requirements**:
- All functions, methods, and class attributes typed
- Strong static typing with Protocols
- Runtime validation at boundaries

**Rationale**: ai-experiments lacks many annotations; learned lesson for new codebase.

### ADR-007: Streaming Default

**Status**: ACCEPTED

**Decision**: Streaming is opt-out, not opt-in

**Implementation**:
- Streaming by default for better UX
- CLI flag to disable when needed
- Non-streaming mode for specific use cases

**Rationale**: Modern LLM interaction pattern; smoother user experience.

## Key Design Decisions

### Content Storage Strategy

**Decision**: Hybrid approach with size-based threshold

**Implementation**:
- Inline storage: Text < 1KB (fast loading)
- Hash storage: Text ≥ 1KB (deduplication for forks)
- Hash storage: Always for system prompts (shared across conversations)
- Hash storage: Always for non-textual content (images, audio, video)

**Benefits**:
- Simplicity for common case (small messages)
- Optimization where it matters (large content)
- Space efficiency for forked conversations
- No unnecessary I/O overhead

**Analysis**: [content-storage-analysis.md](content-storage-analysis.md)

### Ensemble Architecture

**Decision**: Keep ensembles for MCP server lifecycle management

**Key insight**: MCP servers ARE ensembles
- Shared lifecycle (connect/disconnect)
- Shared configuration (URL, auth, timeouts)
- Name scoping (multiple servers can have same tool name)

**Minimal design**:
```python
@dataclass
class Ensemble:
    name: str
    invokers: dict[str, Invoker]
    config: dict[str, Any] = field(default_factory=dict)
    connection: Any | None = None  # MCP client if applicable
```

**Analysis**: [ensembles-analysis.md](ensembles-analysis.md)

### Deduplicator Strategy

**Decision**: Skip deduplicators for MVP

**What they actually do**: Context management - trim stale tool results from conversation history

**Critical tradeoff**: Cache-busting vs token savings
- Without: Server-side caching works (~90% cheaper), but tokens accumulate
- With: Save tokens, but bust cache (re-process entire conversation)

**When to add** (future):
- Conversations routinely exceed 50-75% of context window
- Many file edit operations with large content
- Token costs exceed cache-miss costs

**Analysis**: [deduplicator-analysis.md](deduplicator-analysis.md)

## MVP Requirements

### Non-Negotiable
- Tool/function calling support
- Multimodal content architecture (ImageContent from start)
- Conversation forking
- Full type annotations

### Required Provider Implementations
- Anthropic (primary)
- Ollama or VLLM (with server forking if necessary)
- OpenAI Conversations API (legacy)
- OpenAI Responses API (new)

### Deferred to Future
- Google provider (models not yet proven)
- Prompt templates/libraries
- Cost tracking (nice-to-have)
- Conversation import/export
- Multiple simultaneous conversations (TUI concern)
- Wrapping converser as MCP server

## Implementation Roadmap

### Phase 1: Core Foundations (MVP)

1. **Base Protocols**
   - Canister hierarchy (all 6 types)
   - Content protocol (Text, Image)
   - Provider/Client protocols
   - Event definitions

2. **Storage Layer**
   - JSONL message serialization
   - TOML metadata handling
   - Hybrid content storage (inline + hash)
   - Conversation forking

3. **Message Events**
   - Single callback with pattern matching
   - Event hierarchy implementation
   - Provider event emission

4. **Tool Calling**
   - Invoker core abstraction
   - Ensemble for grouping
   - InvocationsProcessor
   - MCP server tool discovery/invocation
   - Configuration loading from TOML

5. **Provider Implementation**
   - Anthropic provider (all processors)
   - Streaming and non-streaming modes
   - Tool calling integration

6. **CLI Interface**
   - Basic commands (chat, list, show)
   - Provider selection
   - Conversation management

### Phase 2: Extended Features

1. Additional providers (OpenAI, Ollama/VLLM)
2. Deduplicators (if needed based on usage patterns)
3. Tool result caching
4. Permission/sandbox system for tools
5. Wrapping converser as MCP server
6. Conversation import/export

## Detailed Design Documents

### Architecture Analyses
- **[callbacks-vs-events.md](callbacks-vs-events.md)**: Complete comparison of callback vs event bus architectures, including stakeholder feedback and final single-callback decision
- **[content-storage-analysis.md](content-storage-analysis.md)**: Deep analysis of storage strategies with quantitative scenarios and hybrid approach justification
- **[deduplicator-analysis.md](deduplicator-analysis.md)**: Actual ai-experiments implementation, cache-busting tradeoffs, and recommendation to skip for MVP
- **[ensembles-analysis.md](ensembles-analysis.md)**: MCP server lifecycle requirements and ensemble architecture justification
- **[invocations.md](invocations.md)**: Complete tool calling architecture with MCP integration, ensemble decisions, and implementation details
- **[roles-vs-canisters-analysis.md](roles-vs-canisters-analysis.md)**: Clarification that no merge occurred - ai-experiments pattern preserved

### Reference Materials
- ai-experiments: https://github.com/emcd/ai-experiments
- MCP Specification: https://modelcontextprotocol.io/
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- OpenAI SDK: https://github.com/openai/openai-python

## Summary: What We're Preserving vs Changing

### Preserved from ai-experiments
- All canister types (User, Assistant, Supervisor, Document, Invocation, Result)
- Callback pattern for message events (simplified to single callback)
- Directory hierarchy for storage
- All processors (Controls, Messages, Invocations, Tokenizer)
- Ensemble abstraction for tool grouping
- TOML for configuration
- ModelsIntegrator with regex pattern matching

### Enhancements/Changes
- JSONL for message history (vs JSON)
- Single callback with pattern matching (vs multiple typed callbacks)
- Full type annotations from start
- Multimodal content designed from start
- Streaming opt-out by default
- Conversation forking in MVP
- Hybrid content storage (inline + hash)
- Skip deduplicators for MVP (rely on caching)

### Explicitly Deferred
- Prompt templates/libraries
- Google provider
- Multiple simultaneous conversations
- Cost tracking
- Wrapping converser as MCP server
