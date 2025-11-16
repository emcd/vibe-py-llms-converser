# Content Storage Strategy Analysis

## Question: Should Textual Content Also Use the Content Hierarchy?

### Current Proposal (from architecture-initial.md)

**Textual content**: Stored inline in JSONL messages
**Non-textual content**: Stored in `content/{hash}/` hierarchy

```jsonl
{"role": "user", "content": [
  {"type": "text", "text": "What's in this image?"},
  {"type": "image", "content_id": "a1b2c3d4e5f6..."}
]}
```

### Alternative: All Content in Hierarchy

**All content types**: Stored in `content/{hash}/` hierarchy

```jsonl
{"role": "user", "content": [
  {"type": "text", "content_id": "f7e8d9c0b1a2..."},
  {"type": "image", "content_id": "a1b2c3d4e5f6..."}
]}
```

## Tradeoff Analysis

### Benefits of Storing Textual Content in Hierarchy

#### 1. **Sharing Large LLM Responses Across Forks**

When forking a conversation, large assistant responses can be shared:

```
# Original conversation
conv-001/messages.jsonl:
{"role": "assistant", "content": [{"type": "text", "content_id": "abc123..."}]}

# Forked conversation
conv-002/messages.jsonl:
{"role": "assistant", "content": [{"type": "text", "content_id": "abc123..."}]}

# Both reference same content
content/abc123.../data → "...10KB of text response..."
```

**Impact**: Significant space savings for conversations with long responses that are forked

**Example Scenario**:
- LLM generates 8KB analysis
- User forks conversation 5 times to explore different follow-ups
- **Inline storage**: 8KB × 6 = 48KB
- **Hash storage**: 8KB × 1 = 8KB (83% reduction)

#### 2. **Sharing System Prompts and Canned Prompts**

Reusable prompts can be referenced instead of duplicated:

```python
# System prompt used in multiple conversations
system_prompt_id = "prompt-def456..."

# Referenced in many conversations
conv-001: {"role": "supervisor", "content": [{"type": "text", "content_id": "prompt-def456..."}]}
conv-002: {"role": "supervisor", "content": [{"type": "text", "content_id": "prompt-def456..."}]}
conv-003: {"role": "supervisor", "content": [{"type": "text", "content_id": "prompt-def456..."}]}
```

**Impact**: Reduces duplication of common system prompts across conversations

#### 3. **Uniform Content Handling**

All content types handled identically:
- Same storage mechanism
- Same reference semantics
- Same deduplication strategy
- Simpler mental model

#### 4. **Deduplication of Identical Text**

User repeats same question across conversations:

```python
# Same user message in different conversations
question_id = hash("What is the capital of France?")

conv-001: {"role": "user", "content": [{"type": "text", "content_id": question_id}]}
conv-014: {"role": "user", "content": [{"type": "text", "content_id": question_id}]}
```

**Impact**: Minor space savings for repeated queries

### Costs of Storing Textual Content in Hierarchy

#### 1. **Increased I/O Operations**

**Inline storage**:
- Read one file: `messages.jsonl`
- Parse N JSON lines
- All text immediately available

**Hash storage**:
- Read `messages.jsonl` (get content IDs)
- Read M separate files: `content/{id}/data` for each unique text content
- Potential random access pattern (not sequential)

**Performance impact**:
- **Best case** (all content unique to conversation): M = N file reads (2× I/O)
- **Worst case** (small text chunks): M >> N file reads (many small I/Os)

**Mitigation**: Caching, bulk loading

#### 2. **Loading Latency**

From ai-experiments experience:
> "There are some noticeable pauses when loading conversations"

