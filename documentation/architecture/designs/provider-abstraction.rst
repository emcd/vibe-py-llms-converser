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
Provider Abstraction Layer
*******************************************************************************

:Author: Architecture Team
:Date: 2025-11-18
:Status: Active

Overview
===============================================================================

The provider abstraction layer decouples application logic from LLM provider
APIs through a unified interface. This enables seamless provider switching,
multi-provider support, and consistent conversation handling across different
LLM services.

**Core abstractions**:

* **Provider/Client protocols**: Uniform provider access interface
* **Processor pattern**: Composable provider adapters
* **Normalization/nativization**: Bidirectional message format conversion

Goals and Non-Goals
===============================================================================

**Goals:**

* Abstract provider-specific APIs behind uniform protocols
* Enable adding new providers without modifying application code
* Support provider-specific features while maintaining common interface
* Provide bidirectional message format conversion (normalization ↔ nativization)
* Handle model parameter normalization across providers

**Non-Goals:**

* Provider feature parity (providers may have unique capabilities)
* Cost tracking and optimization (separate concern)
* Provider failover and load balancing (future enhancement)

Design Details
===============================================================================

Provider Interface Protocols
-------------------------------------------------------------------------------

**Provider**: Top-level protocol for LLM provider access.

.. code-block:: python

   from . import __

   class Provider( __.immut.Protocol ):
       ''' LLM provider abstraction. '''

       @property
       def name( self ) -> str: ...
       ''' Provider identifier (e.g., "anthropic", "openai"). '''

       def produce_client(
           self,
           configuration: __.cabc.Mapping[ str, __.typx.Any ],
       ) -> Client: ...
       ''' Creates provider client from configuration. '''

**Client**: Provider-specific client managing model access.

.. code-block:: python

   class Client( __.immut.Protocol ):
       ''' Provider client managing model access and conversations. '''

       def access_model(
           self,
           identifier: str,
       ) -> Model: ...
       ''' Accesses specific model by identifier. '''

       def survey_models( self ) -> __.cabc.Sequence[ ModelDescriptor ]: ...
       ''' Lists available models from provider. '''

**Model**: Interface for conducting conversations with specific LLM.

.. code-block:: python

   class Model( __.immut.Protocol ):
       ''' Interface for LLM conversation execution. '''

       async def converse(
           self,
           canisters: __.cabc.Sequence[ Canister ],
           controls: __.Absential[ Controls ] = __.absent,
           event_handler: __.Absential[ EventHandler ] = __.absent,
       ) -> __.cabc.Sequence[ Canister ]: ...
       ''' Executes conversation and returns assistant responses. '''

       @property
       def identifier( self ) -> str: ...
       ''' Model identifier (e.g., "claude-sonnet-4.5"). '''

       @property
       def descriptor( self ) -> ModelDescriptor: ...
       ''' Model metadata and capabilities. '''

**ModelDescriptor**: Model metadata and capabilities.

.. code-block:: python

   class ModelDescriptor( __.immut.Protocol ):
       ''' Model metadata and capabilities description. '''

       @property
       def identifier( self ) -> str: ...

       @property
       def name( self ) -> str: ...
       ''' Human-readable model name. '''

       @property
       def context_window( self ) -> int: ...
       ''' Maximum context window size in tokens. '''

       @property
       def supports_vision( self ) -> bool: ...
       ''' Whether model supports image inputs. '''

       @property
       def supports_tools( self ) -> bool: ...
       ''' Whether model supports tool/function calling. '''

Processor Pattern
-------------------------------------------------------------------------------

Provider implementations compose focused processors for specific
responsibilities. This pattern preserves the proven ai-experiments architecture.

**MessagesProcessor**: Message format conversion.

.. code-block:: python

   class MessagesProcessor( __.immut.Protocol ):
       ''' Handles message normalization and nativization. '''

       def normalize_messages(
           self,
           native_messages: __.cabc.Sequence[ __.typx.Any ],
       ) -> __.cabc.Sequence[ Canister ]: ...
       ''' Converts provider-native messages to normalized canisters. '''

       def nativize_messages(
           self,
           canisters: __.cabc.Sequence[ Canister ],
       ) -> __.cabc.Sequence[ __.typx.Any ]: ...
       ''' Converts normalized canisters to provider-native format. '''

**ControlsProcessor**: Model parameter handling.

.. code-block:: python

   class ControlsProcessor( __.immut.Protocol ):
       ''' Handles model parameter normalization. '''

       def normalize_controls(
           self,
           native_controls: __.cabc.Mapping[ str, __.typx.Any ],
       ) -> Controls: ...
       ''' Converts provider-native parameters to normalized controls. '''

       def nativize_controls(
           self,
           controls: Controls,
       ) -> __.cabc.Mapping[ str, __.typx.Any ]: ...
       ''' Converts normalized controls to provider-native parameters. '''

