# Callbacks vs Event Bus Architecture Analysis

**Date**: 2025-11-15
**Purpose**: Evaluate architectural approaches for handling conversation lifecycle events

## Executive Summary

**Recommendation**: Use **single callback with pattern matching** for message events.

**Rationale**:
- Simplest interface: one function parameter vs multiple typed callbacks
- Python 3.10+ pattern matching provides clean event dispatch
- Extensible: new event types = new case branches, no interface changes
- Extension-friendly: unknown events naturally ignored in `case _` branch
- Proven callback pattern from ai-experiments, simplified
- No wrapper class overhead

## Current Architecture: MessageReactors (ai-experiments)

### Implementation Pattern

```python
class MessageReactors:
    allocator: Callable      # Message cell allocation (GUI allocates new message cell when response starts)
    deallocator: Callable    # Post-conversation cleanup
    failure: Callable        # Error handling
    success: Callable        # Successful completion
    progress: Callable       # Streaming updates (initial chunks)
    updater: Callable        # Message updates as content streams in
```

### Characteristics

**Strengths**:
- **Simple and Direct**: Clear, predictable execution flow
- **Debuggable**: Easy to trace execution with standard debuggers
- **Proven**: 2.5 years of production use in ai-experiments
- **Low Overhead**: No intermediary message routing
- **Type-Safe**: Protocols enforce callback signatures

**Weaknesses**:
- **Tight Coupling**: Callers must know about all callback points
- **Single Consumer**: Only one callback per event type
- **Limited Flexibility**: Adding new event types requires protocol changes
- **Testing Complexity**: Must mock entire reactor structure

## Alternative: Event Bus Architecture

### Conceptual Design

```python
class EventBus:
    def publish(self, event: Event) -> None: ...
    def subscribe(self, event_type: type[Event], handler: Callable) -> None: ...
    def unsubscribe(self, event_type: type[Event], handler: Callable) -> None: ...

# Event hierarchy
class Event(Protocol):
    timestamp: datetime
    conversation_id: str

class ConversationStarted(Event): ...
class MessageReceived(Event): ...
class StreamingChunk(Event): ...
class ToolInvocationRequested(Event): ...
class ToolResultReceived(Event): ...
class ConversationCompleted(Event): ...
class ConversationFailed(Event): ...
```

### Characteristics

**Strengths**:
- **Decoupled**: Publishers and subscribers don't know about each other
- **Multiple Consumers**: Many handlers can listen to same event
- **Extensible**: New event types don't break existing code
- **Flexible Routing**: Events can be filtered, transformed, logged
- **Testable**: Easy to spy on events without affecting production code

**Weaknesses**:
- **Complexity**: More moving parts, harder to trace execution flow
- **Debugging Difficulty**: Breakpoints in publishers don't show subscribers
- **Performance Overhead**: Message routing, type checking, subscription lookup
- **Error Handling**: Failed handlers can't easily signal errors to publishers
- **Temporal Coupling**: Handler registration order can matter

## Detailed Comparison

### 1. Execution Flow Clarity

**Callbacks**: ⭐⭐⭐⭐⭐
- Linear, synchronous execution (or clearly async)
- Stack traces show complete call chain
- Easy to reason about ordering

**Event Bus**: ⭐⭐⭐
- Non-linear execution flow
- Stack traces show only publisher → bus
- Handler execution order may be non-deterministic

**Winner**: Callbacks (especially important for early development)

### 2. Extensibility

**Callbacks**: ⭐⭐⭐
- Adding event types requires protocol changes
- All implementers must provide new callbacks
- Difficult to add optional callbacks

**Event Bus**: ⭐⭐⭐⭐⭐
- New event types are just new classes
- Subscribers opt-in to events they care about
- Easy to add middleware/interceptors

**Winner**: Event Bus

### 3. Testing

**Callbacks**: ⭐⭐⭐
- Must mock entire reactor structure
- Easy to verify callback was invoked
- Difficult to test callback behavior in isolation

