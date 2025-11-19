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
002. Content Storage Strategy
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

The system stores conversation messages in JSONL format (one message per line).
Messages contain multimodal content including text, images, and potentially
audio/video in the future. A key design question is whether textual content
should be stored inline in the JSONL file or in a separate hash-based content
directory like binary content.

**Storage approaches:**

**Inline storage**: Text stored directly in JSONL messages

.. code-block:: json

   {"role": "user", "content": [
     {"type": "text", "text": "What's in this image?"},
     {"type": "image", "content_id": "a1b2c3..."}
   ]}

**Hash storage**: All content (including text) stored by content hash

.. code-block:: json

   {"role": "user", "content": [
     {"type": "text", "content_id": "f7e8d9..."},
     {"type": "image", "content_id": "a1b2c3..."}
   ]}

Decision Drivers
===============================================================================

* **Loading performance**: Conversation loading speed affects UX
* **Storage efficiency**: Deduplication reduces disk usage for forked
  conversations
* **Code simplicity**: Uniform handling is easier to maintain
* **Common case optimization**: Most messages are short text
* **Fork scenario support**: Users may fork conversations with large responses
* **System prompt reuse**: Same prompts used across many conversations
* **Unknown performance factors**: ai-experiments has loading pauses but root
  cause unclear (I/O, mutexes, or other)

Decision
===============================================================================

Use a **hybrid storage strategy with size-based threshold**:

1. **Default**: Inline storage for textual content in most messages

   * Simple and fast loading
   * No reference resolution overhead
   * Ideal for typical short messages

2. **Size threshold**: Hash storage for large text (>= 1KB, configurable)

   * Large LLM responses benefit from deduplication
   * Efficient for conversation forking with long responses
   * Threshold can be tuned based on profiling

3. **System prompts**: Always use hash storage

   * Deduplication across conversations
   * Typically reused multiple times
   * Clear benefit from content addressing

4. **Binary content**: Always use hash storage (images, audio, video)

Alternatives
===============================================================================

Alternative 1: Inline Text Storage Only
-------------------------------------------------------------------------------

Store all textual content inline in JSONL, use hash storage only for binary
content.

**Pros:**

* Simplest implementation
* Fast loading (single file read)
* No reference resolution needed
* All message text immediately available

**Cons:**

* No deduplication of large LLM responses across forks
* System prompts duplicated across all conversations
* Larger storage footprint when conversations are forked
* No benefit from content addressing

**Example scenario**: User forks conversation 5 times after 8KB LLM response.
Inline storage = 8KB × 6 = 48KB. Hash storage = 8KB × 1 = 8KB (83% reduction).

Alternative 2: Hash Storage for All Content
-------------------------------------------------------------------------------

Store all content (text and binary) in hash-based content directory from the
start.

**Pros:**

* Uniform content model (all types handled identically)
* Maximum deduplication benefit
* Space efficient for all fork scenarios
* Clean conceptual model

**Cons:**

* Increased I/O operations (must read multiple files per conversation)
* More complex message rendering (need content manager/cache)
* Filesystem overhead for many small text messages
* Potentially slower loading (needs profiling to confirm)
* Unknown impact: ai-experiments has loading pauses but root cause unclear

**Performance concern**: Loading conversation requires reading ``messages.jsonl``
plus N separate content files. With prompt caching from providers, cache busting
from modified conversation history may cost more than token savings.

Alternative 3: Do Nothing (Text Inline, Defer Optimization)
-------------------------------------------------------------------------------

Start with inline text, migrate to hash storage later if needed.

**Pros:**

* Simplest for MVP
* Fast initial implementation
* Can profile in production before optimizing

**Cons:**

* Migration complexity if behavior changes later
* Early users may have large storage footprint
* Missed optimization opportunity for known use cases (system prompts)

Consequences
===============================================================================

**Positive:**

* **Optimizes common case**: Small messages (majority) stay inline for fast
  loading
* **Deduplication where beneficial**: Large responses and system prompts use
  hash storage
* **Flexible**: Size threshold can be tuned based on actual usage patterns
* **Fork-friendly**: Forked conversations share large LLM responses efficiently
* **System prompt efficiency**: Common prompts deduplicated across conversations
* **Performance hedged**: Unknown ai-experiments loading issue mitigated by
  keeping small content inline

**Negative:**

* **Increased complexity**: Need to handle both inline and hash-based text
  storage
* **Hybrid mental model**: Developers must understand when text is inline vs
  referenced
* **Threshold tuning**: May need to adjust size cutoff based on profiling data
* **Code branches**: Content loading logic has conditional paths

**Neutral:**

* **Migration path exists**: Can adjust threshold or move to pure hash storage
  if profiling shows benefit
* **Two representations**: Messages may have ``{"type": "text", "text": "..."}``
  or ``{"type": "text", "content_id": "..."}``

Implementation Notes
===============================================================================

Size threshold comparison should use UTF-8 byte length:

.. code-block:: python

   HASH_THRESHOLD_BYTES = 1024  # Configurable constant

   if is_system_prompt or len(text.encode('utf-8')) >= HASH_THRESHOLD_BYTES:
       # Use hash storage
       content_id = hash_content(text)
       return {"type": "text", "content_id": content_id}
   else:
       # Use inline storage
       return {"type": "text", "text": text}

Content loading must handle both representations:

.. code-block:: python

   def load_text_content(content_item: dict) -> str:
       if "text" in content_item:
           return content_item["text"]  # Inline
       elif "content_id" in content_item:
           return load_from_content_store(content_item["content_id"])  # Hash
       else:
           raise ValueError("Invalid content item")

Example message representations:

.. code-block:: json

   {
     "role": "user",
     "content": [
       {"type": "text", "text": "What is the capital of France?"}
     ]
   }

   {
     "role": "assistant",
     "content": [
       {"type": "text", "content_id": "a1b2c3d4e5f6..."}
     ]
   }

   {
     "role": "supervisor",
     "content": [
       {"type": "text", "content_id": "prompt-def456..."}
     ]
   }

   {
     "role": "user",
     "content": [
       {"type": "text", "text": "What's in this image?"},
       {"type": "image", "content_id": "789abc..."}
     ]
   }

Caching strategy for hash-based content can amortize I/O costs:

.. code-block:: python

   class ContentManager:
       def __init__(self):
           self._cache: dict[str, str] = {}

       def load_content(self, content_id: str) -> str:
           if content_id in self._cache:
               return self._cache[content_id]
           content = read_content_file(content_id)
           self._cache[content_id] = content
           return content

References
===============================================================================

* Original analysis: ``.auxiliary/notes/content-storage-analysis.md``
* Stakeholder decision: Hybrid approach with size cutoff provides "best of both
  worlds"
* ai-experiments loading performance: Root cause unknown, hedged by hybrid
  approach
