# Tool/Function Calling Architecture

**Date**: 2025-11-15
**Purpose**: Detailed documentation of tool-calling architecture and invocables framework

## Overview

Tool calling (also called function calling) enables LLMs to invoke external functions or tools to gather information, perform actions, or extend their capabilities beyond pure text generation. This is a **critical MVP requirement** for vibe-py-llms-converser.

### Why Tool Calling is Essential

Without tool calling, LLMs are limited to:
- Static knowledge from training data
- No ability to access current information
- No ability to perform actions
- No integration with external systems

With tool calling, LLMs can:
- Query databases and APIs
- Read and write files
- Perform calculations
- Access real-time data
- Execute code
- Interact with external services

**User's requirement**: "Without function calling, the tool is nearly worthless for intended use cases."

## Tool Calling Flow

### 1. User Sends Message
```
User: "What's the weather in San Francisco?"
```

### 2. LLM Requests Tool Invocation
The LLM recognizes it needs external data and responds with a tool call request:
```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [{
    "id": "call_abc123",
    "name": "get_weather",
    "arguments": {"location": "San Francisco, CA"}
  }]
}
```

### 3. Application Executes Tool
The application's `InvocationsProcessor` receives this request, finds the registered `get_weather` invoker, and executes it:
```python
result = await get_weather(location="San Francisco, CA")
# Returns: {"temperature": 62, "conditions": "Partly cloudy"}
```

### 4. Application Sends Tool Result Back
```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "{\"temperature\": 62, \"conditions\": \"Partly cloudy\"}"
}
```

### 5. LLM Generates Final Response
The LLM incorporates the tool result into its response:
```
Assistant: "The current weather in San Francisco is 62°F with partly cloudy conditions."
```

## Invocables Architecture (from ai-experiments)

The ai-experiments project has a sophisticated invocables framework that we'll preserve in vibe-py-llms-converser.

### Core Components

#### Invoker

An **Invoker** wraps a single callable function/tool with metadata and validation:

```python
@dataclass
class Invoker:
    """Wraps a tool function with schema and lifecycle management."""

    name: str                          # Tool identifier
    invocable: Invocable              # Async callable
    arguments_schema: dict            # JSON Schema for validation
    ensemble: Ensemble                # Parent group
    deduplicator: Deduplicator | None # Optional duplicate prevention

    async def __call__(self, context: Context, arguments: Arguments) -> Any:
        """Execute the wrapped function with validation."""
        # Validate arguments against schema
        # Check for duplicates via deduplicator
        # Execute invocable
        # Return result
```

**Key features**:
- **Schema validation**: Arguments validated against JSON Schema before execution
- **Context injection**: Invokers receive execution context (auxdata, namespace)
- **Async-first**: All invocables are coroutines
- **Deduplication**: Optional duplicate call prevention

**Example invoker registration**:
```python
@register_invoker(
    name="get_weather",
    schema={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City and state"}
        },
        "required": ["location"]
    }
)
async def get_weather(context: Context, arguments: Arguments) -> dict:
    location = arguments["location"]
    # ... fetch weather data ...
    return {"temperature": temp, "conditions": conditions}
```

#### Ensemble

An **Ensemble** groups related invokers together for organization and lifecycle management:

```python
@dataclass
class Ensemble:
    """Container grouping related invokers."""

    name: str                    # Ensemble identifier (e.g., "io", "probability")
    invokers: dict[str, Invoker] # Name -> Invoker mapping

    async def prepare_invokers(
        self,
        descriptors: dict,
        defaults: dict,
    ) -> None:
        """Hydrate invokers from configuration."""
        # Instantiate invokers from descriptors
        # Apply defaults
        # Validate schemas
```

**Standard ensembles in ai-experiments**:
- **io**: File operations, network requests, database queries
- **probability**: Statistical functions, random sampling
- **summarization**: Text summarization utilities