**Event Bus**: ⭐⭐⭐⭐
- Can subscribe test handlers dynamically
- Easy to capture and inspect events
- Can test publishers and subscribers independently

**Winner**: Event Bus

### 4. Performance

**Callbacks**: ⭐⭐⭐⭐⭐
- Direct function calls
- No routing overhead
- Minimal memory footprint

**Event Bus**: ⭐⭐⭐⭐
- Hash table lookups for subscribers
- Event object creation/allocation
- Potential queue overhead if async

**Winner**: Callbacks (though difference is likely negligible)

### 5. Error Handling

**Callbacks**: ⭐⭐⭐⭐⭐
- Exceptions propagate naturally to caller
- Caller can catch and handle errors
- Clear ownership of error handling

**Event Bus**: ⭐⭐⭐
- Failed handler doesn't affect publisher
- Must decide: swallow errors or aggregate them?
- Error context may be lost

**Winner**: Callbacks

### 6. Debugging

**Callbacks**: ⭐⭐⭐⭐⭐
- Standard debugger works perfectly
- Can step from caller into callback
- Stack traces are complete

**Event Bus**: ⭐⭐⭐
- Requires logging or event inspection
- Can't easily step from publisher to subscriber
- May need specialized debugging tools

**Winner**: Callbacks

### 7. Multiple Consumers

**Callbacks**: ⭐⭐
- Only one callback per event type
- Workarounds (callback chains) are awkward
- Forces coordination between consumers

**Event Bus**: ⭐⭐⭐⭐⭐
- Natural support for multiple subscribers
- Subscribers are independent
- Easy to add/remove consumers dynamically

**Winner**: Event Bus

### 8. Use Case: MCP Server Integration

**Callbacks**: ⭐⭐⭐
- MCP servers would need to implement reactor protocol
- Callbacks would be marshaled to MCP requests
- Requires careful lifecycle management

**Event Bus**: ⭐⭐⭐⭐
- Events can be serialized and sent over MCP transport
- Multiple MCP servers can subscribe to same events
- Natural fit for distributed architecture

**Winner**: Event Bus

## Hybrid Approach: Event-Based Callbacks

### Design Concept

Define callbacks to receive event objects instead of arbitrary arguments:

```python
# Events as value objects (can be serialized)
@dataclass
class MessageProgressEvent:
    conversation_id: str
    timestamp: datetime
    chunk: str
    total_tokens: int | None = None

# Option 1: Multiple typed callbacks (ai-experiments pattern)
class MessageReactors:
    on_start: Callable[[MessageStartedEvent], None]
    on_progress: Callable[[MessageProgressEvent], None]
    on_complete: Callable[[MessageCompletedEvent], None]
    on_error: Callable[[MessageFailedEvent], None]

# Option 2: Single callback with event type dispatch
class MessageReactors:
    on_event: Callable[[Event], None]  # Single callback receives all events

# Implementation can dispatch to bus internally
class Conversation:
    def __init__(self, reactors: MessageReactors):
        self.reactors = reactors
        # Optional: also maintain an event bus
        self.event_bus: EventBus | None = None

    def _emit_progress(self, event: MessageProgressEvent) -> None:
        # Invoke callback
        self.reactors.on_progress(event)
        # Also publish to bus if configured
        if self.event_bus:
            self.event_bus.publish(event)
```

**Stakeholder clarification on hybrid approach** (from review):
> "Technically, callbacks can feed events to multiple consumers. I.e., we can have a message bus on the side of the initial caller with the provider implementation being completely unaware of it."

**Key insight**: The message bus can be on the **caller side**, not the provider side:

```python
# Provider remains unaware of event bus - just invokes callbacks
class Provider:
    def __init__(self, reactors: MessageReactors):
        self.reactors = reactors

    def _emit_progress(self, event: MessageProgressEvent) -> None:
        # Simple callback invocation
        self.reactors.on_progress(event)

# Caller bridges callbacks to event bus
class EventBridgeReactors:
    """Bridge callbacks to event bus on caller side."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def on_progress(self, event: MessageProgressEvent) -> None:
        # Callback publishes to bus
        self.event_bus.publish(event)

    def on_error(self, event: MessageFailedEvent) -> None:
        self.event_bus.publish(event)

# Usage: Provider is unaware of bus, caller manages event distribution
bus = EventBus()
bus.subscribe(MessageProgressEvent, log_handler)
bus.subscribe(MessageProgressEvent, ui_handler)
bus.subscribe(MessageProgressEvent, metrics_handler)

provider = Provider(EventBridgeReactors(bus))  # Bridge callbacks to bus
```

**Benefits**:
- Provider implementation stays simple (direct callbacks)
- Caller has full control over event distribution
- No provider changes needed to support multiple consumers
- Bus complexity isolated to caller side

### Callback Design Variations

#### Variation 1: Multiple Typed Callbacks (ai-experiments pattern)

**Structure**:
```python
class MessageReactors:
    allocator: Callable[[MessageStartedEvent], None]
    progress: Callable[[MessageProgressEvent], None]
    success: Callable[[MessageCompletedEvent], None]
    failure: Callable[[MessageFailedEvent], None]
    updater: Callable[[MessageUpdatedEvent], None]
    deallocator: Callable[[MessageEndedEvent], None]
```

**Callback Purposes** (from ai-experiments):

- **allocator**: Message allocator, not pre-conversation setup
  - Provider calls back to GUI to allocate new message cell when response starts
  - Example: GUI creates new message widget in the conversation view
- **updater**: Message content updates during streaming
  - Provider calls back to update message cell as more content streams in
  - Example: GUI appends streaming chunks to message widget
- **progress**: Initial streaming updates (first chunks)
- **success/failure**: Final conversation state
- **deallocator**: Cleanup after conversation completes

**Stakeholder clarification** (from review):
> "allocator is actually a message allocator and not pre-conversation setup. In ai-experiments, this is used by the provider to callback to the GUI to allocate a new message cell when a response starts to come back. Then the updater callback is used to update the message as more content is streamed in."

**Pros**:
- ✅ Type-safe: Each callback has specific event type signature
- ✅ Optional callbacks: Can provide None for unneeded callbacks
- ✅ Clear intent: Callback name indicates when it's invoked
- ✅ Familiar: Matches ai-experiments proven pattern

**Cons**:
- ❌ Verbose: Must define/pass 6 separate callbacks
- ❌ Boilerplate: Often want same handler for multiple events
- ❌ Harder to add events: New event types require protocol changes

**Usage**:
```python
def on_progress(event: MessageProgressEvent) -> None:
    print(f"Progress: {event.chunk}")

def on_error(event: MessageFailedEvent) -> None:
    print(f"Error: {event.error}")

reactors = MessageReactors(
    allocator=None,  # Don't care about start
    progress=on_progress,
    success=None,
    failure=on_error,
    updater=None,
    deallocator=None,
)
```

#### Variation 2: Single Callback with Event Type Dispatch

**Stakeholder proposal** (from review):
> "A variation on the hybrid approach where we would have a single callback which would dispatch based on the event types that it received."

**CRITICAL CLARIFICATION** (from review):
> "Also *to be clear*, my proposal did not mean to use a single event type. I meant a single event base class. We would still pass instances of its subclasses and dispatch on those types."

**Key insight**: Single callback takes **Event base class** parameter, receives **subclass instances**, dispatches on concrete types:

```python
# Event hierarchy (base class with subclasses)
class Event(Protocol):
    conversation_id: str
    timestamp: datetime

class MessageProgressEvent(Event): ...  # Subclass
class MessageFailedEvent(Event): ...    # Subclass
class MessageCompletedEvent(Event): ... # Subclass
```

