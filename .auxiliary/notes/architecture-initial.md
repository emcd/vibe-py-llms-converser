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

**Decision**:
- Keep all canister types from ai-experiments - they provide valuable semantic distinction at the persistence layer
- Maintain directory hierarchy - proven over 2.5 years of production use and prevents directory bloat

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

**Decision**:
- Keep full ensemble abstraction - already working and useful for grouping related tools
- Maintain deduplicator - minimal complexity for proven benefit
- **Critical**: Must support MCP servers regardless of ensemble architecture chosen

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

**Decision**:
- Keep all processors from ai-experiments (ControlsProcessor, MessagesProcessor, InvocationsProcessor, ConversationTokenizer)
- Model discovery/organization approach needs clarification (see Open Questions)

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
# Complete canister hierarchy (preserved from ai-experiments)
- Canister (base protocol)
  - UserCanister
  - AssistantCanister
  - SupervisorCanister  # for system/supervisor instructions
  - DocumentCanister    # for document/reference content
  - InvocationCanister  # for tool invocations
  - ResultCanister      # for tool results

# Content model (modality-specific types)
- Content (base protocol)
  - TextualContent      # text with MIME type support
  - ImageContent        # images/visual content
  - AudioContent        # audio content (future)
  - VideoContent        # video content (future)
```

**Rationale**:
- All canister types preserved - they provide semantic distinction at persistence layer
- Nomenclature maintains Latin etymology consistency (SupervisorCanister not SystemCanister)
- Multimodal content designed from the start with separate content types per modality
- Invocation/Result rather than ToolCall/ToolResult to maintain existing terminology

#### 2. Provider Interface

```python
# Core protocols (preserved from ai-experiments)
- Provider
  - name: str
  - produce_client() -> Client

- Client
  - provider: Provider
  - access_model() -> Model
  - survey_models() -> list[Model]

# Provider-specific processors (all preserved)
- ControlsProcessor: Model parameters
- MessagesProcessor: normalize ↔ native conversion
- InvocationsProcessor: Tool invocations (MVP requirement)
- ConversationTokenizer: Token counting
```

**Rationale**: Keep proven processor architecture from ai-experiments

#### 3. History Management

```python
# Conversation model (with branching support)
- Conversation
  - id: str
  - canisters: list[Canister]
  - metadata: ConversationMetadata  # name, created, updated, tags, etc.
  - save() / restore()
  - fork(from_index: int) -> Conversation  # create conversation fork

# Storage (hybrid format)
- JSONL for message history: conversations/{id}/messages.jsonl
- TOML for metadata: conversations/{id}/metadata.toml
- Directory hierarchy: proven ai-experiments structure for content separation

# Content storage (non-textual content)
- Separate directories with content-based IDs (hash-based)
- Enables content sharing across forked conversations
- Example structure:
  - conversations/{conversation-id}/messages.jsonl       # Textual content inline
  - conversations/{conversation-id}/metadata.toml
  - content/{content-hash}/data                          # Actual binary content
  - content/{content-hash}/metadata.toml                 # MIME type, size, etc.
```

**Rationale**:
- JSONL improves readability/navigability over single JSON
- TOML for metadata maintains human-readable configuration
- Directory hierarchy prevents bloat and separates concerns
- **Content deduplication**: Hash-based storage allows forked conversations to reference same content
- **Efficient forking**: Only textual content duplicated; images/videos shared via reference
- Conversation forking included (already implemented in ai-experiments, not complex)

#### 4. Callback/Event System

**Decision**: Event-based callbacks with migration path to event bus

See detailed analysis in [callbacks-vs-events.md](callbacks-vs-events.md)

```python
# Events as value objects (serializable)
@dataclass
class ConversationProgressEvent:
    conversation_id: str
    timestamp: datetime
    chunk: str
    metadata: dict[str, Any]

# Callbacks accept event objects (preserving ConversationReactors pattern)
class ConversationReactors:
    allocator: Callable[[ConversationStartedEvent], None]
    progress: Callable[[ConversationProgressEvent], None]
    success: Callable[[ConversationCompletedEvent], None]
    failure: Callable[[ConversationFailedEvent], None]
    updater: Callable[[ConversationUpdatedEvent], None]
    deallocator: Callable[[ConversationEndedEvent], None]
