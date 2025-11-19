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
Message Abstraction Layer
*******************************************************************************

:Author: Architecture Team
:Date: 2025-11-18
:Status: Active

Overview
===============================================================================

The message abstraction layer provides a unified representation for LLM
conversation messages that works consistently across all provider APIs. This
layer decouples the application logic from provider-specific message formats,
enabling seamless provider switching and multi-provider support.

**Core abstractions**:

* **Canister hierarchy**: Protocol-based message type system
* **Content model**: Multimodal content representation
* **Storage strategy**: Hybrid inline/hash-based persistence

Goals and Non-Goals
===============================================================================

**Goals:**

* Provide unified message format across all LLM providers
* Support multimodal content (text, images, audio, video) from the start
* Enable efficient storage with deduplication where beneficial
* Maintain type safety through Protocol-based interfaces
* Support conversation forking and history management

**Non-Goals:**

* Provider-specific optimizations (handled by provider adapters)
* Streaming response handling (handled by event system)
* Tool execution logic (handled by invocables framework)

Design Details
===============================================================================

Canister Hierarchy
-------------------------------------------------------------------------------

**Canister** is the base protocol representing any message in a conversation.
The complete hierarchy preserves patterns from the ai-experiments project:

.. code-block:: python

   from . import __

   class Canister( __.immut.Protocol ):
       ''' Base protocol for conversation messages. '''

       @property
       def role( self ) -> Role: ...

       @property
       def timestamp( self ) -> __.datetime.datetime: ...

Message Type Protocols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**UserCanister**: Represents user input messages.

.. code-block:: python

   class UserCanister( Canister, __.immut.Protocol ):
       ''' User-provided message in conversation. '''

       @property
       def content( self ) -> Content: ...

**AssistantCanister**: Represents LLM-generated responses.

.. code-block:: python

   class AssistantCanister( Canister, __.immut.Protocol ):
       ''' Assistant-generated response in conversation. '''

       @property
       def content( self ) -> __.Absential[ Content ]: ...
       ''' Content may be absent when assistant only requests tool invocations. '''

**SupervisorCanister**: Represents system instructions and prompts.

.. code-block:: python

   class SupervisorCanister( Canister, __.immut.Protocol ):
       ''' System-level instructions for conversation behavior. '''

       @property
       def content( self ) -> Content: ...

**DocumentCanister**: Represents reference documents provided for context.

.. code-block:: python

   class DocumentCanister( Canister, __.immut.Protocol ):
       ''' Reference document provided for conversation context. '''

       @property
       def content( self ) -> Content: ...

       @property
       def title( self ) -> __.Absential[ str ]: ...
       ''' Optional document title for organization. '''

**InvocationCanister**: Represents tool call requests from the LLM.

.. code-block:: python

   class InvocationCanister( Canister, __.immut.Protocol ):
       ''' Tool invocation request from assistant. '''

       @property
       def identifier( self ) -> str: ...
       ''' Unique invocation identifier for result correlation. '''

       @property
       def name( self ) -> str: ...
       ''' Invoker name being called. '''

       @property
       def arguments( self ) -> __.immut.Dictionary[ str, __.typx.Any ]: ...
       ''' Arguments provided to invoker. '''

**ResultCanister**: Represents tool execution results.

.. code-block:: python

   class ResultCanister( Canister, __.immut.Protocol ):
       ''' Tool execution result sent back to assistant. '''

       @property
       def invocation_id( self ) -> str: ...
       ''' References InvocationCanister identifier. '''

       @property
       def content( self ) -> Content: ...
       ''' Result payload (typically textual content). '''

       @property
       def error( self ) -> __.Absential[ str ]: ...
       ''' Error message if tool execution failed. '''

Design Rationale
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The canister hierarchy uses distinct types rather than a single class with role
enumeration. This design provides:

* **Type safety**: Each message type has appropriate attributes
* **Clear contracts**: Protocol-based interfaces define expected behaviors
* **Provider flexibility**: Adapters normalize to appropriate canister types
* **Extensibility**: New message types can be added without breaking existing code

