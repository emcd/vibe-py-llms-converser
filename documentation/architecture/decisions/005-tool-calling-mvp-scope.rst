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
005. Tool Calling MVP Scope
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

Tool/function calling is a critical MVP requirement (REQ-005). Without it, LLMs
are limited to static knowledge and cannot access current information, perform
actions, or integrate with external systems.

The ai-experiments project has a comprehensive invocables framework with three
major components:

1. **Invoker**: Wraps callable tools with schema validation
2. **Ensemble**: Groups related invokers for lifecycle management
3. **Deduplicator**: Trims stale tool results from conversation history

Additionally, MCP (Model Context Protocol) server support is required to enable
integration with external tool providers.

The question is which components are essential for MVP and which can be deferred
to Phase 2.

Decision Drivers
===============================================================================

* **MVP requirement**: Tool calling is critical per REQ-005
* **Proven architecture**: ai-experiments patterns are battle-tested (2.5 years
  production use)
* **MCP integration**: Must support calling tools on MCP servers (REQ-302)
* **Simplicity**: Minimize scope while delivering core functionality
* **Extensibility**: Design for future capabilities without over-building
* **Stakeholder input**: "Tool calling is non-negotiable for MVP"

Decision
===============================================================================

**Include in MVP**:

1. **Invoker framework**: Core abstraction wrapping tools with schema validation
2. **Ensemble organization**: Required for MCP server lifecycle management (see
   :doc:`003-tool-organization-with-ensembles`)
3. **MCP server integration**: Calling tools ON external MCP servers
4. **Fail-fast error handling**: User alerts and rollback on tool failures

**Defer to Phase 2**:

1. **Deduplicators**: Skip conversation history trimming (see
   :doc:`004-conversation-history-trimming`)
2. **Wrapping converser AS MCP server**: Exposing converser to other tools
3. **Advanced context management**: Beyond basic prompt caching
4. **Tool result caching**: Explicit caching beyond deduplication

**Invoker framework** (MVP):

.. code-block:: python

   @dataclass
   class Invoker:
       """Wraps a tool with schema and lifecycle management."""

       name: str
       invocable: Callable  # Async callable
       arguments_schema: dict  # JSON Schema for validation
       ensemble: Ensemble

       async def __call__(self, context: Context, arguments: dict) -> Any:
           """Execute tool with validation."""
           # Validate arguments against schema
           # Execute invocable
           # Return result

**Ensemble organization** (MVP - see ADR-003):

.. code-block:: python

   @dataclass
   class Ensemble:
       name: str
       invokers: dict[str, Invoker]
       config: dict[str, Any] = field(default_factory=dict)
       connection: Any | None = None  # MCP client

       async def connect(self) -> None: ...
       async def disconnect(self) -> None: ...

**MCP integration** (MVP):

.. code-block:: python

   # Connect to MCP server
   client = await mcp.connect("stdio://weather-server")
   tools = await client.list_tools()

   # Create ensemble for MCP server
   ensemble = Ensemble(name="weather-server", connection=client)

   # Register tools from MCP server
   for tool in tools:
       invoker = create_invoker_from_mcp_tool(tool, client)
       ensemble.add_invoker(invoker)

Alternatives
===============================================================================

Alternative 1: Full ai-experiments Architecture in MVP
-------------------------------------------------------------------------------

Include all components from ai-experiments: invokers, ensembles, deduplicators,
and full MCP integration (including wrapping converser as MCP server).

**Pros:**

* **Complete feature parity**: Nothing left out
* **Proven system**: Known to work well in production
* **No future rework**: Everything built once

**Cons:**

* **Scope creep**: Too much for MVP
* **Deduplicators premature**: May not be needed (see ADR-004)
* **Delayed MVP**: More components = longer development time
* **Unused features**: Wrapping as MCP server not immediately critical per
  stakeholder

Alternative 2: Minimal Tool Calling (No Ensembles)
-------------------------------------------------------------------------------

Implement basic tool calling without ensembles or deduplicators:

.. code-block:: python

   _TOOLS: dict[str, Callable] = {}

   def register_tool(name: str, func: Callable):
       _TOOLS[name] = func

**Pros:**

* **Simplest possible**: Minimal abstraction
* **Fast to implement**: Fewer components

**Cons:**

