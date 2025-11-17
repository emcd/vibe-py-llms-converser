# Key Updates for Callbacks vs Events

## Event Naming: Message* not Conversation*

**Rationale**: LLM APIs prescribe message state, not conversation state. Events are about individual messages streaming, not conversation lifecycle.

### Corrected Event Names

```python
# Event hierarchy (base class with subclasses)
class MessageEvent(Protocol):
    """Base class for message-level events."""
    message_id: str
    timestamp: datetime

# Specific message events
@dataclass
class MessageStartedEvent(MessageEvent):
    """Message cell allocation begins (allocator callback)."""
    message_id: str
    timestamp: datetime

@dataclass
class MessageProgressEvent(MessageEvent):
    """Message content chunk received during streaming."""
    message_id: str
    timestamp: datetime
    chunk: str
    total_tokens: int | None = None

@dataclass
class MessageUpdatedEvent(MessageEvent):
    """Message content updated (updater callback)."""
    message_id: str
    timestamp: datetime
    content: str

@dataclass
class MessageCompletedEvent(MessageEvent):
    """Message fully received and finalized."""
    message_id: str
    timestamp: datetime
    final_content: str
    token_count: int

@dataclass
class MessageFailedEvent(MessageEvent):
    """Message generation failed."""
    message_id: str
    timestamp: datetime
    error: str
    error_type: str

@dataclass
class MessageEndedEvent(MessageEvent):
    """Message lifecycle ended, cleanup needed (deallocator callback)."""
    message_id: str
    timestamp: datetime
```

## Variation 2: Single Callback WITHOUT ConversationReactors Class

**User feedback**: "I am not sure why we need the ConversationReactors class to contain a single callback"

**Answer**: We don't! Just pass the callback function directly.

### Simplified Single Callback Design

```python
# No wrapper class needed - just a function signature
MessageEventHandler = Callable[[MessageEvent], None]

# Provider API
class Provider:
    def __init__(
        self,
        event_handler: MessageEventHandler,
    ):
        self.event_handler = event_handler

    def _emit_progress(self, event: MessageProgressEvent) -> None:
        # Directly invoke the handler
        self.event_handler(event)

# User implements dispatch function
def handle_message_events(event: MessageEvent) -> None:
    match event:
        case MessageProgressEvent(chunk=chunk):
            print(f"Progress: {chunk}")
        case MessageFailedEvent(error=error):
            print(f"Error: {error}")
        case MessageCompletedEvent(final_content=content):
            print(f"Done: {content}")
        case _:
            pass  # Ignore other events

# Usage - no wrapper class
provider = Provider(event_handler=handle_message_events)
```

**Benefits**:
- ✅ Simpler: No class wrapper needed
- ✅ Functional: Just a function, not an object
- ✅ Flexible: Easy to compose, wrap, or chain handlers
- ✅ Clear: One callback parameter, not nested in object

### With Helper for Multiple Handlers

If user wants to register multiple handlers for same events:

```python
def combine_handlers(*handlers: MessageEventHandler) -> MessageEventHandler:
    """Combine multiple event handlers into one."""
    def combined(event: MessageEvent) -> None:
        for handler in handlers:
            handler(event)
    return combined

# Usage
provider = Provider(
    event_handler=combine_handlers(
        log_events,
        update_ui,
        track_metrics,
    )
)
```

## Detailed Comparison: Add Single Callback Variant

### Updated Comparison Table

| Criterion | Multiple Typed Callbacks | Single Callback (Match/Case) | Event Bus |
|-----------|-------------------------|------------------------------|-----------|
| **Interface Simplicity** | ⭐⭐⭐ (6 callbacks) | ⭐⭐⭐⭐⭐ (1 function) | ⭐⭐⭐⭐ (subscription API) |
| **Type Safety** | ⭐⭐⭐⭐⭐ (each callback typed) | ⭐⭐⭐ (single Event parameter) | ⭐⭐⭐⭐ (typed subscribe) |
| **Selective Handling** | ⭐⭐⭐⭐⭐ (None for unused) | ⭐⭐⭐⭐ (case _ : pass) | ⭐⭐⭐⭐⭐ (subscribe what you want) |
| **Execution Flow Clarity** | ⭐⭐⭐⭐⭐ (direct calls) | ⭐⭐⭐⭐⭐ (direct calls) | ⭐⭐⭐ (via bus) |
| **Extensibility** | ⭐⭐⭐ (protocol changes) | ⭐⭐⭐⭐⭐ (new case branches) | ⭐⭐⭐⭐⭐ (new event types) |
| **Multiple Consumers** | ⭐⭐ (one per callback) | ⭐⭐⭐ (combine_handlers helper) | ⭐⭐⭐⭐⭐ (native support) |
| **Pattern Matching** | ⭐⭐ (not applicable) | ⭐⭐⭐⭐⭐ (native match/case) | ⭐⭐⭐ (in handlers) |
| **Boilerplate** | ⭐⭐ (must define all 6) | ⭐⭐⭐⭐⭐ (single function) | ⭐⭐⭐ (setup overhead) |
| **Debugging** | ⭐⭐⭐⭐⭐ (step into each) | ⭐⭐⭐⭐⭐ (step into function) | ⭐⭐⭐ (bus indirection) |

**Winner for MVP**: **Single Callback** - simpler interface, extensible, works well with pattern matching

### Revised Recommendation for MVP

**Use Single Callback with Pattern Matching** (Variation 2, simplified)

```python
# Provider signature
class Provider:
    def __init__(self, event_handler: Callable[[MessageEvent], None]):
        ...

# User implementation
def my_event_handler(event: MessageEvent) -> None:
    match event:
        case MessageStartedEvent():
            allocate_message_cell()
        case MessageProgressEvent(chunk=chunk):
            append_to_message(chunk)
        case MessageCompletedEvent():
            finalize_message()
        case MessageFailedEvent(error=error):
            show_error(error)
            rollback_changes()
        case _:
            pass
```

**Rationale**:
1. **Simpler**: One function parameter vs 6 callback fields
2. **Python 3.10+ pattern matching**: Clean, readable dispatch
3. **Extensible**: New event types = new case branches
4. **No overhead**: Direct function call, no wrapper class
5. **Forward compatible**: Can always add typed callbacks later if needed