**Benefits**:
- **Organization**: Related tools grouped logically
- **Lifecycle**: Enable/disable entire groups
- **Configuration**: Ensemble-level defaults and settings

**Ensemble configuration example**:
```toml
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
```

#### Deduplicator

A **Deduplicator** prevents redundant tool calls within a conversation:

```python
class Deduplicator(Protocol):
    """Protocol for detecting duplicate invocations."""

    def is_duplicate(
        self,
        name: str,
        arguments: Arguments,
    ) -> bool:
        """Check if invocation is duplicate of previous call."""
        ...

    def record(
        self,
        name: str,
        arguments: Arguments,
    ) -> None:
        """Record invocation for future duplicate detection."""
        ...
```

**Why deduplication matters**:

LLMs sometimes request the same tool call multiple times:
- Redundant API calls waste resources and money
- Repeated file reads are inefficient
- Duplicate database queries slow conversations

**Deduplication strategies**:

1. **Exact match**: Same name + same arguments = duplicate
2. **Semantic match**: Similar arguments treated as duplicates
3. **Time-window**: Only dedupe within N seconds/messages
4. **Result caching**: Return cached result for duplicates

**Example deduplicator implementation**:
```python
class ExactDeduplicator:
    """Deduplicates based on exact name+arguments match."""

    def __init__(self):
        self._history: set[tuple[str, str]] = set()

    def is_duplicate(self, name: str, arguments: Arguments) -> bool:
        key = (name, json.dumps(arguments, sort_keys=True))
        return key in self._history

    def record(self, name: str, arguments: Arguments) -> None:
        key = (name, json.dumps(arguments, sort_keys=True))
        self._history.add(key)
```

**Decision**: Keep deduplicator in vibe-py-llms-converser (minimal complexity, proven benefit)

### Invocation Flow in Code

```python
# 1. Setup: Register tools in ensembles
io_ensemble = Ensemble(name="io")
await io_ensemble.prepare_invokers(
    descriptors=load_invoker_descriptors("io"),
    defaults={"timeout": 30}
)

# 2. LLM requests tool call
assistant_message = {
    "role": "assistant",
    "tool_calls": [{
        "name": "read_file",
        "arguments": {"path": "/data/report.txt"}
    }]
}

# 3. InvocationsProcessor finds and executes invoker
processor = InvocationsProcessor(ensembles=[io_ensemble])
invoker = processor.find_invoker("read_file")

# 4. Check for duplicates
if invoker.deduplicator and invoker.deduplicator.is_duplicate(
    "read_file",
    {"path": "/data/report.txt"}
):
    result = get_cached_result(...)
else:
    # 5. Execute invoker
    context = Context(auxdata={...}, invoker=invoker, namespace={...})
    result = await invoker(context, {"path": "/data/report.txt"})
    invoker.deduplicator.record("read_file", {"path": "/data/report.txt"})

# 6. Create Result canister
result_canister = ResultCanister(
    invocation_id="call_abc123",
    content=TextualContent(text=json.dumps(result))
)

# 7. Send back to LLM
conversation.add_canister(result_canister)
response = await model.converse(conversation.canisters)
```

## Message Representation: Invocation and Result Canisters

### InvocationCanister

Represents a tool call request from the LLM:

```python
@dataclass
class InvocationCanister:
    """Tool invocation request from assistant."""

    id: str                          # Unique invocation ID
    name: str                        # Invoker name
    arguments: dict[str, Any]        # Tool arguments
    timestamp: datetime

    @property
    def role(self) -> Role:
        return Role.invocation
```

**Provider mapping**:
- **Anthropic**: Maps to `tool_use` content block
- **OpenAI**: Maps to `tool_calls` in assistant message
- **Other providers**: Normalize to provider's tool calling format

### ResultCanister

Represents the result of a tool execution:

```python
@dataclass
class ResultCanister:
    """Tool execution result sent back to assistant."""

    invocation_id: str               # References InvocationCanister.id
    content: Content                 # Result payload (usually TextualContent)
    timestamp: datetime
    error: str | None = None         # If tool execution failed

    @property
    def role(self) -> Role:
        return Role.result
```

**Provider mapping**:
- **Anthropic**: Maps to `tool_result` content block
- **OpenAI**: Maps to `tool` role message
- **Other providers**: Normalize to provider's result format

### Example Conversation with Tool Calls

```python
conversation = [
    UserCanister(content=TextualContent("What's the weather in SF?")),

    # LLM requests tool call
    AssistantCanister(content=None),  # No text content
    InvocationCanister(
        id="call_123",
        name="get_weather",
        arguments={"location": "San Francisco, CA"}
    ),

    # Application provides result
    ResultCanister(
        invocation_id="call_123",
        content=TextualContent('{"temp": 62, "conditions": "Partly cloudy"}')
    ),

    # LLM generates final response
    AssistantCanister(
        content=TextualContent("The weather in San Francisco is 62°F and partly cloudy.")
    ),
]
```

## InvocationsProcessor

The **InvocationsProcessor** is responsible for:
1. Converting normalized Invocation/Result canisters to provider-native format
2. Converting provider-native tool calls to normalized canisters
3. Managing invoker registry and execution
4. Handling tool call errors

### Provider-Specific Processing

#### Anthropic

**To native**:
```python
# InvocationCanister -> tool_use content block
{
    "type": "tool_use",
    "id": invocation.id,
    "name": invocation.name,
    "input": invocation.arguments
}

# ResultCanister -> tool_result content block
{
    "type": "tool_result",
    "tool_use_id": result.invocation_id,
    "content": result.content.text
}
```

**From native**:
```python
# tool_use block -> InvocationCanister
InvocationCanister(
    id=block["id"],
    name=block["name"],
    arguments=block["input"]
)
```

#### OpenAI

**To native**:
```python
# InvocationCanister -> tool_calls in message
{
    "role": "assistant",
    "content": null,
    "tool_calls": [{
        "id": invocation.id,
        "type": "function",
        "function": {
            "name": invocation.name,
            "arguments": json.dumps(invocation.arguments)
        }
    }]
}

# ResultCanister -> tool message
{
    "role": "tool",
    "tool_call_id": result.invocation_id,
    "content": result.content.text
}
```

**From native**:
```python
# tool_calls -> InvocationCanister
for call in message["tool_calls"]:
    InvocationCanister(
        id=call["id"],
        name=call["function"]["name"],
        arguments=json.loads(call["function"]["arguments"])
    )
```

## MCP Server Integration

**MCP (Model Context Protocol)** defines a standard for tools/resources that LLMs can use.

### Important Distinction: Two Separate MCP Concerns

#### 1. Calling Tools ON MCP Servers (MVP - NOT Deferred)

**What**: Invoking tools that are hosted on external MCP servers

**Status**: **Required for MVP** (Phase 1)

**Rationale** (from stakeholder review):
> "Calling tools on MCP servers was *not* deferred"

This is part of the core invocables architecture and essential for tool/function calling functionality.

#### 2. Wrapping Converser AS an MCP Server (Deferred)

**What**: Exposing vibe-py-llms-converser itself as an MCP server that other tools can call

**Status**: **Phase 2** (can be deferred)

**Rationale** (from stakeholder review):
> "Only wrapping the converser as an MCP server itself" is deferred. Integration with Claude Code desired but "not immediately critical for Phase 1"

### MCP Concepts

- **Tools**: Functions that LLMs can invoke (maps to our Invokers)
- **Resources**: Data sources that LLMs can read (file systems, databases, APIs)
- **Prompts**: Pre-defined prompt templates

### Integration Strategy for Calling MCP Tools

**Phase 1 (MVP)**: MCP server tool discovery and invocation