**Structure**:
```python
class MessageReactors:
    on_event: Callable[[Event], None]  # Single callback, Event BASE CLASS parameter

# Provider passes subclass instances
def _emit_progress(event: MessageProgressEvent) -> None:
    self.reactors.on_event(event)  # Pass subclass instance

# User implements dispatch on subclass types
def event_handler(event: Event) -> None:  # Receives base class, dispatches on subclass
    match event:
        case MessageProgressEvent():  # Pattern matches subclass
            print(f"Progress: {event.chunk}")
        case MessageFailedEvent():    # Pattern matches subclass
            print(f"Error: {event.error}")
        case MessageCompletedEvent(): # Pattern matches subclass
            print("Done!")
        case _:
            pass  # Ignore other event subclasses
```

**Benefits of this approach**:
- ✅ Single callback interface (simple)
- ✅ Multiple event types via inheritance (extensible)
- ✅ Type dispatch on concrete subclasses (flexible)
- ✅ New event subclasses don't break interface (forward compatible)

**Pros**:
- ✅ Simple interface: Only one callback to provide
- ✅ Flexible dispatch: User controls which events to handle
- ✅ Easy to extend: New event types don't change interface
- ✅ Natural event bus bridge: Already dispatching on type
- ✅ Pattern matching: Clean with Python 3.10+ match/case

**Cons**:
- ❌ Less type-safe: Single Event parameter loses specific typing
- ❌ Manual dispatch: User must implement switching logic
- ❌ All or nothing: Can't easily skip callback if not interested

**Usage with match/case**:
```python
def handle_conversation_events(event: Event) -> None:
    match event:
        case MessageProgressEvent(chunk=chunk):
            update_ui_progress(chunk)
        case MessageFailedEvent(error=error):
            show_error_dialog(error)
            rollback_state()
        case MessageCompletedEvent():
            finalize_conversation()
        case _:
            pass  # Ignore events we don't care about

conversation = Conversation(MessageReactors(
    on_event=handle_conversation_events
))
```

**Usage with isinstance**:
```python
def handle_conversation_events(event: Event) -> None:
    if isinstance(event, MessageProgressEvent):
        update_ui_progress(event.chunk)
    elif isinstance(event, MessageFailedEvent):
        show_error_dialog(event.error)
        rollback_state()
    elif isinstance(event, MessageCompletedEvent):
        finalize_conversation()
    # Implicitly ignore other events
```

**Helper for selective handling**:
```python
class EventDispatcher:
    """Helper to register handlers for specific event types."""

    def __init__(self):
        self._handlers: dict[type, list[Callable]] = {}

    def register(self, event_type: type, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def dispatch(self, event: Event) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)

# Usage
dispatcher = EventDispatcher()
dispatcher.register(MessageProgressEvent, lambda e: print(e.chunk))
dispatcher.register(MessageFailedEvent, lambda e: rollback(e.error))

conversation = Conversation(MessageReactors(
    on_event=dispatcher.dispatch
))
```

#### Variation 3: Hybrid of Both

Provide both interfaces for flexibility:

```python
class MessageReactors:
    # Option 1: Typed callbacks (backwards compatible)
    allocator: Callable[[MessageStartedEvent], None] | None = None
    progress: Callable[[MessageProgressEvent], None] | None = None
    success: Callable[[MessageCompletedEvent], None] | None = None
    failure: Callable[[MessageFailedEvent], None] | None = None

    # Option 2: Single dispatcher (new style)
    on_event: Callable[[Event], None] | None = None

# Implementation invokes both
def _emit(self, event: Event) -> None:
    # Invoke specific callback if provided
    if isinstance(event, MessageProgressEvent) and self.reactors.progress:
        self.reactors.progress(event)
    # ... handle other event types

    # Also invoke generic dispatcher if provided
    if self.reactors.on_event:
        self.reactors.on_event(event)
```

**Pros**:
- ✅ Maximum flexibility: Users choose their preferred style
- ✅ Backwards compatible: Existing code using typed callbacks still works
- ✅ Progressive enhancement: Can use both simultaneously

**Cons**:
- ❌ More complex implementation
- ❌ Two ways to do the same thing (violates "one obvious way")

### Recommendation

**For MVP**: **Variation 1** (Multiple Typed Callbacks)

