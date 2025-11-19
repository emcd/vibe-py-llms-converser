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
   | Unless required by                                                       |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
Tool Calling Architecture
*******************************************************************************

:Author: Architecture Team
:Date: 2025-11-18
:Status: Active

Overview
===============================================================================

Tool calling (function calling) enables LLMs to invoke external functions for
gathering information, performing actions, and extending capabilities beyond
text generation. This architecture provides a provider-agnostic invocables
framework with schema validation, lifecycle management, and MCP server support.

**Core components**:

* **Invoker**: Wraps callable tools with metadata and validation
* **Ensemble**: Groups related invokers for lifecycle management
* **InvocationsProcessor**: Provider-specific tool calling normalization
* **Configuration system**: TOML-based invoker and ensemble definitions

Goals and Non-Goals
===============================================================================

**Goals:**

* Enable LLMs to call external tools and functions
* Provide schema-based argument validation
* Support MCP server tool discovery and invocation
* Organize tools into logical ensembles
* Handle tool execution errors gracefully
* Abstract provider-specific tool calling formats

**Non-Goals:**

* Conversation history trimming (see :doc:`../decisions/004-conversation-history-trimming`)
* Tool result caching beyond deduplication
* Permission/sandbox system (Phase 2)
* Wrapping converser as MCP server (Phase 2)

Design Details
===============================================================================

Invoker Architecture
-------------------------------------------------------------------------------

**Invoker**: Wraps a callable tool with schema validation and metadata.

.. code-block:: python

   from . import __

   class Invoker( __.immut.Protocol ):
       ''' Wraps tool with schema and lifecycle management. '''

       @property
       def name( self ) -> str: ...
       ''' Tool identifier used in invocations. '''

       @property
       def invocable( self ) -> Invocable: ...
       ''' Async callable implementing tool logic. '''

       @property
       def arguments_schema( self ) -> __.immut.Dictionary[ str, __.typx.Any ]: ...
       ''' JSON Schema for argument validation. '''

       @property
       def ensemble( self ) -> Ensemble: ...
       ''' Parent ensemble providing lifecycle and configuration. '''

       async def __call__(
           self,
           context: Context,
           arguments: __.immut.Dictionary[ str, __.typx.Any ],
       ) -> __.typx.Any: ...
       ''' Executes tool with validation and context. '''

**Invocable**: Signature for tool implementations.

.. code-block:: python

   Invocable: __.typx.TypeAlias = __.cabc.Callable[
       [ Context, __.immut.Dictionary[ str, __.typx.Any ] ],
       __.cabc.Awaitable[ __.typx.Any ],
   ]

**Context**: Execution context provided to invocables.

.. code-block:: python

   class Context( __.immut.Protocol ):
       ''' Execution context for tool invocations. '''

       @property
       def auxdata( self ) -> __.immut.Dictionary[ str, __.typx.Any ]: ...
       ''' Auxiliary data from conversation or configuration. '''

       @property
       def invoker( self ) -> Invoker: ...
       ''' Invoker being executed. '''

       @property
       def namespace( self ) -> __.immut.Dictionary[ str, __.typx.Any ]: ...
       ''' Namespace for tool state and caching. '''

Invoker Execution Flow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Validate arguments against JSON Schema
2. Create execution context with auxdata and namespace
3. Execute invocable with context and validated arguments
4. Return result for inclusion in conversation
5. Handle exceptions and produce error results

Ensemble Architecture
-------------------------------------------------------------------------------

**Ensemble**: Groups related invokers for organization and lifecycle management.

.. code-block:: python

   class Ensemble( __.immut.Protocol ):
       ''' Container grouping related invokers with shared lifecycle. '''

       @property
       def name( self ) -> str: ...
       ''' Ensemble identifier (e.g., "io", "mcp-weather"). '''

       @property
       def invokers( self ) -> __.immut.Dictionary[ str, Invoker ]: ...
       ''' Name-to-invoker mapping. '''

       @property
       def configuration( self ) -> __.immut.Dictionary[ str, __.typx.Any ]: ...
       ''' Ensemble-level configuration. '''

       @property
       def connection( self ) -> __.Absential[ __.typx.Any ]: ...
       ''' Optional connection (e.g., MCP client). '''

       async def connect( self ) -> None: ...
       ''' Initializes ensemble (e.g., connects to MCP server). '''

       async def disconnect( self ) -> None: ...
       ''' Teardown ensemble (e.g., disconnects from MCP server). '''

       def access_invoker( self, name: str ) -> Invoker: ...
       ''' Accesses invoker by name. '''

Ensemble Lifecycle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Configuration loading**: Load ensemble descriptor from TOML
2. **Invoker registration**: Register all enabled invokers
3. **Connection**: Connect to external resources (MCP servers, databases)
4. **Execution**: Handle tool invocations during conversation
5. **Disconnection**: Clean up resources when conversation ends

Ensemble Organization Rationale
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See :doc:`../decisions/003-tool-organization-with-ensembles` for the full
decision rationale. Key benefits:

* **MCP mapping**: One ensemble per MCP server for lifecycle management
* **Name scoping**: Multiple ensembles can have tools with same names
* **Configuration locality**: Ensemble-level defaults and settings
* **Lifecycle management**: Connect/disconnect operations for external resources

InvocationsProcessor
-------------------------------------------------------------------------------

**InvocationsProcessor**: Handles provider-specific tool calling normalization.

.. code-block:: python

   class InvocationsProcessor( __.immut.Protocol ):
       ''' Handles tool calling normalization for provider. '''

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

       async def execute_invocations(
           self,
           invocations: __.cabc.Sequence[ InvocationCanister ],
           ensembles: __.cabc.Sequence[ Ensemble ],
       ) -> __.cabc.Sequence[ ResultCanister ]: ...
       ''' Executes tool invocations and produces results. '''

Provider-Specific Normalization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Anthropic tool definitions**:

.. code-block:: python

   # Ensemble invokers → Anthropic tools
   {
       "name": "get_weather",
       "description": "Get current weather for location",
       "input_schema": {
           "type": "object",
           "properties": {
               "location": {"type": "string", "description": "City and state"}
           },
           "required": ["location"]
       }
   }

**OpenAI tool definitions**:

.. code-block:: python

   # Ensemble invokers → OpenAI functions
   {
       "type": "function",
       "function": {
           "name": "get_weather",
           "description": "Get current weather for location",
           "parameters": {
               "type": "object",
               "properties": {
                   "location": {"type": "string", "description": "City and state"}
               },
               "required": ["location"]
           }
       }
   }

Configuration System
-------------------------------------------------------------------------------

Invokers and ensembles are configured through TOML descriptors, enabling
declarative tool registration without code changes.

**Invoker descriptor example**:

.. code-block:: toml

   # data/ensembles/io/invokers/read_file.toml
   [invoker]
   name = "read_file"
   enabled = true
   description = "Reads contents of a file"

   [arguments]
   type = "object"
   required = ["path"]

   [arguments.properties.path]
   type = "string"
   description = "Absolute path to file"

   [arguments.properties.encoding]
   type = "string"
   description = "File encoding"
   default = "utf-8"

**Ensemble descriptor example**:

.. code-block:: toml

   # data/ensembles/io.toml
   [ensemble]
   name = "io"
   enabled = true

   [defaults]
   timeout = 30
   max_retries = 3

   [[invokers]]
   source = "io/invokers/read_file.toml"

   [[invokers]]
   source = "io/invokers/write_file.toml"

Configuration Loading
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   async def prepare_ensembles(
       configuration: __.cabc.Mapping[ str, __.typx.Any ],
   ) -> __.cabc.Sequence[ Ensemble ]:
       ''' Loads and prepares ensembles from configuration. '''

       ensembles = [ ]

       for ensemble_config in configuration[ 'ensembles' ]:
           if not ensemble_config.get( 'enabled', True ):
               continue

           ensemble = await create_ensemble_from_configuration( ensemble_config )
           await ensemble.connect( )
           ensembles.append( ensemble )

       return ensembles

Error Handling
-------------------------------------------------------------------------------

Tool execution errors are handled with fail-fast approach per
:doc:`../decisions/005-tool-calling-mvp-scope`.

**Error categories**:

1. **Schema validation errors**: Arguments don't match JSON Schema
2. **Execution errors**: Tool raises exception during execution
3. **Timeout errors**: Tool exceeds time limit
4. **Permission errors**: Tool lacks required access
5. **Network errors**: External resource unavailable

**Error handling strategy**:

.. code-block:: python

   async def execute_invoker(
       invoker: Invoker,
       arguments: __.immut.Dictionary[ str, __.typx.Any ],
       context: Context,
   ) -> ResultCanister:
       ''' Executes invoker with comprehensive error handling. '''

       try:
           # Validate arguments against schema
           validate_schema( arguments, invoker.arguments_schema )

           # Execute with timeout
           result = await __.asyncio.wait_for(
               invoker( context, arguments ),
               timeout = 30.0,
           )

           # Return successful result
           return create_result_canister( result )

       except __.jsonschema.ValidationError as exception:
           # Schema validation failed
           return create_error_result( exception, "validation" )

       except __.asyncio.TimeoutError:
           # Tool exceeded timeout
           return create_error_result( "Tool execution timed out.", "timeout" )

       except Exception as exception:
           # Tool execution failed - fail fast
           alert_user( f"Tool '{invoker.name}' failed: {exception}" )
           raise ToolExecutionFailure(
               f"Tool '{invoker.name}' failed.",
           ) from exception

Interactions and Data Flow
===============================================================================

Tool Calling Flow
-------------------------------------------------------------------------------

1. **User sends message**: User provides input requiring external data
2. **LLM requests tool**: Assistant responds with InvocationCanister
3. **Processor finds invoker**: InvocationsProcessor locates invoker by name
4. **Invoker executes**: Tool executes with validated arguments
5. **Result returned**: ResultCanister created with tool output
6. **LLM generates response**: Assistant incorporates tool result