**InvocationsProcessor**: Tool calling support.

.. code-block:: python

   class InvocationsProcessor( __.immut.Protocol ):
       ''' Handles tool/function calling normalization. '''

       def prepare_tools(
           self,
           ensembles: __.cabc.Sequence[ Ensemble ],
       ) -> __.cabc.Sequence[ __.typx.Any ]: ...
       ''' Converts ensembles to provider-native tool definitions. '''

       def normalize_invocations(
           self,
           native_message: __.typx.Any,
       ) -> __.cabc.Sequence[ InvocationCanister ]: ...
       ''' Extracts tool invocations from provider response. '''

       def nativize_results(
           self,
           results: __.cabc.Sequence[ ResultCanister ],
       ) -> __.cabc.Sequence[ __.typx.Any ]: ...
       ''' Converts tool results to provider-native format. '''

**ConversationTokenizer**: Token counting.

.. code-block:: python

   class ConversationTokenizer( __.immut.Protocol ):
       ''' Handles token counting for cost tracking. '''

       def count_tokens(
           self,
           canisters: __.cabc.Sequence[ Canister ],
       ) -> int: ...
       ''' Counts tokens in conversation for provider's pricing model. '''

Processor Composition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Provider implementations select and configure appropriate processors:

.. code-block:: python

   class AnthropicModel:
       ''' Anthropic-specific model implementation. '''

       messages_processor: AnthropicMessagesProcessor
       controls_processor: AnthropicControlsProcessor
       invocations_processor: AnthropicInvocationsProcessor
       tokenizer: AnthropicTokenizer

       async def converse(
           self,
           canisters: __.cabc.Sequence[ Canister ],
           controls: __.Absential[ Controls ] = __.absent,
           event_handler: __.Absential[ EventHandler ] = __.absent,
       ) -> __.cabc.Sequence[ Canister ]:
           # Nativize messages using processor
           native_messages = self.messages_processor.nativize_messages( canisters )

           # Nativize controls
           native_controls = self.controls_processor.nativize_controls( controls )

           # Call provider API
           response = await self.anthropic_client.messages.create(
               messages = native_messages,
               **native_controls,
           )

           # Normalize response
           response_canisters = self.messages_processor.normalize_messages( [ response ] )

           return response_canisters

Normalization and Nativization
-------------------------------------------------------------------------------

**Normalization**: Converting provider-specific formats to unified canisters.

**Nativization**: Converting unified canisters to provider-specific formats.

These bidirectional transformations enable provider-agnostic conversation
management while leveraging provider-specific APIs.

Normalization Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Anthropic → Normalized**:

