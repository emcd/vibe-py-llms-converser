ComparisonResult        # unused variable
NominativeArguments     # unused variable
PositionalArguments     # unused variable
package_name            # unused variable

# --- BEGIN: Injected by Copier ---
Omnierror              # unused base exception class for derivation
# --- END: Injected by Copier ---

# Phase 1.1 Core Protocols - Used in future phases
# Canisters
Content                 # unused protocol - base for content types
mime_type               # unused variable - protocol attribute
role                    # unused variable - protocol attribute
UserCanister            # unused protocol - Phase 1.2+
AssistantCanister       # unused protocol - Phase 1.2+
SupervisorCanister      # unused protocol - Phase 1.2+
DocumentCanister        # unused protocol - Phase 1.2+
InvocationCanister      # unused protocol - Phase 1.2+
ResultCanister          # unused protocol - Phase 1.2+
TextContent             # unused class - concrete content implementation
text                    # unused variable - dataclass attribute
PictureContent          # unused class - concrete content implementation
content_id              # unused variable - dataclass attribute
source_location         # unused variable - dataclass attribute

# Events
message_id              # unused variable - dataclass attribute
chunk                   # unused variable - dataclass attribute
ConversationEvent       # unused type alias - Phase 1.4+

# Invocables
invocable               # unused variable - protocol attribute
arguments_schema        # unused variable - protocol attribute
ensemble                # unused variable - protocol/parameter
context                 # unused variable - parameter
invokers                # unused variable - protocol attribute
configuration           # unused variable - protocol attribute
connection              # unused variable - protocol attribute
InvokerRegistry         # unused protocol - Phase 1.3+

# Messages
UserMessage             # unused class - Phase 1.2+
produce                 # unused method - factory method
AssistantMessage        # unused class - Phase 1.2+
SupervisorMessage       # unused class - Phase 1.2+
DocumentMessage         # unused class - Phase 1.2+
InvocationMessage       # unused class - Phase 1.3+
ResultMessage           # unused class - Phase 1.3+

# Providers
identifier              # unused variable - protocol attribute
supports_streaming      # unused variable - protocol attribute
supports_tool_calling   # unused variable - protocol attribute
context_window_size     # unused variable - protocol attribute
descriptor              # unused variable - protocol attribute
controls                # unused variable - parameter
event_handler           # unused variable - parameter
provider_name           # unused variable - protocol attribute
Provider                # unused protocol - Phase 1.4+
MessagesProcessor       # unused protocol - Phase 1.4+
native_messages         # unused variable - parameter
ControlsProcessor       # unused protocol - Phase 1.4+
native_controls         # unused variable - parameter
InvocationsProcessor    # unused protocol - Phase 1.4+
native_tools            # unused variable - parameter
tool_schemas            # unused variable - parameter
ConversationTokenizer   # unused protocol - Phase 1.4+
