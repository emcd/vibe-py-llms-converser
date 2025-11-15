# Callbacks vs Event Bus Architecture Analysis

**Date**: 2025-11-15
**Purpose**: Evaluate architectural approaches for handling conversation lifecycle events

## Executive Summary

**Recommendation**: Start with an **enhanced callbacks architecture** that is designed for future event bus migration, with a clear migration path.

**Rationale**:
- Callbacks are proven in ai-experiments (2.5 years of production use)
- Simpler mental model and easier debugging for initial development
- Event bus adds complexity that isn't justified until we have multiple concurrent event consumers
- We can design callbacks to be event-bus-compatible from day one
- Migration path is straightforward when/if needs evolve

## Current Architecture: ConversationReactors (ai-experiments)

### Implementation Pattern

```python
class ConversationReactors:
    allocator: Callable      # Pre-conversation setup
    deallocator: Callable    # Post-conversation cleanup
    failure: Callable        # Error handling
    success: Callable        # Successful completion
    progress: Callable       # Streaming updates
    updater: Callable        # State changes
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
class ConversationProgressEvent:
    conversation_id: str
    timestamp: datetime
    chunk: str
    total_tokens: int | None = None

# Callbacks accept events
class ConversationReactors:
    on_start: Callable[[ConversationStartedEvent], None]
    on_progress: Callable[[ConversationProgressEvent], None]
    on_complete: Callable[[ConversationCompletedEvent], None]
    on_error: Callable[[ConversationFailedEvent], None]

# Implementation can dispatch to bus internally
class Conversation:
    def __init__(self, reactors: ConversationReactors):
        self.reactors = reactors
        # Optional: also maintain an event bus
        self.event_bus: EventBus | None = None

    def _emit_progress(self, event: ConversationProgressEvent) -> None:
        # Invoke callback
        self.reactors.on_progress(event)
        # Also publish to bus if configured
        if self.event_bus:
            self.event_bus.publish(event)
```

### Benefits

1. **Events as First-Class Objects**: Events are serializable, loggable, testable
2. **Clean Migration Path**: Can add event bus later without changing event definitions
3. **Callback Simplicity**: Still have direct invocation and clear error propagation
4. **Future Flexibility**: Events can be published to bus when multiple consumers needed
5. **MCP Compatibility**: Events can be serialized and sent to MCP servers

### Migration Strategy

**Phase 1 (MVP)**: Callbacks with event objects
```python
def handle_progress(event: ConversationProgressEvent) -> None:
    print(f"Received: {event.chunk}")

conversation = Conversation(ConversationReactors(
    on_progress=handle_progress,
    ...
))
```

**Phase 2 (Event Bus)**: Add optional bus without breaking existing code
```python
# Old code still works
conversation = Conversation(ConversationReactors(
    on_progress=handle_progress,
    ...
))

# New code can use bus
bus = EventBus()
bus.subscribe(ConversationProgressEvent, log_progress)
bus.subscribe(ConversationProgressEvent, update_ui)
conversation.event_bus = bus  # Opt-in to bus publishing
```

**Phase 3 (Full Event Bus)**: Deprecate callbacks in favor of bus
```python
bus = EventBus()
bus.subscribe(ConversationProgressEvent, handle_progress)
conversation = Conversation(event_bus=bus)  # No reactors needed
```

## Event Bus Implementation Options

If we decide to implement an event bus, here are the options:

### Option 1: Built-in Python (Simple)

```python
from collections import defaultdict
from typing import Callable, DefaultDict

class SimpleEventBus:
    def __init__(self):
        self._handlers: DefaultDict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
```

**Pros**: No dependencies, simple, fully typed
**Cons**: No async support, no priority/ordering, no filtering

### Option 2: PyPubSub

```python
from pypubsub import pub

# Subscribe
pub.subscribe(handler, 'conversation.progress')

# Publish
pub.sendMessage('conversation.progress', event=event_data)
```

**Pros**: Mature library, well-tested, topic-based routing
**Cons**: String-based topics (less type-safe), synchronous only

### Option 3: Asyncio Event System

```python
import asyncio

class AsyncEventBus:
    def __init__(self):
        self._handlers: DefaultDict[type, list[Callable]] = defaultdict(list)

    async def publish(self, event: object) -> None:
        tasks = []
        for handler in self._handlers[type(event)]:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(event))
            else:
                handler(event)  # Sync handlers run immediately
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
```

