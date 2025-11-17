# Deduplicator Analysis

**Question**: Do we need deduplication of tool calls, or is this premature optimization?

## Honest Assessment - UPDATED with Actual Usage

**TL;DR**: **Not needed for MVP**, but valuable to understand for future. Deduplicators are a **context management mechanism** for trimming stale tool results from conversation history.

## What ai-experiments Deduplicator Actually Does

**Reference**: https://raw.githubusercontent.com/emcd/ai-experiments/refs/heads/master/sources/aiwb/invocables/ensembles/io/deduplicators.py

### Protocol Definition

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

### Purpose: Context Management, Not Call Prevention

**Stakeholder clarification**:
> "They are a context management mechanism that I added near the beginning of this year. They allow us to trim stale function results from conversation history. For example, a newer read of a file with line numbers may replace a previous write with line numbers, which returned the updated content."

**Key insight**: Deduplicators don't prevent tool execution - they identify which **previous tool results** in conversation history can be safely removed to save tokens.

### Actual Implementations from ai-experiments

#### IoContentDeduplicator

Handles file operations: `read`, `write_file`, `write_pieces`

**Logic**:
- Compares file locations between current and previous operations
- If locations match, previous result can be trimmed from conversation history
- Exception: `write_pieces` only supersedes if `return-content` is true

**Example scenario**:
```python
# Message 5: Write file and return content
Assistant: [calls write_file("foo.py", "def hello(): pass")]
Result: "File written. Content:\n1: def hello(): pass"

# ... conversation continues ...

# Message 12: Write same file again
Assistant: [calls write_file("foo.py", "def hello():\n    print('hi')")]
Result: "File written. Content:\n1: def hello():\n2:     print('hi')"

# IoContentDeduplicator: Message 5's result is now STALE
# The newer write at message 12 supersedes it
# Can trim message 5's result from history → save ~50 tokens
```

**Trimming logic**: When preparing conversation for next API call, omit outdated results.

#### SurveyDirectoryDeduplicator

Handles `list_folder` directory operations

**Logic**:
- Checks if both operations target same location
- Verifies filter sets compatible (previous filters ⊆ current filters)
- Ensures recursion settings equivalent or new call more inclusive

**Example**:
```python
# Message 8: List directory
Assistant: [calls list_folder("src/", filters=["*.py"])]
Result: "src/main.py, src/utils.py"

# Message 15: List same directory with more inclusive filters
Assistant: [calls list_folder("src/", filters=["*.py", "*.md"])]
Result: "src/main.py, src/utils.py, src/README.md"

# SurveyDirectoryDeduplicator: Message 8's result is STALE
# Message 15 includes everything from message 8 plus more
# Can trim message 8's result from history
```

## Critical Tradeoff: Cache Busting vs Token Savings

**Stakeholder insight**:
> "Server-side caching with client keepalives can be cheaper as long as conversation is flowing up to some percentage of the context window size. Using deduplicators busts cache; it really only makes sense to use them when we want to bust cache because of conversation size."

### The Tradeoff

#### Without Deduplicators (Keep All Results)

**Pros**:
- ✅ **Server-side prompt caching works**: Anthropic/OpenAI cache repeated prefixes
- ✅ **Cheaper**: Cache hits are ~90% cheaper than re-processing
- ✅ **Faster**: Cached responses are quicker
- ✅ **Simpler**: No trimming logic needed

**Cons**:
- ❌ **Token bloat**: Old results accumulate in conversation
- ❌ **Context limits**: May hit window size with redundant data
- ❌ **Cost at scale**: Eventually pay for processing stale results

#### With Deduplicators (Trim Stale Results)

**Pros**:
- ✅ **Token savings**: Remove redundant/stale results from history
- ✅ **Context efficiency**: More room for useful conversation
- ✅ **Semantic clarity**: LLM sees current state, not outdated info

**Cons**:
- ❌ **Cache busting**: Modifying conversation prefix invalidates cache
- ❌ **Higher cost**: Re-process entire modified prefix
- ❌ **Complexity**: Need trimming logic and supersession rules

### When Each Approach Wins

**Keep all results (no deduplicators) when**:
- Conversation is short (< 50% of context window)
- Cache hit rate is high (conversation has stable prefix)
- Tool results are small (few tokens per result)
- Cost of cache miss > cost of extra tokens

**Trim with deduplicators when**:
- Conversation is long (approaching context window limit)
- Many superseded results (file edits, directory listings)
- Tool results are large (big file contents, long listings)
- Cost of extra tokens > cost of cache miss

### Practical Example

```python
# Scenario: Editing a file 10 times in conversation

# Without deduplicators:
# - 10 write results in history (10 × 100 tokens = 1000 tokens)
# - But: Prompt cache works! Only pay full price once
# - Subsequent turns: ~100 tokens (cache hit on stable prefix)

# With deduplicators:
# - Only latest write result in history (100 tokens)
# - But: Cache busted on every trim
# - Each turn: ~1000+ tokens (re-process modified prefix)

# Winner: No deduplicators (until context window becomes issue)
```

## Recommendation for vibe-py-llms-converser

**MVP**: **Skip deduplicators**

**Rationale**:
1. **Start simple**: Let server-side caching work
2. **Monitor usage**: See if conversations approach context limits
3. **Measure impact**: Track token costs with/without trimming
4. **Add when needed**: If context window becomes issue

**Future consideration**: Implement deduplicators when:
- Conversations routinely exceed 50-75% of context window
- Many file edit operations with large content returns
- Token costs exceed cache-miss costs
- Users report hitting context limits

**Design for future**: Structure tool results to be trimmable:
```python
@dataclass
class ResultCanister:
    invocation_id: str
    content: Content
    timestamp: datetime

    # Future: Add supersession metadata
    supersedes: list[str] = field(default_factory=list)  # IDs of results this replaces
```

## Implementation Notes (If Needed Later)

```python
class ConversationTrimmer:
    """Trim stale tool results from conversation history."""

    def __init__(self, deduplicators: dict[str, Deduplicator]):
        self.deduplicators = deduplicators

    def trim_conversation(
        self,
        canisters: list[Canister],
    ) -> list[Canister]:
        """Remove superseded tool results."""

        # Find all result canisters
        results = [(i, c) for i, c in enumerate(canisters)
                   if isinstance(c, ResultCanister)]

        # Track which results to keep
        keep = set(range(len(canisters)))

        # For each result, check if later results supersede it
        for i, result in results:
            for j, later_result in results:
                if j <= i:
                    continue  # Only check later results

                # Find deduplicator for this tool
                dedup = self.deduplicators.get(result.invocation.name)
                if not dedup:
                    continue

                # Check if later result supersedes this one
                if dedup.is_duplicate(
                    later_result.invocation.name,
                    later_result.invocation.arguments,
                ):
                    keep.remove(i)  # Trim this result
                    break

        # Return filtered conversation
        return [c for i, c in enumerate(canisters) if i in keep]
```

## Conclusion

Deduplicators are a **context management optimization**, not a call prevention mechanism. They trade off:
- **Token savings** (remove stale results)
- vs **Cache efficiency** (stable conversation prefix)

For MVP: **Skip deduplicators**, rely on server-side caching. Add later if conversations grow large and token costs exceed cache-miss costs.

**Key learnings**:
1. Deduplicators trim history, don't prevent execution
2. Cache busting is a real cost to consider
3. Makes sense when context window becomes constraining
4. Tool-specific supersession rules (file ops, directory listings)
