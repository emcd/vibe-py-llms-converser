# LLM Conversation Architecture - Initial Analysis

**Date**: 2025-11-15
**Session**: Initial architecture review from ai-experiments project

## Project Goals

Build a simpler, focused architecture for LLM conversation management with learnings from the ai-experiments project. Core features:

1. **Normalization Layer**: Unified message format across different LLM providers
2. **Provider Abstraction**: "Nativize" normalized messages to provider-specific formats
3. **History Management**: Simple CLI for managing conversation history
4. **Callback/Message Bus**: Event-driven architecture for provider interactions

## Architecture Review from ai-experiments

### Core Patterns Observed

#### 1. Message Normalization (messages/core.py)

**Canister Pattern**: Messages are encapsulated in role-based "canister" objects:
- `AssistantCanister`, `UserCanister`, `DocumentCanister`, `InvocationCanister`, `ResultCanister`, `SupervisorCanister`
- Each canister has a `role` property and can contain multiple content items
- Content uses a polymorphic `Content` protocol (currently `TextualContent` with MIME type support)

**Persistence**: Bidirectional save/restore with TOML descriptors and directory-based organization

**Strengths**:
- Clean role-based abstraction
- MIME-type classification for content
- Symmetric persistence operations

**Simplification Opportunities**:
- Could reduce number of canister types for initial MVP
- Directory hierarchy might be over-engineered for simple CLI use case

#### 2. Invocables Framework (invocables/core.py)

**Key Components**:
- `Invoker`: Wraps tool functions with schema validation
- `Ensemble`: Groups related invokers
- `Deduplicator`: Prevents duplicate tool calls
- Async preparation pipeline with configuration-driven setup

**Strengths**:
- Configuration-driven, declarative approach
- JSON Schema validation for arguments
- Graceful error handling

**Questions**:
- Do we need the full ensemble abstraction for MVP?
- Is deduplication necessary for initial version?

#### 3. Provider Architecture (providers/core.py, interfaces.py)

**Core Abstractions**:
- `Provider` protocol: Produces clients
- `Client` protocol: Manages model access
- Processor-based design for specialized handling:
  - `ControlsProcessor`: Model parameters
  - `MessagesProcessor`: Message conversion
  - `InvocationsProcessor`: Tool invocations
  - `ConversationTokenizer`: Token counting

**Configuration**:
- Descriptor-driven instantiation via `from_descriptor()`
- Genus-based model organization
- `ModelsIntegrator` for attribute merging with regex pattern matching

**Strengths**:
- Clean separation of concerns
- Provider-agnostic through protocols
- Flexible configuration system

**Potential Simplifications**:
- Start with fewer processors (messages + controls)
- Defer tokenizer implementation
- Simpler model discovery/organization

#### 4. Anthropic Implementation (providers/clients/anthropic/conversers.py)

**Message Conversion Strategy**:
- Role-based dispatch via `_nativize_message()`
- Refinement pipeline: `_refine_native_messages()` merges consecutive user messages and filters unmatched tool uses
- Special handling for supervisor instructions → system parameters

**Streaming**:
- Dual-mode: complete (single request) vs continuous (event streaming)
- Event-driven accumulation with per-event handlers
- Deferred tool result matching

**Provider Configuration** (attributes.toml):
- Model pattern matching
- Capability flags (supervisor instructions, continuous responses, function invocations)
- Token limits and control parameters (temperature, top-k, etc.)

**Strengths**:
- Clean streaming abstraction
- Flexible dual-mode operation
- Well-structured configuration

## Initial Architecture Proposal for vibe-py-llms-converser

### Phase 1: Core Foundations (MVP)

#### 1. Message Abstraction

```python
# Simplified canister hierarchy
- Message (base protocol)
  - UserMessage
  - AssistantMessage
  - SystemMessage  # for supervisor/system instructions
  - ToolCallMessage  # for tool invocations (future)
  - ToolResultMessage  # for tool results (future)

# Content model
- TextContent (primary)
- MultimodalContent (future: images, audio)
```

**Rationale**: Start with essential message types, defer complex tool handling

#### 2. Provider Interface

```python
# Core protocols
- Provider
  - name: str
  - produce_client() -> Client

- Client
  - provider: Provider
  - send_message() -> Response
  - send_message_streaming() -> AsyncIterator[ResponseChunk]

# Provider-specific processors (initially just 2)
- MessageProcessor: normalize ↔ native conversion
- ControlsProcessor: map parameters to provider format
```

**Rationale**: Minimal viable abstraction, extensible for future processors

#### 3. History Management

```python
# Simple conversation model
- Conversation
  - id: str
  - messages: list[Message]
  - metadata: dict
  - save() / load()

# Storage
- JSON or JSONL format (one file per conversation)
- Directory-based organization: conversations/{id}.jsonl
```

**Rationale**: Simple, inspectable format; defer complex directory hierarchies

#### 4. Callback/Event System

Two approaches to consider:

**Option A: Callback-based** (simpler, like ConversationReactors):
```python
class ConversationCallbacks:
    on_start: Callable
    on_progress: Callable  # for streaming chunks
    on_complete: Callable
    on_error: Callable
```

**Option B: Message bus** (more extensible):
```python
class EventBus:
    publish(event: Event)
    subscribe(event_type: EventType, handler: Callable)

# Events
- ConversationStarted
- MessageReceived
- StreamingChunk
- ConversationCompleted
- ConversationFailed
```