**Rationale**:
1. **Proven**: Matches ai-experiments pattern (2.5 years production)
2. **Type-safe**: Compiler catches callback signature errors
3. **Familiar**: Team knows this pattern already
4. **Simple migration**: Can add Variation 2 later without breaking existing code

**Post-MVP**: Consider adding **Variation 2** (Single Callback Dispatch)

**When to add**:
- User feedback indicates desire for simpler callback interface
- Pattern matching (Python 3.10+) becomes baseline
- Event bus migration is imminent (single callback is closer to bus model)
## Considerations for MCP Server Support

MCP (Model Context Protocol) servers introduce a distributed component where events may need to cross process boundaries.

**Stakeholder clarification on MCP architecture** (from review):
> "I suspect that each MCP server will be a separate process with a separate provider that it is using. So, I am not sure that an event bus bus that is shared across processes is necessary."

**Key insight**: MCP servers are likely **separate processes**, each with their own provider instance:

```
Process 1: Main application
├── Provider A (for Conversation 1)
└── Provider B (for Conversation 2)

Process 2: MCP Server 1
└── Provider C (serving MCP requests)

Process 3: MCP Server 2
└── Provider D (serving MCP requests)
```

**Implication**: Shared in-process event bus may not be useful for MCP integration, since:
- Each process has independent memory space
- Event bus would need IPC (inter-process communication) to share events
- Complexity of distributed event bus may outweigh benefits

**Alternative**: Each provider uses callbacks independently, MCP transport handles cross-process communication

### With Callbacks

```python
# MCP server needs to expose callbacks
class MCPMessageReactors:
    def on_progress(self, event: MessageProgressEvent) -> None:
        # Serialize event and send over MCP transport
        mcp_client.notify('conversation.progress', event.to_dict())
```

**Challenges**:
- Callbacks are synchronous; MCP is async
- Need to marshal callback invocations to RPC calls
- Error handling becomes complex (RPC failures)

**Benefits** (in separate-process MCP context):
- Each process is independent with simple callbacks
- No need for distributed event bus infrastructure
- MCP protocol handles cross-process communication

### With Event Bus

```python
# MCP server subscribes to events
bus.subscribe(MessageProgressEvent, lambda e: mcp_client.notify('conversation.progress', e))

# Or, MCP server can be a bus subscriber
class MCPEventPublisher:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client

    async def publish_event(self, event: Event) -> None:
        await self.mcp_client.notify(event.type, event.to_dict())

bus.subscribe(MessageProgressEvent, mcp_publisher.publish_event)
```

**Benefits** (if MCP servers were in-process):
- Events decouple MCP from core conversation logic
- Multiple MCP servers can subscribe independently
- Failures in one MCP server don't affect others

**Challenges** (with separate-process MCP):
- Would require distributed event bus (complex)
- Or each process has its own bus (no sharing benefit)

**Verdict**: For separate-process MCP servers, callbacks work well within each process. MCP protocol handles cross-process communication. Shared event bus adds complexity without clear benefit in this architecture.

## Decision Matrix

| Criterion | Weight | Callbacks | Event Bus | Hybrid |
|-----------|--------|-----------|-----------|--------|
| **Early Development Velocity** | 5 | 5 | 3 | 4 |
| **Debugging/Traceability** | 5 | 5 | 3 | 4 |
| **Proven in Production** | 4 | 5 | 3 | 3 |
| **Extensibility** | 4 | 3 | 5 | 5 |
| **MCP Integration** | 4 | 3 | 5 | 5 |
| **Testing** | 3 | 3 | 4 | 4 |
| **Multiple Consumers** | 3 | 2 | 5 | 5 |
| **Performance** | 2 | 5 | 4 | 4 |
| **Error Handling** | 3 | 5 | 3 | 4 |
| **Total (weighted)** | — | **140** | **134** | **145** |

## Recommendation: Hybrid Approach

### Phase 1: Event-Based Callbacks (MVP)

**Implementation**:
1. Define all events as dataclasses with clear schemas
2. Use MessageReactors pattern accepting event objects
3. Keep direct callback invocation for simplicity
4. Design events to be serializable (for future MCP support)

