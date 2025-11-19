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
003. Tool Organization with Ensembles
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

The system needs to organize callable tools (functions/methods that LLMs can
invoke) for registration, lifecycle management, and invocation. Tools come from
multiple sources:

* **Local tools**: Functions defined in the application
* **MCP servers**: External Model Context Protocol servers providing tools via
  stdio or HTTP

MCP servers have specific characteristics:

* **Shared lifecycle**: Connect/disconnect operations affect all tools from a
  server
* **Shared configuration**: Server URL, authentication, timeouts apply to all
  tools
* **Logical grouping**: All weather tools, all file tools, etc. from one server
* **Independent processes**: Each MCP server is a separate process/connection
* **Name scoping needs**: Different MCP servers may provide tools with identical
  names

The ai-experiments project used "ensembles" to group related tools, though the
original rationale was unclear. The question is whether this abstraction is
necessary or whether a simpler flat tool registry suffices.

Decision Drivers
===============================================================================

* **MCP server support**: Must integrate with external MCP servers (critical
  requirement)
* **Lifecycle management**: Need to connect/disconnect MCP servers cleanly
* **Configuration locality**: Server-level settings should be cohesive
* **Name conflict resolution**: Handle tools with same name from different
  sources
* **Simplicity**: Avoid unnecessary abstractions
* **Consistency**: One pattern is better than multiple patterns

Decision
===============================================================================

**Keep ensembles** as the tool organization abstraction.

An ensemble is a container for related tools with shared lifecycle and
configuration:

.. code-block:: python

   @dataclass
   class Ensemble:
       """Container for related tools with shared lifecycle."""

       name: str  # "weather-mcp", "file-mcp", "local-tools"
       invokers: dict[str, Invoker]  # Tool registry
       config: dict[str, Any] = field(default_factory=dict)
       connection: Any | None = None  # MCP client if applicable

       async def connect(self) -> None:
           """Initialize ensemble (e.g., connect to MCP server)."""
           if self.connection:
               await self.connection.connect()

       async def disconnect(self) -> None:
           """Teardown ensemble (e.g., disconnect from MCP server)."""
           if self.connection:
               await self.connection.disconnect()

**MCP servers map naturally to ensembles:**

* One ensemble per MCP server
* MCP server name → ensemble name
* MCP server tools → invokers in ensemble
* MCP connection stored in ensemble

**Local tools also use ensembles:**

* Consistent API (everything goes through ensembles)
* Logical grouping ("math-tools", "file-tools", "db-tools")
* Enable/disable groups
* Per-group configuration

Alternatives
===============================================================================

Alternative 1: Flat Tool Registry
-------------------------------------------------------------------------------

Use a global dictionary mapping tool names to tool implementations:

.. code-block:: python

   _INVOKERS: dict[str, Invoker] = {}

   def register_invoker(name: str, source: str, invocable: Callable):
       _INVOKERS[name] = Invoker(name=name, source=source, invocable=invocable)

**Pros:**

* Simplest possible implementation
* Direct tool lookup by name
* No additional abstraction layer
* Works fine for local tools

**Cons:**

* **MCP lifecycle management awkward**: How to connect/disconnect a server?
  Loop through all invokers checking source string?
* **Configuration scattered**: Where do server-level settings live? Global dict
  by source name?
* **No natural grouping**: String matching on source is fragile
* **Name conflicts**: What if two MCP servers both have ``get_weather``? Global
  namespace collision.
* **Inconsistent patterns**: Need different code paths for MCP vs local tools

Alternative 2: MCP-Only Ensembles
-------------------------------------------------------------------------------

Use ensembles for MCP servers but flat registry for local tools:

.. code-block:: python

   # MCP servers use ensembles
   mcp_ensembles: dict[str, Ensemble] = {}

   # Local tools use flat registry
   local_invokers: dict[str, Invoker] = {}

**Pros:**

* Minimal abstraction for local tools
* Ensembles only where needed (MCP)

**Cons:**

* **Two patterns**: Different APIs for MCP vs local tools
* **Inconsistent**: Developers must remember which pattern applies
* **Tool lookup complexity**: Check both registries
* **Lost grouping benefits**: Local tools can't be organized into logical groups
* **Future migration pain**: If local tools need grouping later, requires
  refactoring

Alternative 3: Do Nothing (Defer Decision)
-------------------------------------------------------------------------------

Start without any tool organization, add it when MCP support is implemented.

**Pros:**

* Simplest for initial development
* Don't solve problems before they exist

**Cons:**

* **MCP is critical requirement**: Tool calling with MCP support is REQ-005
  (Critical priority)
* **Rework risk**: May need to refactor tool registration later
* **Unclear architecture**: Team doesn't know what pattern to follow

Consequences
===============================================================================

**Positive:**

* **Natural MCP mapping**: Ensembles directly correspond to MCP servers
* **Clean lifecycle**: ``ensemble.connect()`` / ``ensemble.disconnect()`` for
  MCP servers
* **Configuration locality**: Server config lives with its ensemble
* **Name scoping**: Tools scoped by ensemble (``weather-mcp:get_weather`` vs
  ``file-mcp:get_weather``)
* **Consistent API**: Same pattern for local and MCP tools
* **Logical organization**: Tools grouped by purpose/source
* **Proven pattern**: Used successfully in ai-experiments for 2+ years
* **Enable/disable groups**: Can disable entire MCP server or local tool group

**Negative:**

* **Slight overhead for local tools**: Must create ensemble even for simple
  local functions
* **More structure**: Additional class and concepts to understand
* **Tool lookup indirection**: Must find ensemble first, then tool within it

**Neutral:**

* **Implementation complexity**: More code than flat registry but manageable
* **Minimal overhead**: Since we need ensembles for MCP, cost for local tools is
  minimal

Implementation Notes
===============================================================================

Ensemble-to-MCP-server mapping:

.. code-block:: python

   # Connect to MCP server
   client = await mcp.connect("stdio://weather-server")

   # Discover tools
   tools = await client.list_tools()

   # Create ensemble for this MCP server
   ensemble = Ensemble(
       name="weather-server",
       config={"url": "stdio://weather-server"},
       connection=client,
   )

   # Register all tools from this server
   for tool in tools:
       invoker = create_invoker_from_mcp_tool(tool, client)
       ensemble.add_invoker(invoker)

Local tools also use ensembles:

.. code-block:: python

   local_ensemble = Ensemble(name="local-tools", config={})

   local_ensemble.add_invoker(Invoker(
       name="calculate",
       invocable=calculate_fn,
       schema={...},
   ))

Tool lookup with ensemble scoping:

.. code-block:: python

   def find_invoker(
       name: str,
       ensemble_name: str | None = None
   ) -> Invoker:
       if ensemble_name:
           return ensembles[ensemble_name].invokers[name]

       # Search all ensembles
       for ensemble in ensembles.values():
           if name in ensemble.invokers:
               return ensemble.invokers[name]

       raise ToolNotFoundError(name)

Multiple MCP servers:

.. code-block:: python

   # Weather MCP server
   weather = Ensemble(name="weather-mcp")
   await weather.connect()

   # File operations MCP server
   files = Ensemble(name="files-mcp")
   await files.connect()

   # Each ensemble manages its own MCP connection lifecycle

References
===============================================================================

* Original analysis: ``.auxiliary/notes/ensembles-analysis.md``
* MCP specification: https://modelcontextprotocol.io/
* Key insight: "MCP servers are effectively ensembles" - they naturally map to
  this abstraction
* ai-experiments usage: Ensembles used for 2+ years, pattern proven in practice