**Initial Recommendation**: Start with callbacks (simpler), design for future message bus migration

#### 5. CLI Interface

```bash
# Basic commands
vibe chat                      # Start new conversation
vibe chat --continue <id>      # Continue conversation
vibe list                      # List conversations
vibe show <id>                 # Show conversation history
vibe export <id>               # Export conversation

# Provider selection
vibe chat --provider anthropic
vibe chat --model claude-sonnet-4.5
```

### Phase 2: Enhanced Features (Future)

- Tool/function calling support
- Multiple provider implementations (OpenAI, Google, etc.)
- Advanced history management (search, tagging, archiving)
- Message bus for complex event workflows
- Multimodal content support
- Token counting and cost tracking
- Conversation branching/forking

## Key Questions for Discussion

### 1. Message Format

**Q**: Should we use a TOML-based persistence like ai-experiments, or prefer JSON/JSONL?

**Considerations**:
- TOML: Human-readable, good for configuration
- JSON/JSONL: Simpler parsing, better for streaming, more universal tooling
- **Recommendation**: JSON/JSONL for messages, TOML for provider config

### 2. Async vs Sync API

**Q**: Should the public API be async (like ai-experiments) or provide both sync and async?

**Considerations**:
- Async: Better for streaming, non-blocking I/O
- Sync: Simpler for CLI usage
- **Recommendation**: Async core with optional sync wrappers for CLI

### 3. Configuration Strategy

**Q**: How should we handle provider configuration?

**Options**:
- Embedded TOML files (like ai-experiments)
- Python dataclasses with defaults
- External config files with override mechanism
- **Recommendation**: Python dataclasses for code, TOML for user overrides

### 4. Tool/Function Calling

**Q**: Should we include tool calling in MVP, or defer to Phase 2?

**Considerations**:
- Essential for many LLM use cases
- Adds significant complexity
- **Recommendation**: Design the message abstraction to support it, but implement in Phase 2

### 5. Streaming Strategy

**Q**: Should streaming be the default mode, or opt-in?

**Considerations**:
- Streaming provides better UX for long responses
- Not all providers support streaming uniformly
- **Recommendation**: Support both, make streaming opt-in via CLI flag

### 6. Type System

**Q**: How strict should type checking be? Runtime validation vs static typing?

**Observations from ai-experiments**:
- Heavy use of Protocol and runtime_checkable
- Generic types for flexibility
- **Recommendation**: Strong static typing with Protocols, runtime validation at boundaries

### 7. Error Handling

**Q**: How should we handle provider-specific errors?

**Approach**:
- Normalize common errors (rate limit, auth, timeout)
- Preserve provider-specific error details
- Map to user-friendly CLI messages
- **Recommendation**: Exception hierarchy with provider context

## Architecture Decisions to Make

### ADR-001: Message Storage Format

**Status**: Proposed

**Decision**: Use JSONL for conversation storage
- One message per line for streaming/incremental writes
- Easy to parse and debug
- Universal tooling support

**Alternatives Considered**:
- TOML (verbose for many messages)
- SQLite (over-engineered for MVP)
- Pickle (not human-readable)

### ADR-002: Provider Plugin System

**Status**: Proposed

**Decision**: Start with hardcoded providers, design for plugin architecture
- Phase 1: Anthropic provider built-in
- Phase 2: Entry point-based plugin discovery

**Rationale**: Avoid premature abstraction

### ADR-003: Callback vs Message Bus

**Status**: Proposed

**Decision**: Callbacks for MVP, design for message bus migration
- Simple callback protocol initially
- Events are value objects (can be published to bus later)

**Migration Path**: Events can be passed to callbacks now, published to bus in future

## Next Steps

1. **Finalize message abstraction design**
   - Decide on exact message types
   - Define content protocol
   - Design serialization format

2. **Create provider interface specification**
   - Define Protocol contracts
   - Specify processor responsibilities
   - Document conversion expectations

3. **Design conversation storage schema**
   - JSONL format specification
   - Metadata structure
   - Migration strategy

4. **Prototype Anthropic provider**
   - Start with simple message conversion
   - Add streaming support
   - Test with real API

5. **Build minimal CLI**
   - Basic chat command
   - History list/show
   - Configuration handling

## Open Questions for User

1. Should we support multiple simultaneous conversations (tabs/sessions)?
2. Do you want conversation import/export to other formats (Markdown, HTML)?
3. Should the CLI support conversation templates or saved prompts?
4. Do you want built-in support for common patterns (system prompts library, few-shot examples)?
5. How important is backwards compatibility with ai-experiments conversation format?
6. Should we include cost tracking (token usage × pricing)?
7. Do you want to support conversation sharing/collaboration features (future)?

## References

- ai-experiments: https://github.com/emcd/ai-experiments
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- OpenAI SDK: https://github.com/openai/openai-python

## Ideas for Future Exploration

1. **Conversation Analysis**: Summarization, statistics, topic extraction
2. **Multi-Provider Routing**: Send to different providers based on task type
3. **Caching Layer**: Avoid redundant API calls for similar prompts
4. **Conversation Templates**: Pre-built conversation starters for common tasks
5. **Integration with MCP Servers**: Leverage existing tool ecosystems
6. **Web Interface**: Optional GUI alongside CLI
7. **Collaboration Features**: Share conversations, multi-user editing
8. **Provider Fallback**: Automatic retry with different provider on failure
