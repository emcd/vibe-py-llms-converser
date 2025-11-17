# Deduplicator Analysis

**Question**: Do we need deduplication of tool calls, or is this premature optimization?

## Honest Assessment

**TL;DR**: **Probably don't need it** for MVP. If we implement caching, make it explicit with TTL, not implicit deduplication.

## What ai-experiments Deduplicator Actually Is

From the actual code, the Deduplicator is a protocol:

```python
class Deduplicator(Protocol):
    invocable_name: str
    arguments: Mapping[str, Any]

    @classmethod
    def provide_invocable_names(cls) -> Collection[str]:
        """Which tool names this deduplicator handles"""
        ...

    def is_duplicate(
        self,
        invocable_name: str,
        arguments: Mapping[str, Any],
    ) -> bool:
        """Check if this invocation is a duplicate"""
        ...
```

**Key observations**:
1. **Protocol-based**: Multiple implementations possible
2. **Per-tool**: Each deduplicator handles specific tool names
3. **Name + arguments**: Deduplication based on exact match of both
4. **Boolean check**: Just says "duplicate or not", doesn't provide cached result

**Actual implementation not shown** - just the protocol. Can't determine if it was actually useful without seeing:
- Real implementations
- Usage patterns
- Whether it was actually enabled in practice

## What Deduplication Might Do (Hypothesized)

### Scenario 1: Exact Match Deduplication

```python
# LLM makes same call twice in one conversation
InvocationCanister(name="get_weather", arguments={"location": "SF"})
# ... later in same conversation ...
InvocationCanister(name="get_weather", arguments={"location": "SF"})

# Deduplicator: "This is a duplicate, return cached result"
```

**Problem**: Weather might have changed! Time-sensitive data goes stale.

### Scenario 2: Deduplication with Caching

```python
class Deduplicator:
    def __init__(self):
        self._cache: dict[tuple[str, str], tuple[Any, datetime]] = {}

    def get_cached_result(
        self,
        name: str,
        arguments: dict,
        ttl: timedelta,
    ) -> Any | None:
        key = (name, json.dumps(arguments, sort_keys=True))
        if key in self._cache:
            result, timestamp = self._cache[key]
            if datetime.now() - timestamp < ttl:
                return result  # Still fresh
        return None  # Cache miss or stale

    def cache_result(self, name: str, arguments: dict, result: Any) -> None:
        key = (name, json.dumps(arguments, sort_keys=True))
        self._cache[key] = (result, datetime.now())
```

**This is just caching with extra steps.**

### Scenario 3: Preventing Redundant Calls

```python
# LLM asks for same info in rapid succession
User: "What's the weather in SF?"
Assistant: [calls get_weather("SF")] -> "62°F, partly cloudy"
User: "And what about the temperature there?"
Assistant: [wants to call get_weather("SF") again]

# Deduplicator: "We just called this 10 seconds ago, use cached result"
```

**But**: LLMs with good context should see the previous result and not re-call the tool.

## When Would Deduplication Help?

### Legitimate Use Cases

1. **LLM hallucinating duplicate calls**:
   - LLM calls same tool twice in single turn
   - Actually happens with streaming - might generate partial tool call, backtrack, re-generate
   - **Better fix**: Proper streaming parsing to avoid this