* **MCP integration awkward**: No place for server lifecycle (see ADR-003)
* **Name conflicts**: Global namespace collisions
* **Configuration scattered**: No cohesive server config
* **Inconsistent with ai-experiments**: Throws away proven patterns
* **Future refactoring burden**: Would need ensembles for MCP anyway

Alternative 3: Defer All Tool Calling to Phase 2
-------------------------------------------------------------------------------

Ship MVP without any tool calling support.

**Pros:**

* **Fastest MVP**: Fewest features to build
* **Simplest codebase**: No invocables complexity

**Cons:**

* **Violates requirements**: REQ-005 is Critical priority
* **Stakeholder rejection**: "Without function calling, the tool is nearly
  worthless for intended use cases"
* **Limited utility**: LLMs can't access external data or perform actions
* **Not actually MVP**: Missing minimum viable functionality

Consequences
===============================================================================

**Positive:**

* **Clear MVP scope**: Core tool calling without advanced optimizations
* **Proven patterns**: Invoker and Ensemble from ai-experiments
* **MCP ready**: Architecture supports external tool servers from start
* **Fail-fast UX**: Errors are visible and handled cleanly
* **Extensible**: Deduplicators and MCP server wrapping can be added later
  without breaking changes
* **Data-driven**: Can profile usage before adding deduplicators

**Negative:**

* **No history trimming**: Stale tool results remain in conversation (mitigated
  by server-side caching per ADR-004)
* **Cannot expose as MCP server**: Other tools can't call converser yet
  (deferred per stakeholder input)
* **Future implementation**: May need to add deduplicators if conversations grow
  long

**Neutral:**

* **Ensemble overhead**: Slight complexity for local tools, but required for MCP
  anyway (see ADR-003)
* **Phase 2 features**: Clear roadmap for advanced capabilities

Implementation Notes
===============================================================================

**Fail-fast error handling strategy**:

.. code-block:: python

   async def execute_invoker(
       invoker: Invoker,
       arguments: dict,
   ) -> ResultMessage:
       try:
           # Validate arguments
           validate_schema(arguments, invoker.arguments_schema)

           # Execute with timeout
           result = await asyncio.wait_for(
               invoker(context, arguments),
               timeout=30.0
           )

           return ResultMessage(
               invocation_id=invocation_id,
               content=result
           )

       except ValidationError as e:
           # Alert user about invalid arguments
           alert_user(f"Invalid arguments for {invoker.name}: {e}")
           return ResultMessage(
               invocation_id=invocation_id,
               content=f"Error: {e}",
               error=str(e)
           )

       except asyncio.TimeoutError:
           # Alert user about timeout
           alert_user(f"Tool {invoker.name} timed out")
           raise ToolExecutionError("timeout")

       except Exception as e:
           # Alert user and fail fast
           alert_user(f"Tool '{invoker.name}' failed: {e}")
           raise ToolExecutionError(f"Tool failed") from e

**MCP tool adapter pattern**:

.. code-block:: python

   def create_invoker_from_mcp_tool(
       tool: MCPTool,
       client: MCPClient,
   ) -> Invoker:
       """Wrap MCP tool as an invoker."""

       async def mcp_invocable(context: Context, arguments: dict) -> Any:
           result = await client.call_tool(tool.name, arguments)
           return result

       return Invoker(
           name=tool.name,
           invocable=mcp_invocable,
           arguments_schema=tool.input_schema,
           ensemble=mcp_ensemble,
       )

**Configuration-driven invoker registration**:

.. code-block:: toml

   # data/ensembles/io.toml
   [ensemble]
   name = "io"
   enabled = true

   [[invokers]]
   name = "read_file"
   enabled = true
   description = "Read contents of a file"

   [[invokers]]
   name = "write_file"
   enabled = true
   description = "Write content to a file"

**Phase 2 roadmap**:

1. Add deduplicators if profiling shows benefit (see ADR-004)
2. Implement converser as MCP server wrapper
3. Tool result caching (explicit, not via deduplication)
4. Permission/sandbox system for tools
5. Advanced context management beyond prompt caching

References
===============================================================================

* Original analysis: ``.auxiliary/notes/invocations.md``
* ai-experiments invocables: https://github.com/emcd/ai-experiments
* MCP specification: https://modelcontextprotocol.io/
* Related ADRs:

  * :doc:`003-tool-organization-with-ensembles` - Why ensembles are required
  * :doc:`004-conversation-history-trimming` - Why deduplicators are deferred

* Stakeholder input: "Without function calling, the tool is nearly worthless"
