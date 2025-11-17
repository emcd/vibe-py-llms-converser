# Ensemble Architecture Analysis

**Question**: Do we need ensembles, or can we use a simpler flat invoker registry?

## Honest Assessment

**TL;DR**: **Yes, keep ensembles** - primarily because MCP servers ARE ensembles. The architecture naturally emerges from MCP requirements.

## The Core Insight

MCP servers are groups of tools with:
- Shared lifecycle (connect/disconnect)
- Shared configuration (server URL, auth, timeouts)
- Logical grouping (all weather tools, all file tools, etc.)
- Independent processes/connections

**This is exactly what ensembles provide.**

## Architecture Comparison

### Option A: Flat Registry (No Ensembles)

```python
# Global flat registry
_INVOKERS: dict[str, Invoker] = {}

# Each invoker tracks its source
@dataclass
class Invoker:
    name: str
    invocable: Callable
    source: str  # "mcp://weather-server", "local", etc.
    schema: dict

# Register invokers
register_invoker("get_weather", source="mcp://weather-server", ...)
register_invoker("read_file", source="local", ...)

# Lookup by name
invoker = _INVOKERS["get_weather"]

# To enable/disable MCP server
for invoker in _INVOKERS.values():
    if invoker.source == "mcp://weather-server":
        invoker.enabled = False  # Awkward
```

**Problems**:
1. **Lifecycle management is awkward**: How do we connect/disconnect an MCP server?
2. **Configuration is distributed**: Where do server-level settings live?
3. **No natural grouping**: String matching on source is fragile
4. **Name conflicts**: What if two MCP servers have `get_weather`?

### Option B: Ensemble Architecture (Current Proposal)

```python
# Ensemble per source
@dataclass
class Ensemble:
    name: str  # "weather-server", "file-ops", "local-tools"
    invokers: dict[str, Invoker]
    config: dict  # Server-level configuration
    connection: Any | None  # MCP client, if applicable

# Natural grouping
weather_ensemble = Ensemble(
    name="weather-server",
    config={"url": "stdio://weather-server", "timeout": 30},
    connection=mcp_client,
)

# Add invokers to ensemble
weather_ensemble.add_invoker(get_weather_invoker)
weather_ensemble.add_invoker(get_forecast_invoker)

# Lifecycle management
await weather_ensemble.connect()  # Start MCP server
await weather_ensemble.disconnect()  # Stop MCP server

# Global registry indexes by ensemble
_ENSEMBLES: dict[str, Ensemble] = {
    "weather-server": weather_ensemble,
    "file-ops": file_ensemble,
    "local-tools": local_ensemble,
}

# Lookup invoker (scoped by ensemble)
def find_invoker(name: str) -> Invoker | None:
    for ensemble in _ENSEMBLES.values():
        if name in ensemble.invokers:
            return ensemble.invokers[name]
    return None

# Or lookup with ensemble hint (handles name conflicts)
def find_invoker(name: str, ensemble_name: str | None = None) -> Invoker:
    if ensemble_name:
        return _ENSEMBLES[ensemble_name].invokers[name]
    # Fall back to global search
    return find_invoker(name)
```

**Benefits**:
1. **Natural lifecycle**: Connect/disconnect entire MCP servers
2. **Configuration locality**: Server config lives with ensemble
3. **Name scoping**: `weather-server:get_weather` vs `file-ops:get_weather`
4. **Clear organization**: Tools grouped by source/purpose

## Real-World Usage Patterns

### MCP Server Connection

```python
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

# Later: disconnect server
await ensemble.disconnect()
# All invokers in this ensemble become unavailable
```

### Local Tools

```python
# Local tools can live in a simple ensemble
local_ensemble = Ensemble(name="local-tools", config={})

local_ensemble.add_invoker(Invoker(
    name="calculate",
    invocable=calculate_fn,
    schema={...},
))
```

### Multiple MCP Servers

```python
# Weather MCP server
weather = Ensemble(name="weather-mcp")
weather.add_invoker(get_weather_invoker)
weather.add_invoker(get_forecast_invoker)

# File operations MCP server
files = Ensemble(name="files-mcp")
files.add_invoker(read_file_invoker)
files.add_invoker(write_file_invoker)

# Database MCP server
database = Ensemble(name="db-mcp")
database.add_invoker(query_invoker)
database.add_invoker(update_invoker)

# Each ensemble manages its own MCP connection
await weather.connect()
await files.connect()
await database.connect()
```

## Alternative: Just Use "Source" Tag?

Could we skip ensembles and just tag invokers with source?

```python
@dataclass
class Invoker:
    name: str
    source: str  # "weather-mcp", "files-mcp", "local"
    connection: Any | None  # MCP client if from MCP server
```

**Problems**:
1. Where does connection management live? Each invoker? Duplicated across all invokers from same server.
2. Where does server-level config live? Duplicated or in global dict?
3. How to disconnect server? Loop through all invokers checking source string?
4. Name conflicts still exist without scoping

**Verdict**: Ensemble is not just tagging, it's lifecycle + configuration + scoping.

## Do Local Tools Need Ensembles?

**Honest answer**: Not really. Local tools could live in a flat registry or a default "local" ensemble.

But since we need ensembles for MCP servers anyway, putting local tools in ensembles too provides:
- Consistent API (everything goes through ensembles)
- Logical grouping ("math-tools", "file-tools", "db-tools")
- Enable/disable groups
- Per-group configuration (timeouts, permissions, etc.)

**Cost**: Minimal - we already have ensemble infrastructure for MCP.

## Decision Matrix

| Criterion | Flat Registry | Ensembles |
|-----------|---------------|-----------|
| MCP server lifecycle | ❌ Awkward | ✅ Natural |
| MCP server config | ❌ Scattered | ✅ Localized |
| Name conflicts | ❌ Global namespace | ✅ Scoped |
| Multiple MCP servers | ❌ String matching | ✅ Clear separation |
| Local tools simplicity | ✅ Simple | ⚠️ Slight overhead |
| Consistent API | ❌ Two patterns | ✅ One pattern |
| Implementation complexity | ✅ Simpler | ⚠️ More structure |

## Recommendation

**Keep ensembles** for these reasons:

1. **MCP servers require them**: Lifecycle, configuration, and connection management need a container
2. **Name scoping**: Multiple MCP servers might have overlapping tool names
3. **Consistent architecture**: One pattern for MCP and local tools
4. **Proven in practice**: Two years of ai-experiments usage (even if reasons weren't clear at time)

The overhead for local tools is minimal since we need ensemble infrastructure for MCP anyway.

## Minimal Ensemble Design

If we want to keep ensembles simple:

```python
@dataclass
class Ensemble:
    """Container for related invokers with shared lifecycle."""

    name: str
    invokers: dict[str, Invoker]

    # Optional: for MCP servers
    config: dict[str, Any] = field(default_factory=dict)
    connection: Any | None = None

    async def connect(self) -> None:
        """Initialize ensemble (e.g., connect to MCP server)."""
        if self.connection:
            await self.connection.connect()

    async def disconnect(self) -> None:
        """Teardown ensemble (e.g., disconnect from MCP server)."""
        if self.connection:
            await self.connection.disconnect()

    def add_invoker(self, invoker: Invoker) -> None:
        """Register an invoker in this ensemble."""
        self.invokers[invoker.name] = invoker
```

**This is minimal but sufficient for MCP server management.**

## Conclusion

Ensembles aren't premature abstraction - they're the natural consequence of MCP server requirements. The user's observation that "MCP servers are effectively ensembles" is exactly right. We should embrace that rather than fighting it.