**Example**:
```python
@dataclass
class MessageProgressEvent:
    conversation_id: str
    timestamp: datetime
    chunk: str
    metadata: dict[str, Any]

class MessageReactors:
    allocator: Callable[[MessageStartedEvent], None]
    progress: Callable[[MessageProgressEvent], None]
    success: Callable[[MessageCompletedEvent], None]
    failure: Callable[[MessageFailedEvent], Awaitable[None]]
```

### Phase 2: Optional Event Bus

**Trigger**: When we need one of:
- Multiple concurrent event consumers (e.g., logging + UI + MCP server)
- Dynamic subscription/unsubscription
- Complex event routing or filtering

**Implementation**:
```python
class Conversation:
    def __init__(
        self,
        reactors: MessageReactors,
        event_bus: EventBus | None = None,
    ):
        self.reactors = reactors
        self.event_bus = event_bus

    def _emit(self, event: Event, callback: Callable) -> None:
        # Invoke callback (existing behavior)
        callback(event)
        # Also publish to bus if configured (new behavior)
        if self.event_bus:
            self.event_bus.publish(event)
```

### Phase 3: Bus-First Architecture

**Trigger**: When callbacks become limiting (unlikely in MVP timeframe)

**Implementation**:
- Make event_bus required, reactors optional
- Deprecate direct callback invocation
- Full pub/sub architecture

## Alternative Recommendation: Pure Callbacks (Conservative)

If we want to minimize risk and maximize short-term velocity:

**Keep callbacks exactly as they are in ai-experiments with two improvements**:

1. **Event Objects**: Pass structured event objects instead of loose arguments
2. **Protocol Typing**: Ensure full type coverage with Protocols

**Defer event bus decision** until we have concrete evidence that callbacks are insufficient.

**When would we need event bus?**
- Supporting 3+ concurrent event consumers
- Dynamic plugin architecture requiring runtime subscription
- Distributed architecture with multiple MCP servers

## Open Questions (ANSWERED)

### Question 1: Multiple Concurrent Consumers in MVP?

**Answer**: **No** concurrent event consumers in MVP

**Rationale** (from stakeholder review):
> "No multiple concurrent consumers of conversation events in MVP"

However, potential future needs if wrapping with TUI/GUI interfaces.

**Decision Impact**: Supports callbacks approach for MVP

### Question 2: MCP Server Support Criticality

**Answer**: **Distinction required** - two separate concerns:

1. **Calling tools on MCP servers**: **NOT deferred**, required for MVP
   - This is about invoking tools that live on MCP servers
   - Part of invocables architecture
   - Critical functionality

2. **Wrapping converser as MCP server**: **Can be deferred**
   - This is about exposing the converser itself as an MCP server
   - Integration with Claude Code desired but not Phase 1 critical
   - Can be added later

**Rationale** (from stakeholder review):
> "MCP server support is not immediately critical" for the library itself, though integration with Claude Code was desired. Stressed that calling tools on MCP servers was *not* deferred, only wrapping the converser as an MCP server itself.

**Decision Impact**: Callbacks work well for tool invocation; event bus not required for MCP tool calling

### Question 3: Plugin/Extension Model

**Answer**: **Extensions can define new event types, but consumers ignore until support added**

**Stakeholder clarification**:
> "Extensions could define new event types but I would expect them to be ignored by consumers until support is implemented in the consumers."

**Implications**:
- Extensions CAN add new event types
- Existing consumers won't break (they ignore unknown events)
- Consumers opt-in to new events when ready
- Forward-compatible design needed

**Decision Impact**: This actually supports **single callback with pattern matching**:
```python
def handle_events(event: MessageEvent) -> None:
    match event:
        case MessageProgressEvent():
            # Handle known event
            ...
        case SomePluginEvent():  # New event from extension
            # Consumer can choose to handle or ignore
            ...
        case _:
            # Unknown events silently ignored
            pass
```

With single callback, consumers naturally ignore events they don't recognize.

