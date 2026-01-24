# Microsoft Agent Framework Updates - January 23, 2026

Yesterday saw significant activity in the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) repository with **12 pull requests** merged, including several breaking changes that improve the framework's architecture and usability. Here's a comprehensive breakdown of what changed.

## 🔴 Breaking Changes

### 1. .NET: ChatMessageStore Renamed to ChatHistoryProvider ([PR #3375](https://github.com/microsoft/agent-framework/pull/3375))

**Author:** westey-m

One of the most significant changes addresses a common source of confusion in the framework. The `ChatMessageStore` class has been renamed to `ChatHistoryProvider` to better reflect its actual purpose.

**Why the change?**
Many developers assumed `ChatMessageStore` was a full CRUD abstraction for storing chat history. However, the intention was simply to provide `ChatHistory` to an Agent per run and store the results of the agent. A `ChatHistoryProvider` implementation may use a full CRUD abstraction for loading and saving messages, but this rename makes the distinction clearer.

**Migration example:**

```csharp
// Before
public class MyChatStore : ChatMessageStore
{
    public override Task<ChatHistory> LoadMessagesAsync(string conversationId)
    {
        // Load implementation
    }
}

// After
public class MyChatStore : ChatHistoryProvider
{
    public override Task<ChatHistory> LoadMessagesAsync(string conversationId)
    {
        // Load implementation (same logic)
    }
}
```

**Impact:** All files using `ChatMessageStore` need to be updated to use `ChatHistoryProvider`. The functionality remains the same; only the naming has changed for clarity.

---

### 2. .NET: Improved Agent Hosting in Workflows ([PR #3142](https://github.com/microsoft/agent-framework/pull/3142))

**Author:** lokitoth

This PR significantly improves how Agents are hosted inside Workflows, addressing rough edges in the initial implementation that required developers to create custom Executors for orchestrations.

**Key improvements:**
- ✅ Added support for Human-in-the-Loop (HIL) and uninvoked FunctionCalls for hosted agents
- ✅ Added configurability for emitting streaming updates and the final combined response
- ✅ Added support for forwarding incoming conversation to make Handoffs easier
- ✅ Added support for overwriting other agents' ChatRole when invoking hosted agents
- ✅ Built internal-only support for direct ExternalRequest "raising" by Executor

**Breaking change:**
`AIAgentBinding` now contains `AIAgentHostOptions` rather than a simple boolean flag.

**Before:**
```csharp
var binding = new AIAgentBinding
{
    AgentName = "myAgent",
    IsHosted = true
};
```

**After:**
```csharp
var binding = new AIAgentBinding
{
    AgentName = "myAgent",
    HostOptions = new AIAgentHostOptions
    {
        EmitStreamingUpdates = true,
        EmitFinalResponse = true,
        ForwardConversation = true
    }
};
```

This provides much finer control over agent hosting behavior and eliminates inconsistencies that were cropping up in different executor implementations.

---

### 3. Python: Simplified AG-UI Run Logic ([PR #3322](https://github.com/microsoft/agent-framework/pull/3322))

**Author:** moonbox3

A major refactor of AG-UI (Agent Framework UI) that simplifies orchestration logic and fixes multiple bugs.

**What changed:**
- **Removed confirmation strategies** - The custom `confirmation_strategy` argument is no longer needed or passed into `AgentFrameworkAgent`
- Consolidated orchestration to reduce bespoke state handling
- Simplified state transitions
- Fixed MCP (Model Context Protocol) tool bugs
- Fixed Anthropic client issues in AG-UI

**Breaking change:**
```python
# Before
agent = AgentFrameworkAgent(
    name="my_agent",
    client=client,
    confirmation_strategy=MyConfirmationStrategy()  # ❌ No longer supported
)

# After  
agent = AgentFrameworkAgent(
    name="my_agent",
    client=client
    # confirmation_strategy removed
)
```

**Bugs fixed:**
- #3278, #3297, #3298, #3350, #3331

**Files removed:**
- `_confirmation_strategies.py` (217 lines)
- `_events.py` (589 lines)
- `_state_manager.py` (108 lines)

This cleanup removes over **900 lines of complex state management code**, making the codebase more maintainable.

---

## 🔧 Feature Enhancements

### 4. .NET: Per-Agent Run ChatHistoryProvider Override ([PR #3330](https://github.com/microsoft/agent-framework/pull/3330))

**Author:** westey-m

You can now override the `ChatHistoryProvider` on a per-run basis using `AdditionalProperties`:

```csharp
var result = await agent.RunAsync(
    userMessage: "Hello!",
    additionalProperties: new Dictionary<string, object>
    {
        { "ChatHistoryProvider", myCustomProvider },
        { "ConversationId", "unique-conversation-123" }
    }
);
```

This enables scenarios where different conversations need different storage backends without reconfiguring the entire agent.

---

### 5. Python: Azure AI Reasoning Config Support ([PR #3403](https://github.com/microsoft/agent-framework/pull/3403))

**Author:** moonbox3

Added support for the `reasoning` configuration parameter for OpenAI reasoning models when using `AzureAIProjectAgentProvider`:

```python
from agent_framework.azure_ai import AzureAIClient

client = AzureAIClient(
    project_id="my-project",
    reasoning={
        "effort": "high",  # or "low", "medium"
        "max_tokens": 1000
    }
)

# The reasoning config will be passed to models that support it
agent = AgentFrameworkAgent(
    name="reasoning_agent",
    client=client,
    model="o1-preview"  # OpenAI reasoning model
)
```

This unlocks the full capabilities of OpenAI's reasoning models (like o1) within the Azure AI framework.

---