**Pros**: Native async support, no dependencies, typed
**Cons**: More complex, requires async/await discipline

### Option 4: Custom Type-Safe Event Bus

```python
from typing import Protocol, TypeVar, Generic

E = TypeVar('E', bound='Event', contravariant=True)

class EventHandler(Protocol, Generic[E]):
    def __call__(self, event: E) -> None: ...

class TypedEventBus:
    def subscribe[E](self, event_type: type[E], handler: EventHandler[E]) -> None: ...
    def publish[E](self, event: E) -> None: ...
```

**Pros**: Fully type-safe, custom to our needs, no surprises
**Cons**: Implementation effort, potential bugs

**Recommendation**: If we go with event bus, start with Option 1 (Simple) and enhance with async support when needed.

## Considerations for MCP Server Support

MCP (Model Context Protocol) servers introduce a distributed component where events may need to cross process boundaries.

### With Callbacks

```python
# MCP server needs to expose callbacks
class MCPConversationReactors:
    def on_progress(self, event: ConversationProgressEvent) -> None:
        # Serialize event and send over MCP transport
        mcp_client.notify('conversation.progress', event.to_dict())
```

**Challenges**:
- Callbacks are synchronous; MCP is async
- Need to marshal callback invocations to RPC calls
- Error handling becomes complex (RPC failures)

### With Event Bus

```python
# MCP server subscribes to events
bus.subscribe(ConversationProgressEvent, lambda e: mcp_client.notify('conversation.progress', e))

# Or, MCP server can be a bus subscriber
class MCPEventPublisher:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client

    async def publish_event(self, event: Event) -> None:
        await self.mcp_client.notify(event.type, event.to_dict())

bus.subscribe(ConversationProgressEvent, mcp_publisher.publish_event)
```

**Benefits**:
- Events decouple MCP from core conversation logic
- Multiple MCP servers can subscribe independently
- Failures in one MCP server don't affect others

**Verdict**: Event bus has significant advantages for MCP integration, but we can bridge callbacks to events for MCP servers during MVP.

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
2. Use ConversationReactors pattern accepting event objects
3. Keep direct callback invocation for simplicity
4. Design events to be serializable (for future MCP support)

**Example**:
```python
@dataclass
class ConversationProgressEvent:
    conversation_id: str
    timestamp: datetime
    chunk: str
    metadata: dict[str, Any]

class ConversationReactors:
    allocator: Callable[[ConversationStartedEvent], None]
    progress: Callable[[ConversationProgressEvent], None]
    success: Callable[[ConversationCompletedEvent], None]
    failure: Callable[[ConversationFailedEvent], Awaitable[None]]
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
        reactors: ConversationReactors,
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

## Open Questions

1. **Do we anticipate multiple concurrent consumers of conversation events in MVP?**
   - If yes: Event bus
   - If no: Callbacks

2. **How critical is MCP server support in Phase 1?**
   - Critical: Event bus (better integration model)
   - Can defer: Callbacks (bridge to MCP later)

3. **What is the expected plugin/extension model?**
   - Dynamic, runtime plugins: Event bus
   - Static, compile-time configuration: Callbacks

4. **Error handling philosophy: fail-fast or resilient?**
   - Fail-fast (errors should halt conversation): Callbacks
   - Resilient (some handlers can fail): Event bus

## Recommended Next Steps

1. **User Decision**: Based on answers to open questions above, choose:
   - **Hybrid** (recommended): Event-based callbacks with migration path
   - **Pure Callbacks**: Safest, proven approach
   - **Event Bus**: If multiple consumers are known requirement

2. **Prototype**: Build small proof-of-concept showing:
   - Event definitions
   - Callback/bus invocation
   - Error handling
   - MCP integration (mocked)

3. **Document Decision**: Create ADR-004 documenting the choice

4. **Implement**: Build MVP with chosen approach

## Conclusion

The **hybrid approach** (event-based callbacks with event bus migration path) offers the best balance:
- Maintains proven callback simplicity for MVP
- Designs events as first-class citizens from day one
- Provides clear migration path when needs evolve
- Supports MCP integration through event serialization
- Minimizes risk while preserving future flexibility

**Final Recommendation**: Start with event-based callbacks, design for event bus migration.
