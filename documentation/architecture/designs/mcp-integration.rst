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
MCP Server Integration
*******************************************************************************

:Author: Architecture Team
:Date: 2025-11-18
:Status: Draft

.. note::

   This design document requires closer review and validation against the MCP
   specification and SDK patterns. The interfaces and protocols described here
   represent an initial design that should be revisited during implementation.

Overview
===============================================================================

Model Context Protocol (MCP) provides a standardized interface for tools,
resources, and prompts that LLMs can access. This design describes integration
patterns for calling tools on external MCP servers, enabling the converser to
leverage the growing ecosystem of MCP-compatible services.

**Integration scope**:

* **Phase 1 (MVP)**: Calling tools ON MCP servers
* **Phase 2**: Wrapping converser AS an MCP server

**Core patterns**:

* MCP server connection and lifecycle management
* Tool discovery and schema adaptation
* Invoker adapter pattern for MCP tools
* Ensemble-based organization of MCP tools

Goals and Non-Goals
===============================================================================

**Goals (Phase 1 - MVP):**

* Connect to external MCP servers via stdio and HTTP transports
* Discover tools available on MCP servers
* Adapt MCP tools to invoker interface
* Execute MCP tool calls from LLM requests
* Manage MCP server lifecycle (connect/disconnect)

**Non-Goals (deferred to Phase 2):**

* Wrapping converser as an MCP server
* Exposing converser tools to other MCP clients
* MCP resource and prompt support
* Advanced MCP features (sampling, logging, progress)

Design Details
===============================================================================

MCP Client Interface
-------------------------------------------------------------------------------

**MCPClient**: Protocol for MCP server connection and communication.

.. code-block:: python

   from . import __

   class MCPClient( __.immut.Protocol ):
       ''' MCP server client managing connection and tool access. '''

       async def connect( self ) -> None: ...
       ''' Establishes connection to MCP server. '''

       async def disconnect( self ) -> None: ...
       ''' Closes connection to MCP server. '''

       async def list_tools( self ) -> __.cabc.Sequence[ MCPTool ]: ...
       ''' Discovers available tools from server. '''

       async def call_tool(
           self,
           name: str,
           arguments: __.immut.Dictionary[ str, __.typx.Any ],
       ) -> __.typx.Any: ...
       ''' Invokes tool on MCP server with provided arguments. '''

**MCPTool**: Tool description from MCP server.

.. code-block:: python

   class MCPTool( __.immut.Protocol ):
       ''' Tool description from MCP server. '''

       @property
       def name( self ) -> str: ...
       ''' Tool identifier. '''

       @property
       def description( self ) -> str: ...
       ''' Human-readable tool description. '''

       @property
       def input_schema( self ) -> __.immut.Dictionary[ str, __.typx.Any ]: ...
       ''' JSON Schema for tool arguments. '''

MCP Server Connection
-------------------------------------------------------------------------------

MCP servers support multiple transport mechanisms. The MVP focuses on stdio and
HTTP transports.

**Stdio transport**: Subprocess-based communication.

.. code-block:: python

   class StdioMCPClient:
       ''' MCP client using stdio transport. '''

       def __init__(
           self,
           command: __.cabc.Sequence[ str ],
           environment: __.Absential[ __.cabc.Mapping[ str, str ] ] = __.absent,
       ) -> None:
           ''' Initializes stdio MCP client. '''

       async def connect( self ) -> None:
           ''' Spawns subprocess and establishes communication. '''

       async def disconnect( self ) -> None:
           ''' Terminates subprocess and cleans up resources. '''

**HTTP transport**: Network-based communication.

.. code-block:: python

   class HttpMCPClient:
       ''' MCP client using HTTP transport. '''

       def __init__(
           self,
           url: str,
           headers: __.Absential[ __.cabc.Mapping[ str, str ] ] = __.absent,
       ) -> None:
           ''' Initializes HTTP MCP client. '''

       async def connect( self ) -> None:
           ''' Establishes HTTP connection to server. '''

       async def disconnect( self ) -> None:
           ''' Closes HTTP connection. '''

Connection Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: toml

   # Stdio MCP server configuration
   [mcp.weather]
   transport = "stdio"
   command = ["python", "-m", "weather_mcp_server"]
   environment = {WEATHER_API_KEY = "env:WEATHER_API_KEY"}

   # HTTP MCP server configuration
   [mcp.database]
   transport = "http"
   url = "http://localhost:8080/mcp"
   headers = {Authorization = "env:DATABASE_TOKEN"}

Tool Discovery
-------------------------------------------------------------------------------

MCP servers expose available tools through the ``list_tools`` operation.
Discovered tools are adapted to the invoker interface.

**Discovery flow**:

1. Connect to MCP server
2. Call ``list_tools()`` to discover available tools
3. For each tool, create invoker adapter
4. Register invokers in MCP-specific ensemble
5. Tools become available for LLM invocation

.. code-block:: python

   async def discover_mcp_tools(
       client: MCPClient,
       ensemble_name: str,
   ) -> Ensemble:
       ''' Discovers tools from MCP server and creates ensemble. '''

       # Connect to server
       await client.connect( )

       # Discover tools
       mcp_tools = await client.list_tools( )

       # Create invokers from MCP tools
       invokers = { }
       for mcp_tool in mcp_tools:
           invoker = create_invoker_from_mcp_tool( mcp_tool, client )
           invokers[ mcp_tool.name ] = invoker

       # Create ensemble with MCP client connection
       ensemble = EnsembleClass(
           name = ensemble_name,
           invokers = __.immut.Dictionary( invokers ),
           configuration = __.immut.Dictionary( { } ),
           connection = client,
       )

       return ensemble

Invoker Adapter Pattern
-------------------------------------------------------------------------------

MCP tools are adapted to the invoker interface, enabling transparent invocation
alongside local tools.

**Adapter implementation**:

.. code-block:: python

   def create_invoker_from_mcp_tool(
       mcp_tool: MCPTool,
       client: MCPClient,
   ) -> Invoker:
       ''' Adapts MCP tool to invoker interface. '''

       async def mcp_invocable(
           context: Context,
           arguments: __.immut.Dictionary[ str, __.typx.Any ],
       ) -> __.typx.Any:
           ''' Executes MCP tool via client. '''

           result = await client.call_tool( mcp_tool.name, arguments )
           return result

       return InvokerClass(
           name = mcp_tool.name,
           invocable = mcp_invocable,
           arguments_schema = mcp_tool.input_schema,
           ensemble = mcp_ensemble,
       )

**Key adapter characteristics**:

* MCP tool name maps directly to invoker name
* MCP input schema becomes invoker arguments schema
* Tool invocation delegates to MCP client
* Context provides access to ensemble configuration
* No deduplication (MCP servers handle caching internally)

Ensemble-Based Organization
-------------------------------------------------------------------------------

Each MCP server maps to a dedicated ensemble, providing:

* **Lifecycle management**: Connect/disconnect MCP server as unit
* **Configuration locality**: Server-level settings in ensemble configuration
* **Name scoping**: Multiple MCP servers can expose tools with same names
* **Connection reference**: Ensemble stores MCP client for tool execution

See :doc:`../decisions/003-tool-organization-with-ensembles` for detailed
rationale on ensemble architecture.

**Example ensemble structure**:

.. code-block:: python

   weather_ensemble = EnsembleClass(
       name = "mcp-weather",
       invokers = __.immut.Dictionary( {
           'get_weather': weather_invoker,
           'get_forecast': forecast_invoker,
       } ),
       configuration = __.immut.Dictionary( {
           'api_key': 'xxx',
           'timeout': 10,
       } ),
       connection = weather_mcp_client,
   )

Interactions and Data Flow
===============================================================================

MCP Tool Invocation Flow
-------------------------------------------------------------------------------

1. **Ensemble initialization**: MCP client connects to server
2. **Tool discovery**: Client lists available tools
3. **Invoker creation**: Adapters wrap MCP tools as invokers
4. **LLM requests tool**: InvocationCanister specifies MCP tool
5. **Adapter execution**: Invoker delegates to MCP client
6. **Result normalization**: MCP response becomes ResultCanister
7. **Ensemble cleanup**: MCP client disconnects when conversation ends

Complete Flow Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from . import __

   # 1. Create MCP client
   weather_client = StdioMCPClient(
       command = [ 'python', '-m', 'weather_mcp_server' ],
   )

   # 2. Discover tools and create ensemble
   weather_ensemble = await discover_mcp_tools(
       weather_client,
       ensemble_name = "mcp-weather",
   )

   # 3. Conduct conversation with MCP tools available
   canisters = [
       UserCanisterClass(
           content = TextualContentClass( text = "What's the weather in NYC?" ),
           timestamp = __.datetime.datetime.now( __.datetime.UTC ),
       ),
   ]

   # 4. LLM invokes MCP tool
   response = await model.converse(
       canisters,
       ensembles = [ weather_ensemble ],
   )

   # Response includes InvocationCanister for MCP tool
   # which gets executed via adapter → MCP client → server

   # 5. Cleanup
   await weather_ensemble.disconnect( )

Error Handling
-------------------------------------------------------------------------------

MCP tool invocations may fail due to:

* Connection errors (server unreachable)
* Tool execution errors (server-side failures)
* Timeout errors (slow tool execution)
* Protocol errors (malformed requests/responses)

