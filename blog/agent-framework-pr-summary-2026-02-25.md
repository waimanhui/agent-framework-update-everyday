# Agent Framework Updates - February 25, 2026

The Microsoft Agent Framework had a highly productive day with **24 merged pull requests** on February 25, 2026, bringing significant enhancements across Python and .NET implementations. This update includes major features like nested sub-workflow support, Agent Skills integration, new embedding clients, and critical bug fixes that improve reliability and developer experience.

## 🚀 Major Features

### 1. Python: Agent Skills Support (#4210)

A major addition to the Python SDK - the `FileAgentSkillsProvider` - enables progressive disclosure of agent capabilities following the [Agent Skills specification](https://agentskills.io/).

**Key Features:**
- Automatic discovery of `SKILL.md` files from configured directories
- System prompt injection to advertise available skills
- On-demand loading with `load_skill` and `read_skill_resource` tools
- Security features: path traversal protection and symlink guards

**Example Usage:**

```python
from semantic_kernel.agents.context_providers import FileAgentSkillsProvider

# Configure the skills provider
skills_provider = FileAgentSkillsProvider(
    skill_directories=["./skills", "./custom_skills"]
)

# Skills are automatically advertised in the system prompt
# and can be loaded on-demand by the agent
```

**Sample Skill Structure:**

```markdown
# SKILL.md
---
name: expense-report
description: Generates expense reports from receipt data
---

## Instructions
This skill processes receipt images and generates formatted expense reports...

## Resources
- template.json - Report template
- config.yaml - Processing configuration
```

The implementation includes comprehensive unit tests covering discovery, loading, resource reading, and security scenarios. A basic sample (`Agent_Step01_BasicSkills`) demonstrates usage with an expense-report skill.

### 2. .NET: Nested Sub-Workflow Support (#4190)

This significant enhancement enables **multi-level workflow nesting** in Durable Task workflows, allowing workflows to act as executors within other workflows.

**What's New:**
- Hierarchical workflow execution via Durable Task sub-orchestrations
- Independent checkpointing and replay protection per sub-workflow
- Dashboard visualization for each sub-workflow instance
- Event propagation and shared state across workflow levels

**Implementation Changes:**

```csharp
// DurableWorkflowResult now carries messages from sub-workflows
public class DurableWorkflowResult
{
    // Existing properties...
    
    // New: Enable message routing from sub-workflows to parent
    public List<TypedMessage> SentMessages { get; set; } = new();
}
```

```csharp
// DurableExecutorDispatcher handles sub-workflow dispatch
public async Task<ExecutorOutput> ExecuteSubWorkflowAsync(
    WorkflowDefinition subWorkflowDefinition,
    ExecutorInput input,
    CancellationToken cancellationToken)
{
    // Dispatch via CallSubOrchestratorAsync
    var result = await context.CallSubOrchestratorAsync<DurableWorkflowResult>(
        orchestratorName,
        instanceId,
        input
    );
    
    // Convert to ExecutorOutput format for parent workflow
    return ConvertToExecutorOutput(result);
}
```

**Example: 2-Level Nested Workflow**

```csharp
// Parent workflow configuration
var parentWorkflow = new WorkflowDefinition
{
    Name = "ParentWorkflow",
    Executors = new[]
    {
        new ExecutorDefinition
        {
            Type = "SubWorkflow",
            Name = "ChildProcessor",
            Configuration = childWorkflowDefinition
        }
    }
};

// Events propagate from child to parent
// Each level maintains independent state
```

The PR includes a comprehensive sample (`07_SubWorkflows`) demonstrating 2-level nesting with event propagation, plus integration tests validating execution across three nesting levels.

### 3. Python: Embedding Clients for Ollama, Bedrock, and Azure AI Inference (#4207)

Significant expansion of embedding capabilities with new client implementations for popular AI platforms.

**New Clients:**

**OllamaEmbeddingClient:**
```python
from semantic_kernel.connectors.ai.ollama import OllamaEmbeddingClient

# Text embeddings via Ollama's embed API
embedding_client = OllamaEmbeddingClient(
    model_id="llama2",
    base_url="http://localhost:11434"
)

embeddings = await embedding_client.get_embeddings(
    ["Hello world", "Machine learning"]
)
```

**BedrockEmbeddingClient:**
```python
from semantic_kernel.connectors.ai.bedrock import BedrockEmbeddingClient

# Text embeddings via Amazon Titan on Bedrock
embedding_client = BedrockEmbeddingClient(
    model_id="amazon.titan-embed-text-v1",
    region_name="us-east-1"
)
```

**AzureAIInferenceEmbeddingClient:**
```python
from semantic_kernel.connectors.ai.azure_ai_inference import AzureAIInferenceEmbeddingClient
from semantic_kernel.contents import TextContent, ImageContent

# Supports both text and image embeddings
text_model = os.getenv("AZURE_AI_INFERENCE_EMBEDDING_MODEL_ID")
image_model = os.getenv("AZURE_AI_INFERENCE_IMAGE_EMBEDDING_MODEL_ID")

embedding_client = AzureAIInferenceEmbeddingClient(
    text_model_id=text_model,
    image_model_id=image_model
)

# Text embedding
text_embeddings = await embedding_client.get_embeddings([
    TextContent(text="AI is transforming software")
])

# Image embedding
image_embeddings = await embedding_client.get_embeddings([
    ImageContent(uri="https://example.com/image.jpg")
])
```

**Additional Improvements:**
- Renamed `EmbeddingCoT` → `EmbeddingT`, `EmbeddingOptionsCoT` → `EmbeddingOptionsT`
- Added `otel_provider_name` passthrough for OpenTelemetry integration
- Lazy-loading namespace exports for Ollama and Bedrock
- New image embedding sample using Cohere-embed-v3-english
- Proper usage token tracking across all clients

### 4. Python: Azure AI Search Provider Improvements (#4212)

Enhanced the Azure AI Search integration with better embedding support and async context management.

**Key Improvements:**
- Integrated `EmbeddingGenerator` for automatic vectorization
- Async context manager support for proper resource cleanup
- Improved knowledge base message handling
- Better type safety with mypy compliance

```python
from semantic_kernel.data.providers.azure_ai_search import AzureAISearchVectorStore

# Now supports async context manager
async with AzureAISearchVectorStore(
    endpoint=endpoint,
    embedding_generator=embedding_client
) as vector_store:
    # Automatic vectorization of queries
    results = await vector_store.search(
        query="machine learning concepts",
        vectorize=True  # Automatically generates embeddings
    )
```

## 🐛 Critical Bug Fixes

### 5. Python: Thread Corruption Fix When max_iterations Reached (#4234)

**Issue:** When the function invocation loop exhausted `max_iterations` while the model kept requesting tools, the failsafe code path was unreachable due to premature return, causing thread state corruption.

**Before (Broken):**
```python
for i in range(max_iterations):
    response = await self._invoke_tools(...)
    if response is not None:
        return response  # Short-circuits before failsafe!
    
# Failsafe code never reached
if accumulated_tool_calls:
    response = await self._model_call(tool_choice='none')
```

**After (Fixed):**
```python
for i in range(max_iterations):
    response = await self._invoke_tools(...)
    if response is not None:
        break  # Don't return early
    
# Failsafe always runs after loop exhaustion
if accumulated_tool_calls and response is None:
    response = await self._model_call(
        tool_choice='none',
        messages=fcc_messages + accumulated_messages
    )
return response
```

The fix ensures a final model call with `tool_choice='none'` always happens after exhausting iterations, producing a clean text answer and preserving thread state. Previously skipped tests `test_max_iterations_limit` and `test_streaming_max_iterations_limit` are now enabled.

### 6. .NET: JSON Arrays of Objects Parsed as Empty Records (#4199)

**Issue:** When parsing JSON arrays containing objects without a predefined schema, `DetermineElementType()` created a `VariableType` with an empty (non-null) schema, causing `ParseRecord` to iterate over zero schema fields and discard all JSON properties.

**Before (Broken):**
```csharp
// Input: [{"name": "John", "role": "Admin"}, {"name": "Jane", "role": "User"}]
// Result: [{}, {}]  // All properties lost!

var elementType = targetType.Schema?.Select(...) ?? [];  // Empty array, not null
var result = ParseRecord(element, elementType);  // Iterates over 0 fields
```

**After (Fixed):**
```csharp
var elementType = targetType.HasSchema 
    ? new VariableType { Schema = targetType.Schema.Select(...) }
    : VariableType.RecordType;  // Schema = null, uses dynamic parsing

var result = ParseRecord(element, elementType);  // Preserves all properties
```

The fix checks `HasSchema` and falls back to `VariableType.RecordType` (with `Schema = null`) when no schema is defined, ensuring `ParseRecord` uses the dynamic `ParseValues()` path that preserves all JSON properties.

**Test Case:**
```csharp
[Fact]
public void ParseRecord_ObjectWithArrayOfObjects_NoSchema_PreservesNestedProperties()
{
    var json = JsonDocument.Parse(@"{
        ""users"": [
            {""name"": ""John"", ""role"": ""Admin""},
            {""name"": ""Jane"", ""role"": ""User""}
        ]
    }");
    
    var result = JsonDocumentExtensions.ParseRecord(
        json.RootElement, 
        VariableType.RecordType  // No schema
    );
    
    var users = result["users"] as List<Dictionary<string, object>>;
    Assert.Equal("John", users[0]["name"]);
    Assert.Equal("Admin", users[0]["role"]);
    Assert.Equal("Jane", users[1]["name"]);
    Assert.Equal("User", users[1]["role"]);
}
```

### 7. .NET: OpenTelemetry Span Export Fix for In-Process Workflows (#4196)

**Issue:** The `workflow.run` OpenTelemetry Activity in streaming execution was scoped with `using` to the method lifetime, but the run loop only exits on cancellation, preventing span export until explicit disposal.

**Before (Broken):**
```csharp
public async IAsyncEnumerable<WorkflowEvent> RunLoopAsync()
{
    using var activity = ActivitySource.StartActivity("workflow.run");
    
    while (true)  // Run loop continues after event consumption
    {
        await ProcessEvents();
        yield return evt;
    }
    // Activity never stopped until explicit StopAsync()
}
```

**After (Fixed):**
```csharp
public async IAsyncEnumerable<WorkflowEvent> RunLoopAsync()
{
    Activity? activity = null;
    try
    {
        activity = ActivitySource.StartActivity("workflow.run");
        
        while (true)
        {
            await ProcessEvents();
            
            if (workflowState == WorkflowState.Idle)  // All supersteps complete
            {
                activity?.Dispose();  // Export span when workflow completes
                activity = null;
            }
            
            yield return evt;
        }
    }
    finally
    {
        activity?.Dispose();  // Safety net for cancellation/errors
    }
}
```

The fix removes `using` and explicitly disposes the Activity when the workflow reaches Idle status (all supersteps complete). A safety-net disposal in the finally block handles cancellation and error paths.

## 🔧 .NET Workflow & Declarative Features

### 8. Support for InvokeMcpTool in Declarative Workflows (#4204)

Added support for invoking Model Context Protocol (MCP) tools from declarative workflows, expanding the integration capabilities.

```csharp
// Declarative workflow can now invoke MCP tools
{
    "type": "InvokeMcpTool",
    "toolName": "search",
    "parameters": {
        "query": "{{inputs.search_term}}"
    }
}
```

### 9. A2A Hosting Package Task Support (#3732)

Implemented Task-based API support for the Agent-to-Agent (A2A) Hosting package, enabling async/await patterns for agent communication.

```csharp
// New Task-based API
public async Task<AgentResponse> SendMessageAsync(
    string agentId, 
    AgentMessage message,
    CancellationToken cancellationToken = default)
{
    var response = await _hostingClient.InvokeAgentAsync(
        agentId, 
        message, 
        cancellationToken
    );
    return response;
}
```

## 📚 Documentation & Sample Updates

### 10. Additional Properties ADR (#4246)

Added Architecture Decision Record (ADR) documenting the approach for handling additional/dynamic properties in schemas.

### 11. .NET: Foundry Tool Samples (#4230, #4227)

- **Foundry Fabric Tool Sample (#4230):** Demonstrates integration with Microsoft Fabric for data analytics
- **Foundry SharePoint Tool Sample (#4227):** Shows SharePoint integration patterns for document management

### 12. Azure Functions Durable Agents Parity (#4221)

Restored index parity between AzureFunctions and ConsoleApps under DurableAgents samples, ensuring consistent examples across deployment targets.

## 🔄 Python & .NET: Purview Response Marking (#4225)

Fixed epoch timestamp bug in Python and properly marked Purview tool responses with response annotations in both Python and .NET implementations.

```python
# Python: Fixed epoch time conversion
response_time = datetime.fromtimestamp(epoch_seconds)  # Was: epoch_milliseconds

# Both: Properly mark as response
@response_message
def purview_search_result(data: dict) -> dict:
    return {"status": "success", "data": data}
```

## ⚙️ CI/CD & Testing Improvements

Multiple PRs improved build performance and test reliability:

- **#4243:** Separated build and test into parallel jobs
- **#4244:** Filtered src by framework for tests build
- **#4245:** Pre-built samples via tests to avoid timeouts
- **#4251:** Separated build from run for console sample validation
- **#4255:** Addressed PR review comments for .NET improvements
- **#4241, #4242:** Increased integration test parallelism (4x threads)

## 📦 Package Version Updates

- **#4257:** Updated .NET package version to rc2
- **#4258:** Updated Python package versions to rc2

Both platforms are now aligned on Release Candidate 2, indicating approaching stable releases.

## 📊 Impact Summary

**By the Numbers:**
- 24 PRs merged in a single day
- 2 critical bug fixes preventing data loss and thread corruption
- 3 major new features (Agent Skills, nested workflows, embedding clients)
- 5 new samples and documentation updates
- Significant CI/CD performance improvements

**Key Takeaways:**

1. **Production Readiness:** Critical bug fixes in thread management and JSON parsing significantly improve reliability
2. **Feature Parity:** Python is catching up to .NET with Agent Skills support and expanded embedding options
3. **Enterprise Integration:** New Foundry, Fabric, and SharePoint samples demonstrate enterprise readiness
4. **Developer Experience:** Improved async patterns, better error handling, and comprehensive documentation
5. **Performance:** CI/CD optimizations reduce build times and improve developer feedback loops

**Migration Notes:**

- **Python Users:** Update to rc2 for critical thread corruption fix if using `max_iterations`
- **.NET Users:** Update to rc2 for JSON parsing fix if working with dynamic schemas
- **Embedding Users:** Consider migrating to new specialized clients for better performance
- **Workflow Users:** Nested sub-workflows enable more complex orchestration patterns

## 🔗 Resources

- [Agent Skills Specification](https://agentskills.io/)
- [Microsoft Agent Framework Repository](https://github.com/microsoft/agent-framework)
- [Durable Task Framework](https://github.com/Azure/durabletask)

---

*This summary covers PRs merged on February 25, 2026. For detailed code changes, refer to individual pull requests linked above.*
