# Role Enum Discussion

**Status**: ✅ DECIDED - Adopted 6-role approach
**Created**: 2025-11-19
**Decided**: 2025-11-19

## Decision

We have adopted the 6-role approach from ai-experiments, implementing distinct roles for each canister type.

## Implemented Solution

```python
class Role( __.enum.Enum ):
    '''
    Platform-neutral message role enumeration.

    Implementations must map these roles to their native roles or constructs
    as appropriate. Each role corresponds to a specific canister type.
    '''

    User = 'user'
    Assistant = 'assistant'
    Supervisor = 'supervisor'
    Document = 'document'
    Invocation = 'invocation'
    Result = 'result'
```

Each canister type now has its own corresponding role (1:1 mapping):
- `UserCanister` → Role.User
- `AssistantCanister` → Role.Assistant
- `SupervisorCanister` → Role.Supervisor
- `DocumentCanister` → Role.Document
- `InvocationCanister` → Role.Invocation
- `ResultCanister` → Role.Result

## ai-experiments Implementation

The original project defines 6 distinct roles matching the 6 canister types:

```python
class Role( __.enum.Enum ):
    Assistant = 'assistant'
    Document = 'document'
    Invocation = 'invocation'
    Result = 'result'
    Supervisor = 'supervisor'
    User = 'user'
```

Each canister type has its own corresponding role.

## Analysis

### Current Approach: Conflated Roles
**Pros:**
- Simpler for provider APIs that only understand user/assistant/system roles
- Matches the common three-role pattern in most LLM APIs
- Easier serialization to provider-native formats

**Cons:**
- Loss of semantic precision (can't distinguish a regular user message from a tool result)
- May complicate nativization logic (need to inspect canister type, not just role)
- Inconsistent with ai-experiments precedent

### ai-experiments Approach: Distinct Roles
**Pros:**
- Each canister type has unique semantic identity
- Role directly indicates canister type (1:1 mapping)
- Aligns with ai-experiments precedent and thinking
- Clearer intent in message history

**Cons:**
- Nativization to provider APIs requires mapping (e.g., Document/Result → User)
- More complex but perhaps more honest about the distinction

## Recommendation

**Option 1: Keep current 3-role approach**
- Maintain simplicity
- Document that role != canister type
- Handle semantic distinctions in nativization logic

**Option 2: Adopt 6-role approach from ai-experiments**
- Add Document, Invocation, Result roles
- Update canister implementations to use specific roles
- Map to provider APIs during nativization (Document/Result → user, Invocation → assistant)
- Better semantic precision and alignment with precedent

## Rationale for Decision

After analyzing the ai-experiments provider implementations (Anthropic and OpenAI), the 6-role approach was chosen because:

1. **Cleaner Nativization Logic**: Both providers dispatch on `canister.role` using pattern matching. With 6 roles, this is straightforward exhaustive matching. With 3 roles, we'd need additional type checks or attribute inspection.

2. **Semantic Precision**: Role becomes the primary semantic identifier. Each role unambiguously identifies what kind of message it is, making serialization, deserialization, and debugging clearer.

3. **Provider Mapping is Explicit**: The mapping from 6 roles to provider-specific roles is intentional and documented:
   - **Anthropic**: Document/Result → user, Invocation → assistant, Supervisor → system (extracted separately)
   - **OpenAI**: Document/Result → user (or function/tool), Invocation → assistant, Supervisor → system/developer/user (capability-dependent)

4. **Follows Established Precedent**: The ai-experiments project thoroughly explored this design space. The 6-role approach emerged from practical experience with multiple providers.

5. **Future-Proof**: New canister types can have their own distinct roles rather than awkwardly sharing existing ones.

## Implementation Notes

Provider nativization will need to map platform-neutral roles to provider-specific roles:

```python
# Example Anthropic mapping
match canister.role:
    case Role.User: return {"role": "user", ...}
    case Role.Assistant: return {"role": "assistant", ...}
    case Role.Document: return {"role": "user", ...}  # with supplemental header
    case Role.Invocation: return {"role": "assistant", ...}  # with tool_use
    case Role.Result: return {"role": "user", ...}  # with tool_result
    case Role.Supervisor: # Extract separately as system instruction
```

This explicit mapping is clearer and more maintainable than inferring intent from a limited role set.