```

**Rationale**:
- Maintains proven callback simplicity from ai-experiments
- Events as first-class objects enable future event bus migration
- Events are serializable for MCP integration
- Clear migration path when multiple consumers needed

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

### MVP Requirements (Phase 1)

**Non-Negotiable**:
- Tool/function calling support (InvocationsProcessor)
- Multimodal content architecture (ImageContent from start)
- Conversation forking
- Full type annotations throughout codebase

**Provider Implementations Required**:
- Anthropic (primary)
- Ollama or VLLM (with server forking if necessary)
- OpenAI Conversations API (legacy)
- OpenAI Responses API (new)

**Deferred to Future**:
- Google provider (models not yet proven)
- Prompt templates/libraries
- Cost tracking (nice-to-have)
- Conversation import/export (backward compatibility not essential)
- Multiple simultaneous conversations (TUI concern for later)

## Decisions Made (From Review)

### 1. Message Format
**Decision**: JSONL for message history, TOML for conversation metadata and provider configuration
- Improves readability and navigability over single JSON
- TOML for human-readable metadata

### 2. Async vs Sync API
**Decision**: Async-first
- Start with async API
- Add sync wrappers later only if strong case emerges

### 3. Configuration Strategy
**Decision**: Python dataclasses for code, TOML for provider configuration and user overrides
- Preserves ai-experiments approach

### 4. Tool/Function Calling
**Decision**: **MVP requirement** (non-negotiable)
- Essential for usefulness
- InvocationsProcessor required from start

### 5. Streaming Strategy
**Decision**: Streaming is **opt-out**, not opt-in
- Provides smoother user experience by default
- Can opt-out for specific use cases (e.g., MCP servers)

### 6. Type System
**Decision**: Full type annotations from start
- Strong static typing with Protocols
- Runtime validation at boundaries
- ai-experiments lacks many annotations; this project will be fully annotated

### 7. Error Handling
**Decision**: Exception hierarchy with `__cause__` chaining
- Normalized common errors (rate limit, auth, timeout)
- Preserve provider-specific error details
- Capture specific messages for debugging

### 8. Architecture Elements
**Decisions**:
- Keep all canister types (User, Assistant, Supervisor, Document, Invocation, Result)
- Keep directory hierarchy from ai-experiments
- Keep full ensemble abstraction and deduplicator
- Keep all processors (Controls, Messages, Invocations, Tokenizer)
- Use Latin-derived nomenclature (SupervisorCanister not SystemCanister)
- Separate content types per modality (TextualContent, ImageContent, etc.)

## Architecture Clarifications

### Model Discovery/Organization: Keep ModelsIntegrator

**Decision**: **Preserve** the `ModelsIntegrator` with regex pattern matching and genus-based organization from ai-experiments

**Rationale** (from stakeholder review):
> "ModelsIntegrator attribute merging is valuable because when Anthropic releases new models...they can automatically inherit attributes...from their families."

**How it works**:
1. **Regex pattern matching**: Model names match patterns like `^claude-.*$`
2. **Family-based inheritance**: New models (e.g., `claude-sonnet-5.0`) automatically inherit attributes from their family pattern
3. **Attribute merging**: `ModelsIntegrator` merges configuration hierarchically:
   - Base provider defaults
   - Model family attributes (matched by regex)
   - Specific model overrides

**Example**:
```toml
# Provider-level defaults
[defaults]
temperature = 1.0

# Family pattern for all Claude models
[[models]]
pattern = "^claude-.*$"
max_tokens = 4096
supports_tools = true

# Specific model override
[[models]]
pattern = "^claude-opus-.*$"
max_tokens = 8192  # Opus models get higher limit
```

When `claude-sonnet-5.0` is released:
- Automatically matches `^claude-.*$` pattern
- Inherits `max_tokens = 4096` and `supports_tools = true`
- No configuration update needed

**Benefits**:
- **Future-proof**: New models work without configuration changes
- **DRY**: Family attributes defined once, inherited by all matching models
- **Flexible**: Specific models can override family defaults
- **Maintainable**: Less configuration to maintain

**Conclusion**: Keep the proven ModelsIntegrator architecture from ai-experiments

### Content Storage for Non-Textual Content

**Question** (from stakeholder review): How should we handle "non-textual content within messages" (images, audio, video)?

**Decision**: Use **hash-based content storage** with separate directories, preserving the ai-experiments approach

**Architecture**:

```
project-root/
├── conversations/
│   ├── conv-001/
│   │   ├── messages.jsonl          # Conversation messages
│   │   └── metadata.toml            # Conversation metadata
│   └── conv-002/                    # Forked from conv-001
│       ├── messages.jsonl
│       └── metadata.toml
└── content/
    ├── a1b2c3.../                   # Content hash (SHA-256)
    │   ├── data                     # Raw binary content
    │   └── metadata.toml            # MIME type, size, created
    └── d4e5f6.../
        ├── data
        └── metadata.toml