Content Model
-------------------------------------------------------------------------------

**Content** is the base protocol for message payload representation, designed
for multimodal support from the start.

.. code-block:: python

   class Content( __.immut.Protocol ):
       ''' Base protocol for message content. '''

       @property
       def mime_type( self ) -> str: ...
       ''' MIME type identifying content format. '''

Content Type Protocols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TextualContent**: Text content with MIME type support.

.. code-block:: python

   class TextualContent( Content, __.immut.Protocol ):
       ''' Textual content with optional formatting. '''

       @property
       def text( self ) -> str: ...
       ''' Text content string. '''

       @property
       def mime_type( self ) -> str: ...
       ''' Defaults to "text/plain"; may be "text/markdown", "text/html", etc. '''

**ImageContent**: Visual content representation.

.. code-block:: python

   class ImageContent( Content, __.immut.Protocol ):
       ''' Image or visual content. '''

       @property
       def data( self ) -> bytes: ...
       ''' Binary image data. '''

       @property
       def mime_type( self ) -> str: ...
       ''' Image MIME type: "image/png", "image/jpeg", etc. '''

       @property
       def content_id( self ) -> __.Absential[ str ]: ...
       ''' Hash-based content identifier for storage. '''

**AudioContent**: Audio content (future implementation).

.. code-block:: python

   class AudioContent( Content, __.immut.Protocol ):
       ''' Audio content (designed for future implementation). '''

       @property
       def data( self ) -> bytes: ...

       @property
       def mime_type( self ) -> str: ...
       ''' Audio MIME type: "audio/mpeg", "audio/wav", etc. '''

       @property
       def content_id( self ) -> __.Absential[ str ]: ...

**VideoContent**: Video content (future implementation).

.. code-block:: python

   class VideoContent( Content, __.immut.Protocol ):
       ''' Video content (designed for future implementation). '''

       @property
       def data( self ) -> bytes: ...

       @property
       def mime_type( self ) -> str: ...
       ''' Video MIME type: "video/mp4", "video/webm", etc. '''

       @property
       def content_id( self ) -> __.Absential[ str ]: ...

Storage Strategy
-------------------------------------------------------------------------------

Content storage uses a hybrid approach balancing performance and deduplication.
See :doc:`../decisions/002-content-storage-strategy` for the full decision
rationale.

**Inline storage** (small text):

.. code-block:: python

   TextualContent(
       text = "What is the weather?",
       mime_type = "text/plain",
   )

**Hash-based storage** (large content):

.. code-block:: python

   TextualContent(
       text = "",  # Not stored inline
       mime_type = "text/plain",
       content_id = "sha256:a1b2c3d4...",
   )

**Storage thresholds**:

* Small text (< 1KB): Stored inline in messages.jsonl
* Large text (≥ 1KB): Hash-based storage for deduplication
* System prompts: Always hash-based (shared across conversations)
* Binary content: Always hash-based storage

Role Enumeration
-------------------------------------------------------------------------------

The ``Role`` enumeration identifies canister types in storage and provider
communication.

.. code-block:: python

   class Role( __.enum.Enum ):
       ''' Message role enumeration. '''

       User = __.enum.auto( )
       Assistant = __.enum.auto( )
       Supervisor = __.enum.auto( )
       Document = __.enum.auto( )
       Invocation = __.enum.auto( )
       Result = __.enum.auto( )

Interactions and Data Flow
===============================================================================

Message Creation
-------------------------------------------------------------------------------

Applications create canisters using immutable dataclass implementations:

.. code-block:: python

   from . import __

   user_message = UserCanisterClass(
       content = TextualContentClass( text = "Explain photosynthesis." ),
       timestamp = __.datetime.datetime.now( __.datetime.UTC ),
   )

Provider Normalization
-------------------------------------------------------------------------------

Provider adapters convert provider-specific formats to normalized canisters.
See :doc:`provider-abstraction` for detailed normalization patterns.

**Example** (Anthropic → normalized):