**Potential causes**:
1. **I/O overhead**: Opening many small files vs one larger file
2. **Event handler mutexes**: GUI synchronization (may be primary cause)
3. **Content directory traversal**: stat calls, directory operations
4. **Hash computation**: If done during load (shouldn't be)

**Question**: Which is the dominant factor?

#### 3. **Complexity in Message Rendering**

**Inline storage**:
```python
# Direct access
for message in messages:
    print(message["content"][0]["text"])
```

**Hash storage**:
```python
# Need to resolve references
for message in messages:
    content_id = message["content"][0]["content_id"]
    text = load_content(content_id)
    print(text)
```

**Impact**: More complex code, need content manager/cache

#### 4. **Small Text Overhead**

Short messages incur same overhead as large ones:

```
"ok" → content/{hash}/data (minimum 4KB filesystem block)
"Hello, how are you?" → content/{hash}/data (4KB block)
```

**Impact**: Filesystem overhead for many small messages

## Quantitative Analysis

### Scenario 1: Typical Conversation

- 20 messages (10 user, 10 assistant)
- Average user message: 100 bytes
- Average assistant message: 500 bytes
- No forks

**Inline storage**:
- Total size: ~6KB (compressed in one JSONL file)
- Load time: 1 file read

**Hash storage**:
- Total size: ~6KB + 20 × (metadata overhead)
- Load time: 21 file reads (1 JSONL + 20 content files)

**Winner**: **Inline storage** (no benefit from deduplication, higher I/O cost)

### Scenario 2: Conversation with Long Response, 5 Forks

- Original conversation: 10 messages, 1 long response (10KB)
- 5 forks, each adds 5 messages

**Inline storage**:
- Original: ~11KB
- 5 forks: 5 × 11KB = 55KB
- Total: 66KB

**Hash storage**:
- Original: ~1KB messages + 10KB shared content = 11KB
- 5 forks: 5 × 1KB = 5KB messages (share same content references)
- Total: 16KB + shared content (76% reduction)

**Winner**: **Hash storage** (significant space savings from sharing)

### Scenario 3: 100 Conversations with Common System Prompt

- System prompt: 2KB
- Each conversation: 10 messages

**Inline storage**:
- 100 × 2KB = 200KB for duplicated prompts
- Plus conversation messages

**Hash storage**:
- 1 × 2KB = 2KB for shared prompt
- Plus conversation messages (99% reduction on prompt)

**Winner**: **Hash storage** (deduplication benefit)

## Hybrid Approach: Size-Based Strategy

### Strategy: Hash Storage for Large Text, Inline for Small

```python
# Threshold: 1KB (configurable)
HASH_THRESHOLD = 1024

def store_text_content(text: str) -> dict:
    if len(text) < HASH_THRESHOLD:
        # Inline for small text
        return {"type": "text", "text": text}
    else:
        # Hash storage for large text
        content_id = hash_content(text)
        store_content(content_id, text)
        return {"type": "text", "content_id": content_id}
```

**Benefits**:
- Small messages (majority) stay inline → fast loading
- Large responses use hash storage → space savings on forks
- System prompts use hash storage → deduplication

**Tradeoffs**:
- More complex logic
- Hybrid mental model
- Need to handle both storage types

## Performance Considerations

### Caching Strategy

```python
class ContentManager:
    def __init__(self):
        self._cache: dict[str, str] = {}

    def load_content(self, content_id: str) -> str:
        if content_id in self._cache:
            return self._cache[content_id]

        content = read_file(f"content/{content_id}/data")
        self._cache[content_id] = content
        return content
```

**Impact**: Amortizes I/O cost for frequently referenced content

### Bulk Loading

```python
def load_conversation_with_content(conv_id: str) -> Conversation:
    # 1. Load message references
    messages = load_jsonl(f"conversations/{conv_id}/messages.jsonl")

    # 2. Collect all content IDs
    content_ids = collect_content_ids(messages)

    # 3. Bulk load all content (parallel I/O possible)
    content = bulk_load_content(content_ids)

    # 4. Assemble conversation
    return assemble_conversation(messages, content)
```

**Impact**: Can parallelize I/O, better filesystem caching

## Recommendation

### For MVP: **Inline Textual Content**

**Rationale**:
1. **Simplicity**: Straightforward implementation, easier to debug
2. **Performance**: Most conversations won't be forked, so no deduplication benefit
3. **Loading speed**: Single file read, no reference resolution
4. **Defer optimization**: Can migrate to hash storage later if needed

**When to migrate to hash storage**:
- Conversation forking becomes common use case
- Loading performance becomes issue (after profiling!)
- Storage space becomes concern

### For Post-MVP: **Hybrid Approach**

**Migration path**:
1. Implement hash storage for all content (including text)
2. Add size threshold configuration
3. Profile loading performance with real usage data
4. Adjust threshold or revert to inline if hash storage hurts performance

### Specific Recommendations

#### System Prompts: Always Hash Storage

```python
# System prompts are:
# - Reused across many conversations
# - Relatively large (hundreds of bytes to KBs)
# - Read-only, perfect for deduplication

system_prompt_id = hash_content(system_prompt)
```

**Rationale**: Clear win for deduplication

#### User/Assistant Messages: Decision Based on Testing

- **Start inline** (MVP)
- **Profile** ai-experiments loading performance to identify bottleneck
- **Migrate selectively** if space/forking becomes issue

## Open Questions

1. **What is the primary cause of loading pauses in ai-experiments?**
   - I/O (number of files)?
   - Event handler mutexes?
   - Other GUI overhead?

   **Recommendation**: Profile before optimizing

2. **How common is conversation forking in practice?**
   - If rare, no benefit from hash storage
   - If common, significant space savings

3. **What is the typical size distribution of messages?**
   - Mostly small → inline better
   - Mix of small and large → hybrid better
   - Mostly large → hash storage better

4. **Is content shared across conversations (not forks)?**
   - System prompts: yes
   - User queries: unlikely
   - Assistant responses: no (each is unique)

## Proposal for Architecture Document

### Updated Storage Architecture

**Phase 1 (MVP)**:
- **Textual content**: Inline in JSONL (except system prompts)
- **System prompts**: Hash storage (deduplication benefit)
- **Non-textual content**: Hash storage (already designed)

**Phase 2** (after profiling):
- **Evaluate** hash storage for all textual content
- **Implement** hybrid size-based strategy if beneficial
- **Profile** loading performance to identify optimizations

**Rationale**:
- Start simple, optimize when needed
- System prompts get deduplication benefit immediately
- User/assistant messages stay fast to load
- Clear migration path if hash storage proves beneficial

## Decision

**Your input needed**: Should we:

**Option A**: Inline text (MVP), migrate later if needed
- ✅ Simple
- ✅ Fast loading
- ❌ No deduplication benefit
- ❌ Larger forks

**Option B**: Hash storage for all content from day one
- ✅ Uniform model
- ✅ Deduplication ready
- ✅ Space efficient for forks
- ❌ More complex
- ❌ Potentially slower loading (needs testing)

**Option C**: Hybrid (hash for large text + system prompts, inline for small)
- ✅ Best of both
- ❌ Most complex
- ❌ Premature optimization?

**Recommendation**: **Option A** for MVP, measure before optimizing. If ai-experiments profiling shows I/O is not the bottleneck, no reason to add complexity.
