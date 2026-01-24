# Agent Framework Updates - January 23, 2026

On January 23, 2026, the Microsoft Agent Framework received 12 significant updates, including three breaking changes that improve API clarity and workflow capabilities. This release focuses on enhancing the developer experience through better naming conventions, improved agent hosting in workflows, and several bug fixes across both .NET and Python implementations.

## ⚠️ BREAKING CHANGES

### 1. ChatMessageStore Renamed to ChatHistoryProvider (.NET)

**PR**: [#3375](https://github.com/microsoft/agent-framework/pull/3375)  
**Impact**: High - Requires code changes in all projects using ChatMessageStore

The core abstraction `ChatMessageStore` has been renamed to `ChatHistoryProvider` to better reflect its actual purpose. The old name implied it was a full CRUD abstraction for storing chat history, when the actual intention is to provide chat history to an agent per run and store the results.

**Before:**
```csharp
public abstract class ChatMessageStore
{
    public abstract Task<ChatHistory> GetChatHistoryAsync(string conversationId);
    public abstract Task SaveChatHistoryAsync(string conversationId, ChatHistory history);
}

// Usage
var store = new InMemoryChatMessageStore();
var agent = new ChatClientAgent(new ChatClientAgentOptions
{
    ChatMessageStoreFactory = () => store
});
```

**After:**
```csharp
public abstract class ChatHistoryProvider
{
    public abstract Task<ChatHistory> GetChatHistoryAsync(string conversationId);
    public abstract Task SaveChatHistoryAsync(string conversationId, ChatHistory history);
}

// Usage
var provider = new InMemoryChatHistoryProvider();
var agent = new ChatClientAgent(new ChatClientAgentOptions
{
    ChatHistoryProviderFactory = () => provider
});
```

**Migration Guide:**
- Replace `ChatMessageStore` → `ChatHistoryProvider`
- Replace `InMemoryChatMessageStore` → `InMemoryChatHistoryProvider`
- Replace `CosmosChatMessageStore` → `CosmosChatHistoryProvider`
- Replace `WorkflowMessageStore` → `WorkflowChatHistoryProvider`
- Update property `ChatMessageStoreFactory` → `ChatHistoryProviderFactory`

**Files Changed**: 43 files across the .NET codebase

---

### 2. Simplified ag-ui Run Logic (Python)

**PR**: [#3322](https://github.com/microsoft/agent-framework/pull/3322)  
**Impact**: Medium - Changes to ag-ui run interfaces and MCP handling

This PR simplifies the ag-ui run logic and fixes several bugs related to MCP (Model Context Protocol) and Anthropic client issues. The changes affect how runs are executed and how tools are invoked.

**Key Changes:**
- Simplified run execution flow in `_run.py`
- Fixed MCP tool invocation bugs
- Resolved Anthropic client compatibility issues
- Improved message adapter handling

**Before:**
```python
# Complex run logic with multiple branching paths
async def execute_run(self, agent, messages):
    # Multiple validation steps
    # Complex state management
    # Nested error handling
    pass
```

**After:**
```python
# Streamlined run logic with clearer flow
async def execute_run(self, agent, messages):
    # Simplified validation
    # Clear state transitions
    # Unified error handling
    pass
```

**Migration Notes:**
- Review custom run implementations for compatibility
- Update MCP tool integrations to use new argument filtering
- Test Anthropic client integrations thoroughly

---

### 3. Improved Agent Hosting in Workflows (.NET)

**PR**: [#3142](https://github.com/microsoft/agent-framework/pull/3142)  
**Impact**: High - Major refactoring of workflow agent hosting

This comprehensive update improves how agents are hosted within workflows, introducing `AIAgentHostOptions` for fine-grained control over agent behavior.

**New Configuration Class:**
```csharp
public class AIAgentHostOptions
{
    // Control whether events are emitted
    public bool EmitEvents { get; set; } = true;
    
    // Enable request interception
    public bool InterceptRequests { get; set; } = false;
    
    // Allow role reassignment
    public bool AllowRoleReassignment { get; set; } = false;
    
    // Forward messages to workflow
    public bool ForwardMessages { get; set; } = true;
}
```

**Before:**
```csharp
// Simple boolean flag
builder.AddAgent(
    "myAgent", 
    agent,
    emitEvents: true
);
```

**After:**
```csharp
// Rich configuration object
builder.AddAgent(
    "myAgent", 
    agent,
    new AIAgentHostOptions
    {
        EmitEvents = true,
        InterceptRequests = true,
        AllowRoleReassignment = false,
        ForwardMessages = true
    }
);
```

**New Features:**
- **Request Interception**: Intercept and handle external requests from agents
- **Port Handlers**: Register dynamic port handlers for routing
- **Turn Continuation**: Better control over turn-based execution
- **Configurable Event Emission**: Fine-tune which events are emitted

**Additional Changes:**
- Added `AddPortHandler` method to `RouteBuilder`
- New `ProcessTurnMessagesAsync` helper in `ChatProtocolExecutor`
- Added `TryRegisterPort` for dynamic port registration
- Improved lifecycle management with separate binding contexts

---

## Major Updates

### 4. Azure AI Reasoning Config Support (Python)

**PR**: [#3403](https://github.com/microsoft/agent-framework/pull/3403)

Added support for reasoning configuration in the Azure AI Client, enabling advanced reasoning capabilities for AI models.

**New Feature:**
```python
from agent_framework_azure_ai import AzureAIClient

client = AzureAIClient(
    endpoint="https://your-endpoint.azure.com",
    api_key="your-api-key",
    reasoning_config={
        "enable_reasoning": True,
        "max_reasoning_steps": 10,
        "reasoning_strategy": "chain_of_thought"
    }
)
```

**Benefits:**
- Enable step-by-step reasoning for complex tasks
- Configure reasoning depth and strategy
- Better control over model thinking process

---

### 5. Override ChatMessageStore Per Agent Run (.NET)

**PR**: [#3330](https://github.com/microsoft/agent-framework/pull/3330)

Allows overriding the ChatHistoryProvider (formerly ChatMessageStore) on a per-run basis, enabling more flexible chat history management.

**New Extension Methods:**
```csharp
// Store typed objects in AdditionalProperties
public static void Set<T>(this AdditionalPropertiesDictionary dict, T value);
public static T? Get<T>(this AdditionalPropertiesDictionary dict);
```

**Usage:**
```csharp
var customProvider = new CustomChatHistoryProvider();

// Override for this specific run
var options = new ChatOptions();
options.AdditionalProperties.Set(customProvider);

var response = await agent.InvokeAsync("Hello", options);
```

**Use Cases:**
- A/B testing different history storage strategies
- Per-user custom history providers
- Temporary history for sensitive conversations

---

### 6. Prefer Runtime kwargs for conversation_id (Python)

**PR**: [#3312](https://github.com/microsoft/agent-framework/pull/3312)

Improved the OpenAI Responses client to prefer runtime `kwargs` for `conversation_id`, allowing more flexible conversation management.

**Before:**
```python
# conversation_id was fixed at client initialization
client = OpenAIResponsesClient(conversation_id="conv-123")
# Could not change conversation_id per call
```

**After:**
```python
client = OpenAIResponsesClient()

# Can specify conversation_id per call
response = await client.create(
    messages=messages,
    conversation_id="conv-123"  # Runtime override
)

# Or use default from client
response = await client.create(messages=messages)
```

**Benefits:**
- More flexible conversation routing
- Easier multi-tenant implementations
- Dynamic conversation switching

---

## Minor Updates and Bug Fixes

### 7. Filter Internal Args in MCP Tools (Python)

**PR**: [#3292](https://github.com/microsoft/agent-framework/pull/3292)

Fixed a bug where internal framework arguments were being passed to MCP (Model Context Protocol) tools, causing invocation failures.

**Fix:**
```python
# Filter out internal arguments before passing to MCP tools
def invoke_mcp_tool(tool_name: str, **kwargs):
    # Remove internal args like _context, _metadata, etc.
    clean_kwargs = {
        k: v for k, v in kwargs.items() 
        if not k.startswith('_')
    }
    return mcp_tool.invoke(**clean_kwargs)
```

**Impact**: MCP tool integrations now work reliably without manual argument filtering.

---

### 8. Azure AI Image Generation Tool Mapping (Python)

**PR**: [#3263](https://github.com/microsoft/agent-framework/pull/3263)

Added proper mapping between `HostedImageGenerationTool` and `ImageGenTool` in the Azure AI package.

**Implementation:**
```python
# Automatic tool mapping
from agent_framework_azure_ai import AzureAIClient

client = AzureAIClient(...)

# HostedImageGenerationTool is now automatically mapped to ImageGenTool
agent = client.create_agent(
    tools=[HostedImageGenerationTool()]  # Works seamlessly
)
```

**Benefits:**
- Simplified tool registration
- Better Azure AI integration
- Consistent tool interfaces

---

### 9. OpenAI Content Types Tests (Python)

**PR**: [#3259](https://github.com/microsoft/agent-framework/pull/3259)

Added comprehensive unit tests for OpenAI content types, improving test coverage and reliability.

**Test Coverage:**
- Text content handling
- Image content validation
- Audio content processing
- Multi-modal content combinations
- Error handling for invalid content types

**Result**: Improved test coverage from 82% to 84%

---

### 10. Update Package Versions (Python)

**PR**: [#3421](https://github.com/microsoft/agent-framework/pull/3421)

Updated Python package versions to latest compatible versions:
- Updated dependency versions for security patches
- Aligned package versions across the monorepo
- Fixed version conflicts

---

### 11. Merge main into feature-durabletask Branch

**PR**: [#3385](https://github.com/microsoft/agent-framework/pull/3385)

Merged the latest changes from `main` into the `feature-durabletask` branch, keeping the Durable Task integration work up-to-date.

**Scope**: Both .NET and Python components

---

### 12. Update Build and Format Instructions

**PR**: [#3412](https://github.com/microsoft/agent-framework/pull/3412)

Updated documentation to require automatic building and formatting before commits.

**New Requirements:**
```bash
# Before committing
dotnet build
dotnet format

# Or for Python
python -m black .
python -m ruff check .
```

---

## Summary

This release brings significant improvements to the Microsoft Agent Framework with a focus on:

1. **Better API Clarity**: The rename from `ChatMessageStore` to `ChatHistoryProvider` more accurately reflects the component's purpose
2. **Enhanced Workflow Capabilities**: New `AIAgentHostOptions` provides fine-grained control over agent behavior in workflows
3. **Improved Flexibility**: Per-run overrides and runtime configuration options enable more dynamic agent applications
4. **Bug Fixes**: Critical fixes for MCP tool invocation and ag-ui execution
5. **Better Testing**: Increased test coverage and comprehensive content type testing

### Recommended Actions

For .NET developers:
- Update all references from `ChatMessageStore` to `ChatHistoryProvider`
- Review workflow agent hosting code to leverage new `AIAgentHostOptions`
- Test per-run ChatHistoryProvider overrides if needed

For Python developers:
- Update ag-ui integrations following the simplified run logic
- Test MCP tool integrations with the new argument filtering
- Review OpenAI Responses client usage for conversation_id handling

### Testing Considerations

- All 12 PRs include comprehensive tests
- Python test coverage maintained at 84%
- .NET tests updated to reflect breaking changes
- Integration tests verify backward compatibility where possible

---

**Contributors**: @westey-m, @moonbox3, @giles17, @lokitoth, @larohra  
**Total Files Changed**: 100+ files across .NET and Python  
**Lines Changed**: 5000+ additions, 2000+ deletions  

For detailed code changes, visit the individual PRs linked above.