2. **Expensive idempotent operations**:
   - Database schema queries (won't change mid-conversation)
   - File metadata (mostly static)
   - API calls with rate limits
   - **Better fix**: Explicit caching layer with TTL

3. **Result caching for forked conversations**:
   - Fork conversation at message 10
   - Both branches need same tool result from message 5
   - **Better fix**: Content-addressed storage (we already have this for messages)

### Problematic Cases

1. **Time-sensitive data**:
   - Weather, stock prices, system status
   - Results go stale quickly
   - Deduplication without TTL is wrong

2. **Non-deterministic operations**:
   - Random number generation
   - Current timestamp
   - Process IDs
   - Deduplication is semantically incorrect

3. **State-changing operations**:
   - Writing files
   - Database updates
   - API calls with side effects
   - Deduplication breaks idempotency assumptions

## Analysis: Is This Premature Optimization?

Let's think about actual LLM behavior:

### Modern LLMs (2024+) with Context

- **Claude Sonnet 4**: 200K context window, excellent at tracking conversation state
- **GPT-4**: Strong context retention
- **Gemini**: Large context windows

These models can SEE previous tool results in conversation history. They rarely make redundant calls unless:
1. They want updated information ("what's the weather NOW?")
2. Streaming parser issues (implementation bug, not feature need)
3. Model hallucination/confusion (rare with good prompting)

### What We Actually Need

Instead of implicit deduplication, we probably want:

1. **Explicit result caching** (if needed):
   ```python
   @cache_tool_result(ttl=timedelta(minutes=5))
   async def get_weather(location: str) -> dict:
       # Expensive API call
       ...
   ```

2. **Idempotency tokens** (for state-changing operations):
   ```python
   async def create_order(items: list, idempotency_key: str) -> dict:
       # Prevent duplicate order creation
       ...
   ```

3. **Content-addressed storage** (we already have):
   - Tool results stored by hash
   - Forked conversations share results
   - No deduplication logic needed

## Decision Matrix

| Criterion | Deduplicator | Explicit Caching |
|-----------|--------------|------------------|
| Handles time-sensitive data | ❌ Stale results | ✅ Configurable TTL |
| Handles non-deterministic ops | ❌ Breaks semantics | ✅ Can opt-out |
| Implementation complexity | ⚠️ Moderate | ✅ Simple |
| Debugging clarity | ❌ "Why didn't tool run?" | ✅ Clear cache hit/miss |
| Configuration flexibility | ❌ Global behavior | ✅ Per-tool policy |
| Developer understanding | ❌ Implicit magic | ✅ Explicit intent |

## Recommendation

**Do NOT include deduplicator in MVP** for these reasons:

1. **Modern LLMs don't need it**: Large context windows mean they track previous calls
2. **Time-sensitive data**: Most tool calls fetch current data (weather, time, status)
3. **Explicit is better**: If caching is needed, use explicit `@cache` decorator with TTL
4. **Content storage handles forking**: Hash-based content storage already provides result sharing
5. **YAGNI**: We might not actually need this - wait for real-world evidence

### If Deduplication Is Actually Needed Later

Implement as **explicit caching layer** outside core architecture:

```python
# Optional caching middleware
class CachedInvoker:
    """Wrapper that caches invoker results."""

    def __init__(
        self,
        invoker: Invoker,
        ttl: timedelta = timedelta(minutes=5),
    ):
        self.invoker = invoker
        self.ttl = ttl
        self._cache: dict[str, tuple[Any, datetime]] = {}

    async def __call__(
        self,
        context: Context,
        arguments: Arguments,
    ) -> Any:
        cache_key = json.dumps(arguments, sort_keys=True)

        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self.ttl:
                logger.debug(f"Cache hit for {self.invoker.name}: {cache_key}")
                return result

        # Cache miss - call real invoker
        result = await self.invoker(context, arguments)

        # Store in cache
        self._cache[cache_key] = (result, datetime.now())
        return result

# Opt-in per tool
weather_invoker = CachedInvoker(
    base_weather_invoker,
    ttl=timedelta(minutes=5),  # Weather changes slowly
)

time_invoker = base_time_invoker  # Don't cache - always want current time
```

**Benefits of this approach**:
- Explicit opt-in per tool
- Configurable TTL per tool
- Easy to debug (clear cache hit/miss logs)
- Can be added later without architecture changes

## Conclusion

Deduplicator is likely **premature optimization**. Without seeing ai-experiments usage patterns, and given modern LLM capabilities, I recommend:

1. **Skip deduplicator in MVP**
2. **Monitor for redundant calls** in production
3. **Add explicit caching** if specific tools show duplicate call patterns
4. **Use TTL-based caching**, not implicit deduplication

If the user has evidence from ai-experiments that deduplication provided significant benefit, I'd love to hear about specific use cases - but without that data, I'd vote to keep things simple.