### 6. Python: Azure AI Image Generation Tool Mapping ([PR #3263](https://github.com/microsoft/agent-framework/pull/3263))

**Author:** giles17

Fixed the Azure AI image generation sample by properly mapping `HostedImageGenerationTool` to `ImageGenTool`:

```python
from agent_framework.azure_ai import AzureAIClient
from agent_framework.tools import HostedImageGenerationTool
import tempfile
import os

# Configure the tool
image_tool = HostedImageGenerationTool(
    model="gpt-image-1",  # Updated from gpt-image-1-mini
    size="1024x1024",
    quality="standard"
)

agent = AgentFrameworkAgent(
    name="image_agent",
    client=AzureAIClient(project_id="my-project"),
    tools=[image_tool]
)

response = await agent.run("Generate an image of a sunset")

# Extract image data correctly
for content in response.content:
    if isinstance(content, ImageGenerationToolResultContent):
        image_data = content.data
        # Save to temp directory instead of script directory
        temp_dir = tempfile.gettempdir()
        image_path = os.path.join(temp_dir, "generated_image.png")
        with open(image_path, "wb") as f:
            f.write(image_data)
```

**Changes:**
- Added `HostedImageGenerationTool` → `ImageGenTool` mapping
- Updated to use `ImageGenerationToolResultContent` instead of generic `DataContent`
- Changed default save location to OS temp directory
- Corrected model name to `gpt-image-1`

---

## 🐛 Bug Fixes

### 7. Python: Fixed Conversation ID Propagation ([PR #3312](https://github.com/microsoft/agent-framework/pull/3312))

**Author:** giles17

Fixed stale tool-call routing by preferring the freshest `conversation_id` propagated via runtime `kwargs`:

```python
# The fix ensures conversation_id from runtime kwargs takes precedence
# over stale IDs, preventing routing issues in multi-turn conversations
async def _create_response(self, **kwargs):
    # Prefer runtime conversation_id over instance variable
    conversation_id = kwargs.get('conversation_id', self._conversation_id)
    # ... rest of implementation
```

---

### 8. Python: Filtered Internal Args from MCP Tools ([PR #3292](https://github.com/microsoft/agent-framework/pull/3292))

**Author:** moonbox3

When Azure AI returns a response with a `conversation_id`, it was incorrectly being forwarded to MCP (Model Context Protocol) tools:

```python
# Before: conversation_id leaked to tools
tool_result = await mcp_tool.call(**kwargs)  # ❌ includes conversation_id

# After: filtered out
INTERNAL_KWARGS = {'conversation_id', 'thread_id', 'agent_id'}
filtered_kwargs = {k: v for k, v in kwargs.items() if k not in INTERNAL_KWARGS}
tool_result = await mcp_tool.call(**filtered_kwargs)  # ✅ clean kwargs
```

This prevents MCP servers from receiving unexpected internal arguments like `conversation_id='resp_0aee1...'`.

---

### 9. Python: Added OpenAI Content Type Tests ([PR #3259](https://github.com/microsoft/agent-framework/pull/3259))

**Author:** giles17

Added comprehensive unit tests for OpenAI content types, improving test coverage for various content handling scenarios across the framework's OpenAI clients. This ensures better reliability when working with different message content types (text, images, function calls, etc.).

---

## 📚 Documentation & Tooling

### 10. Update Build and Format Instructions ([PR #3412](https://github.com/microsoft/agent-framework/pull/3412))

**Author:** westey-m

Updated contribution instructions to require automatic building and formatting after any code changes. This helps ensure that Copilot and other AI coding assistants produce code that passes build and formatting checks.

---

### 11. Python: Package Version Updates ([PR #3421](https://github.com/microsoft/agent-framework/pull/3421))

**Author:** giles17

Updated Python package versions to maintain compatibility and security.

---

### 12. Merge Main into Feature Branch ([PR #3385](https://github.com/microsoft/agent-framework/pull/3385))

**Author:** larohra

Merged `main` into the `feature-durabletask` branch to keep the durable task implementation in sync with the latest changes.

---

## 📊 Summary Statistics

- **Total PRs merged:** 12
- **Breaking changes:** 3
- **Bug fixes:** 4
- **New features:** 3
- **Documentation/Maintenance:** 2
- **Lines removed:** ~900+ (simplification)
- **Contributors:** 4 (giles17, westey-m, lokitoth, moonbox3, larohra)

## 🎯 Key Takeaways

1. **Better naming conventions** - The rename from `ChatMessageStore` to `ChatHistoryProvider` makes the framework's intentions clearer
2. **More flexible workflows** - Enhanced agent hosting in workflows with granular configuration options
3. **Cleaner architecture** - Removal of confirmation strategies and complex state management in AG-UI
4. **Better Azure AI integration** - Support for reasoning models and fixed image generation
5. **Bug fixes for production issues** - Conversation ID handling and MCP tool argument filtering

## ⚠️ Migration Guide

If you're upgrading to include yesterday's changes:

### For .NET developers:
1. Replace all `ChatMessageStore` references with `ChatHistoryProvider`
2. Update `AIAgentBinding` to use `AIAgentHostOptions` instead of boolean `IsHosted`
3. Test your workflow hosting scenarios

### For Python developers:
1. Remove `confirmation_strategy` from `AgentFrameworkAgent` initialization
2. Test MCP tool integrations (fixes were applied automatically)
3. Update image generation code if using Azure AI image tools
4. Verify conversation ID handling in multi-turn scenarios

---

**Full changelog:** [microsoft/agent-framework commits on Jan 23, 2026](https://github.com/microsoft/agent-framework/commits/main/?since=2026-01-23&until=2026-01-24)

**Join the discussion:** [Discussions](https://github.com/microsoft/agent-framework/discussions)