Complete Conversation Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from . import __

   conversation = [
       # 1. User asks question requiring tool
       UserCanisterClass(
           content = TextualContentClass( text = "What's the weather in SF?" ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),

       # 2. LLM requests tool invocation
       AssistantCanisterClass(
           content = __.absent,  # No text content
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
       InvocationCanisterClass(
           identifier = "call_abc123",
           name = "get_weather",
           arguments = __.immut.Dictionary( { 'location': 'San Francisco, CA' } ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),

       # 3. Application executes tool and provides result
       ResultCanisterClass(
           invocation_id = "call_abc123",
           content = TextualContentClass(
               text = '{"temperature": 62, "conditions": "Partly cloudy"}',
           ),
           error = __.absent,
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),

       # 4. LLM generates final response
       AssistantCanisterClass(
           content = TextualContentClass(
               text = "The weather in San Francisco is 62°F and partly cloudy.",
           ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

Ensemble Lifecycle Management
-------------------------------------------------------------------------------

.. code-block:: python

   # Initialize ensembles
   ensembles = await prepare_ensembles( configuration )

   # Conduct conversation with tool support
   try:
       response = await model.converse(
           canisters,
           ensembles = ensembles,
       )
   finally:
       # Clean up ensemble resources
       for ensemble in ensembles:
           await ensemble.disconnect( )

Examples and Usage Patterns
===============================================================================

Example 1: Simple Tool Invocation
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Define invocable
   async def get_weather(
       context: Context,
       arguments: __.immut.Dictionary[ str, __.typx.Any ],
   ) -> __.immut.Dictionary[ str, __.typx.Any ]:
       ''' Fetches weather for specified location. '''

       location = arguments[ 'location' ]
       # ... fetch weather data ...
       return __.immut.Dictionary( {
           'temperature': 62,
           'conditions': 'Partly cloudy',
       } )

   # Create invoker
   invoker = InvokerClass(
       name = "get_weather",
       invocable = get_weather,
       arguments_schema = __.immut.Dictionary( {
           'type': 'object',
           'properties': {
               'location': { 'type': 'string', 'description': 'City and state' },
           },
           'required': [ 'location' ],
       } ),
       ensemble = io_ensemble,
   )

Example 2: Ensemble with Multiple Tools
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Create ensemble
   io_ensemble = EnsembleClass(
       name = "io",
       invokers = __.immut.Dictionary( {
           'read_file': read_file_invoker,
           'write_file': write_file_invoker,
           'list_directory': list_directory_invoker,
       } ),
       configuration = __.immut.Dictionary( { 'timeout': 30 } ),
       connection = __.absent,
   )

   # Connect ensemble
   await io_ensemble.connect( )

   # Access invoker
   invoker = io_ensemble.access_invoker( 'read_file' )

Example 3: Error Handling
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Execute with error handling
   try:
       result = await execute_invoker( invoker, arguments, context )

       if not __.is_absent( result.error ):
           # Tool execution failed
           handle_tool_error( result.error )
       else:
           # Tool execution succeeded
           process_tool_result( result.content )

   except ToolExecutionFailure as exception:
       # Fatal tool execution error
       logger.error( f"Tool failed: {exception}" )
       rollback_conversation( )

Alternative Approaches Considered
===============================================================================

See :doc:`../decisions/003-tool-organization-with-ensembles` for ensemble vs
flat registry analysis.

See :doc:`../decisions/005-tool-calling-mvp-scope` for scope decisions
(including deduplicator deferral).

**Flat invoker registry** vs ensembles:

* Flat registry simpler but lacks lifecycle management for MCP servers
* Ensembles provide natural mapping to MCP servers
* Ensembles enable name scoping and configuration locality

**Eager deduplication** vs deferred:

* Deduplication saves tokens but may bust server-side caching
* MVP relies on provider caching for cost efficiency
* Deduplication added when conversations approach context limits

Implementation Roadmap
===============================================================================

**Phase 1 (MVP)**:

1. Implement ``Invoker``, ``Ensemble``, ``Context`` protocols
2. Implement ``InvocationsProcessor`` protocol
3. Create configuration loading for TOML descriptors
4. Implement schema validation using JSON Schema
5. Create fail-fast error handling strategy
6. Implement Anthropic InvocationsProcessor
7. Add MCP server tool discovery (see :doc:`mcp-integration`)

**Phase 2**:

1. Implement OpenAI InvocationsProcessor
2. Add tool result caching beyond deduplication
3. Implement permission/sandbox system for tools
4. Add tool execution metrics and monitoring
5. Enhance error recovery strategies

References
===============================================================================

* :doc:`../decisions/003-tool-organization-with-ensembles` - Ensemble decision
* :doc:`../decisions/005-tool-calling-mvp-scope` - MVP scope and deferrals
* :doc:`message-abstraction` - Invocation and Result canisters
* :doc:`mcp-integration` - MCP server integration patterns
* ai-experiments invocables: https://github.com/emcd/ai-experiments
* JSON Schema specification: https://json-schema.org/
