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
Product Requirements Document
*******************************************************************************

Executive Summary
===============================================================================

This project builds a simpler, focused architecture for LLM conversation
management, incorporating learnings from the ai-experiments project. The system
provides a provider-agnostic conversation layer with support for multiple LLM
providers, tool/function calling via MCP servers, and flexible conversation
history management.

Problem Statement
===============================================================================

Current LLM conversation management systems face several challenges:

* **Provider lock-in**: Conversation code is tightly coupled to specific LLM
  provider APIs (Anthropic, OpenAI, etc.), making it difficult to switch
  providers or support multiple providers simultaneously.

* **Message format inconsistency**: Each provider uses different message
  formats and conventions, requiring custom code for each integration.

* **Limited tool calling support**: Function/tool calling implementations are
  provider-specific and difficult to extend with custom tools or MCP servers.

* **Complex history management**: Conversation history storage and
  manipulation lacks a simple, human-readable format.

* **Missing abstractions**: No clean separation between message representation,
  provider communication, and conversation management.

Goals and Objectives
===============================================================================

Primary Objectives
-------------------------------------------------------------------------------

* **Provider abstraction**: Enable seamless switching between LLM providers
  (Anthropic, OpenAI, Ollama, VLLM) without changing application code.

* **Unified message format**: Establish a normalized message representation
  that works across all providers.

* **Tool calling support**: Implement comprehensive function/tool calling with
  MCP server integration for extensibility.

* **Simple history management**: Provide straightforward CLI tools for viewing,
  editing, and managing conversation history.

* **Type-safe architecture**: Full type annotations throughout to catch errors
  at development time rather than runtime.

Secondary Objectives
-------------------------------------------------------------------------------

* **Async-first design**: Native async/await support for efficient I/O
  operations.

* **Multimodal content**: Support text, images, and future content types
  (audio, video) from the start.

* **Configuration-driven**: Provider setup and tool registration via
  declarative configuration files.

* **Event-driven extensibility**: Simple callback mechanism for extending
  conversation lifecycle behavior.

Core Capabilities
===============================================================================

The system provides five core capabilities:

REQ-001: Message Normalization Layer (Critical)
-------------------------------------------------------------------------------

**Description**: Unified message format across different LLM providers.

**Rationale**: Different providers use incompatible message formats. A
normalized representation allows application code to be provider-agnostic.

**Acceptance Criteria**:

* Messages can be represented in a provider-neutral format.
* All provider-specific message formats can be converted to/from normalized
  format.
* Message types include: user input, assistant responses, system instructions,
  reference documents, tool invocations, and tool results.
* Multimodal content (text, images) is supported in normalized format.

REQ-002: Provider Abstraction (Critical)
-------------------------------------------------------------------------------

**Description**: "Nativize" normalized messages to provider-specific formats
and vice versa.

**Rationale**: Applications should work with normalized messages; providers
handle conversion to their native formats.

**Acceptance Criteria**:

* Provider interface supports message normalization (native → normalized) and
  nativization (normalized → native).
* Minimum viable providers: Anthropic, one local provider (Ollama or VLLM).
* Provider switching requires only configuration changes, not code changes.
* All provider-specific features are accessible through normalized interface
  where semantically equivalent.

REQ-003: Conversation History Management (Critical)
-------------------------------------------------------------------------------

**Description**: Simple CLI for managing conversation history with
human-readable storage format.

**Rationale**: Users need to inspect, edit, fork, and manage conversation
history outside the application.

**Acceptance Criteria**:

* Conversations stored in JSONL format (one message per line).
* Conversation metadata stored in TOML format.
* CLI commands for listing, viewing, creating, and deleting conversations.
* Support for conversation forking (branching from a specific message).
* Content deduplication via hash-based storage for large/binary content.

REQ-004: Event-Driven Architecture (High)
-------------------------------------------------------------------------------

**Description**: Event-driven architecture for provider interactions using
callback pattern.

**Rationale**: Applications need to react to conversation lifecycle events
(message allocation, streaming updates, completion, errors).

**Acceptance Criteria**:

* Callback mechanism for handling conversation lifecycle events.
* Events include: message allocation, streaming progress, completion, and
  failure.
* Extensions can handle events without modifying core code.
* Streaming is enabled by default.

REQ-005: Tool/Function Calling with MCP Support (Critical)
-------------------------------------------------------------------------------

**Description**: Function/tool invocation with MCP (Model Context Protocol)
server support.

