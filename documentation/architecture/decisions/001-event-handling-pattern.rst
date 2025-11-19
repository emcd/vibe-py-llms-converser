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
001. Event Handling Pattern for Conversation Lifecycle
*******************************************************************************

Status
===============================================================================

Accepted

Context
===============================================================================

The system needs to handle conversation lifecycle events to enable extensibility
and integration with different user interfaces (CLI, GUI, TUI). During
conversation flow, multiple events occur:

* Message allocation (preparing UI for new message)
* Streaming progress (incremental content updates)
* Message updates (content modifications)
* Completion (conversation finished successfully)
* Failure (errors during conversation)

The ai-experiments project used a ``MessageReactors`` class with multiple typed
callbacks (allocator, deallocator, failure, success, progress, updater). While
proven over 2.5 years of production use, this approach has limitations:

* **Tight coupling**: Callers must know about all callback points
* **Single consumer**: Only one callback per event type
* **Limited flexibility**: Adding new event types requires protocol changes
* **Testing complexity**: Must mock entire reactor structure

Decision Drivers
===============================================================================

* **Simplicity**: Minimize interface complexity for common use cases
* **Extensibility**: New event types should not break existing code
* **Type safety**: Leverage Python's type system for correctness
* **Debugging**: Execution flow should be easy to trace
* **Python 3.10+ features**: Take advantage of structural pattern matching
* **Proven patterns**: Build on ai-experiments learnings

Decision
===============================================================================

Use a **single callback with pattern matching** for conversation lifecycle
events.

The callback receives event objects and uses Python 3.10+ pattern matching to
dispatch to appropriate handlers:

.. code-block:: python

   def handle_conversation_events(event: ConversationEvent) -> None:
       match event:
           case MessageStartedEvent():
               # Allocate UI cell for new message
               allocate_message_cell()

           case MessageProgressEvent(chunk=chunk):
               # Append streaming content
               append_to_message(chunk)

           case MessageCompletedEvent():
               # Finalize message display
               finalize_message()

           case MessageFailedEvent(error=error):
               # Show error and rollback
               show_error(error)
               rollback_changes()

           case _:
               # Ignore unknown events (forward compatibility)
               pass

Event hierarchy includes:

* ``MessageStartedEvent``: Message allocation begins
* ``MessageProgressEvent``: Streaming chunk received
* ``MessageUpdatedEvent``: Message content updated
* ``MessageCompletedEvent``: Message finalized
* ``MessageFailedEvent``: Generation failed

Alternatives
===============================================================================

Alternative 1: MessageReactors with Multiple Typed Callbacks
-------------------------------------------------------------------------------

Continue the ai-experiments pattern with separate callback fields:

.. code-block:: python

   class MessageReactors:
       allocator: Callable
       deallocator: Callable
       failure: Callable
       success: Callable
       progress: Callable
       updater: Callable

**Pros:**

* Proven pattern with 2.5 years of production use
* Type-safe callback signatures via protocols
* Clear, direct execution flow
* Simple to debug (linear call chains)

**Cons:**

* Tight coupling: callers must provide all callbacks
* No support for multiple consumers of same event
* Adding new event types requires protocol changes
* Testing requires mocking entire reactor structure
* Verbose interface with many parameters

Alternative 2: Event Bus Architecture
-------------------------------------------------------------------------------

Implement a publish-subscribe event bus:

.. code-block:: python

   class EventBus:
       def publish(self, event: Event) -> None: ...
       def subscribe(self, event_type: type[Event], handler: Callable) -> None: ...

**Pros:**

* Decoupled publishers and subscribers
* Multiple consumers can listen to same event
* Flexible routing (filtering, transformation, logging)
* Easy to add observers for testing

**Cons:**

* Increased complexity with message routing
* Harder to trace execution flow in debugger
* Performance overhead from subscription lookup
* Error handling complexity (failed handlers can't signal publishers easily)
* Temporal coupling (handler registration order may matter)
* Overkill for the single-consumer use case (one UI per conversation)

Alternative 3: Do Nothing (No Events)
-------------------------------------------------------------------------------

Handle all conversation flow synchronously without extensibility points.

**Pros:**

* Simplest possible implementation
* No callback overhead

**Cons:**

* No way to integrate with different UI frameworks
* Cannot extend conversation behavior without modifying core code
* Blocks reusability across CLI/GUI/TUI contexts

Consequences
===============================================================================

**Positive:**

* **Simple interface**: Single callback parameter instead of six separate
  callbacks
* **Extensible**: New event types can be added without breaking existing code
  (unknown events handled by ``case _`` branch)
* **Type-safe**: Event classes provide structure and type hints
* **Python 3.10+ alignment**: Uses modern pattern matching features
* **Forward compatible**: Older code ignores newer event types gracefully
* **Testable**: Easy to construct event objects for testing
* **Clear intent**: Event class names document their purpose

**Negative:**

* **Requires Python 3.10+**: Pattern matching is mandatory (already a project
  constraint)
* **Single consumer limitation**: Still only one callback like MessageReactors,
  but this matches actual use case (one UI per conversation)
* **Runtime dispatch**: Pattern matching happens at runtime vs compile-time
  method dispatch (minimal performance impact)

**Neutral:**

* **Learning curve**: Developers need to understand pattern matching if
  unfamiliar
* **Event proliferation**: May lead to many small event classes (mitigated by
  clear naming conventions)

Implementation Notes
===============================================================================

Event classes should be simple dataclasses or frozen dataclasses for immutability:

.. code-block:: python

   @dataclass(frozen=True)
   class MessageProgressEvent:
       chunk: str
       timestamp: datetime = field(default_factory=datetime.now)

Callback signature is type-safe via protocol:

.. code-block:: python

   class ConversationEventHandler(Protocol):
       def __call__(self, event: ConversationEvent) -> None: ...

For extensions that need multiple handlers, they can use their own pattern
matching or dispatch table internally:

.. code-block:: python

   handlers = {
       MessageStartedEvent: [logger.log_start, metrics.track_start],
       MessageCompletedEvent: [logger.log_complete, metrics.track_complete],
   }

References
===============================================================================

* ai-experiments MessageReactors implementation: https://github.com/emcd/ai-experiments
* Python pattern matching (PEP 634): https://peps.python.org/pep-0634/
* Original analysis: ``.auxiliary/notes/callbacks-vs-events.md``