### Question 4: Error Handling Philosophy

**Answer**: **Fail-fast**

**Rationale** (from stakeholder review):
> "If a chat completion fails, we need to alert the user and roll back any GUI/TUI changes."

**Decision Impact**:
- Errors should halt conversation
- User alerts required
- GUI/TUI rollback needed
- Strongly supports callbacks (exceptions propagate naturally)

## Decision Summary (Based on Answered Questions)

### Factors Favoring Callbacks for MVP

1. ✅ **No concurrent consumers** in MVP phase
2. ✅ **Fail-fast error handling** required (natural exception propagation)
3. ✅ **MCP tool calling** doesn't require event bus architecture
4. ✅ **Proven approach** from ai-experiments (2.5 years production)

### Factors Neutral/Future

1. ⏸️ **Plugin/extension model** - awaiting clarification
2. ⏸️ **Wrapping as MCP server** - deferred, not MVP requirement
3. ⏸️ **TUI/GUI integration** - potential future need for multiple consumers

### Recommended Approach - UPDATED

**Single Callback with Pattern Matching** (Variation 2, simplified)

**Implementation**:
```python
# Provider signature - just takes a function
class Provider:
    def __init__(self, event_handler: Callable[[MessageEvent], None]):
        self.event_handler = event_handler

    def _emit(self, event: MessageEvent) -> None:
        self.event_handler(event)

# User implements handler with pattern matching
def handle_message_events(event: MessageEvent) -> None:
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
            pass  # Ignore unknown events (e.g., from extensions)

# Usage - no wrapper class needed
provider = Provider(event_handler=handle_message_events)
```

**Rationale**:
1. **Simpler interface**: One function parameter vs MessageReactors with 6 fields
2. **Python 3.10+ pattern matching**: Clean, readable event dispatch
3. **Extensible**: New event types = new case branches, no protocol changes
4. **Extension-friendly**: Unknown events fall through to `case _: pass`
5. **No wrapper overhead**: Direct function call, no MessageReactors object
6. **Forward compatible**: Can add typed callbacks later if multiple consumers needed

**Event hierarchy** (Message-centric naming):
```python
@dataclass
class MessageEvent(Protocol):
    """Base class for all message events."""
    message_id: str
    timestamp: datetime

@dataclass
class MessageStartedEvent(MessageEvent):
    """Message cell allocation begins."""

@dataclass
class MessageProgressEvent(MessageEvent):
    """Message content chunk received during streaming."""
    chunk: str

@dataclass
class MessageUpdatedEvent(MessageEvent):
    """Message content updated."""
    content: str

@dataclass
class MessageCompletedEvent(MessageEvent):
    """Message fully received and finalized."""
    final_content: str

@dataclass
class MessageFailedEvent(MessageEvent):
    """Message generation failed."""
    error: str
```

## Recommended Next Steps

1. ✅ **Decision Made**: Single callback with pattern matching
   - To be documented in ADR-003 (see architecture-initial.md)

2. **Implement**: Build MVP with single event handler
   - Define MessageEvent hierarchy with message-centric naming
   - Provider accepts single `Callable[[MessageEvent], None]`
   - Design events for serialization (MCP compatibility)
   - Fail-fast error handling via exceptions

3. **Future Enhancement**: Add typed callbacks if needed
   - If multiple consumers become common
   - If explicit callback names improve clarity
   - Can coexist with single callback approach

## Conclusion

The **answers to open questions support single callback** for MVP:

| Question | Answer | Implication |
|----------|--------|-------------|
| Multiple consumers? | No (MVP) | Single callback ✓ |
| MCP critical? | Tool calling yes; wrapping no | Simple callbacks ✓ |
| Error handling? | Fail-fast | Exceptions propagate naturally ✓ |
| Extensions? | New events ignored until supported | Pattern matching `case _` ✓ |

**Final Recommendation**: Implement single callback with pattern matching as specified in ADR-003.

**Status**: ✅ Decision made, to be documented in architecture-initial.md (ADR-003)
