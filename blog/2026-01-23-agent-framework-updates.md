# Microsoft Agent Framework Updates - January 23, 2026

## Overview

Yesterday saw a flurry of significant updates to the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework), with **12 pull requests** merged spanning both .NET and Python implementations. These changes include major breaking changes, new features, bug fixes, and substantial refactoring efforts that improve the framework's capabilities and developer experience.

## Breaking Changes

### .NET: ChatMessageStore → ChatHistoryProvider Rename ([PR #3375](https://github.com/microsoft/agent-framework/pull/3375))

**Author:** westey-m  
**Impact:** 45 files changed, +1037 -904

One of the most significant changes is the renaming of `ChatMessageStore` to `ChatHistoryProvider`. This breaking change addresses widespread confusion about the abstraction's purpose.

**Why the change?**  
The name `ChatMessageStore` led many developers to assume it was a full CRUD abstraction for storing chat history. However, its actual intention is to provide `ChatHistory` to an Agent per run and store the results.

**Migration Example:**

```csharp
// Before
ChatMessageStoreFactory = (ctx, ct) => new ValueTask<ChatMessageStore>(
    new InMemoryChatMessageStore(ctx.SerializedState, ctx.JsonSerializerOptions)
        .WithAIContextProviderMessageRemoval()
)

// After
ChatHistoryProviderFactory = (ctx, ct) => new ValueTask<ChatHistoryProvider>(
    new InMemoryChatHistoryProvider(ctx.SerializedState, ctx.JsonSerializerOptions)
        .WithAIContextProviderMessageRemoval()
)
```

The implementation may still use a full CRUD abstraction internally for loading and saving messages, but the interface name now better reflects its actual purpose.

### .NET: Improved Agent Hosting in Workflows ([PR #3142](https://github.com/microsoft/agent-framework/pull/3142))

**Author:** lokitoth  
**Impact:** 37 files changed, +1884 -310

This breaking change overhauls how Agents are hosted inside Workflows, addressing rough edges in the initial implementation.

**Key Improvements:**
- Eliminates the need for custom Executors when implementing Orchestrations
- Adds proper support for Human-in-the-Loop (HIL) scenarios
- Reduces inconsistencies in behavior across different hosting scenarios
- Consolidates agent workflow building logic

**New Features:**
- Introduced `AIAgentHostOptions` for configurable agent hosting
- Enhanced `ChatProtocolExecutor` with better state management
- Improved edge mapping in workflow execution

This change makes it significantly easier to build complex multi-agent workflows with consistent behavior.

### Python: AG-UI Orchestration Refactor ([PR #3322](https://github.com/microsoft/agent-framework/pull/3322))

**Author:** moonbox3  
**Impact:** 42 files changed, +2789 -5395

A massive refactoring of the AG-UI orchestration layer that removes over 5,000 lines of code while adding cleaner, more maintainable logic.

**Breaking Changes:**
- **Removed confirmation strategies** - The `confirmation_strategy` argument is no longer supported
- Consolidated state management
- Simplified orchestration flow

**What was fixed:**
- MCP (Model Context Protocol) bug fixes
- Anthropic client issues in ag-ui
- Complex state handling that was growing increasingly brittle

**Deleted Files:**
```python
# Removed files indicate simplified architecture
_confirmation_strategies.py  # -217 lines
_events.py                   # -589 lines
_state_manager.py            # -108 lines
```

Despite removing confirmation strategies, the core orchestration is now more robust and easier to maintain.

## New Features

### Python: Reasoning Configuration Support for Azure AI ([PR #3403](https://github.com/microsoft/agent-framework/pull/3403))

**Author:** moonbox3  
**Impact:** 7 files changed, +424 -196

Azure AI now supports reasoning configuration for OpenAI reasoning models (like GPT-4 with reasoning capabilities).

**Example Usage:**

```python
from agent_framework.azure import AzureAIProjectAgentProvider
from azure.ai.projects.models import Reasoning
from azure.identity.aio import AzureCliCredential

async with (
    AzureCliCredential() as credential,
    AzureAIProjectAgentProvider(credential=credential) as provider,
):
    agent = await provider.create_agent(
        name="ReasoningWeatherAgent",
        instructions="You are a helpful weather agent who likes to understand the underlying physics.",
        default_options={
            "reasoning": Reasoning(effort="medium", summary="concise")
        }
    )

    result = await agent.run("How does the Bernoulli effect work?")
    
    for msg in result.messages:
        for content in msg.contents:
            if content.type == "text_reasoning":
                print(f"[Reasoning]: {content.text}")
            elif content.type == "text":
                print(f"[Answer]: {content.text}")
```

**Key Features:**
- Configure reasoning effort level (`low`, `medium`, `high`)
- Control summary verbosity (`concise`, `detailed`)
- Access reasoning content separately from answers
- Full support for both streaming and non-streaming responses

The implementation properly handles the reasoning configuration through the Azure AI Project provider and separates reasoning traces from final answers.

