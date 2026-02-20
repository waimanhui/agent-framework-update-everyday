# Agent Framework Updates - February 19, 2026

On February 19, 2026, the Microsoft Agent Framework merged an impressive **34 pull requests**, marking a pivotal day in the project's evolution. This update includes **three critical breaking changes** affecting both Python and .NET developers, major improvements to reasoning model support, comprehensive new learning path samples, and the official RC (Release Candidate) version update for all .NET packages.

## ⚠️ BREAKING CHANGES

### 1. Python: Redesigned Exception Hierarchy

**PR**: [#4082](https://github.com/microsoft/agent-framework/pull/4082)  
**Impact**: High - Requires updates to exception handling code across Python projects

The Python SDK has undergone a complete exception hierarchy redesign, replacing the flat `ServiceException` family with a domain-scoped architecture. This change provides better error categorization and more precise exception handling.

**What Changed:**

The old flat structure with `ServiceException`, `ServiceInitializationError`, `AgentExecutionException`, and `AgentInvocationError` has been replaced with domain-specific exception branches:

```python
# New exception hierarchy

# Agent-related exceptions
class AgentException(Exception):
    """Base for all agent-related errors"""
    pass

class AgentInvalidAuthException(AgentException):
    """Authentication/authorization failures"""
    pass

class AgentInvalidRequestException(AgentException):
    """Invalid request parameters or structure"""
    pass

class AgentInvalidResponseException(AgentException):
    """Malformed or unexpected response from agent"""
    pass

class AgentContentFilterException(AgentException):
    """Content policy violations"""
    pass

# Chat client exceptions
class ChatClientException(Exception):
    """Base for all chat client errors"""
    pass

class ChatClientInvalidAuthException(ChatClientException):
    pass

class ChatClientInvalidRequestException(ChatClientException):
    pass

class ChatClientInvalidResponseException(ChatClientException):
    pass

# Integration exceptions
class IntegrationException(Exception):
    """Base for external service integrations"""
    pass

class IntegrationInitializationError(IntegrationException):
    """Failed to initialize external service connection"""
    pass

# Workflow exceptions
class WorkflowException(Exception):
    """Base for all workflow-related errors"""
    pass

class WorkflowRunnerException(WorkflowException):
    """Workflow execution failures"""
    pass

class WorkflowConvergenceException(WorkflowException):
    """Workflow failed to converge"""
    pass

class WorkflowCheckpointException(WorkflowException):
    """Checkpoint save/load failures"""
    pass

class WorkflowValidationException(WorkflowException):
    """Invalid workflow configuration"""
    pass

class WorkflowActionException(WorkflowException):
    """Action execution failures"""
    pass

class WorkflowDeclarativeException(WorkflowException):
    """Declarative workflow parsing/execution errors"""
    pass
```

**Migration Guide:**

Old code:
```python
from agent_framework import ServiceException, AgentExecutionException

try:
    response = await agent.run(request)
except ServiceException as e:
    logger.error(f"Service error: {e}")
except AgentExecutionException as e:
    logger.error(f"Agent error: {e}")
```

New code:
```python
from agent_framework import (
    AgentException, 
    AgentInvalidRequestException,
    AgentInvalidResponseException,
    ChatClientException
)

try:
    response = await agent.run(request)
except AgentInvalidRequestException as e:
    logger.error(f"Invalid request: {e}")
except AgentInvalidResponseException as e:
    logger.error(f"Invalid response: {e}")
except ChatClientException as e:
    logger.error(f"Chat client error: {e}")
except AgentException as e:
    logger.error(f"Agent error: {e}")
```

**Key Changes:**
- All `Service*` exceptions removed
- `AgentExecutionException` split into `AgentInvalidRequestException` and `AgentInvalidResponseException`
- `AgentInvocationError` removed
- Workflow exceptions consolidated from `_workflows/_exceptions.py` into main `exceptions.py`
- Purview exceptions now inherit from `IntegrationException`
- Initialization validation now uses built-in `ValueError`/`TypeError` instead of custom exceptions

**Related Issue**: [#3410](https://github.com/microsoft/agent-framework/issues/3410)

---

### 2. .NET: Polymorphic Routing Implementation

**PR**: [#3792](https://github.com/microsoft/agent-framework/pull/3792)  
**Impact**: Medium-High - Changes workflow routing behavior for declarative workflows

This breaking change introduces polymorphic routing capabilities to .NET declarative workflows, enabling more flexible message routing based on runtime types.

**What Changed:**

Declarative workflow executors now support polymorphic routing, where routes can match not just the exact type but also derived types. This enables more flexible workflow designs where a single route can handle multiple related message types.

```csharp
// New: Annotations added to Declarative workflow executors
[Route(typeof(BaseMessageType))]  // Now matches BaseMessageType and all derived types
public class MessageHandler : IWorkflowExecutor
{
    public async Task<WorkflowResult> ExecuteAsync(
        WorkflowContext context, 
        CancellationToken cancellationToken)
    {
        // Handle BaseMessageType and any derived types
        var message = context.Input as BaseMessageType;
        // ...
    }
}
```

**Key Improvements:**
- Implicit filter support in collection loops
- Fixed `ProtocolBuilder` implicit output registrations
- Enhanced `ExecuteRouteGenerator` test coverage
- Fixed `ConcurrentEndExecutor` to properly handle `TurnTokens`
- Renamed `DeclarativeActionExecutor.ExecuteAsync` to `ExecuteActionAsync` to avoid conflicts

**Migration Required:**
- Review custom route configurations for type matching behavior
- Update any code relying on exact-type-only routing
- Test workflows with inheritance hierarchies

---

### 3. .NET: Decoupled Checkpointing from Run/StreamAsync APIs

**PR**: [#4037](https://github.com/microsoft/agent-framework/pull/4037)  
**Impact**: High - Changes checkpoint management API surface

Checkpointing is no longer passed directly to `Run`/`StreamAsync` APIs. Instead, it becomes a property of the `IWorkflowExecutionEnvironment`, enabling tighter coupling between execution environments and their checkpoint managers.

**What Changed:**

Previously, checkpoint managers were passed as parameters to workflow execution methods. Now, each execution environment owns its checkpoint configuration:

```csharp
// OLD approach (no longer supported)
var checkpointManager = new InMemoryCheckpointManager();
await workflow.RunAsync(
    input, 
    checkpointManager: checkpointManager  // ❌ No longer valid
);

// NEW approach
public interface IWorkflowExecutionEnvironment
{
    ICheckpointManager? CheckpointManager { get; }  // ✅ Environment owns checkpointing
}

// Example: In-process execution with checkpointing
var environment = new InProcessExecutionEnvironment
{
    CheckpointManager = new InMemoryCheckpointManager()
};

await workflow.RunAsync(input, environment);
```

**Why This Change:**

This decoupling prevents API mismatches where execution environments (like Durable Tasks) are tightly coupled to specific checkpoint implementations. For example, Durable Tasks cannot accept an `InMemoryCheckpointManager` since it manages its own durable state.

**Migration Guide:**

1. Remove checkpoint parameters from `RunAsync`/`StreamAsync` calls
2. Configure checkpointing on the execution environment instead:

```csharp
// Before
var checkpoint = new FileSystemCheckpointManager("./checkpoints");
await InProcessExecution.RunAsync(workflow, input, checkpointManager: checkpoint);

// After
var environment = new InProcessExecutionEnvironment
{
    CheckpointManager = new FileSystemCheckpointManager("./checkpoints")
};
await workflow.RunAsync(input, environment);
```

---

## 🚀 Major Updates

### Python: Reasoning Model Workflow Handoff and History Serialization Fixes

**PR**: [#4083](https://github.com/microsoft/agent-framework/pull/4083)  
**Impact**: Critical fix for multi-agent workflows using reasoning models (gpt-5-mini, gpt-5.2)

This comprehensive fix addresses multiple critical issues when using reasoning models in multi-agent workflows. The problems surfaced when reasoning model outputs (with `text_reasoning` and `function_call` items) were passed between agents in a workflow.

**Problems Solved:**

1. **Reasoning Items in Handoff**: When Agent 1 (reasoning model) handed off to Agent 2, the response included server-scoped reasoning IDs (`rs_XXXX`) and function call IDs that caused API errors in Agent 2's context.

2. **Service Session ID Conflicts**: Explicit history replay caused duplicate item errors when `service_session_id` wasn't cleared.

3. **Reasoning Serialization**: The Responses API only accepts reasoning items when paired with a `function_call`, but the framework serialized them unconditionally.

4. **Summary Field Format**: The reasoning summary field must be an array, not an object.

**Code Changes:**

```python
# agent_framework/_agents/_agent_executor.py

def _filter_messages_for_handoff(messages: list[Content]) -> list[Content]:
    """Filter out internal reasoning/call items before handoff"""
    filtered = []
    for msg in messages:
        # Strip reasoning and call items (server-scoped IDs)
        # but KEEP function_result (actual tool output content)
        if msg.type not in [
            'function_call', 
            'text_reasoning',
            'function_approval_request',
            'function_approval_response'
        ]:
            filtered.append(msg)
    return filtered

# Reset service_session_id for explicit history replay
class AgentExecutorRequest:
    reset_service_session: bool = False  # New field

async def run(self, request: AgentExecutorRequest) -> AgentResponse:
    if request.reset_service_session:
        self._session.service_session_id = None  # Clear server state
    # ... proceed with execution
```

**Serialization Fix:**

```python
def _prepare_message_for_openai(message: ChatMessage) -> dict:
    """Only serialize reasoning when paired with function_call"""
    has_function_call = any(
        c.type == 'function_call' for c in message.content
    )
    
    serialized_content = []
    for content in message.content:
        if content.type == 'text_reasoning':
            if has_function_call:  # Only include if followed by call
                serialized_content.append({
                    'type': 'reasoning',
                    'summary': [  # Must be array, not object
                        {'type': 'summary_text', 'text': content.text}
                    ]
                })
        else:
            serialized_content.append(_serialize_content(content))
    
    return serialized_content
```

**Impact:** Multi-agent workflows with reasoning models now work reliably. Function results are preserved across handoffs while preventing API errors from server-scoped IDs.

**Related Issue**: [#4047](https://github.com/microsoft/agent-framework/issues/4047)

---

### .NET: Remove Function Calls and Tool Messages from Handoff

**PR**: [#3811](https://github.com/microsoft/agent-framework/pull/3811)  
**Impact**: Improves agent handoff behavior by filtering internal messages

This update filters out internal handoff function call and tool result messages before passing conversation history to the target agent's LLM. These internal messages were confusing models into ignoring the original user question.

**What Changed:**

```csharp
// New HandoffToolCallFilteringBehavior enum
public enum HandoffToolCallFilteringBehavior
{
    RemoveAll,          // Remove all tool calls and results
    RemoveHandoffOnly,  // Remove only handoff-related tool messages (default)
    PreserveAll         // Keep all messages (old behavior)
}

// Usage in HandoffsWorkflowBuilder
var workflow = new HandoffsWorkflowBuilder()
    .AddHandoff(
        fromAgent: "Agent1",
        toAgent: "Agent2",
        handoffInstructions: "You are now Agent2...",
        filteringBehavior: HandoffToolCallFilteringBehavior.RemoveHandoffOnly
    )
    .Build();
```

**Why This Matters:**

When Agent 1 calls an internal handoff tool to transfer to Agent 2, the conversation history included:
- User: "Help me with task X"
- Agent 1: [function_call: handoff_to_agent2]
- [function_result: handoff successful]

Agent 2 would see these internal messages and get confused, sometimes focusing on the handoff mechanism instead of the user's original question.

**New Behavior:**

The framework now filters these messages by default (`RemoveHandoffOnly`), so Agent 2 receives a clean conversation history focused on the actual user intent.

---

### .NET: Message-Only AIContextProvider as Agent Decorator

**PR**: [#4009](https://github.com/microsoft/agent-framework/pull/4009)  
**Impact**: Enables simpler context injection patterns

This feature allows `AIContextProvider` implementations to work as agent decorators even when they only need to inject messages (not tools or full context configuration).

```csharp
// Simple message-only context provider
public class UserProfileContextProvider : AIContextProvider
{
    public override Task<IEnumerable<ChatMessage>> GetContextMessagesAsync(
        AgentRequest request, 
        CancellationToken cancellationToken)
    {
        var userProfile = await _profileService.GetProfileAsync(request.UserId);
        
        return new[] 
        {
            new ChatMessage(
                ChatRole.System, 
                $"User preferences: {userProfile.Preferences}"
            )
        };
    }
}

// Use as decorator without implementing tool/config methods
var decoratedAgent = new AIContextProviderDecorator(
    baseAgent,
    new UserProfileContextProvider()
);
```

**Benefits:**
- Simpler implementation for message-only context injection
- No need to implement unused abstract methods
- Cleaner separation of concerns

---

### .NET: Agent Skills Improvements

**PR**: [#4081](https://github.com/microsoft/agent-framework/pull/4081)  
**Impact**: Enhanced .NET agent skills functionality

Various improvements and refinements to the .NET agent skills system, including better tool registration, improved skill configuration APIs, and enhanced documentation.

---

### Python: Add Unit Test Coverage Gates

**PR**: [#4104](https://github.com/microsoft/agent-framework/pull/4104)  
**Impact**: Improved code quality and testing infrastructure

Added additional unit test coverage requirements to ensure higher code quality standards. The PR also fixed a missing `files` parameter in the `print_coverage_table()` docstring.

```python
def print_coverage_table(
    coverage_data: dict,
    threshold: float = 0.8,
    files: list[str] | None = None  # Now properly documented
) -> None:
    """
    Print coverage statistics in table format.
    
    Args:
        coverage_data: Coverage statistics dictionary
        threshold: Minimum coverage threshold (0.0-1.0)
        files: Optional list of files to include in report
    """
    # ...
```

---

### .NET: RC Release Version Update

**PR**: [#4067](https://github.com/microsoft/agent-framework/pull/4067)  
**Impact**: All .NET packages now at Release Candidate stage

All Microsoft.Agents.AI.* packages have been updated to Release Candidate (RC) versions, signaling that the .NET SDK is approaching stable 1.0 release.

**Packages Updated:**
- `Microsoft.Agents.AI`
- `Microsoft.Agents.AI.Abstractions`
- `Microsoft.Agents.AI.Anthropic`
- `Microsoft.Agents.AI.AzureAI`
- `Microsoft.Agents.AI.Declarative`
- `Microsoft.Agents.AI.OpenAI`
- `Microsoft.Agents.AI.Purview`
- `Microsoft.Agents.AI.Workflows`
- `Microsoft.Agents.AI.Workflows.Declarative`
- `Microsoft.Agents.AI.Workflows.Declarative.AzureAI`
- `Microsoft.Agents.AI.Workflows.Generators`

**Changes:**

```xml
<!-- dotnet/nuget/nuget-package.props -->
<PropertyGroup>
  <!-- Centralized RC versioning -->
  <VersionPrefix>1.0.0</VersionPrefix>
  <VersionSuffix>rc.1</VersionSuffix>
  
  <!-- Date-stamped preview/alpha only for non-RC builds -->
  <BuildDate>$([System.DateTime]::UtcNow.ToString('yyyyMMdd'))</BuildDate>
</PropertyGroup>
```

This signifies the framework is entering the final stabilization phase before the 1.0 release.

---

### .NET: Fixed CheckpointInfo.Parent Always Null in InProcessRunner

**PR**: [#3812](https://github.com/microsoft/agent-framework/pull/3812)  
**Impact**: Fixes checkpoint parent reference tracking

Fixed a bug where `CheckpointInfo.Parent` was always `null` in the `InProcessRunner`, preventing proper checkpoint lineage tracking. This is essential for workflow recovery and debugging.

---

## 📚 New .NET Learning Path Samples

Five comprehensive learning path samples were added to help developers learn the Agent Framework step-by-step:

### 1. Get Started (01-get-started)
**PR**: [#4094](https://github.com/microsoft/agent-framework/pull/4094)

Introduction to Agent Framework basics, including:
- Setting up your first agent
- Basic agent configuration
- Simple request/response patterns

### 2. Agents (02-agents)
**PR**: [#4107](https://github.com/microsoft/agent-framework/pull/4107)

Deep dive into agent concepts:
- Creating custom agents
- Agent composition
- Agent behaviors and lifecycle

### 3. Workflows (03-workflows)
**PR**: [#4102](https://github.com/microsoft/agent-framework/pull/4102)

Introduction to multi-agent workflows:
- Building agent chains
- Conditional routing
- Workflow patterns (sequential, parallel, conditional)

### 4. Hosting (04-hosting)
**PR**: [#4098](https://github.com/microsoft/agent-framework/pull/4098)

Production deployment scenarios:
- Hosting agents in web applications
- ASP.NET Core integration
- Scalability considerations
- Monitoring and logging

### 5. End-to-End (05-end-to-end)
**PR**: [#4091](https://github.com/microsoft/agent-framework/pull/4091)

Complete application examples:
- Real-world scenarios
- Best practices
- Performance optimization
- Error handling patterns

---

## 🐛 Bug Fixes and Minor Updates

### Python: Add load_dotenv() to Samples

**PR**: [#4043](https://github.com/microsoft/agent-framework/pull/4043)

All Python samples now support `.env` file configuration for easier local development:

```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access configuration
api_key = os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")
```

Create a `.env` file in your sample directory:
```bash
OPENAI_API_KEY=sk-...
AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
MODEL_DEPLOYMENT=gpt-4
```

---

### Documentation and Link Fixes

Several PRs fixed broken documentation links:

- **PR [#4108](https://github.com/microsoft/agent-framework/pull/4108)**: Fixed broken relative link in .NET GroupChatToolApproval README
- **PR [#4105](https://github.com/microsoft/agent-framework/pull/4105)**: Fixed broken markdown links to repository resources outside `/docs`
- **PR [#4101](https://github.com/microsoft/agent-framework/pull/4101)**: Fixed broken sample links in durable-agents README
- **PR [#4106](https://github.com/microsoft/agent-framework/pull/4106)**: Fixed missing `files` parameter documentation

---

## 📊 Summary and Impact

February 19, 2026 represents a **major milestone** for the Microsoft Agent Framework:

### Breaking Changes Impact
- **Python developers** must update exception handling across projects (high priority)
- **.NET developers** need to refactor checkpoint configuration and review routing logic
- Migration guides provided for all breaking changes

### Key Wins
- ✅ **Reasoning models now work reliably** in multi-agent workflows
- ✅ **.NET packages at RC stage** - approaching 1.0 stable release
- ✅ **Comprehensive learning path** - 5 new step-by-step samples
- ✅ **Improved code quality** - enhanced test coverage gates
- ✅ **Better developer experience** - .env support in all Python samples

### Recommended Actions

**For Python Developers:**
1. **URGENT**: Update exception handling to use new hierarchy
2. Test multi-agent workflows with reasoning models (gpt-5-mini, gpt-5.2)
3. Add `.env` file support to your projects for easier configuration

**For .NET Developers:**
1. **HIGH PRIORITY**: Migrate checkpoint configuration to execution environments
2. Review polymorphic routing impact on declarative workflows
3. Explore new learning path samples (01-get-started through 05-end-to-end)
4. Update to RC package versions
5. Test handoff workflows with new message filtering behavior

**For All Developers:**
- Review the three breaking changes and assess impact on your codebase
- Test thoroughly before upgrading to production
- Check documentation link fixes if you maintain framework documentation

### Statistics
- **Total PRs merged**: 34
- **Breaking changes**: 3
- **Major features**: 5+
- **New samples**: 5 learning path steps
- **Bug fixes**: 10+
- **Lines of code changed**: Significant refactoring across both Python and .NET SDKs

This release demonstrates the Agent Framework team's commitment to both stability (RC release) and innovation (reasoning model support, polymorphic routing). The comprehensive learning path samples significantly lower the barrier to entry for new developers.

---

## Links

- [Microsoft Agent Framework Repository](https://github.com/microsoft/agent-framework)
- [All PRs merged on February 19, 2026](https://github.com/microsoft/agent-framework/pulls?q=is%3Apr+is%3Aclosed+merged%3A2026-02-19)
- [Python Exception Hierarchy Redesign (#4082)](https://github.com/microsoft/agent-framework/pull/4082)
- [.NET Polymorphic Routing (#3792)](https://github.com/microsoft/agent-framework/pull/3792)
- [.NET Decouple Checkpointing (#4037)](https://github.com/microsoft/agent-framework/pull/4037)
- [Python Reasoning Model Fixes (#4083)](https://github.com/microsoft/agent-framework/pull/4083)
