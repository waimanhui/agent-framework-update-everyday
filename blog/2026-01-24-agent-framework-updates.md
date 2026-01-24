# Microsoft Agent Framework Updates - January 23, 2026

A comprehensive roundup of all PRs merged on January 23, 2026, to the [microsoft/agent-framework](https://github.com/microsoft/agent-framework) repository. This was an exceptionally productive day with **21 PRs merged**, including several breaking changes and major improvements across both .NET and Python implementations.

## 🔴 Breaking Changes

### .NET: ChatMessageStore Renamed to ChatHistoryProvider ([#3375](https://github.com/microsoft/agent-framework/pull/3375))

**Impact:** This is a significant naming change that affects how developers interact with chat history management.

**Motivation:** The previous name `ChatMessageStore` created confusion, with many developers assuming it was a full CRUD abstraction for storing chat history. The reality is that it's designed to provide `ChatHistory` to an agent per run and store the results.

**Changes:**
- Renamed `ChatMessageStore` to `ChatHistoryProvider` throughout the codebase
- Updated `ChatMessageStoreExtensions` to `ChatHistoryProviderExtensions`
- All samples and documentation updated accordingly

```csharp
// Before
public class InMemoryChatMessageStore : IChatMessageStore
{
    // Implementation
}

// After
public class InMemoryChatHistoryProvider : IChatHistoryProvider
{
    // Implementation
}
```

This change better reflects the actual purpose: providing chat history context rather than being a general-purpose storage abstraction.

---

### .NET: Improved Agent Hosting in Workflows ([#3142](https://github.com/microsoft/agent-framework/pull/3142))

**Impact:** Major enhancement to how agents are hosted inside workflows, with breaking changes to executor interfaces.

**Motivation:** The initial implementation had rough edges requiring custom executors for orchestrations, leading to behavioral inconsistencies as fixes accumulated. This PR also adds Human-in-the-Loop (HIL) support.

**Key Changes:**
- New `AIAgentHostOptions` for configurable agent hosting
- Enhanced `ChatProtocolExecutor` with better request/response handling
- Introduction of `ExternalResponse` and `IExternalRequestContext` for external interactions
- New `AIContentExternalHandler` for processing external content
- Improved `RouteBuilder` with 125 new lines for better routing logic

```csharp
// New AIAgentHostOptions for better configuration
public class AIAgentHostOptions
{
    public bool EnableHumanInLoop { get; set; }
    public TimeSpan? Timeout { get; set; }
    // ... additional configuration options
}

// Enhanced ChatProtocolExecutor
public class ChatProtocolExecutor : Executor
{
    public async Task<ExternalResponse> HandleExternalRequestAsync(
        IExternalRequestContext context,
        CancellationToken cancellationToken)
    {
        // New external request handling logic
    }
}
```

The changes significantly improve the workflow execution model and make agent orchestrations more maintainable.

---

### Python: AG-UI Orchestration Refactor ([#3322](https://github.com/microsoft/agent-framework/pull/3322))

**Impact:** Major breaking change that simplifies the AG-UI run logic and removes custom confirmation strategies.

**Breaking Change:** The `confirmation_strategy` argument is no longer passed into orchestrator functions.

**Changes:**
- Removed 802 lines from `_orchestrators.py` (entire file deleted)
- Removed 589 lines from `_events.py` (entire file deleted)
- Removed 217 lines from `_confirmation_strategies.py` (entire file deleted)
- Removed 108 lines from `_state_manager.py` (entire file deleted)
- **Added 963 new lines in `_run.py`** - a complete rewrite of the orchestration logic
- Fixed MCP (Model Context Protocol) bugs
- Fixed Anthropic client issues in AG-UI

**Motivation:** The existing code was growing in complexity and brittleness with bespoke state handling. This refactor consolidates orchestration, simplifies state transitions, and removes ad hoc management paths.

```python
# Before: Complex orchestration with confirmation strategies
async def run_agent(
    agent: Agent,
    confirmation_strategy: ConfirmationStrategy,
    **kwargs
):
    # Complex state management across multiple files
    pass

# After: Simplified orchestration
async def run_agent(agent: Agent, **kwargs):
    # Streamlined execution in _run.py
    pass
```

The refactor makes AG-UI more maintainable and reduces the cognitive load for contributors.

---

### .NET: Subworkflow Fixes for Chat Protocol and Checkpointing ([#3240](https://github.com/microsoft/agent-framework/pull/3240))

**Breaking Changes:** 
- Subworkflows can no longer be used without explicitly attaching checkpoint support
- `ResetAsync()` implementation changes in `WorkflowHostExecutor`

**Issues Fixed:**
- Hang when using subworkflows with `ChatProtocol` and streaming execution
- Improper reset of `joinContext` during checkpoint restoration
- Subworkflows couldn't be used without enabling checkpointing

This PR ensures subworkflows work correctly with the chat protocol and state persistence features.

---

### .NET: CosmosDB Authentication Token Support ([#3250](https://github.com/microsoft/agent-framework/pull/3250))

**Breaking:** CosmosDB extension methods now require explicit authentication token credentials instead of using defaults.

**Motivation:** Default credentials may not be deterministic enough for production scenarios.

```csharp
// Before
services.AddCosmosChatHistoryProvider(cosmosDbEndpoint, databaseName);

// After  
services.AddCosmosChatHistoryProvider(
    cosmosDbEndpoint, 
    databaseName, 
    tokenCredential);
```

---

## 🐛 Bug Fixes

### Python: Fix conversation_id Propagation in OpenAI Responses Client ([#3312](https://github.com/microsoft/agent-framework/pull/3312))

**Issue:** Stale tool-call routing due to using stale `conversation_id` values.

**Fix:** Runtime `kwargs` now take precedence over instance-level `conversation_id`, ensuring the freshest conversation context is used.

```python
# In OpenAI Responses Client
def get_conversation_id(self, **kwargs):
    # Prefer runtime kwargs over instance variable
    return kwargs.get('conversation_id', self._conversation_id)
```

Resolves issue [#3304](https://github.com/microsoft/agent-framework/issues/3304).

---

### Python: Filter Internal Args for MCP Tools ([#3292](https://github.com/microsoft/agent-framework/pull/3292))

**Issue:** When Azure AI returns a response with `conversation_id`, it was being incorrectly forwarded to MCP tools that accept `**kwargs`, causing errors like `conversation_id='resp_0aee1...'`.

**Fix:** Internal arguments are now filtered out before passing kwargs to tools.

```python
# Before: conversation_id leaked to tools
async def call_tool(tool, **kwargs):
    result = await tool.invoke(**kwargs)  # conversation_id included!

# After: internal args filtered
async def call_tool(tool, **kwargs):
    # Filter out internal framework arguments
    filtered_kwargs = {
        k: v for k, v in kwargs.items() 
        if k not in ['conversation_id', 'thread_id', ...]
    }
    result = await tool.invoke(**filtered_kwargs)
```

---

### Python: Azure Functions MCP Tool Routing Fix ([#3339](https://github.com/microsoft/agent-framework/pull/3339))

**Issue:** MCP tool invocations weren't routing to the correct agent based on thread ID.

**Fix:** Properly route tool calls to the correct agent instance using thread-based routing.

---

### Python: Azure AI Image Generation Mapping ([#3263](https://github.com/microsoft/agent-framework/pull/3263))

**Issue:** Azure AI image generation sample was broken due to missing handler for `HostedImageGenerationTool`.

**Fixes:**
- Added `HostedImageGenerationTool` to `ImageGenTool` mapping
- Updated sample to use `ImageGenerationToolResultContent` instead of `DataContent`
- Changed image save logic

```python
# Added to Azure AI integration layer
def map_hosted_tool(tool: HostedImageGenerationTool) -> ImageGenTool:
    return ImageGenTool(
        name=tool.name,
        description=tool.description,
        # ... mapping logic
    )

# Updated sample
async def handle_image_result(result):
    # Before: Used generic DataContent
    data = result.data
    
    # After: Use specific ImageGenerationToolResultContent
    image_content = ImageGenerationToolResultContent.from_result(result)
    image_data = image_content.image_data
```

---

### Python: Checkpoint Deserialization Security Fix ([#3243](https://github.com/microsoft/agent-framework/pull/3243))

**Security Issue:** Reserved checkpoint markers (`__af_model__` and `__af_dataclass__`) could be spoofed by arbitrary dicts, causing incorrect type instantiation.

**Fix:** Added validation during deserialization:
- Verify `DATACLASS_MARKER` classes are actually dataclass types
- Verify `MODEL_MARKER` classes implement the model protocol
- Prevent marker spoofing attacks

```python
def deserialize_checkpoint(data: dict):
    if '__af_dataclass__' in data:
        cls = data['__af_dataclass__']
        # NEW: Verify it's actually a dataclass
        if not is_dataclass(cls):
            raise SecurityError(f"{cls} is not a valid dataclass")
    
    if '__af_model__' in data:
        cls = data['__af_model__']
        # NEW: Verify it implements model protocol
        if not implements_model_protocol(cls):
            raise SecurityError(f"{cls} is not a valid model")
```

This prevents potential security exploits through checkpoint tampering.

---

## ✨ New Features

### Python: Reasoning Config Support for Azure AI Client ([#3403](https://github.com/microsoft/agent-framework/pull/3403))

**Feature:** Added support for OpenAI reasoning models configuration in `AzureAIProjectAgentProvider`.

**Usage:**
```python
from agent_framework_azure_ai import AzureAIClient

client = AzureAIClient(
    project_endpoint="https://...",
    credential=credential,
    reasoning_config={
        "effort": "high",  # or "medium", "low"
        "max_reasoning_tokens": 10000
    }
)
```

Includes a new sample: `azure_ai_with_reasoning.py` demonstrating reasoning model usage.

---

### .NET: Per-Agent Run ChatHistoryProvider Override ([#3330](https://github.com/microsoft/agent-framework/pull/3330))

**Feature:** Allow overriding the ChatHistoryProvider per agent run via `AdditionalProperties`.

**Use Case:** Different runs of the same agent might need different history sources (e.g., multi-tenant scenarios, testing).

```csharp
// New extension methods in AdditionalPropertiesExtensions
var additionalProps = new Dictionary<string, object>
{
    { "ChatHistoryProvider", customHistoryProvider },
    { "ConversationId", "conversation-123" }
};

var result = await agent.RunAsync(
    userMessage, 
    additionalProperties: additionalProps);
```

Also includes:
- New `AdditionalPropertiesExtensions.cs` with 99 lines of helper methods
- 490 lines of new tests in `AdditionalPropertiesExtensionsTests.cs`
- Moved 296 lines of chat history tests to dedicated `ChatClientAgent_ChatHistoryManagementTests.cs`

---

### .NET & Python: Executor Source Generation for Workflows ([#3131](https://github.com/microsoft/agent-framework/pull/3131))

**Feature:** New Roslyn source generator for compile-time route configuration using `[MessageHandler]` attribute.

**Benefits:**
- Compile-time route validation
- No runtime reflection overhead
- Better IDE support and autocomplete
- Type-safe executor routing

```csharp
// Declarative routing with source generation
public class MyWorkflowExecutor : Executor
{
    [MessageHandler("user_message")]
    public async Task<Response> HandleUserMessage(UserMessage msg)
    {
        // Handler implementation
        // Routes are generated at compile time!
    }
    
    [MessageHandler("tool_call")]
    public async Task<Response> HandleToolCall(ToolCall msg)
    {
        // Another handler
    }
}
```

The source generator creates routing infrastructure automatically, eliminating the need for manual registration or `ReflectingExecutor` (which will be obsoleted in future PRs).

---

### .NET: Expose Executor Binding Metadata from Workflows ([#3389](https://github.com/microsoft/agent-framework/pull/3389))

**Feature:** Workflows now expose executor binding metadata for runtime message routing.

**Motivation:** Required for Durable Task support in workflows - the orchestration runner needs access to binding metadata to correctly route messages.

**Parity:** The Python implementation already exposed this; .NET now matches that functionality.

---

## 📚 Documentation & Samples

### Update Build and Format Instructions ([#3412](https://github.com/microsoft/agent-framework/pull/3412))

**Change:** Updated `.github/copilot-instructions.md` to require automatic building and formatting.

**Motivation:** Copilot was often creating code that failed to build or had formatting errors.

```markdown
# Added to copilot instructions:
- Always build the code after making changes
- Always format the code before committing
- Verify no build errors or warnings
```

---

### .NET: Sample Fixes ([#3270](https://github.com/microsoft/agent-framework/pull/3270))

Fixed issues in samples reported in [#3269](https://github.com/microsoft/agent-framework/issues/3269), including adjustments to make examples work correctly with recent framework changes.

---

### .NET: Feature Collections ADR ([#3332](https://github.com/microsoft/agent-framework/pull/3332))

Added Architecture Decision Record (ADR) for feature collections pattern - a 423-line document explaining the design philosophy and usage patterns.

---

## 🧪 Testing & Quality

### Python: Comprehensive OpenAI Content Types Tests ([#3259](https://github.com/microsoft/agent-framework/pull/3259))

**Added:** 948 lines of new unit tests across three test files:
- `test_openai_assistants_client.py` (+75 lines)
- `test_openai_chat_client.py` (+426 lines)  
- `test_openai_responses_client.py` (+447 lines)

Significantly improved test coverage for content handling scenarios in OpenAI clients.

---

### .NET: Improved Unit Test Coverage for OpenAI Package ([#3349](https://github.com/microsoft/agent-framework/pull/3349))

**Before:** 66.6% line coverage / 50% branch coverage
**Target:** 85% coverage

**Added:** 47 new unit tests covering previously untested classes:
- `AsyncStreamingResponseUpdateCollectionResult` (was 0%)
- `StreamingUpdatePipelineResponse` (was 13.3%)
- `AgentResponseExtensions` (was 50%)
- `AIAgentWithOpenAIExtensions` (was 50%)

This brings the OpenAI package closer to the 85% coverage requirement.

---

## 📦 Maintenance

### Python: Package Version Updates ([#3421](https://github.com/microsoft/agent-framework/pull/3421))

Updated Python package versions across all 19 packages in the monorepo, including changelog updates documenting recent changes.

---

### Merge main into feature-durabletask Branch ([#3385](https://github.com/microsoft/agent-framework/pull/3385))

Integration PR merging main branch improvements into the durable task feature branch, including:
- Azure Functions integration setup updates
- New ADRs (Architecture Decision Records)
- 3 new Durable Agent samples
- Dependency updates

---

## 📊 Summary Statistics

- **Total PRs Merged:** 21
- **Breaking Changes:** 5 major
- **Lines Added:** ~3,500+
- **Lines Removed:** ~2,800+
- **New Test Lines:** ~1,400+
- **Bug Fixes:** 6
- **New Features:** 5
- **Documentation Updates:** 3

## 🎯 Key Themes

1. **Simplification:** Major refactoring efforts to reduce complexity (AG-UI orchestration, workflow hosting)
2. **Security:** Checkpoint deserialization hardening
3. **Better Naming:** ChatMessageStore → ChatHistoryProvider for clarity
4. **Testing:** Significant investment in test coverage improvements
5. **Production Readiness:** CosmosDB auth tokens, better error handling
6. **Developer Experience:** Source generators, better IDE support, clearer APIs

## 🔮 Looking Ahead

Several PRs mention follow-up work:
- Durable Task support landing in upcoming PRs
- Obsoleting `ReflectingExecutor` once source generator adoption is complete
- Potential full CRUD chat history abstraction in the future
- More samples showcasing new workflow capabilities

---

*This blog post covers all 21 PRs merged to microsoft/agent-framework on January 23, 2026. For detailed implementation specifics, please refer to the individual PRs linked throughout.*
