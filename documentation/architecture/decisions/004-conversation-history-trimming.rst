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
004. Conversation History Trimming
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

In conversations with tool/function calling, tool results accumulate in the
conversation history. When the same tool is invoked multiple times with the same
or similar arguments (e.g., repeatedly editing the same file), older tool
results may become stale and redundant.

**Example scenario**: File editing workflow

.. code-block:: python

   # Message 5: Write file and return content
   Assistant: [calls write_file("foo.py", "def hello(): pass")]
   Result: "File written. Content:\n1: def hello(): pass"

   # ... conversation continues ...

   # Message 12: Write same file again
   Assistant: [calls write_file("foo.py", "def hello():\n    print('hi')")]
   Result: "File written. Content:\n1: def hello():\n2:     print('hi')"

The result at message 5 is now **stale** - it shows outdated file content. The
message 12 result supersedes it.

**Deduplicators** (from ai-experiments) identify which previous tool results can
be safely removed from conversation history to save tokens.

Decision Drivers
===============================================================================

* **Context window limits**: LLM providers have finite context windows
* **Token costs**: More tokens = higher API costs
* **Server-side prompt caching**: Anthropic/OpenAI cache repeated prefixes (~90%
  cheaper)
* **Cache busting**: Modifying conversation history invalidates prompt cache
* **MVP simplicity**: Start with simple implementation, optimize later
* **Unknown performance factors**: Impact of trimming vs caching unclear without
  profiling
* **Common conversation patterns**: Most conversations stay well under context
  limits

Decision
===============================================================================

**Skip deduplicators for MVP**. Rely on server-side prompt caching instead of
trimming conversation history.

**Rationale**:

1. **Server-side caching works**: Keeping conversation history stable allows
   provider caching (cache hits are ~90% cheaper)
2. **Start simple**: Implement and ship MVP faster without trimming complexity
3. **Monitor usage**: Measure if conversations approach context limits in
   practice
4. **Measure tradeoff**: Profile token costs vs cache-miss costs before
   optimizing
5. **Add when needed**: Implement trimming only if context window becomes
   actual bottleneck

**Future trigger conditions** for implementing deduplicators:

* Conversations routinely exceed 50-75% of context window
* Many file edit operations with large content returns
* Token costs from stale results exceed cache-miss costs from trimming
* Users report hitting context limits

Alternatives
===============================================================================

Alternative 1: Implement Deduplicators from Start
-------------------------------------------------------------------------------

Add deduplication logic to trim stale tool results from conversation history
before sending to LLM:

.. code-block:: python

   class Deduplicator(Protocol):
       def is_duplicate(
           self,
           invocable_name: str,
           arguments: dict[str, Any],
       ) -> bool:
           """Check if invocation supersedes previous result."""

**Example deduplicators from ai-experiments**:

* ``IoContentDeduplicator``: File operations (read, write)
* ``SurveyDirectoryDeduplicator``: Directory listings

**Pros:**

* **Token savings**: Remove redundant/stale results from history
* **Context efficiency**: More room for useful conversation
* **Semantic clarity**: LLM sees current state, not outdated info
* **Proactive optimization**: Ready when conversations grow long

**Cons:**

* **Cache busting**: Modifying conversation prefix invalidates server-side
  cache
* **Higher cost initially**: Re-process entire modified prefix at full price
* **Added complexity**: Need trimming logic and supersession rules
* **Unknown impact**: Token savings may not outweigh cache-miss costs
* **Premature optimization**: Most conversations may never hit context limits

**Cost comparison example**:

Without deduplicators (cache enabled):

* 10 file edits in conversation
* 10 × 100 tokens = 1000 tokens in history
* Prompt cache works → only pay full price once
* Subsequent turns: ~100 new tokens (cache hit on prefix)

With deduplicators (cache busted):

* Latest file edit only: 100 tokens in history (900 tokens saved)
* Cache busted on every trim → re-process conversation each time
* Each turn: ~1000+ tokens (full conversation re-processing)
* **Winner**: No deduplicators (until conversation approaches context limit)

Alternative 2: Configurable Trimming
-------------------------------------------------------------------------------

Implement deduplicators but make them optional/configurable:

.. code-block:: python

   config = {
       "enable_deduplication": False,  # Default off for MVP
       "deduplication_threshold": 0.75,  # Only trim when >75% of context used
   }

**Pros:**

* **Flexible**: Can enable when needed
* **Hedge both bets**: Support both caching and trimming strategies
* **User choice**: Power users can optimize for their use case

**Cons:**

* **Configuration complexity**: More knobs to understand and tune
* **Implementation cost**: Build feature that may never be used
* **Testing burden**: Must test both modes
* **Delayed decision**: Still don't know which strategy is actually better

Alternative 3: Do Nothing (No Trimming Ever)
-------------------------------------------------------------------------------

Never implement deduplicators, rely entirely on context window size and
caching.

**Pros:**

* **Simplest**: No trimming code at all
* **Cache-friendly**: Conversation history always stable

**Cons:**

* **No mitigation**: If conversations do hit limits, no recourse
* **Locks out optimization**: Can't improve if token costs become issue
* **Ignores real use case**: Long-running conversations with many tool calls
  will eventually need trimming

Consequences
===============================================================================

**Positive:**

* **Simpler MVP**: Faster implementation, fewer moving parts
* **Cache optimization**: Server-side caching works at full effectiveness
* **Deferred complexity**: Don't build feature until proven necessary
* **Data-driven decision**: Can profile actual usage patterns before optimizing
* **Lower initial costs**: Cache hits cheaper than re-processing trimmed
  conversations

**Negative:**

* **No token savings**: Stale results remain in conversation history
* **Context window risk**: Long conversations may eventually hit limits
* **Future refactoring**: May need to add trimming later if usage patterns
  demand it
* **Missed optimization**: Some conversations could benefit from trimming now

**Neutral:**

* **Design for future**: Structure tool results to support trimming later if
  needed (e.g., include supersession metadata)
* **Migration path exists**: Can add deduplicators in Phase 2 without breaking
  changes
* **Monitoring required**: Track conversation lengths and token costs in
  production

Implementation Notes
===============================================================================

For future implementation, design tool results to be trimmable:

.. code-block:: python

   @dataclass
   class ResultMessage:
       invocation_id: str
       content: Content
       timestamp: datetime

       # Future: Add supersession metadata
       supersedes: list[str] = field(default_factory=list)

If deduplicators are added later, follow ai-experiments patterns:

**IoContentDeduplicator** for file operations:

* Compares file locations between operations
* Newer write supersedes older write/read of same file
* Exception: partial updates only supersede if return content

**SurveyDirectoryDeduplicator** for directory listings:

* Same location + compatible filter sets
* More inclusive listing supersedes less inclusive

**Trigger metrics to watch**:

* Average conversation length (number of messages)
* Percentage of conversations exceeding 50% of context window
* Token costs for conversations with many tool calls
* Cache hit rates from provider APIs

References
===============================================================================

* Original analysis: ``.auxiliary/notes/deduplicator-analysis.md``
* ai-experiments deduplicators: https://github.com/emcd/ai-experiments (reference
  implementation)
* Key insight: Deduplicators trade token savings for cache efficiency
* Decision: Rely on caching for MVP, add trimming if profiling shows benefit
