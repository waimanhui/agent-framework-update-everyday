# Agent Framework Updates - February 23, 2026

On February 23, 2026, the Microsoft Agent Framework merged **11 pull requests**, bringing significant improvements across both .NET and Python implementations. This update includes **two breaking changes** affecting .NET developers, critical bug fixes for Python's OpenAI chat client and Claude agent, enhanced workflow support in the Python ag-ui package, and new Foundry Agents tool samples.

## ⚠️ BREAKING CHANGES

### 1. .NET: ChatClient Decorator for AIContextProviders

**PR**: [#4097](https://github.com/microsoft/agent-framework/pull/4097)  
**Impact**: High - Requires code changes for developers using AIContextProviders

The .NET SDK introduces a new ChatClient decorator pattern for calling `AIContextProviders`, fundamentally changing how context providers integrate with chat clients. This breaking change standardizes the way context is injected into agent conversations.

**What Changed:**

Previously, AIContextProviders were called through a different mechanism. The new decorator pattern provides a cleaner, more composable API that integrates seamlessly with the Microsoft.Extensions.AI `IChatClient` interface.

**Migration Guide:**

The new decorator allows you to wrap any `IChatClient` with context provider capabilities:

```csharp
// New approach with decorator
var chatClient = new OpenAIChatClient(apiKey, modelId);
var contextAwareChatClient = chatClient.AsIChatClientWithContextProviders(
    new[] { new MyCustomContextProvider() }
);

// Use the decorated client with agents
var agent = new ChatClientAgent(contextAwareChatClient);
```

**Benefits:**

- Clean separation of concerns
- Composable with other IChatClient decorators
- Consistent with .NET extension patterns
- Better testability through decorator isolation

### 2. Python: Hardened Streaming Semantics in ag-ui with Workflow Support

**PR**: [#3911](https://github.com/microsoft/agent-framework/pull/3911)  
**Impact**: Medium - Requires updates to ag-ui streaming implementations

The Python `ag-ui` package has undergone significant changes to support workflows and harden streaming semantics. This includes breaking changes to how streaming responses are handled and consumed.

**What Changed:**

The streaming API has been hardened to provide more reliable semantics when working with agent responses, especially in UI contexts. The changes ensure consistent behavior across different agent types (simple agents vs. workflows) and improve error handling during streaming operations.

**Key Improvements:**

1. **Workflow Support**: Full integration with the Agent Framework workflow system
2. **Unified Streaming**: Consistent streaming behavior across agent types
3. **Dynamic Handoff**: New demo showcasing dynamic agent handoff patterns

**New Workflow Integration:**

```python
from agent_framework.ag_ui import StreamingUIHandler
from agent_framework.workflows import Workflow

# Workflows now work seamlessly with ag-ui
workflow = Workflow(...)
ui_handler = StreamingUIHandler()

# Stream workflow execution to UI
async for update in workflow.run_async(streaming=True):
    await ui_handler.process_update(update)
```

**Dynamic Handoff Demo:**

The PR includes a comprehensive demo showing how agents can dynamically hand off conversations to specialized agents based on context:

```python
# Dynamic handoff pattern
class RouterAgent:
    async def handle_message(self, message: str):
        # Analyze message and route to appropriate specialist
        specialist = self.select_specialist(message)
        async for response in specialist.handle(message):
            yield response
```

## Major Updates

### Python: OpenAI Chat Client Compatibility Fixes

**PR**: [#4161](https://github.com/microsoft/agent-framework/pull/4161)  
**Impact**: Critical bug fixes for third-party OpenAI-compatible endpoints

This comprehensive update fixes multiple compatibility issues with third-party OpenAI-compatible endpoints and updates telemetry support for OpenTelemetry 0.4.14.

**1. System Message Content Flattening**

Some OpenAI-compatible endpoints (e.g., NVIDIA NIM, Foundry Local's Neutron backend) reject system messages when content is sent as a list of content parts instead of a plain string. The fix automatically flattens text-only content to strings while preserving multimodal content (text + images/audio) as lists.

```python
# Before: Some endpoints would reject this
messages = [
    {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]}
]

# After: Automatically flattened to string for text-only content
messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

# Multimodal content still uses list format (correct behavior)
messages = [
    {"role": "user", "content": [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "..."}}
    ]}
]
```

**2. OpenTelemetry 0.4.14 Compatibility**

Version 0.4.14 of `opentelemetry-semantic-conventions-ai` removed several `LLM_*` attributes from `SpanAttributes`. The update migrates to the new `gen_ai.*` string values:

```python
# Old attributes (removed in 0.4.14)
SpanAttributes.LLM_SYSTEM
SpanAttributes.LLM_REQUEST_MODEL
SpanAttributes.LLM_RESPONSE_MODEL
SpanAttributes.LLM_REQUEST_MAX_TOKENS
SpanAttributes.LLM_REQUEST_TEMPERATURE
SpanAttributes.LLM_REQUEST_TOP_P
SpanAttributes.LLM_TOKEN_TYPE

# New approach using OtelAttr enum
OtelAttr.REQUEST_MODEL = "gen_ai.request.model"
OtelAttr.RESPONSE_MODEL = "gen_ai.response.model"
OtelAttr.REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
OtelAttr.REQUEST_TEMPERATURE = "gen_ai.request.temperature"
OtelAttr.REQUEST_TOP_P = "gen_ai.request.top_p"
```

**3. Streaming Text Lost with Usage Data**

Some providers (e.g., Gemini) include both usage data and text content in the same streaming chunk. The early return on `chunk.usage` caused text and tool call parsing to be skipped. The fix processes usage alongside text/tool calls:

```python
# Fixed streaming logic
async for chunk in stream:
    # Process usage if present (don't return early)
    if chunk.usage:
        usage_data = process_usage(chunk.usage)
    
    # Also process text content in same chunk
    if chunk.choices and chunk.choices[0].delta.content:
        text_content = chunk.choices[0].delta.content
        yield text_content
    
    # And process tool calls
    if chunk.choices and chunk.choices[0].delta.tool_calls:
        tool_calls = process_tool_calls(chunk.choices[0].delta.tool_calls)
        yield tool_calls
```

**Issues Fixed:**
- [#1407](https://github.com/microsoft/agent-framework/issues/1407) - NVIDIA NIM system message rejection
- [#4160](https://github.com/microsoft/agent-framework/issues/4160) - OTel 0.4.14 compatibility
- [#4084](https://github.com/microsoft/agent-framework/issues/4084) - Foundry Local Neutron backend compatibility
- [#3434](https://github.com/microsoft/agent-framework/issues/3434) - Gemini streaming text loss

### Python: Fix Structured Output in ClaudeAgent

**PR**: [#4137](https://github.com/microsoft/agent-framework/pull/4137)  
**Impact**: Critical - Fixes broken structured output functionality

The Claude agent was silently discarding `structured_output` from streaming responses, making the `output_format` parameter completely unusable.

**Problem:**

When using Claude with structured output format, the schema-validated response was lost during streaming:

```python
# This would fail - structured_output was discarded
agent = ClaudeAgent(
    model="claude-3-opus-20240229",
    output_format=MyPydanticModel
)

response = await agent.run_async("Generate user data")
# response.value was None instead of MyPydanticModel instance
```

**Solution:**

The fix captures `structured_output` from `ResultMessage` in the `_get_stream()` method and propagates it to `AgentResponse.value` via a custom finalizer:

```python
class ClaudeAgent:
    async def _get_stream(self, messages, options):
        structured_output = None
        
        async for update in self._stream_messages(messages, options):
            if isinstance(update, ResultMessage):
                structured_output = update.structured_output
            yield update
        
        # Finalize with structured output
        if structured_output:
            yield AgentResponse.from_updates(
                updates=updates,
                value=structured_output
            )
```

**Now works correctly:**

```python
from pydantic import BaseModel

class UserData(BaseModel):
    name: str
    age: int
    email: str

agent = ClaudeAgent(
    model="claude-3-opus-20240229",
    output_format=UserData
)

response = await agent.run_async("Generate sample user data")
print(response.value)  # UserData instance with validated fields
```

**Issue Fixed:** [#4095](https://github.com/microsoft/agent-framework/issues/4095)

### .NET: Simplified Store=False API for OpenAI Responses

**PR**: [#4124](https://github.com/microsoft/agent-framework/pull/4124)  
**Impact**: Developer experience improvement

Previously, creating agents with `store=false` for the OpenAI Responses API required a verbose "break glass" approach using `RawRepresentationFactory`. The new `AsIChatClientWithStoredOutputDisabled()` extension method provides a clean, fluent API.

**Before (verbose approach):**

```csharp
var chatOptions = new ChatOptions
{
    RawRepresentationFactory = async (messages) =>
    {
        var request = new CreateChatCompletionRequest
        {
            Model = "gpt-4",
            Messages = messages.ToOpenAIMessages(),
            Store = false  // Hidden deep in the factory
        };
        return await client.CreateChatCompletionAsync(request);
    }
};

var agent = new ChatClientAgent(chatClient, chatOptions);
```

**After (simplified API):**

```csharp
var chatClient = new OpenAIChatClient(apiKey, "gpt-4")
    .AsIChatClientWithStoredOutputDisabled();

var agent = new ChatClientAgent(chatClient);
```

**Benefits:**

- Clear intent in code
- Discoverable through IntelliSense
- Chainable with other IChatClient extensions
- Encapsulates complexity

**Sample code** demonstrating the new API has been added to `GettingStarted/AgentProviders/Agent_With_AzureOpenAIResponses/Program.cs`.

**Issue Fixed:** [#1118](https://github.com/microsoft/agent-framework/issues/1118)

### .NET: Fix Structured Output with Function Middleware

**PR**: [#4179](https://github.com/microsoft/agent-framework/pull/4179)  
**Impact**: Bug fix for agents using function middleware

The `FunctionInvocationDelegatingAgent` middleware wasn't properly preserving all `AgentRunOptions` properties when converting to `ChatClientAgentRunOptions`, causing structured output to fail.

**Problem:**

When using function middleware, only `ResponseFormat` was being preserved during options conversion. Other critical properties like `AllowBackgroundResponses`, `ContinuationToken`, and `AdditionalProperties` were lost.

**Solution:**

```csharp
public class FunctionInvocationDelegatingAgent : DelegatingAgent
{
    protected override async Task<AgentResponse> InvokeAsync(
        AgentInput input,
        AgentRunOptions? options,
        CancellationToken cancellationToken)
    {
        // Fixed: Now preserves ALL properties
        var chatOptions = new ChatClientAgentRunOptions
        {
            ResponseFormat = options?.ResponseFormat,
            AllowBackgroundResponses = options?.AllowBackgroundResponses,
            ContinuationToken = options?.ContinuationToken,
            AdditionalProperties = options?.AdditionalProperties
        };
        
        return await InnerAgent.InvokeAsync(input, chatOptions, cancellationToken);
    }
}
```

**Impact:**

Agents configured with function middleware can now properly use structured output and other advanced features:

```csharp
var agent = new FunctionInvocationDelegatingAgent(baseAgent);

var response = await agent.InvokeAsync(
    "Generate data",
    new AgentRunOptions 
    { 
        ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
            "UserData", 
            schema
        )
    }
);
// Now correctly returns structured data
```

## New Samples and Tools

### .NET: Foundry Agents Tool Sample - Web Search

**PR**: [#4040](https://github.com/microsoft/agent-framework/pull/4040)

A comprehensive sample demonstrating how to use the OpenAI Responses API built-in web search capability with Foundry Agents. The sample was also corrected to remove incorrect Bing Grounding connection ID requirements.

**Key Features:**

```csharp
using Microsoft.Agents.Foundry;

// No connection ID needed - uses built-in capability
var agent = new OpenAIResponsesAgent(
    endpoint: foundryEndpoint,
    credential: new DefaultAzureCredential(),
    modelId: "gpt-4o",
    tools: new[] { new HostedWebSearchTool() }
);

var response = await agent.InvokeAsync(
    "What are the latest developments in AI agents?"
);

Console.WriteLine(response.Text);
```

**Corrections Made:**

- Removed incorrect `AZURE_FOUNDRY_BING_CONNECTION_ID` requirement
- Simplified tool initialization (no `connectionId` properties needed)
- Updated authentication to use `DefaultAzureCredential`
- Added sample to main solution file and updated README

**Location:** `samples/FoundryAgents/Step25_WebSearch/`

### .NET: Foundry Agents Tool Sample - Memory Search

**PR**: [#3700](https://github.com/microsoft/agent-framework/pull/3700)

Demonstrates using the Foundry Agents memory search tool for semantic retrieval over stored memories. This sample shows how to build agents with long-term memory capabilities.

**Example Usage:**

```csharp
using Microsoft.Agents.Foundry;
using Microsoft.Agents.Memory;

// Create memory store
var memoryStore = new CosmosMemoryStore(
    endpoint: cosmosEndpoint,
    key: cosmosKey,
    databaseId: "agent-memories"
);

// Create agent with memory search capability
var agent = new OpenAIResponsesAgent(
    endpoint: foundryEndpoint,
    credential: new DefaultAzureCredential(),
    modelId: "gpt-4o",
    tools: new[] 
    { 
        new MemorySearchTool(memoryStore) 
    }
);

// Store some memories
await memoryStore.AddAsync("User prefers Python over JavaScript");
await memoryStore.AddAsync("User's favorite color is blue");

// Query with memory context
var response = await agent.InvokeAsync(
    "What programming language should I recommend?"
);

// Agent uses memory search to recall preferences
Console.WriteLine(response.Text);
// Output: "Based on your preferences, I'd recommend Python..."
```

**Features:**

- Semantic search over stored memories
- Integration with Cosmos DB for persistence
- Cross-reference with `AgentWithMemory` sample
- Full documentation in sample README

**Location:** `samples/FoundryAgents/Step26_MemorySearch/`

## Minor Updates and Improvements

### .NET: Fix Cosmos DB Case-Sensitive Property Queries

**PR**: [#3485](https://github.com/microsoft/agent-framework/pull/3485)

Fixed a critical bug in `CosmosChatHistoryProvider` where queries used `c.Type` (capital T) instead of `c.type` (lowercase t). Since Cosmos DB property names are case-sensitive, this caused `GetMessageCountAsync` and `ClearMessagesAsync` to always return 0 results.

**Fixed Queries:**

```csharp
// Before (broken)
var countQuery = $"SELECT VALUE COUNT(1) FROM c WHERE c.Type = 'message'";

// After (fixed)
var countQuery = $"SELECT VALUE COUNT(1) FROM c WHERE c.type = 'message'";
```

Added comprehensive unit tests to verify the fix.

### .NET: Cosmos DB Test Configuration from Environment Variables

**PR**: [#4156](https://github.com/microsoft/agent-framework/pull/4156)

Updated Cosmos DB integration tests to read `COSMOSDB_ENDPOINT` and `COSMOSDB_KEY` from environment variables, following the project's standard configuration convention. This improves CI/CD reliability and developer experience.

**Changes:**

```csharp
// Now reads from environment variables
var endpoint = Environment.GetEnvironmentVariable("COSMOSDB_ENDPOINT");
var key = Environment.GetEnvironmentVariable("COSMOSDB_KEY");

if (string.IsNullOrEmpty(endpoint) || string.IsNullOrEmpty(key))
{
    Assert.Inconclusive("Cosmos DB credentials not configured");
}
```

### Updated GitHub Action for Manual Integration Tests

**PR**: [#4147](https://github.com/microsoft/agent-framework/pull/4147)

Restructured the GitHub Actions workflow for manual integration testing with significant improvements:

**New Features:**

1. **Dedicated Integration Workflows**: Created separate `dotnet-integration-tests.yml` and `python-integration-tests.yml` workflows
2. **Automatic Change Detection**: Only runs relevant test suites based on changed files
3. **Improved Permissions**: Fixed `python-merge-tests.yml` from `contents: write` to `contents: read`
4. **Cleanup**: Removed orphaned `workflow_call` triggers

**Workflow Logic:**

```yaml
# Detect which language changed
- name: Detect changes
  run: |
    if [[ "$CHANGED_FILES" =~ dotnet/ ]]; then
      echo "DOTNET_CHANGES=true" >> $GITHUB_ENV
    fi
    if [[ "$CHANGED_FILES" =~ python/ ]]; then
      echo "PYTHON_CHANGES=true" >> $GITHUB_ENV
    fi

# Run only relevant tests
- name: Run .NET tests
  if: env.DOTNET_CHANGES == 'true'
  uses: ./.github/workflows/dotnet-integration-tests.yml

- name: Run Python tests
  if: env.PYTHON_CHANGES == 'true'
  uses: ./.github/workflows/python-integration-tests.yml
```

**Benefits:**

- Faster CI execution by skipping irrelevant tests
- Better separation of concerns
- Easier maintenance and debugging

## Summary

February 23, 2026 brings substantial improvements to the Microsoft Agent Framework:

### Breaking Changes (Action Required)

1. **.NET Developers**: Update AIContextProvider integration to use new decorator pattern
2. **Python ag-ui Users**: Review streaming implementations for workflow compatibility

### Critical Fixes

1. **Python OpenAI Client**: Now works reliably with NVIDIA NIM, Gemini, and Foundry Local endpoints
2. **Python ClaudeAgent**: Structured output now works correctly
3. **.NET Function Middleware**: All AgentRunOptions properties properly preserved
4. **.NET Cosmos DB**: Case-sensitivity bugs fixed

### New Capabilities

1. **Python ag-ui**: Full workflow support with hardened streaming
2. **.NET Foundry**: Web Search and Memory Search tool samples
3. **.NET OpenAI Responses**: Simplified `store=false` API

### Recommended Actions

1. **If using .NET AIContextProviders**: Migrate to new decorator pattern immediately
2. **If using Python ag-ui**: Test streaming implementations with new semantics
3. **If using third-party OpenAI endpoints**: Update to latest Python SDK for compatibility fixes
4. **If using Claude with structured output**: Update to get working functionality
5. **If using Cosmos DB chat history**: Verify queries work correctly after case-sensitivity fix
6. **Review new Foundry samples** if building agents with web search or memory capabilities

### Next Steps

The Agent Framework team continues rapid development with focus on:
- Enhanced tool capabilities
- Improved observability and telemetry
- Better third-party LLM compatibility
- Richer sample collection

Stay tuned for more updates as the framework evolves!

## Resources

- [Microsoft Agent Framework Repository](https://github.com/microsoft/agent-framework)
- [Latest Release Notes](https://github.com/microsoft/agent-framework/releases)
- [Documentation](https://github.com/microsoft/agent-framework#readme)
- [Foundry Agents Samples](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/FoundryAgents)

---

*This update covers pull requests merged on February 23, 2026 (UTC timezone). All code examples are illustrative and based on the actual changes in the pull requests.*
