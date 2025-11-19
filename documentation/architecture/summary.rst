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
System Overview
*******************************************************************************

This document provides a high-level overview of the system architecture,
describing major components and their relationships. For detailed implementation
specifications, see the design documents under ``designs/``. For architectural
decisions and their rationale, see the ADRs under ``decisions/``.

Architectural Vision
===============================================================================

Build a simpler, focused architecture for LLM conversation management that
incorporates learnings from the ai-experiments project. The system provides a
provider-agnostic conversation layer with support for multiple LLM providers,
tool/function calling via MCP servers, and flexible conversation history
management.

Core architectural principles:

* **Provider abstraction**: Unified message format works across all LLM
  providers
* **Type-safe**: Full type annotations throughout the codebase
* **Async-first**: All I/O operations use async/await
* **Configuration-driven**: Providers and tools configured via TOML files
* **Event-driven**: Simple callback mechanism for lifecycle events
* **Multimodal**: Text, images, and future content types supported from start

Major Components
===============================================================================

The system consists of five major components:

1. **Message Abstraction Layer**: Normalized message representation
2. **Provider Interface**: LLM provider abstraction and adapters
3. **Storage Layer**: Conversation and content persistence
4. **Event System**: Lifecycle event handling via callbacks
5. **Invocables Framework**: Tool/function calling with MCP support

Message Abstraction Layer
-------------------------------------------------------------------------------

**Purpose**: Provide a unified message format that works across all LLM
providers, abstracting away provider-specific formats.

**Key abstractions**:

* **Message types**: User input, assistant responses, system instructions,
  reference documents, tool invocations, tool results
* **Multimodal content**: Text, images, audio, video (future)
* **Content storage**: Hybrid inline/hash-based strategy

**Message type hierarchy**:

* User messages
* Assistant responses
* System/supervisor instructions (system prompts)
* Reference documents
* Tool invocation requests
* Tool execution results

**Content model**:

* Textual content with MIME type support
* Image/visual content
* Audio content (future)
* Video content (future)

**Storage strategy** (see :doc:`decisions/002-content-storage-strategy`):

* Small text (< 1KB): Stored inline in messages for fast loading
* Large text (>= 1KB): Hash-based storage for deduplication
* System prompts: Always hash-based for cross-conversation sharing
* Binary content: Always hash-based storage

**Design details**: See ``designs/message-abstraction.rst``

Provider Interface
-------------------------------------------------------------------------------

**Purpose**: Abstract LLM provider APIs behind a unified interface, enabling
seamless provider switching and multi-provider support.

**Core protocols**:

* **Provider**: Client creation and model discovery
* **Client**: Model access and conversation execution
* **Model**: LLM instance with specific capabilities

**Provider processors**:

* **MessagesProcessor**: Convert between normalized and provider-native message
  formats (normalization/nativization)
* **ControlsProcessor**: Handle model parameters (temperature, max_tokens, etc.)
* **InvocationsProcessor**: Manage tool/function calling
* **ConversationTokenizer**: Count tokens for cost tracking

**MVP providers**:

* Anthropic (primary)
* Ollama or VLLM (one local provider)

**Future providers**:

* OpenAI Conversations API (legacy)
* OpenAI Responses API (new)

**Normalization**: Provider-specific formats → unified message representation

**Nativization**: Unified message representation → provider-specific formats

**Design details**: See ``designs/provider-abstraction.rst``

Storage Layer
-------------------------------------------------------------------------------

**Purpose**: Persist conversations and content in human-readable, editable
formats.

**Conversation storage structure**:

.. code-block:: text

   conversations/{id}/
   ├── messages.jsonl        # One message per line
   └── metadata.toml         # Name, created, tags, etc.

**Content storage structure** (see :doc:`decisions/002-content-storage-strategy`):

.. code-block:: text

   content/{hash}/
   ├── data                  # Binary content or large text
   └── metadata.toml         # MIME type, size, etc.

**JSONL advantages**:

* One message per line enables line-by-line processing
* Human-readable and editable with standard text tools
* Appendable without parsing entire file
* Standard JSON format for each line

**TOML advantages**:

* Human-readable configuration format
* Type-safe value representation
* Standard for Python project configuration

**Content deduplication**:

* Hash-based content addressing (SHA-256 or similar)
* Shared content across conversations (system prompts, large responses)
* Efficient for forked conversations

**Design details**: See ``designs/storage-architecture.rst``

Event System
-------------------------------------------------------------------------------

**Purpose**: Enable extensibility and UI integration through conversation
lifecycle events.

**Event handling pattern** (see :doc:`decisions/001-event-handling-pattern`):

Single callback with Python 3.10+ pattern matching:

.. code-block:: python

   def handle_conversation_events(event: ConversationEvent) -> None:
       match event:
           case MessageStartedEvent():
               # Allocate UI cell for new message
               pass
           case MessageProgressEvent(chunk=chunk):
               # Append streaming content
               pass
           case MessageCompletedEvent():
               # Finalize message display
               pass
           case MessageFailedEvent(error=error):
               # Show error and rollback
               pass
           case _:
               # Ignore unknown events
               pass

**Event types**:

* ``MessageStartedEvent``: Message allocation begins
* ``MessageProgressEvent``: Streaming chunk received
* ``MessageUpdatedEvent``: Message content updated
* ``MessageCompletedEvent``: Message finalized
* ``MessageFailedEvent``: Generation failed

**Benefits**:

* Simple interface (one callback parameter)
* Extensible (new events don't break existing code)
* Forward compatible (unknown events ignored)
* Type-safe event objects

**Use cases**:

* CLI progress indicators
* GUI message rendering
* TUI live updates
* Logging and metrics collection

**Design details**: See ``designs/event-system.rst``

Invocables Framework
-------------------------------------------------------------------------------

**Purpose**: Enable LLMs to invoke external tools and functions, with support
for local tools and MCP servers.

**Core components**:

**Invoker**: Wraps a callable tool with metadata and validation

.. code-block:: python

   @dataclass
   class Invoker:
       name: str
       invocable: Callable  # Async callable
       arguments_schema: dict  # JSON Schema
       ensemble: Ensemble

**Ensemble**: Groups related invokers for lifecycle management (see
:doc:`decisions/003-tool-organization-with-ensembles`)

.. code-block:: python

   @dataclass
   class Ensemble:
       name: str
       invokers: dict[str, Invoker]
       config: dict[str, Any]
       connection: Any | None  # MCP client if applicable

**MCP integration** (see :doc:`decisions/005-tool-calling-mvp-scope`):

* Connect to external MCP servers via stdio or HTTP
* Discover tools from MCP servers
* Invoke MCP tools identically to local tools
* One ensemble per MCP server for lifecycle management

**Tool organization**:

* Local tools organized into logical ensembles
* MCP servers naturally map to ensembles
* Name scoping prevents conflicts between sources
* Configuration per ensemble

**MVP scope** (see ADR-005):

* Invoker framework with schema validation
* Ensemble organization
* MCP server integration (calling tools ON servers)
* Fail-fast error handling

**Deferred to Phase 2**:

* Deduplicators for conversation trimming (see
  :doc:`decisions/004-conversation-history-trimming`)
* Wrapping converser AS an MCP server
* Advanced context management

**Design details**: See ``designs/tool-calling.rst`` and
``designs/mcp-integration.rst``

Component Relationships
===============================================================================

Data Flow
-------------------------------------------------------------------------------

**Conversation execution flow**:

1. User provides input (CLI command or API call)
2. Message Abstraction Layer creates normalized user message
3. Storage Layer persists message to JSONL
4. Provider Interface nativizes messages to provider format
5. LLM provider processes conversation and returns response
6. Provider Interface normalizes response to unified format
7. If tool calls requested:

   a. Invocables Framework finds and validates tool
   b. Tool executes and returns result
   c. Result added as normalized message
   d. Flow returns to step 4 (send result to LLM)

8. Storage Layer persists final messages
9. Event System notifies callbacks of completion

**Event flow**:

1. Provider starts generating response → ``MessageStartedEvent``
2. Provider streams content chunks → ``MessageProgressEvent`` (multiple)
3. Provider completes successfully → ``MessageCompletedEvent``
4. OR provider fails → ``MessageFailedEvent``

**Content loading flow**:

1. Read ``messages.jsonl`` file
2. For each message, check content items:

   a. If ``{"type": "text", "text": "..."}`` → use inline text
   b. If ``{"type": "text", "content_id": "..."}`` → load from content store
   c. If ``{"type": "image", "content_id": "..."}`` → load from content store

3. Cache loaded content for performance
4. Return fully hydrated conversation

Component Dependencies
-------------------------------------------------------------------------------

**Dependency graph** (arrows show "depends on"):

.. code-block:: text

   Provider Interface
   ├── → Message Abstraction (for normalization/nativization)
   └── → Invocables Framework (for tool calling)

   Invocables Framework
   ├── → Message Abstraction (for tool invocation/result messages)
   └── → Storage Layer (for content storage if needed)

   Event System
   └── → Message Abstraction (event types reference messages)

   Storage Layer
   └── → Message Abstraction (persists messages and content)

**Layer separation**:

* Message Abstraction is the foundation (no dependencies)
* Storage Layer depends only on Message Abstraction
* Provider Interface and Invocables are at same level
* Event System is cross-cutting (used by all components)

**Configuration flow**:

1. Load provider configuration from TOML
2. Load ensemble/invoker configuration from TOML
3. Initialize providers with configuration
4. Initialize ensembles and register invokers
5. Connect to MCP servers (if configured)
6. System ready for conversations

Deployment Architecture
===============================================================================

For MVP, deployment is simple:

**Single-machine deployment**:

* CLI application installed via ``uv`` or ``pipx``
* Local filesystem storage in user's home directory
* MCP servers as separate processes (stdio or HTTP)
* Provider API calls via HTTPS to external services

**Configuration location**:

* User-specific: ``~/.config/vibe-llms-converser/``
* Project-specific: ``.vibe-llms-converser/`` in current directory
* Ensemble definitions: ``data/ensembles/`` in package

**Data storage location**:

* Conversations: ``~/.local/share/vibe-llms-converser/conversations/``
* Content: ``~/.local/share/vibe-llms-converser/content/``

**Future deployment models** (Phase 2+):

* Multi-user server deployment
* Cloud storage integration
* Distributed conversation sync
* Web interface frontend

Key Architectural Patterns
===============================================================================

Protocol-Based Interfaces
-------------------------------------------------------------------------------

All major components use Protocol classes for interface definitions:

.. code-block:: python

   class Provider(Protocol):
       def produce_client(...) -> Client: ...

   class Client(Protocol):
       def access_model(...) -> Model: ...

   class Invoker(Protocol):
       async def __call__(...) -> Any: ...

**Benefits**:

* Structural subtyping (duck typing with type safety)
* No forced inheritance hierarchies
* Easy to add new implementations
* Type checker validates compatibility

Processor Pattern
-------------------------------------------------------------------------------

Provider adapters split responsibilities into focused processors:

* **MessagesProcessor**: Message format conversion
* **ControlsProcessor**: Parameter handling
* **InvocationsProcessor**: Tool calling
* **ConversationTokenizer**: Token counting

**Benefits**:

* Single responsibility per processor
* Composable (providers configure which processors they need)
* Testable in isolation
* Reusable across similar providers

Content Addressing
-------------------------------------------------------------------------------

Hash-based content storage enables deduplication:

.. code-block:: python

   content_id = sha256(content).hexdigest()
   store_path = f"content/{content_id}/data"

**Benefits**:

* Automatic deduplication (same content = same ID)
* Immutable content (can't modify without changing ID)
* Cache-friendly (stable IDs)
* Fork-efficient (conversations share content)

Configuration-Driven Architecture
-------------------------------------------------------------------------------

Providers, ensembles, and invokers configured via TOML:

.. code-block:: toml

   [provider.anthropic]
   enabled = true
   api_key_env = "ANTHROPIC_API_KEY"

   [ensemble.io]
   enabled = true

   [[ensemble.io.invokers]]
   name = "read_file"
   enabled = true

**Benefits**:

* No code changes for configuration updates
* Version control configuration separately from code
* Easy to enable/disable features
* Declarative over imperative

References
===============================================================================

* **ADRs**: See ``decisions/`` for architectural decisions and rationale
* **Design docs**: See ``designs/`` for detailed specifications
* **Filesystem**: See :doc:`filesystem` for code organization
* **PRD**: See :doc:`../prd` for requirements and goals