```python
# Connect to MCP server and discover tools
mcp_client = MCPClient("stdio://weather-server")
tools = await mcp_client.list_tools()

# Create invokers from MCP tools
for tool in tools:
    invoker = create_invoker_from_mcp_tool(tool, mcp_client)
    io_ensemble.register(invoker)
```

**Phase 2**: Advanced MCP features (resources, prompts, wrapping as server)
```python
# Discover tools from MCP servers
mcp_client = MCPClient("stdio://weather-server")
tools = await mcp_client.list_tools()

# Create invokers from MCP tools
for tool in tools:
    invoker = create_invoker_from_mcp_tool(tool, mcp_client)
    io_ensemble.register(invoker)
```

**MCP tool to invoker adapter**:
```python
def create_invoker_from_mcp_tool(
    tool: MCPTool,
    client: MCPClient,
) -> Invoker:
    """Wrap MCP tool as an invoker."""

    async def mcp_invocable(context: Context, arguments: Arguments) -> Any:
        # Call MCP server's tool
        result = await client.call_tool(tool.name, arguments)
        return result

    return Invoker(
        name=tool.name,
        invocable=mcp_invocable,
        arguments_schema=tool.input_schema,
        ensemble=mcp_ensemble,
        deduplicator=None,  # MCP tools handle caching internally
    )
```

### Why Ensemble Architecture Supports MCP

The user noted: "We can evaluate whether we need full ensembles or not, but I have found them useful for grouping related tools. However, I do want to ensure that we support MCP servers, no matter what we decide in terms of ensemble architecture."

Ensembles naturally map to MCP servers:
- One ensemble per MCP server
- MCP server name → ensemble name
- MCP tools → invokers in ensemble

**Example**:
```python
# MCP server: weather-server
weather_ensemble = Ensemble(name="weather-server")
weather_ensemble.add_invoker(get_weather_invoker)
weather_ensemble.add_invoker(get_forecast_invoker)

# MCP server: file-server
file_ensemble = Ensemble(name="file-server")
file_ensemble.add_invoker(read_file_invoker)
file_ensemble.add_invoker(write_file_invoker)
```

This allows:
- Enabling/disabling entire MCP servers
- MCP server lifecycle management
- Clear separation of tool sources

## Configuration-Driven Invocables

Following ai-experiments pattern, invokers are configured via TOML:

### Invoker Descriptor

```toml
# data/ensembles/io/invokers/read_file.toml
[invoker]
name = "read_file"
enabled = true
description = "Read contents of a file"

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
```

### Ensemble Descriptor

```toml
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
```

### Loading Invocables

```python
async def prepare_invocables(provider_config: dict) -> list[Ensemble]:
    """Load and prepare invocables from configuration."""
    ensembles = []

    for ensemble_desc in provider_config["ensembles"]:
        ensemble = Ensemble(name=ensemble_desc["name"])

        for invoker_desc in ensemble_desc["invokers"]:
            if not invoker_desc.get("enabled", True):
                continue

            # Load invoker implementation
            invocable = load_invocable(invoker_desc["name"])

            # Create invoker with schema
            invoker = Invoker(
                name=invoker_desc["name"],
                invocable=invocable,
                arguments_schema=invoker_desc["arguments"],
                ensemble=ensemble,
                deduplicator=create_deduplicator(invoker_desc.get("deduplicator")),
            )

            ensemble.register(invoker)

        ensembles.append(ensemble)

    return ensembles
```

## Error Handling in Tool Calling

### Error Categories

1. **Schema validation errors**: Arguments don't match JSON Schema
2. **Execution errors**: Tool raises exception during execution
3. **Timeout errors**: Tool exceeds time limit
4. **Permission errors**: Tool lacks required access
5. **Network errors**: API/resource unavailable

### Error Handling Strategy

**Decision from review**: "Fail-fast approach with user alerts and GUI/TUI rollback on failures"

