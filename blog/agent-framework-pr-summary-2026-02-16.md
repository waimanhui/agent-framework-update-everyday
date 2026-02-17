# Agent Framework Updates - February 16, 2026

The Microsoft Agent Framework saw significant development activity on February 16, 2026, with 7 merged pull requests bringing important improvements to both .NET and Python implementations. This update introduces 2 breaking changes alongside several feature enhancements and bug fixes that improve the framework's reliability and developer experience.

## ⚠️ BREAKING CHANGES

### 1. .NET: Refactor Providers to Move Common Functionality to Base

**Impact**: High - Requires updates to custom AIContextProvider and ChatHistoryProvider implementations

**PR**: [#3900](https://github.com/microsoft/agent-framework/pull/3900)

The provider architecture has been refactored to consolidate common functionality into base classes, introducing new protected virtual methods and modifying the provider lifecycle. This change affects all custom provider implementations.

**Key Changes:**

1. **New Constructor Parameters**: Provider base classes now accept optional message filter functions:

```csharp
protected AIContextProvider(
    Func<IEnumerable<ChatMessage>, IEnumerable<ChatMessage>>? provideInputMessageFilter = null,
    Func<IEnumerable<ChatMessage>, IEnumerable<ChatMessage>>? storeInputMessageFilter = null)
{
    this._provideInputMessageFilter = provideInputMessageFilter ?? DefaultExternalOnlyFilter;
    this._storeInputMessageFilter = storeInputMessageFilter ?? DefaultExternalOnlyFilter;
}
```

2. **Abstract to Virtual Method Change**: `InvokingCoreAsync` and `InvokedCoreAsync` are no longer abstract:

**Before:**
```csharp
// Subclasses were required to implement InvokingCoreAsync
protected abstract ValueTask<AIContext> InvokingCoreAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default);
```

**After:**
```csharp
// Now has a default implementation with automatic filtering and merging
protected virtual async ValueTask<AIContext> InvokingCoreAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default)
{
    var inputContext = context.AIContext;
    
    // Create filtered context for ProvideAIContextAsync
    var filteredContext = new InvokingContext(
        context.Agent,
        context.Session,
        new AIContext {
            Instructions = inputContext.Instructions,
            Messages = inputContext.Messages is not null 
                ? this._provideInputMessageFilter(inputContext.Messages) 
                : null,
            Tools = inputContext.Tools
        });
    
    var provided = await this.ProvideAIContextAsync(filteredContext, cancellationToken);
    
    // Merge contexts with automatic source stamping
    var providedMessages = provided.Messages is not null 
        ? provided.Messages.Select(m => m.WithAgentRequestMessageSource(
            AgentRequestMessageSourceType.AIContextProvider, 
            this.GetType().FullName!)) 
        : null;
    
    return new AIContext {
        Instructions = MergeInstructions(inputContext.Instructions, provided.Instructions),
        Messages = MergeMessages(inputContext.Messages, providedMessages),
        Tools = MergeTools(inputContext.Tools, provided.Tools)
    };
}
```

3. **New Protected Methods**: Two new extensibility points have been added:

```csharp
// Provide additional context to be merged with input
protected virtual ValueTask<AIContext> ProvideAIContextAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default)
{
    return new ValueTask<AIContext>(new AIContext());
}

// Process invocation results after completion
protected virtual ValueTask StoreAIContextAsync(
    InvokedContext context, 
    CancellationToken cancellationToken = default) => default;
```

4. **Automatic Error Handling and Filtering**: `InvokedCoreAsync` now has built-in error handling:

```csharp
protected virtual ValueTask InvokedCoreAsync(
    InvokedContext context, 
    CancellationToken cancellationToken = default)
{
    // Skip on errors
    if (context.InvokeException is not null)
    {
        return default;
    }
    
    // Automatically filter messages and call StoreAIContextAsync
    var subContext = new InvokedContext(
        context.Agent,
        context.Session,
        this._storeInputMessageFilter(context.RequestMessages),
        context.ResponseMessages!);
        
    return this.StoreAIContextAsync(subContext, cancellationToken);
}
```

**Migration Guide:**

For simple providers that only need to provide additional context:
- Remove `override` of `InvokingCoreAsync` if you only need to add context
- Implement `ProvideAIContextAsync` instead - it will be automatically called and merged
- The base implementation handles filtering, source stamping, and merging

For providers that need custom filtering or merging:
- Continue overriding `InvokingCoreAsync` for full control
- Optionally call `ProvideAIContextAsync` to get additional context

For providers that store context:
- Remove `override` of `InvokedCoreAsync` if you only need to store filtered messages
- Implement `StoreAIContextAsync` instead - it will be automatically called with filtered messages
- The base implementation handles error checking and message filtering

**Example Migration:**

Before:
```csharp
protected override async ValueTask<AIContext> InvokingCoreAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default)
{
    // Manual filtering
    var externalMessages = context.AIContext.Messages?
        .Where(m => m.GetAgentRequestMessageSourceType() == AgentRequestMessageSourceType.External);
    
    // Fetch additional context
    var history = await _storage.GetHistoryAsync(context.Session.Id);
    
    // Manual merging and source stamping
    var historyMessages = history.Select(m => 
        m.WithAgentRequestMessageSource(AgentRequestMessageSourceType.AIContextProvider, "MyProvider"));
    
    return new AIContext {
        Messages = context.AIContext.Messages.Concat(historyMessages)
    };
}

protected override async ValueTask InvokedCoreAsync(
    InvokedContext context, 
    CancellationToken cancellationToken = default)
{
    if (context.InvokeException is not null) return;
    
    var externalMessages = context.RequestMessages
        .Where(m => m.GetAgentRequestMessageSourceType() == AgentRequestMessageSourceType.External);
    
    await _storage.StoreAsync(context.Session.Id, externalMessages, context.ResponseMessages);
}
```

After:
```csharp
// Much simpler - base class handles filtering, merging, and source stamping
protected override async ValueTask<AIContext> ProvideAIContextAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default)
{
    // Context already filtered to external messages only
    var history = await _storage.GetHistoryAsync(context.Session.Id);
    
    // Just return additional context - base will merge and stamp source
    return new AIContext { Messages = history };
}

protected override async ValueTask StoreAIContextAsync(
    InvokedContext context, 
    CancellationToken cancellationToken = default)
{
    // Messages already filtered to external only, errors already handled
    await _storage.StoreAsync(context.Session.Id, context.RequestMessages, context.ResponseMessages);
}
```

### 2. Python: Fix Message Typing Alignment Between Chat and Agent APIs

**Impact**: High - Changes message input types across chat clients and agents

**PR**: [#3920](https://github.com/microsoft/agent-framework/pull/3920)

This PR addresses issue #3613 by aligning message typing between chat clients and agent run methods, introducing new type aliases and standardizing how messages are passed throughout the framework.

**Key Changes:**

1. **New Type Aliases**: Standardized input types for agent run methods:

```python
from typing import Sequence
from agent_framework import ChatMessage

# New unified type aliases
AgentRunMessages = str | ChatMessage | Sequence[str | ChatMessage]
AgentRunInputs = AgentRunMessages | None
```

2. **Updated Agent.run() Signature**:

**Before:**
```python
def run(
    self,
    messages: str | ChatMessage | list[ChatMessage] | None = None,
    *,
    stream: bool = False,
    thread: AgentThread | None = None,
    **kwargs: Any,
) -> Awaitable[AgentResponse] | ResponseStream:
    ...
```

**After:**
```python
from agent_framework import AgentRunInputs

def run(
    self,
    messages: AgentRunInputs = None,  # Uses new type alias
    *,
    stream: bool = False,
    thread: AgentThread | None = None,
    **kwargs: Any,
) -> Awaitable[AgentResponse] | ResponseStream:
    ...
```

3. **Chat Client Alignment**: Chat clients now accept the same message types:

```python
# Anthropic chat client example
async def complete(
    self,
    messages: AgentRunMessages,  # Standardized type
    model: str | None = None,
    **kwargs: Any,
) -> ChatMessage:
    # Implementation...
```

4. **Sample Updates**: All samples have been updated to use the new typing:

```python
# Old style - still works
response = await agent.run([
    ChatMessage(role="user", content="Hello")
])

# New style - also supported
response = await agent.run("Hello")  # String directly
response = await agent.run([
    "Hello",  # Mix strings and ChatMessages
    ChatMessage(role="user", content="World")
])
```

**Migration Guide:**

Most code will continue to work without changes, as the new types are more permissive. However:

1. **Type Annotations**: Update type hints in your code to use the new aliases:

```python
# Before
def process_messages(messages: list[ChatMessage]) -> None:
    ...

# After
from agent_framework import AgentRunMessages

def process_messages(messages: AgentRunMessages) -> None:
    ...
```

2. **Custom Chat Clients**: If you've implemented custom chat clients, update method signatures:

```python
from agent_framework import AgentRunMessages

class MyCustomClient(ChatClient):
    async def complete(
        self,
        messages: AgentRunMessages,  # Updated type
        **kwargs: Any,
    ) -> ChatMessage:
        # Convert to list if needed
        if isinstance(messages, str):
            messages = [ChatMessage(role="user", content=messages)]
        elif isinstance(messages, ChatMessage):
            messages = [messages]
        # Process messages...
```

3. **Context Providers**: Update context provider implementations:

```python
from agent_framework import AgentRunMessages

class MyContextProvider(AIContextProvider):
    async def provide_context(
        self,
        messages: AgentRunMessages,  # Use new type
    ) -> AIContext:
        ...
```

**Benefits:**
- Consistent typing across chat and agent APIs
- More flexible message input (strings, single messages, or lists)
- Better type checking and IDE support
- Simplified code in many cases

## Major Updates

### .NET: Add CreateSessionAsync Overload with taskId for A2A Agent Session Resumption

**PR**: [#3924](https://github.com/microsoft/agent-framework/pull/3924)

Added a new `CreateSessionAsync` overload to the A2A Agent that accepts a `taskId` parameter, enabling session resumption for long-running agent-to-agent interactions.

**New Method Signature:**

```csharp
public async Task<AgentSession> CreateSessionAsync(
    string taskId,
    CancellationToken cancellationToken = default)
{
    // Create or resume session based on taskId
    var session = await this.SessionManager.GetOrCreateSessionAsync(
        taskId, 
        cancellationToken);
    
    return session;
}
```

**Usage Example:**

```csharp
// Create A2A agent
var a2aAgent = new A2AAgent(config);

// Resume existing task/session
var taskId = "task-12345";
var session = await a2aAgent.CreateSessionAsync(taskId);

// Continue conversation in the same session
var response = await a2aAgent.RunAsync("Continue where we left off", session);
```

**Benefits:**
- Enables persistent A2A conversations across multiple interactions
- Supports checkpoint/resume patterns for long-running tasks
- Simplifies distributed agent scenarios
- Better support for async agent workflows

**Unit Tests Added:**

```csharp
[Fact]
public async Task CreateSessionAsync_WithTaskId_ReusesExistingSession()
{
    // Arrange
    var agent = new A2AAgent(config);
    var taskId = "test-task-123";
    
    // Act
    var session1 = await agent.CreateSessionAsync(taskId);
    var session2 = await agent.CreateSessionAsync(taskId);
    
    // Assert
    Assert.Equal(session1.Id, session2.Id);
}
```

### Python: Warn on Unsupported AzureAIClient Runtime Tool/Structured Output Overrides

**PR**: [#3919](https://github.com/microsoft/agent-framework/pull/3919)

Enhanced the AzureAI client to emit warnings when users attempt runtime overrides that aren't supported by the underlying Azure AI model.

**Implementation:**

```python
import warnings
from typing import Any

class AzureAIClient:
    def complete(
        self,
        messages: AgentRunMessages,
        *,
        tools: list[Tool] | None = None,
        structured_output: type | None = None,
        **kwargs: Any,
    ) -> ChatMessage:
        # Check for unsupported runtime overrides
        if tools is not None and not self._supports_tool_override:
            warnings.warn(
                "This Azure AI model does not support runtime tool overrides. "
                "The 'tools' parameter will be ignored. "
                "Configure tools at agent initialization instead.",
                UserWarning,
                stacklevel=2
            )
        
        if structured_output is not None and not self._supports_structured_output_override:
            warnings.warn(
                "This Azure AI model does not support runtime structured output overrides. "
                "The 'structured_output' parameter will be ignored. "
                "Configure structured output at agent initialization instead.",
                UserWarning,
                stacklevel=2
            )
        
        # Continue with execution...
```

**Example Usage:**

```python
from agent_framework_azure_ai import AzureAIClient

client = AzureAIClient(
    endpoint="https://my-endpoint.azure.com",
    model="gpt-4"  # Assuming this model doesn't support runtime overrides
)

# This will now emit a warning
response = await client.complete(
    messages="Hello",
    tools=[my_tool]  # Runtime override not supported
)
# Warning: This Azure AI model does not support runtime tool overrides...
```

**Benefits:**
- Better developer experience with clear feedback
- Prevents silent failures when overrides are ignored
- Guides users to correct configuration patterns
- Comprehensive test coverage for warning scenarios

### Python: Fix Tool Normalization and Provider Sample Consolidation

**PR**: [#3953](https://github.com/microsoft/agent-framework/pull/3953)

Improved tool normalization across providers and consolidated sample code for better maintainability.

**Key Improvements:**

1. **Consistent Tool Normalization**: All chat clients now normalize tools consistently:

```python
from agent_framework import Tool, ToolCallSpec

class ChatClient:
    def _normalize_tools(
        self, 
        tools: list[Tool] | None
    ) -> list[ToolCallSpec] | None:
        """Normalize tools to internal format."""
        if tools is None:
            return None
        
        return [
            ToolCallSpec(
                name=tool.name,
                description=tool.description or "",
                parameters=tool.parameters or {}
            )
            for tool in tools
        ]

    async def complete(
        self,
        messages: AgentRunMessages,
        *,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> ChatMessage:
        # Normalize before sending to provider
        normalized_tools = self._normalize_tools(tools)
        # Use normalized tools...
```

2. **Provider Sample Consolidation**: Bedrock, Anthropic, and Azure AI samples now share common patterns:

```python
# packages/bedrock/samples/__init__.py
from agent_framework_bedrock import BedrockChatClient

def create_bedrock_agent():
    """Create a Bedrock agent with standard configuration."""
    return BedrockChatClient(
        region="us-east-1",
        model="anthropic.claude-3-sonnet"
    )

# Similar patterns in other providers for consistency
```

3. **Updated CODING_STANDARD.md**: Enhanced guidelines for provider implementation:

```markdown
## Provider Implementation Standards

### Tool Handling
- Always normalize tool definitions before sending to the API
- Handle None/empty tool lists gracefully
- Validate tool schemas against provider requirements
- Use consistent error messages for tool validation failures

### Sample Code
- Keep samples DRY by using shared utility functions
- Document provider-specific configuration clearly
- Include both basic and advanced usage examples
- Test samples in CI/CD pipelines
```

**Benefits:**
- More reliable tool execution across providers
- Easier to maintain and extend provider implementations
- Better sample code that follows best practices
- Reduced code duplication

## Minor Updates and Bug Fixes

### .NET: Bug Bash Fixes

**PR**: [#3927](https://github.com/microsoft/agent-framework/pull/3927)

Multiple fixes addressing issues found during internal bug bash testing:

1. **Fixed Agent_Step06_PersistedConversations Sample**: Corrected session persistence logic
2. **Updated Agent_Step10_AsMcpTool README**: Improved documentation clarity
3. **Fixed Agent_Step16_ChatReduction Sample**: Corrected message filtering implementation

**Example Fix in ChatReduction Sample:**

```csharp
// Before - incorrect filtering
var filteredMessages = messages.Where(m => m.Role == "user");

// After - correct filtering with proper null checks
var filteredMessages = messages?
    .Where(m => m.Role == ChatRole.User && !string.IsNullOrEmpty(m.Content))
    .ToList() ?? new List<ChatMessage>();
```

### .NET: Add Skill to Verify Samples

**PR**: [#3931](https://github.com/microsoft/agent-framework/pull/3931)

Added a GitHub Copilot skill to automatically verify .NET sample code in CI/CD pipelines.

**Skill Definition:**

```markdown
---
name: verify-dotnet-samples
description: Verifies that .NET sample code compiles and runs successfully
---

# Sample Verification Skill

This skill automatically:
1. Discovers all .csproj files in samples/ directory
2. Runs `dotnet build` on each sample
3. Executes samples with test inputs
4. Validates expected outputs
5. Reports any failures

## Usage

Triggered automatically on PR creation and updates.
Manual trigger: `@copilot verify samples`
```

**Benefits:**
- Catches sample code errors before merge
- Ensures samples stay in sync with framework changes
- Automated verification in CI/CD
- Better documentation quality

## Summary

February 16, 2026 brings significant architectural improvements and quality enhancements to the Microsoft Agent Framework:

**Breaking Changes Summary:**
- 2 breaking changes requiring migration effort
- .NET provider architecture refactored for better extensibility
- Python message typing aligned between chat and agent APIs

**Key Improvements:**
- Enhanced A2A agent session resumption capabilities
- Better developer warnings for unsupported features
- Improved tool normalization across providers
- Comprehensive bug fixes from testing
- Automated sample verification

**Recommended Actions:**

1. **For .NET Developers:**
   - Review and update custom `AIContextProvider` implementations
   - Consider simplifying providers using new `ProvideAIContextAsync` method
   - Test A2A agent session resumption if using agent-to-agent patterns
   - Review bug bash fixes to ensure samples align with your code

2. **For Python Developers:**
   - Update message type annotations to use new `AgentRunMessages` aliases
   - Review custom chat client implementations for typing alignment
   - Test Azure AI client warning behavior for runtime overrides
   - Check tool usage against the updated normalization logic

3. **For All Developers:**
   - Update dependencies to the latest framework versions
   - Run comprehensive tests after migration
   - Review updated samples for new patterns and best practices
   - Monitor for deprecation warnings in logs

**Impact Assessment:**
- **High Priority**: Breaking changes in providers (.NET) and message typing (Python) require immediate attention
- **Medium Priority**: Runtime override warnings may affect Azure AI users
- **Low Priority**: Bug fixes and sample improvements enhance quality without requiring changes

This release continues the framework's evolution toward a more consistent, maintainable, and developer-friendly API surface. The breaking changes consolidate common patterns into base classes, reducing boilerplate while maintaining flexibility for advanced scenarios.