.. code-block:: python

   # Anthropic message
   anthropic_msg = {
       "role": "user",
       "content": [
           {"type": "text", "text": "Describe this image."},
           {"type": "image", "source": {"type": "base64", "data": "..."}}
       ]
   }

   # Normalized canisters
   canisters = [
       UserCanisterClass(
           content = TextualContentClass( text = "Describe this image." ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       UserCanisterClass(
           content = ImageContentClass(
               data = base64.b64decode( "..." ),
               mime_type = "image/png",
           ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

**OpenAI → Normalized**:

.. code-block:: python

   # OpenAI message
   openai_msg = {
       "role": "user",
       "content": "Explain photosynthesis."
   }

   # Normalized canister
   canister = UserCanisterClass(
       content = TextualContentClass( text = "Explain photosynthesis." ),
       timestamp = __.datetime.datetime.now( __.datetime.UTC ),
   )

Nativization Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Normalized → Anthropic**:

.. code-block:: python

   # Normalized canister
   canister = AssistantCanisterClass(
       content = TextualContentClass( text = "Photosynthesis is..." ),
       timestamp = __.datetime.datetime.now( __.datetime.UTC ),
   )

   # Anthropic message
   anthropic_msg = {
       "role": "assistant",
       "content": "Photosynthesis is..."
   }

**Normalized → OpenAI**:

.. code-block:: python

   # Normalized canister
   canister = UserCanisterClass(
       content = TextualContentClass( text = "What is 2 + 2?" ),
       timestamp = __.datetime.datetime.now( __.datetime.UTC ),
   )

   # OpenAI message
   openai_msg = {
       "role": "user",
       "content": "What is 2 + 2?"
   }

Controls Normalization
-------------------------------------------------------------------------------

**Controls**: Unified model parameter representation.

.. code-block:: python

   class Controls( __.immut.Protocol ):
       ''' Normalized model parameters. '''

       @property
       def temperature( self ) -> __.Absential[ float ]: ...
       ''' Sampling temperature (0.0 to 1.0). '''

       @property
       def max_tokens( self ) -> __.Absential[ int ]: ...
       ''' Maximum tokens to generate. '''

       @property
       def top_p( self ) -> __.Absential[ float ]: ...
       ''' Nucleus sampling threshold. '''

       @property
       def stop_sequences( self ) -> __.Absential[ __.cabc.Sequence[ str ] ]: ...
       ''' Sequences that stop generation. '''

**Provider mapping examples**:

.. code-block:: python

   # Normalized controls
   controls = ControlsClass(
       temperature = 0.7,
       max_tokens = 1024,
   )

   # Anthropic native
   anthropic_params = {
       "temperature": 0.7,
       "max_tokens": 1024,
   }

   # OpenAI native
   openai_params = {
       "temperature": 0.7,
       "max_tokens": 1024,
   }

Interactions and Data Flow
===============================================================================

Conversation Flow
-------------------------------------------------------------------------------

1. Application creates normalized canisters
2. ``Model.converse()`` receives canisters and controls
3. ``MessagesProcessor`` nativizes canisters to provider format
4. ``ControlsProcessor`` nativizes controls to provider parameters
5. Provider API call executes with native format
6. ``MessagesProcessor`` normalizes provider response to canisters
7. Application receives normalized response canisters

Provider Registration
-------------------------------------------------------------------------------

Providers register through configuration-driven mechanism:

.. code-block:: python

   # Provider registration
   def register_provider(
       name: str,
       provider_class: type[ Provider ],
   ) -> None:
       ''' Registers provider for configuration-driven access. '''
       _PROVIDERS[ name ] = provider_class

   # Provider discovery
   def access_provider( name: str ) -> Provider:
       ''' Accesses registered provider by name. '''
       if name not in _PROVIDERS:
           raise ProviderAbsence( f"Provider not registered: {name}" )
       return _PROVIDERS[ name ]( )

Configuration Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: toml

   # Configuration file
   [providers.anthropic]
   enabled = true
   api_key_env = "ANTHROPIC_API_KEY"
   default_model = "claude-sonnet-4.5"

   [providers.openai]
   enabled = true
   api_key_env = "OPENAI_API_KEY"
   default_model = "gpt-4-turbo"

Examples and Usage Patterns
===============================================================================

Example 1: Basic Conversation
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Access provider
   provider = access_provider( "anthropic" )
   client = provider.produce_client( configuration )
   model = client.access_model( "claude-sonnet-4.5" )

   # Create conversation
   canisters = [
       UserCanisterClass(
           content = TextualContentClass( text = "Explain quantum entanglement." ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

   # Execute conversation
   responses = await model.converse( canisters )

   # Process responses
   for canister in responses:
       if isinstance( canister, AssistantCanister ):
           print( canister.content.text )

Example 2: Conversation with Controls
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Create controls
   controls = ControlsClass(
       temperature = 0.3,
       max_tokens = 2048,
   )

   # Execute with controls
   responses = await model.converse(
       canisters,
       controls = controls,
   )

Example 3: Multi-Provider Conversation
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Access multiple providers
   anthropic_model = access_provider( "anthropic" ).produce_client( config1 ).access_model( "claude-sonnet-4.5" )
   openai_model = access_provider( "openai" ).produce_client( config2 ).access_model( "gpt-4-turbo" )

   # Same canisters work with both providers
   canisters = [
       UserCanisterClass(
           content = TextualContentClass( text = "Compare approaches to X." ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

   # Execute on both providers
   anthropic_response = await anthropic_model.converse( canisters )
   openai_response = await openai_model.converse( canisters )

Alternative Approaches Considered
===============================================================================

**Single unified API wrapper** vs processor composition:

* Single wrapper simpler but less flexible for provider-specific features
* Processor composition allows selective capability support
* Processors can be reused across similar providers

**Direct SDK usage** vs abstraction layer:

* Direct SDK usage couples application to specific providers
* Abstraction enables provider switching without code changes
* Abstraction supports multi-provider conversations

Implementation Roadmap
===============================================================================

**Phase 1 (MVP)**:

1. Implement ``Provider``, ``Client``, ``Model`` protocols
2. Implement processor protocols (Messages, Controls, Invocations, Tokenizer)
3. Create Anthropic provider with full processor implementations
4. Implement provider registration and discovery mechanisms
5. Create ``Controls`` and ``ModelDescriptor`` classes
6. Implement configuration-driven provider access

**Phase 2**:

1. Implement OpenAI provider (both Conversations and Responses APIs)
2. Implement Ollama or VLLM provider
3. Add provider feature detection and capability negotiation
4. Enhance model selection with capability filtering
5. Add provider failover and retry mechanisms

References
===============================================================================

* :doc:`message-abstraction` - Canister and content protocols
* :doc:`tool-calling` - Invocations processor details
* :doc:`../decisions/001-event-handling-pattern` - Event handling for streaming
* ai-experiments provider patterns: https://github.com/emcd/ai-experiments
* Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
* OpenAI SDK: https://github.com/openai/openai-python