**Error handling strategy**:

.. code-block:: python

   async def mcp_invocable(
       context: Context,
       arguments: __.immut.Dictionary[ str, __.typx.Any ],
   ) -> __.typx.Any:
       ''' MCP tool adapter with error handling. '''

       try:
           result = await client.call_tool( tool_name, arguments )
           return result

       except MCPConnectionFailure as exception:
           # Server unreachable
           raise ToolExecutionFailure(
               f"MCP server connection failed: {exception}",
           ) from exception

       except MCPExecutionFailure as exception:
           # Tool execution failed on server
           raise ToolExecutionFailure(
               f"MCP tool execution failed: {exception}",
           ) from exception

       except __.asyncio.TimeoutError:
           # Tool execution timed out
           raise ToolExecutionFailure(
               f"MCP tool timed out.",
           )

Examples and Usage Patterns
===============================================================================

Example 1: Stdio MCP Server
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Configuration
   config = {
       'transport': 'stdio',
       'command': [ 'npx', '-y', '@modelcontextprotocol/server-filesystem' ],
       'environment': { 'ALLOWED_PATHS': '/data,/tmp' },
   }

   # Create client
   filesystem_client = StdioMCPClient(
       command = config[ 'command' ],
       environment = __.immut.Dictionary( config[ 'environment' ] ),
   )

   # Discover and use tools
   filesystem_ensemble = await discover_mcp_tools(
       filesystem_client,
       ensemble_name = "mcp-filesystem",
   )

Example 2: HTTP MCP Server
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Configuration
   config = {
       'transport': 'http',
       'url': 'https://api.example.com/mcp',
       'headers': { 'Authorization': f"Bearer {token}" },
   }

   # Create client
   api_client = HttpMCPClient(
       url = config[ 'url' ],
       headers = __.immut.Dictionary( config[ 'headers' ] ),
   )

   # Discover and use tools
   api_ensemble = await discover_mcp_tools(
       api_client,
       ensemble_name = "mcp-api",
   )

Example 3: Multiple MCP Servers
-------------------------------------------------------------------------------

.. code-block:: python

   from . import __

   # Create multiple MCP ensembles
   weather_ensemble = await discover_mcp_tools(
       weather_client,
       "mcp-weather",
   )

   filesystem_ensemble = await discover_mcp_tools(
       filesystem_client,
       "mcp-filesystem",
   )

   database_ensemble = await discover_mcp_tools(
       database_client,
       "mcp-database",
   )

   # Use all ensembles in conversation
   response = await model.converse(
       canisters,
       ensembles = [
           weather_ensemble,
           filesystem_ensemble,
           database_ensemble,
       ],
   )

   # Cleanup all MCP connections
   for ensemble in [ weather_ensemble, filesystem_ensemble, database_ensemble ]:
       await ensemble.disconnect( )

Alternative Approaches Considered
===============================================================================

**Direct MCP SDK usage** vs adapter pattern:

* Direct usage couples application to MCP protocol details
* Adapter pattern enables uniform tool interface
* Adapters allow mixing local and MCP tools seamlessly

**Global MCP client** vs ensemble-scoped:

* Global client simpler but complicates lifecycle management
* Ensemble-scoped enables independent server lifecycles
* Ensemble pattern matches MCP server organizational model

**Flat tool registry** vs ensemble organization:

* See :doc:`../decisions/003-tool-organization-with-ensembles`
* Ensembles provide natural MCP server lifecycle boundaries
* Ensembles enable name scoping across multiple servers

Implementation Roadmap
===============================================================================

**Phase 1 (MVP)**:

1. Implement ``MCPClient`` protocol
2. Create ``StdioMCPClient`` implementation
3. Create ``HttpMCPClient`` implementation
4. Implement tool discovery mechanism
5. Create MCP tool to invoker adapter
6. Add MCP server configuration loading
7. Implement error handling for MCP operations
8. Add lifecycle management (connect/disconnect)

**Phase 2**:

1. Wrap converser as MCP server
2. Expose converser tools to other MCP clients
3. Add MCP resource support
4. Add MCP prompt support
5. Implement advanced MCP features (sampling, logging, progress)
6. Add MCP server health monitoring
7. Enhance error recovery and retry logic

References
===============================================================================

* :doc:`../decisions/003-tool-organization-with-ensembles` - Ensemble rationale
* :doc:`../decisions/005-tool-calling-mvp-scope` - MVP scope for MCP
* :doc:`tool-calling` - Invoker and ensemble architecture
* :doc:`message-abstraction` - Invocation and Result canisters
* MCP specification: https://modelcontextprotocol.io/
* MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