**Rationale**: LLM utility depends on ability to invoke external tools and
functions. MCP provides a standard protocol for tool integration.

**Acceptance Criteria**:

* Tools can be registered and invoked by LLMs during conversations.
* MCP server integration: connect to MCP servers and discover/invoke their
  tools.
* Tool invocations represented as normalized message types.
* Support for tool argument validation via JSON Schema.
* Tool organization into logical groups for lifecycle management.

Architectural Principles
===============================================================================

Learnings from ai-experiments
-------------------------------------------------------------------------------

* **Full type annotations**: Type hints throughout the codebase from the start.
* **Async-first API design**: All I/O operations use async/await.
* **Configuration-driven provider setup**: Providers configured via TOML files.
* **Clear separation of concerns**: Well-defined interfaces between components.
* **Streaming by default**: Streaming enabled by default for responsive user
  experience.

New to this project
-------------------------------------------------------------------------------

* **JSONL for message history**: Improved readability and line-by-line
  processing compared to single JSON files.
* **Simplified event handling**: Streamlined callback mechanism for lifecycle
  events (see :doc:`architecture/decisions/001-event-handling-pattern`).
* **Efficient content storage**: Optimized storage strategy for different
  content sizes (see :doc:`architecture/decisions/002-content-storage-strategy`).
* **Multimodal content designed from start**: Text, images, and future content
  types supported from the beginning.

Target Users
===============================================================================

Primary User Persona
-------------------------------------------------------------------------------

**Role**: Python developer building LLM-powered applications

**Needs**:

* Switch between LLM providers without rewriting application code.
* Integrate custom tools and MCP servers with LLM conversations.
* Inspect and manipulate conversation history programmatically and manually.
* Build on a well-typed, async-first Python architecture.

**Technical proficiency**: Advanced Python developer familiar with async/await,
type hints, and modern Python tooling (uv, ruff, mypy).

**Usage context**: Command-line interface for conversation management;
programmatic API for application integration.

Secondary User Persona
-------------------------------------------------------------------------------

**Role**: LLM application end-user

**Needs**:

* Interact with LLM conversations via simple CLI commands.
* Fork conversations to explore alternative discussion paths.
* View conversation history in human-readable format.

**Technical proficiency**: Comfortable with command-line tools; may not be a
Python developer.

**Usage context**: CLI tool for conversation interaction and management.

Functional Requirements
===============================================================================

Message Representation
-------------------------------------------------------------------------------