### .NET: Per-Run ChatHistoryProvider Override ([PR #3330](https://github.com/microsoft/agent-framework/pull/3330))

**Author:** westey-m  
**Impact:** 9 files changed, +1002 -321

Developers can now override the `ChatHistoryProvider` on a per-run basis using `AdditionalProperties`, providing much more flexibility in conversation management.

**Benefits:**
- Different conversation contexts for different runs
- Better testing capabilities
- More flexible multi-tenant scenarios
- Improved chat history management testing

All ChatMessageStore (now ChatHistoryProvider) and ConversationId tests were moved to a separate test file to improve code organization.

## Bug Fixes and Improvements

### Python: MCP Tool Argument Filtering ([PR #3292](https://github.com/microsoft/agent-framework/pull/3292))

**Author:** moonbox3  
**Impact:** 4 files changed, +278 -190

Fixed a critical bug where internal arguments like `conversation_id` were incorrectly passed to MCP (Model Context Protocol) tools.

**The Problem:**
```python
# Azure AI returns conversation_id in response
# This was being forwarded to tools accepting **kwargs
mcp_tool(conversation_id='resp_0aee1...')  # ❌ Unexpected argument!
```

**The Solution:**
Internal arguments are now filtered out before being passed to MCP tools, preventing unexpected parameter errors.

### Python: Conversation ID Runtime Preference ([PR #3312](https://github.com/microsoft/agent-framework/pull/3312))

**Author:** giles17  
**Impact:** 2 files changed, +20 -2

Fixed stale tool-call routing by preferring the freshest `conversation_id` propagated via runtime `kwargs` instead of stale cached values.

### Python: Azure AI Image Generation Tool Mapping ([PR #3263](https://github.com/microsoft/agent-framework/pull/3263))

**Author:** giles17  
**Impact:** 2 files changed, +64 -10

Added missing handler for `HostedImageGenerationTool` in the Azure AI integration layer.

**Fixes:**
- Maps `HostedImageGenerationTool` to `ImageGenTool`
- Updated samples to use `ImageGenerationToolResultContent` instead of `DataContent`
- Corrected image save logic in samples

## Testing and Quality

### Python: OpenAI Content Types Test Coverage ([PR #3259](https://github.com/microsoft/agent-framework/pull/3259))

**Author:** giles17  
**Impact:** 3 files changed, +948 additions (new tests)

Added comprehensive unit tests for OpenAI content types across three test files, significantly improving test coverage for content handling scenarios in the agent framework's OpenAI clients.

### Documentation: Build and Format Requirements ([PR #3412](https://github.com/microsoft/agent-framework/pull/3412))

**Author:** westey-m  
**Impact:** 1 file changed, +2 additions

Updated contribution guidelines to require automatic building and formatting after any changes, reducing the frequency of code that fails to build or has formatting errors.

## Maintenance

### Python: Package Version Updates ([PR #3421](https://github.com/microsoft/agent-framework/pull/3421))

**Author:** giles17  
**Impact:** 21 files changed, +83 -45

Updated Python package versions across the framework to ensure compatibility and incorporate latest improvements.

### Branch Merge: main → feature-durabletask ([PR #3385](https://github.com/microsoft/agent-framework/pull/3385))

**Author:** larohra  
**Impact:** 552 files changed, +23577 -14363

Massive merge bringing main branch changes into the feature-durabletask branch, ensuring feature parity and preparing for durable task support.

## Migration Guide

### For .NET Developers

If you're using `ChatMessageStore`, update your code to use `ChatHistoryProvider`:

1. **Rename class references:**
   - `ChatMessageStore` → `ChatHistoryProvider`
   - `InMemoryChatMessageStore` → `InMemoryChatHistoryProvider`
   - `ChatMessageStoreFactory` → `ChatHistoryProviderFactory`

2. **Update workflow configurations** if you're hosting agents in workflows - review the new `AIAgentHostOptions` class for configuration options.

### For Python Developers

1. **Remove confirmation strategies** from AG-UI code - this feature has been removed
2. **Update reasoning model usage** to take advantage of the new `Reasoning` configuration
3. **Review MCP tool implementations** - ensure you're not relying on internal arguments like `conversation_id`

## Summary

January 23, 2026, brought significant improvements to the Microsoft Agent Framework:

- **3 breaking changes** that improve clarity and maintainability
- **2 major new features** including reasoning support and per-run history providers
- **5 important bug fixes** addressing MCP tools, conversation management, and image generation
- **2 quality improvements** with expanded test coverage and contribution guidelines

The framework continues to mature with better abstractions, more robust error handling, and improved developer experience. While some changes are breaking, they set the foundation for a more maintainable and powerful agent framework.

## Resources

- [Microsoft Agent Framework GitHub Repository](https://github.com/microsoft/agent-framework)
- [Contributing Guidelines](https://github.com/microsoft/agent-framework/blob/main/CONTRIBUTING.md)
- [Python Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples)
- [.NET Samples](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples)

---

*This blog post summarizes changes merged on January 23, 2026. For the most up-to-date information, please refer to the official repository.*