.. code-block:: python

   # Anthropic format
   anthropic_message = {
       "role": "user",
       "content": "Explain photosynthesis."
   }

   # Normalized canister
   normalized = UserCanisterClass(
       content = TextualContentClass( text = "Explain photosynthesis." ),
       timestamp = __.datetime.datetime.now( __.datetime.UTC ),
   )

Storage Persistence
-------------------------------------------------------------------------------

Canisters serialize to JSONL format for conversation persistence:

.. code-block:: json

   {"role": "user", "content": {"type": "text", "text": "Explain photosynthesis."}, "timestamp": "2025-11-18T10:30:00Z"}
   {"role": "assistant", "content": {"type": "text", "content_id": "sha256:a1b2c3..."}, "timestamp": "2025-11-18T10:30:15Z"}

Content Loading
-------------------------------------------------------------------------------

When loading conversations, the storage layer hydrates content references:

1. Read ``messages.jsonl`` file
2. For each message, check content items:

   a. If ``{"type": "text", "text": "..."}`` → use inline text
   b. If ``{"type": "text", "content_id": "..."}`` → load from content store
   c. If ``{"type": "image", "content_id": "..."}`` → load from content store

3. Cache loaded content for performance
4. Return fully hydrated conversation

Examples and Usage Patterns
===============================================================================

Example 1: Simple Text Conversation
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   conversation = [
       UserCanisterClass(
           content = TextualContentClass( text = "What is 2 + 2?" ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       AssistantCanisterClass(
           content = TextualContentClass( text = "2 + 2 equals 4." ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

Example 2: Multimodal Conversation
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   conversation = [
       UserCanisterClass(
           content = ImageContentClass(
               data = image_bytes,
               mime_type = "image/png",
               content_id = "sha256:abc123...",
           ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       UserCanisterClass(
           content = TextualContentClass( text = "Describe this image." ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       AssistantCanisterClass(
           content = TextualContentClass(
               text = "The image shows a sunset over mountains.",
           ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

Example 3: Tool Invocation
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   conversation = [
       UserCanisterClass(
           content = TextualContentClass( text = "What's the weather in SF?" ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       AssistantCanisterClass(
           content = __.absent,  # No text content
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       InvocationCanisterClass(
           identifier = "call_123",
           name = "get_weather",
           arguments = __.immut.Dictionary( { 'location': 'San Francisco, CA' } ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       ResultCanisterClass(
           invocation_id = "call_123",
           content = TextualContentClass(
               text = '{"temp": 62, "conditions": "Partly cloudy"}',
           ),
           error = __.absent,
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       AssistantCanisterClass(
           content = TextualContentClass(
               text = "The weather in San Francisco is 62°F and partly cloudy.",
           ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

Alternative Approaches Considered
===============================================================================

See :doc:`../decisions/002-content-storage-strategy` for detailed analysis of
storage alternatives (always inline, always hash, hybrid with thresholds).

The decision to use distinct canister types rather than a single class with
role enumeration was made to provide better type safety and clearer contracts
for each message type.

Implementation Roadmap
===============================================================================

**Phase 1 (MVP)**:

1. Implement base ``Canister`` and ``Content`` protocols
2. Implement all six canister types (User, Assistant, Supervisor, Document,
   Invocation, Result)
3. Implement ``TextualContent`` and ``ImageContent`` with full functionality
4. Design ``AudioContent`` and ``VideoContent`` protocols (defer implementation)
5. Implement hybrid storage strategy with size-based thresholds
6. Create serialization/deserialization for JSONL persistence

**Phase 2**:

1. Implement ``AudioContent`` and ``VideoContent`` with provider support
2. Add content caching layer for performance optimization
3. Enhance content deduplication algorithms
4. Add content compression for large payloads

References
===============================================================================

* :doc:`../decisions/002-content-storage-strategy` - Storage strategy decision
* :doc:`provider-abstraction` - Provider normalization patterns
* :doc:`tool-calling` - Tool invocation architecture
* :doc:`../filesystem` - Storage organization
* ai-experiments canister hierarchy: https://github.com/emcd/ai-experiments