```

**Message storage with content references**:

```jsonl
{"role": "user", "timestamp": "2025-11-15T10:00:00Z", "content": [
  {"type": "text", "text": "What's in this image?"},
  {"type": "image", "content_id": "a1b2c3d4e5f6..."}
]}
```

**Content metadata example**:
```toml
# content/a1b2c3d4e5f6.../metadata.toml
[content]
id = "a1b2c3d4e5f6..."
mime_type = "image/png"
size_bytes = 524288
created = 2025-11-15T10:00:00Z
hash_algorithm = "sha256"
```

**Key benefits**:

1. **Deduplication**: Same image uploaded multiple times stored once
2. **Efficient forking**: Forked conversations reference same content
   - Original: `conv-001/messages.jsonl` → `content/a1b2c3.../data`
   - Fork: `conv-002/messages.jsonl` → `content/a1b2c3.../data` (same ref)
3. **Content integrity**: Hash-based IDs prevent corruption
4. **Space efficiency**: Large binary files not duplicated
5. **Clean separation**: Conversations contain only text + refs, content stored separately

**Content lifecycle**:

```python
# 1. User adds image to conversation
image_data = read_image("photo.png")
content_hash = hashlib.sha256(image_data).hexdigest()
content_id = f"{content_hash[:16]}..."  # Truncated for brevity

# 2. Store content if not already present
content_dir = Path(f"content/{content_id}")
if not content_dir.exists():
    content_dir.mkdir(parents=True)
    (content_dir / "data").write_bytes(image_data)
    (content_dir / "metadata.toml").write_text(toml.dumps({
        "content": {
            "id": content_id,
            "mime_type": "image/png",
            "size_bytes": len(image_data),
            "created": datetime.now().isoformat(),
            "hash_algorithm": "sha256",
        }
    }))

# 3. Add message with content reference
conversation.add_canister(UserCanister(
    content=[
        TextualContent(text="What's in this image?"),
        ImageContent(content_id=content_id)
    ]
))