REQ-101: Message Type Support (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support all necessary message types for LLM conversations:

* User messages
* Assistant responses
* System/supervisor instructions
* Reference documents
* Tool invocations
* Tool results

**Acceptance Criteria**:

* All message types can be represented in normalized format.
* Messages can contain multimodal content and metadata.
* Messages can be serialized to/from human-readable formats.

REQ-102: Multimodal Content Support (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support multiple content types in messages:

* Text content with MIME type support
* Image/visual content
* Audio content (future capability)
* Video content (future capability)

**Acceptance Criteria**:

* Messages can contain multiple content items of different types.
* Content storage is efficient for both small and large items.
* Content can be deduplicated when reused across messages.

Provider Integration
-------------------------------------------------------------------------------

REQ-201: Provider Interface (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support interaction with multiple LLM providers through a unified interface:

* Client connection and configuration
* Model access and discovery
* Message format conversion (normalization and nativization)
* Tool invocation handling

**Acceptance Criteria**:

* Provider interface defines required capabilities.
* Provider implementations are swappable via configuration.

REQ-202: Provider Capabilities (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support essential provider interactions:

* Model parameter configuration (temperature, max_tokens, etc.)
* Message format conversion
* Tool/function call handling
* Token counting and usage tracking

**Acceptance Criteria**:

* Each capability can be configured per provider.
* Capabilities are composable and provider-specific.

REQ-203: MVP Provider Implementations (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support these providers for MVP:

* Anthropic (primary)
* Ollama or VLLM (one local provider)

**Future providers**:

* OpenAI Conversations API (legacy)
* OpenAI Responses API (new)

**Acceptance Criteria**:

* Both MVP providers fully functional with all core capabilities.
* Provider switching via configuration change only.

Tool/Function Calling
-------------------------------------------------------------------------------

REQ-301: Tool Registration and Invocation (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support registration and invocation of callable tools:

* Tools can be registered with metadata and schemas
* Tool argument validation via JSON Schema
* Tool organization into logical groups

**Acceptance Criteria**:

* Tools can be registered and made available to LLMs.
* Tool arguments are validated before execution.
* Tools can be organized into groups for management.

REQ-302: MCP Server Integration (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support calling tools on MCP servers:

* Connect to MCP servers via stdio or HTTP.
* Discover tools from MCP servers.
* Invoke MCP server tools during conversations.

**Acceptance Criteria**:

* Can connect to and discover tools from MCP servers.
* MCP tools can be registered and invoked like local tools.
* Tool invocations work identically regardless of tool source.

Conversation Management
-------------------------------------------------------------------------------

REQ-401: Conversation Storage (Critical)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Store conversations in human-readable format:

* messages.jsonl: One message per line
* metadata.toml: Conversation name, creation date, tags, etc.
* content/{hash}/: Binary/large content storage

**Acceptance Criteria**:

* Conversations can be created, read, updated, and deleted.
* JSONL format allows line-by-line streaming and editing.
* Content deduplication via hash-based storage.

REQ-402: CLI Commands (High)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Provide CLI for conversation management:

* List conversations
* View conversation messages
* Create new conversation
* Fork conversation from specific message
* Delete conversation

**Acceptance Criteria**:

* All commands work from command line.
* Human-friendly output formatting.
* Support for filtering and searching conversations.

Non-Functional Requirements
===============================================================================

Performance
-------------------------------------------------------------------------------

* **Message processing latency**: < 100ms for message normalization/nativization
* **Conversation loading**: < 1s for conversations up to 1000 messages
* **Streaming responsiveness**: First token in < 2s for streaming responses

Reliability
-------------------------------------------------------------------------------

* **Error handling**: All tool invocations have timeout and error handling
* **Data integrity**: Conversation storage is crash-safe (atomic writes)
* **Provider fallback**: Clear error messages when provider unavailable

Type Safety
-------------------------------------------------------------------------------

* **100% type coverage**: All public APIs fully typed
* **mypy strict mode**: Passes mypy in strict mode with no errors
* **Runtime validation**: Pydantic or similar for runtime type checking where
  appropriate

Usability
-------------------------------------------------------------------------------

* **CLI discoverability**: Help text for all commands
* **Error messages**: Clear, actionable error messages for common problems
* **Documentation**: API documentation and usage examples

Compatibility
-------------------------------------------------------------------------------

* **Python version**: Python 3.10+ (for pattern matching and modern type hints)
* **Operating systems**: Linux, macOS, Windows (via WSL)
* **Provider APIs**: Compatible with current Anthropic and Ollama/VLLM APIs

Constraints and Assumptions
===============================================================================

Technical Constraints
-------------------------------------------------------------------------------

* Python 3.10+ required for pattern matching and structural pattern matching
  features.
* Async/await throughout; synchronous wrapper may be provided for convenience.
* File-based storage for MVP; database backend deferred to Phase 2.

Dependencies
-------------------------------------------------------------------------------

* Anthropic SDK for Anthropic provider
* httpx for async HTTP (Ollama/VLLM providers)
* MCP SDK for MCP server integration
* Pydantic for data validation (optional, TBD)

Assumptions
-------------------------------------------------------------------------------

* Users have API keys for LLM providers they wish to use.
* MCP servers are available via stdio or HTTP endpoints.
* Conversation storage is on local filesystem (not networked storage).

Out of Scope
===============================================================================

The following are explicitly out of scope for the initial release:

* **Graphical user interface**: Only CLI provided; GUI is Phase 2+.
* **Multi-user support**: Single-user, local conversations only.
* **Cloud storage**: No built-in cloud storage or sync; local filesystem only.
* **Conversation sharing**: No built-in sharing or export to external services.
* **Advanced context management**: Deduplicators deferred to Phase 2 (see
  :doc:`architecture/decisions/004-conversation-trimming`).
* **Wrapping converser as MCP server**: Deferred to Phase 2 (calling tools ON
  MCP servers is in scope; exposing converser AS an MCP server is not).
* **Web interface**: No web UI planned for MVP.
* **Distributed deployment**: Single-machine deployment only.

Success Metrics
===============================================================================

.. todo:: Define quantitative success metrics for MVP evaluation.

   Potential metrics to consider:

   * Developer adoption: GitHub stars, downloads, active users
   * Provider support: Number of providers fully supported
   * MCP integration: Number of MCP servers successfully integrated
   * Code quality: Type coverage percentage, test coverage percentage
   * Performance: Conversation load times, message processing latency
   * Usability: Time to first successful conversation, documentation completeness