```python
async def execute_invoker(
    invoker: Invoker,
    arguments: Arguments,
) -> ResultCanister:
    """Execute invoker with error handling."""

    try:
        # 1. Validate arguments
        validate_schema(arguments, invoker.arguments_schema)

        # 2. Execute with timeout
        result = await asyncio.wait_for(
            invoker(context, arguments),
            timeout=30.0
        )

        # 3. Return successful result
        return ResultCanister(
            invocation_id=invocation_id,
            content=TextualContent(text=json.dumps(result))
        )

    except jsonschema.ValidationError as e:
        # Schema validation failed
        logger.error(f"Invalid arguments for {invoker.name}: {e}")
        return ResultCanister(
            invocation_id=invocation_id,
            content=TextualContent(text=f"Error: Invalid arguments - {e}"),
            error=str(e)
        )

    except asyncio.TimeoutError:
        # Tool exceeded timeout
        logger.error(f"Tool {invoker.name} timed out")
        return ResultCanister(
            invocation_id=invocation_id,
            content=TextualContent(text="Error: Tool execution timed out"),
            error="timeout"
        )

    except Exception as e:
        # Tool execution failed
        logger.error(f"Tool {invoker.name} failed: {e}", exc_info=True)

        # Alert user
        alert_user(f"Tool '{invoker.name}' failed: {e}")

        # Fail-fast: propagate error to conversation level
        raise ToolExecutionError(
            f"Tool '{invoker.name}' failed",
            invoker=invoker,
            arguments=arguments
        ) from e
```

### Result Canister with Error

When a tool fails, we still send a ResultCanister to the LLM (with error info), allowing the LLM to potentially recover or ask for clarification:

```python
ResultCanister(
    invocation_id="call_123",
    content=TextualContent(text="Error: File not found: /data/missing.txt"),
    error="FileNotFoundError"
)
```

The LLM might respond:
```
Assistant: "I couldn't find the file /data/missing.txt. Could you verify the path?"
```

## Summary

### Key Decisions

✅ **Keep full invocables architecture** from ai-experiments:
- Invoker: Wraps tools with schema validation
- Ensemble: Groups related invokers
- Deduplicator: Prevents redundant calls

✅ **Tool calling is MVP requirement** (non-negotiable)
- InvocationsProcessor required from start
- Invocation/Result canisters in message hierarchy
- Configuration-driven invoker registration

✅ **MCP support designed from start**:
- Ensemble architecture naturally maps to MCP servers
- Adapter pattern for MCP tools → invokers
- Deferred to Phase 2 for implementation

✅ **Fail-fast error handling**:
- User alerts on tool failures
- GUI/TUI rollback on errors
- Result canisters with error info

### Architecture Benefits

1. **Provider-agnostic**: InvocationsProcessor normalizes tool calls across providers
2. **Declarative**: TOML configuration for invokers and ensembles
3. **Extensible**: Easy to add new tools or MCP servers
4. **Efficient**: Deduplication prevents redundant calls
5. **Safe**: Schema validation and error handling
6. **Organized**: Ensembles group related functionality

### Implementation Priority

**Phase 1 (MVP)**:
1. Invoker, Ensemble, Deduplicator core abstractions
2. InvocationsProcessor with Anthropic provider
3. Invocation/Result canisters
4. Configuration loading from TOML
5. Basic error handling
6. **MCP server tool discovery and invocation** (calling tools ON MCP servers)

**Phase 2**:
1. Additional providers (OpenAI, Ollama/VLLM)
2. Advanced deduplication strategies
3. Tool result caching
4. Permission/sandbox system for tools
5. **Wrapping converser AS an MCP server** (exposing converser to other tools)

## References

- ai-experiments invocables: https://github.com/emcd/ai-experiments/blob/master/sources/aiwb/invocables/core.py
- MCP Specification: https://modelcontextprotocol.io/
- Anthropic Tool Use: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