# 4. Forking preserves references
forked_conv = conversation.fork(from_index=5)
# forked_conv still references content/{content_id}/data
```

**Garbage collection considerations**:

- Content not referenced by any conversation can be removed
- Implement reference counting or mark-and-sweep
- Defer to future; not essential for MVP

**Conclusion**: Hash-based content storage with separate directories enables efficient conversation forking while deduplicating binary content

## Architecture Decision Records

### ADR-001: Message Storage Format

**Status**: **ACCEPTED**

**Decision**: Use JSONL for message history, TOML for metadata
- JSONL: One message per line for streaming/incremental writes
- TOML: Human-readable conversation metadata (name, created, tags, etc.)
- TOML: Provider configuration

**Rationale**:
- Improves readability and navigability over single JSON
- Maintains human-readable configuration for metadata
- Universal tooling support for both formats

**Alternatives Considered**:
- Single JSON (less navigable, harder to read large conversations)
- SQLite (over-engineered for file-based storage)
- All-TOML (verbose for many messages)

### ADR-002: Provider Plugin System

**Status**: Proposed

**Decision**: Start with hardcoded providers, design for plugin architecture
- Phase 1: Anthropic, Ollama/VLLM, OpenAI (both APIs) built-in
- Future: Entry point-based plugin discovery

**Rationale**: Avoid premature abstraction while MVP proves architecture

### ADR-003: Callback vs Event Bus

**Status**: **ACCEPTED**

**Decision**: Event-based callbacks with migration path to event bus
- Callbacks accept event objects (ConversationReactors pattern from ai-experiments)
- Events are value objects (serializable, testable)
- Internal implementation can publish to optional event bus

**Migration Path**: See detailed analysis in [callbacks-vs-events.md](callbacks-vs-events.md)

### ADR-004: Function Calling in MVP

**Status**: **ACCEPTED**

**Decision**: Function/tool calling is **required** for MVP
- InvocationsProcessor must be implemented from start
- MCP server support is essential
- Invocation/Result canisters included

**Rationale**: Without function calling, the tool is nearly worthless for intended use cases

### ADR-005: Multimodal Content Architecture

**Status**: **ACCEPTED**

**Decision**: Design for multimodal from the start with separate content types
- TextualContent, ImageContent designed immediately
- AudioContent, VideoContent designed but implementation deferred
- Each modality has its own content type (not generic MultimodalContent)

**Rationale**: Primary requirement for reimplementation; architectural decision cannot be retrofitted

### ADR-006: Type Annotation Coverage

**Status**: **ACCEPTED**

**Decision**: Full type annotations required from day one
- All functions, methods, and class attributes typed
- Strong static typing with Protocols
- Runtime validation at boundaries

**Rationale**: ai-experiments lacks many annotations; learned lesson for new codebase

### ADR-007: Streaming Default Behavior

**Status**: **ACCEPTED**

**Decision**: Streaming is opt-out, not opt-in
- Provides smoother UX by default
- Non-streaming mode available for specific use cases
- CLI flag to disable streaming when needed

**Rationale**: Better user experience; modern LLM interaction pattern

## Next Steps

1. **Address model discovery/organization question**
   - Get stakeholder clarification on intended simplification
   - Document final decision

2. **Create detailed module specifications**
   - Canister hierarchy with full type signatures
   - Content protocol specifications
   - Processor interfaces

3. **Design conversation storage schema**
   - JSONL format specification for messages
   - TOML metadata structure
   - Directory hierarchy layout

4. **Implement core abstractions**
   - Base protocols (Canister, Content, Provider, Client)
   - Event definitions for callbacks
   - ConversationReactors structure

5. **Prototype Anthropic provider**
   - All four processors (Controls, Messages, Invocations, Tokenizer)
   - Streaming and non-streaming modes
   - MCP server integration points

6. **Build MVP CLI**
   - Chat command with streaming (opt-out)
   - History management (list, show, branch)
   - Configuration handling

7. **Implement additional providers**
   - Ollama/VLLM
   - OpenAI Conversations API
   - OpenAI Responses API

## Questions Answered (From Review)

1. ~~Should we support multiple simultaneous conversations?~~ **No, TUI concern for later**
2. ~~Do you want conversation import/export?~~ **Deferred; eventually want ai-experiments import**
3. ~~Should the CLI support conversation templates or saved prompts?~~ **No, not in MVP**
4. ~~Do you want built-in support for system prompts library?~~ **No initially, can revisit**
5. ~~How important is backwards compatibility with ai-experiments?~~ **Not important, but import capability desired eventually**
6. ~~Should we include cost tracking?~~ **Nice-to-have, not essential for MVP**
7. ~~Do you want to support conversation sharing/collaboration?~~ **Significantly in the future, not primary use case**

## References

- ai-experiments: https://github.com/emcd/ai-experiments
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- OpenAI SDK: https://github.com/openai/openai-python

## Ideas for Future Exploration

1. **Conversation Analysis**: Summarization, statistics, topic extraction
2. **Multi-Provider Routing**: Send to different providers based on task type
3. **Caching Layer**: Avoid redundant API calls for similar prompts
4. **Web Interface**: Optional GUI alongside CLI (current GUI in ai-experiments is more complex)
5. **Provider Fallback**: Automatic retry with different provider on failure
6. **Cost Tracking**: Token usage × pricing (nice-to-have)
7. **Conversation Import**: Import from ai-experiments, OpenAI/Anthropic data dumps
8. **TUI with Multiple Conversations**: Terminal UI with tabs/sessions support

## Summary of Key Architecture Decisions

### Preserved from ai-experiments
- All canister types (User, Assistant, Supervisor, Document, Invocation, Result)
- ConversationReactors callback pattern (enhanced with event objects)
- Directory hierarchy for storage
- All processors (Controls, Messages, Invocations, Tokenizer)
- Ensemble abstraction for tool grouping
- Deduplicator for tool calls
- TOML for configuration

### Enhancements/Changes
- JSONL for message history (instead of JSON)
- Event objects in callbacks (migration path to event bus)
- Full type annotations from start
- Multimodal content designed from start (separate types per modality)
- Streaming opt-out by default (not opt-in)
- Conversation forking included in MVP
- Function calling in MVP (non-negotiable)
- Multiple provider implementations (Anthropic, Ollama/VLLM, OpenAI×2)

### Explicitly Deferred
- Prompt templates/libraries
- Google provider
- Multiple simultaneous conversations
- Conversation import/export (for MVP)
- Web interface
- Cost tracking
