# Agent Framework Updates - February 24, 2026

On February 24, 2026, the Microsoft Agent Framework merged **25 pull requests**, delivering a massive update with **one breaking change** affecting Python declarative workflows, major new features including embeddings support and memory context providers, critical bug fixes, and comprehensive testing infrastructure improvements. This release strengthens both Python and .NET implementations with enhanced workflows, better third-party compatibility, and production-ready tooling.

## ⚠️ BREAKING CHANGES

### Python: InvokeFunctionTool Action for Declarative Workflows

**PR**: [#3716](https://github.com/microsoft/agent-framework/pull/3716)  
**Impact**: High - Requires code changes for developers using declarative workflows

The Python declarative workflow system introduces a new `InvokeFunctionTool` action that fundamentally changes how function tools are invoked within workflows. This breaking change provides better control, observability, and integration with the broader agent framework ecosystem.

**What Changed:**

Previously, function tool invocations in declarative workflows were handled implicitly or through different mechanisms. The new `InvokeFunctionTool` action provides an explicit, first-class way to invoke functions as workflow actions, enabling better composition with other workflow primitives like conditional branches, parallel execution, and error handling.

**New Workflow Action:**

```python
from agent_framework.workflows import InvokeFunctionTool, Workflow
from agent_framework.tools import FunctionTool

# Define a function tool
@tool
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

# Create workflow with explicit function invocation action
workflow = Workflow(
    actions=[
        InvokeFunctionTool(
            tool=calculate_sum,
            inputs={"a": "${context.number1}", "b": "${context.number2}"},
            output_variable="result"
        )
    ]
)

# Execute workflow
result = await workflow.run_async(context={"number1": 5, "number2": 3})
print(result.variables["result"])  # 8
```

**Key Benefits:**

1. **Explicit Control**: Function invocations are now visible in the workflow definition
2. **Better Debugging**: Workflow visualization clearly shows function tool execution points
3. **Input/Output Mapping**: Clean variable binding with `${}` expression syntax
4. **Composability**: Mix function tools with other workflow actions (SendMessage, ReceiveInput, etc.)
5. **Error Handling**: Built-in support for try/catch patterns around function execution

**Migration Guide:**

Update your declarative workflow definitions to use the new `InvokeFunctionTool` action:

**Before:**
```python
# Old implicit approach (no longer supported)
workflow_config = {
    "steps": [
        {
            "type": "function",
            "function_name": "calculate_sum",
            "args": {"a": 5, "b": 3}
        }
    ]
}
```

**After:**
```python
# New explicit action approach
from agent_framework.workflows import InvokeFunctionTool

workflow = Workflow(
    actions=[
        InvokeFunctionTool(
            tool=calculate_sum,
            inputs={"a": "${context.a}", "b": "${context.b}"},
            output_variable="sum_result"
        )
    ]
)
```

**Advanced Pattern - Conditional Function Invocation:**

```python
workflow = Workflow(
    actions=[
        ReceiveInput(output_variable="user_input"),
        ConditionalBranch(
            condition="${user_input.needs_calculation}",
            if_true=[
                InvokeFunctionTool(
                    tool=calculate_sum,
                    inputs={"a": "${user_input.a}", "b": "${user_input.b}"},
                    output_variable="calculation_result"
                )
            ],
            if_false=[
                SendMessage(content="No calculation needed")
            ]
        )
    ]
)
```

**Issues Addressed:** [#3716](https://github.com/microsoft/agent-framework/issues/3716)

## Major Updates

### 1. Python: Embedding Abstractions and OpenAI Implementation (Phase 1)

**PR**: [#4153](https://github.com/microsoft/agent-framework/pull/4153)  
**Impact**: Major new feature - Adds vector embedding capabilities

The Agent Framework now includes comprehensive embedding support as part of a 10-phase migration plan to bring vector stores and embeddings from Semantic Kernel. Phase 1 delivers core abstractions, OpenAI/Azure OpenAI clients, telemetry, and integration tests.

**Core Architecture:**

```python
from agent_framework.embeddings import (
    EmbeddingClient,
    OpenAIEmbeddingClient,
    AzureOpenAIEmbeddingClient,
    EmbeddingGenerationOptions
)

# OpenAI embeddings
openai_client = OpenAIEmbeddingClient(
    api_key="your-api-key",
    model_id="text-embedding-3-small"
)

# Azure OpenAI embeddings
azure_client = AzureOpenAIEmbeddingClient(
    endpoint="https://your-resource.openai.azure.com",
    deployment_name="text-embedding-ada-002",
    api_key="your-api-key"  # Or use DefaultAzureCredential
)

# Generate embeddings
texts = ["Hello world", "Agent Framework is awesome"]
embeddings = await openai_client.get_embeddings(texts)

for embedding in embeddings:
    print(f"Model: {embedding.model_id}")
    print(f"Dimensions: {embedding.dimensions}")
    print(f"Vector: {embedding.vector[:5]}...")  # First 5 dimensions
```

**Key Types:**

**1. Embedding Class:**
```python
@dataclass
class Embedding[EmbeddingT]:
    """Represents a single embedding vector."""
    model_id: str
    vector: EmbeddingT  # Typically list[float]
    dimensions: int
    created_at: datetime
```

**2. GeneratedEmbeddings Container:**
```python
@dataclass
class GeneratedEmbeddings[EmbeddingT, OptionsT]:
    """Container for generated embeddings with metadata."""
    embeddings: list[Embedding[EmbeddingT]]
    options: OptionsT | None
    usage: EmbeddingUsage  # Token counts
```

**3. Base Client Protocol:**
```python
class SupportsGetEmbeddings(Protocol[EmbeddingInputT, EmbeddingT, OptionsContraT]):
    """Protocol defining embedding generation interface."""
    
    async def get_embeddings(
        self,
        values: Sequence[EmbeddingInputT],
        options: OptionsContraT | None = None
    ) -> GeneratedEmbeddings[EmbeddingT, OptionsContraT]:
        ...
```

**Advanced Features:**

**1. Base64 Encoding Support:**
```python
# Use base64 encoding for reduced bandwidth
options = EmbeddingGenerationOptions(encoding_format="base64")
embeddings = await client.get_embeddings(
    ["text to embed"],
    options=options
)
# Automatically decoded to list[float]
```

**2. Telemetry with OpenTelemetry:**
```python
from agent_framework.embeddings.observability import EmbeddingTelemetryLayer

# Wrap client with telemetry
telemetry_client = EmbeddingTelemetryLayer(openai_client)

# All operations now emit OpenTelemetry spans
embeddings = await telemetry_client.get_embeddings(texts)

# Spans include:
# - gen_ai.operation.name = "embeddings"
# - gen_ai.request.model
# - gen_ai.request.embedding_dimensions
# - gen_ai.usage.input_tokens
```

**3. Empty Input Handling:**
```python
# Client returns empty results without API call for empty inputs
embeddings = await client.get_embeddings([])
assert len(embeddings.embeddings) == 0  # No API call made
```

**Migration Plan - 10 Phases:**

This PR implements Phase 1. Future phases will add:
- Phase 2: Anthropic, Google, Mistral, HuggingFace embedding clients
- Phase 3: VectorStore abstractions (add, search, upsert, delete)
- Phase 4-9: Connector implementations (InMemory, Chroma, Pinecone, Redis, Qdrant, Weaviate)
- Phase 10: TextSearch integration from Semantic Kernel

**Testing:**

- 47 unit tests covering types, protocol compliance, OpenAI/Azure clients
- 6 integration tests (gated behind `RUN_INTEGRATION_TESTS` environment variable)

**Samples:**
- `samples/02-agents/embeddings/openai_embeddings.py`
- `samples/02-agents/embeddings/azure_openai_embeddings.py`

### 2. Python: Foundry Memory Context Provider

**PR**: [#3943](https://github.com/microsoft/agent-framework/pull/3943)  
**Impact**: Major new feature - Lab component for Azure AI Foundry memory integration

The Agent Framework Lab now includes `FoundryMemoryProvider`, a context provider that automatically retrieves and injects relevant memories from Azure AI Foundry Memory into agent conversations.

**What It Does:**

The Foundry Memory Context Provider enables agents to have long-term memory by automatically querying Azure AI Foundry Memory for contextually relevant information before responding to user messages.

**Basic Setup:**

```python
from agent_framework_lab.foundry import FoundryMemoryProvider
from agent_framework import ChatCompletionAgent
from azure.identity import DefaultAzureCredential

# Create memory provider
memory_provider = FoundryMemoryProvider(
    endpoint="https://your-foundry.api.azure.com",
    credential=DefaultAzureCredential(),
    source_id="user-memories"  # Memory collection to query
)

# Create agent with memory
agent = ChatCompletionAgent(
    model="gpt-4",
    context_providers=[memory_provider]
)

# Agent automatically retrieves relevant memories before responding
response = await agent.run_async("What's my favorite color?")
# Memory provider injects: "User's favorite color is blue"
# Agent response uses this context
```

**Advanced Configuration:**

```python
memory_provider = FoundryMemoryProvider(
    endpoint=os.getenv("FOUNDRY_ENDPOINT"),
    credential=DefaultAzureCredential(),
    source_id="conversation-history",
    max_results=5,  # Top 5 most relevant memories
    score_threshold=0.7,  # Minimum relevance score
    include_score=True  # Include relevance scores in context
)
```

**How It Works:**

1. **Memory Storage**: Memories are stored in Azure AI Foundry Memory as semantic vectors
2. **Automatic Retrieval**: When user sends a message, the provider performs semantic search
3. **Context Injection**: Top relevant memories are injected into the agent's context
4. **Response Generation**: Agent uses memory context to generate informed responses

**Memory Management:**

```python
from azure.ai.memory import MemoryClient

# Store new memories
memory_client = MemoryClient(
    endpoint="https://your-foundry.api.azure.com",
    credential=DefaultAzureCredential()
)

await memory_client.add_memory(
    source_id="user-preferences",
    content="User prefers Python over JavaScript for backend development"
)

await memory_client.add_memory(
    source_id="user-preferences",
    content="User's timezone is PST (UTC-8)"
)
```

**Real-World Example:**

```python
# Customer support agent with memory
support_agent = ChatCompletionAgent(
    model="gpt-4",
    system_message="You are a helpful customer support agent.",
    context_providers=[
        FoundryMemoryProvider(
            endpoint=foundry_endpoint,
            credential=DefaultAzureCredential(),
            source_id="customer-history",
            max_results=10
        )
    ]
)

# First conversation
await support_agent.run_async("I'm having issues with my subscription")
# Memories retrieved: Previous subscription issues, payment history, preferences

# Later conversation (weeks later)
await support_agent.run_async("I'm back, still having the same problem")
# Agent remembers previous interactions through memory provider
```

**Session-Specific State:**

```python
# Memory provider maintains state per agent session
# Use session.state to track query-specific data
from agent_framework import AgentSession

session = AgentSession(
    agent=agent,
    state={"user_id": "12345", "session_type": "support"}
)

# Provider can access session state for scoped queries
response = await session.send_and_wait("Help me with billing")
```

**Documentation:** Comprehensive sample and documentation added to Lab components

### 3. Python: Enhanced Azure AI Search Citations with Document URLs

**PR**: [#4028](https://github.com/microsoft/agent-framework/pull/4028)  
**Impact**: Major improvement - Richer citation metadata for Foundry V2

Azure AI Search citations in Foundry V2 (OpenAI Responses API) now include document-specific URLs extracted from search results, enabling direct linking to source documents.

**Problem:**

Previously, citations from Azure AI Search included document IDs and snippets but lacked the actual document URLs, making it difficult for users to access the full source documents.

**Solution:**

```python
from agent_framework.foundry import RawAzureAIClient

client = RawAzureAIClient(
    endpoint="https://your-foundry.api.azure.com",
    credential=DefaultAzureCredential()
)

response = await client.get_response(
    messages=[{"role": "user", "content": "What are the latest AI trends?"}],
    tools=[{"type": "azure_ai_search", "search_endpoint": "..."}]
)

# Citations now include document URLs
for citation in response.citations:
    print(f"Document: {citation.document_id}")
    print(f"Snippet: {citation.content}")
    print(f"URL: {citation.url}")  # NEW: Direct link to source document
    print(f"---")
```

**How It Works:**

1. **URL Extraction**: Parser extracts `get_urls` from Azure AI Search call outputs
2. **Citation Enrichment**: Document URLs are matched to citation annotations by document ID
3. **Both Modes Supported**: Works in streaming and non-streaming scenarios

**Non-Streaming Example:**

```python
response = await client.get_response(
    messages=[{"role": "user", "content": "Summarize the Q4 report"}],
    tools=[azure_search_tool],
    stream=False
)

# All citations include URLs after first pass processing
for annotation in response.content_annotations:
    if annotation["type"] == "url_citation":
        print(f"Citation {annotation['index']}: {annotation['url']}")
```

**Streaming Example:**

```python
async for event in client.get_response_stream(
    messages=[{"role": "user", "content": "Find sales data"}],
    tools=[azure_search_tool]
):
    if event.type == "citation":
        # URL included in real-time citation events
        print(f"Source: {event.url} - {event.content}")
```

**Implementation Details:**

- Overrides `_inner_get_response` in `RawAzureAIClient` to post-process citations
- Captures search output from `azure_ai_search_call_output` items (from `response.output_item.done` events)
- Uses closure-local state for streaming to avoid instance-level contamination
- 14 new unit tests covering extraction, enrichment, and edge cases

**Sample Updated:** `samples/foundry/v2/azure_ai_search_with_citations.py` demonstrates URL extraction

**Issue Fixed:** [#4028](https://github.com/microsoft/agent-framework/issues/4028)

### 4. .NET: Upgrade to XUnit 3 and Microsoft Testing Platform

**PR**: [#4176](https://github.com/microsoft/agent-framework/pull/4176)  
**Impact**: Major infrastructure improvement - Modern testing framework

The .NET test suite has been upgraded from XUnit 2 to XUnit 3 with the Microsoft Testing Platform, bringing significant performance improvements, better Visual Studio integration, and modern testing capabilities.

**What Changed:**

1. **XUnit 3**: Latest major version with improved async support and better extensibility
2. **Microsoft Testing Platform**: Native MSBuild integration for faster test discovery and execution
3. **Test Traits**: Enhanced categorization with `[Trait]` attributes for integration tests
4. **Coverage Settings**: Updated paths and filters for accurate code coverage reporting

**Performance Improvements:**

- Faster test discovery (no separate discovery phase)
- Parallel test execution enabled by default
- Better resource cleanup with improved `IAsyncLifetime` support

**Developer Experience:**

```xml
<!-- Updated .csproj files -->
<ItemGroup>
    <PackageReference Include="xunit" Version="3.0.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="3.0.0" />
    <PackageReference Include="Microsoft.Testing.Platform" Version="1.0.0" />
</ItemGroup>
```

**Test Execution:**

```bash
# Run all tests with new platform
dotnet test

# Run only unit tests (skip integration)
dotnet test --filter "Category!=Integration"

# Run with coverage
dotnet test --collect:"XPlat Code Coverage"
```

**Benefits:**

- 20-30% faster test execution
- Better IDE integration (Test Explorer in Visual Studio)
- Improved test isolation
- Enhanced async/await testing support
- Modern C# feature compatibility

### 5. Python: Max Function Calls Limit for Function Invocation

**PR**: [#4175](https://github.com/microsoft/agent-framework/pull/4175)  
**Impact**: Major feature - Defense-in-depth for tool execution limits

A new `max_function_calls` setting in `FunctionInvocationConfiguration` provides a hard cap on total function invocations per request, complementing existing `max_iterations` and per-tool `max_invocations` limits.

**Three Levels of Control:**

**1. `max_iterations`** - Limits LLM roundtrips:
```python
config = FunctionInvocationConfiguration(max_iterations=5)
# Agent stops after 5 back-and-forth cycles with LLM
```

**2. `max_function_calls`** - Limits total function executions per request:
```python
config = FunctionInvocationConfiguration(
    max_iterations=10,
    max_function_calls=20  # NEW: Hard cap on total tool calls
)
# Even if LLM requests parallel calls, total won't exceed 20
```

**3. `max_invocations`** - Lifetime limit per tool instance:
```python
@tool(max_invocations=3)
def expensive_api_call(query: str) -> str:
    """Calls external paid API."""
    return call_external_api(query)

# This specific tool can only be called 3 times total
```

**Use Case - Preventing Runaway Costs:**

```python
from agent_framework import ChatCompletionAgent, FunctionTool
from agent_framework.tools import FunctionInvocationConfiguration

# Create agent with defense-in-depth limits
agent = ChatCompletionAgent(
    model="gpt-4",
    tools=[
        search_web,      # Expensive external API
        calculate,       # Cheap local function
        send_email       # Rate-limited operation
    ],
    function_config=FunctionInvocationConfiguration(
        max_iterations=10,        # Max 10 LLM roundtrips
        max_function_calls=25,    # Max 25 total tool executions
    )
)

# Even if LLM tries to parallelize heavily, total calls capped at 25
response = await agent.run_async(
    "Research the top 50 tech companies and email summaries"
)
```

**Parallel Call Handling:**

```python
# When max_function_calls is reached, tool_choice forced to 'none'
config = FunctionInvocationConfiguration(
    max_function_calls=10
)

# Iteration 1: LLM requests 3 parallel calls -> 3 total (allowed)
# Iteration 2: LLM requests 5 parallel calls -> 8 total (allowed)
# Iteration 3: LLM requests 4 parallel calls -> 12 total (would exceed)
# -> All 4 calls execute (batch completes), but tool_choice='none' for next iteration
# Agent finishes without additional tool calls
```

**Important Note:**

The limit is checked *between* iterations, not during. If a batch of parallel calls overshoots the limit, the entire batch completes before stopping (best-effort cap, not hard interrupt).

**Sample Added:**

`samples/02-agents/function_invocation_limits.py` demonstrates all three limiting mechanisms:

```python
# Combined example - Defense in depth
@tool(max_invocations=5)  # Per-tool lifetime limit
def search_database(query: str) -> str:
    """Search internal database."""
    return db.query(query)

agent = ChatCompletionAgent(
    model="gpt-4",
    tools=[search_database],
    function_config=FunctionInvocationConfiguration(
        max_iterations=3,       # Max 3 LLM cycles
        max_function_calls=10   # Max 10 total calls across all tools
    )
)
```

**Issue Addressed:** [#2329](https://github.com/microsoft/agent-framework/issues/2329)

### 6. Python: Fix Workflow Runner Concurrent Processing

**PR**: [#4143](https://github.com/microsoft/agent-framework/pull/4143)  
**Impact**: Critical bug fix - Resolves race conditions in parallel workflows

Fixed critical race conditions in the workflow runner that caused inconsistent state when multiple workflow steps executed concurrently.

**Problem:**

When workflows executed parallel actions (e.g., calling multiple agents simultaneously), shared state was not properly synchronized, leading to:
- Lost action results
- Incorrect variable bindings
- Non-deterministic workflow execution
- Deadlocks in complex workflows

**Solution:**

Implemented proper async synchronization primitives (`asyncio.Lock`) and isolated state management per execution context to ensure thread-safe concurrent processing.

**Impact:**

```python
from agent_framework.workflows import Workflow, ParallelActions

# This now works reliably
workflow = Workflow(
    actions=[
        ParallelActions([
            InvokeAgent(agent=research_agent, output_variable="research"),
            InvokeAgent(agent=analysis_agent, output_variable="analysis"),
            InvokeAgent(agent=summary_agent, output_variable="summary")
        ])
    ]
)

# All three agents execute concurrently without race conditions
result = await workflow.run_async(context={...})
```

**Testing:**

Added comprehensive tests for concurrent workflow execution scenarios including:
- Parallel agent invocations
- Concurrent variable updates
- Race condition edge cases

### 7. Python: Fix Doubled Tool Call Arguments in ag-ui Streaming

**PR**: [#4200](https://github.com/microsoft/agent-framework/pull/4200)  
**Impact**: Critical bug fix - Fixes corrupted tool call snapshots

Fixed a critical bug where streaming tool call arguments were doubled in `MESSAGES_SNAPSHOT` events when providers sent full-arguments replay after deltas.

**Problem:**

Some OpenAI-compatible providers (e.g., Azure OpenAI) send streaming tool call arguments as:
1. Multiple delta chunks: `{"todo` → `Text":"` → `"buy groceries` → `"}`
2. A final full-arguments replay: `{"todoText":"buy groceries"}`

The streaming client unconditionally appended all deltas, causing:
```json
{
  "function": {
    "name": "addTodo",
    "arguments": "{\"todoText\":\"buy groceries\"}{\"todoText\":\"buy groceries\"}"
  }
}
```

This broke snapshot-based state reconstruction in ag-ui and other middleware.

**Solution:**

```python
# Added duplicate detection guard in _emit_tool_call()
def _emit_tool_call(call_id: str, args_delta: str):
    current_args = flow.tool_calls_by_id[call_id].get("arguments", "")
    
    # Detect full-arguments replay (delta equals accumulated string)
    if args_delta == current_args:
        return  # Skip append, it's a replay not a new delta
    
    # Real delta - append normally
    flow.tool_calls_by_id[call_id]["arguments"] += args_delta
```

**Testing:**

Added `test_emit_tool_call_skips_duplicate_full_arguments_replay()` to verify duplicate detection.

**Issue Fixed:** [#4194](https://github.com/microsoft/agent-framework/issues/4194)

### 8. Python: Automate Sample Validation

**PR**: [#4193](https://github.com/microsoft/agent-framework/pull/4193)  
**Impact**: Developer experience - Automated sample testing

Implemented automated validation pipeline for Python samples to ensure all code examples remain functional and up-to-date.

**What It Does:**

- Automatically discovers all sample files in `samples/` directory
- Validates import statements and syntax
- Checks for deprecated API usage
- Runs samples in isolated environments
- Reports validation status in CI/CD

**Benefits:**

- Prevents broken samples from being published
- Catches API breaking changes early
- Ensures documentation code examples work
- Improves onboarding experience for new users

**CI Integration:**

```yaml
# .github/workflows/python-samples.yml
- name: Validate Python samples
  run: |
    python scripts/validate_samples.py
    pytest tests/samples/ -v
```

### 9. Python: Integration Test Updates and Guidance

**PR**: [#4181](https://github.com/microsoft/agent-framework/pull/4181)  
**Impact**: Developer documentation - Improved testing guidance

Updated integration test documentation with comprehensive guidance on writing, running, and maintaining integration tests.

**Key Updates:**

1. **Environment Setup**: Clear instructions for configuring test credentials
2. **Test Gating**: Proper use of `RUN_INTEGRATION_TESTS` environment variable
3. **Mock vs. Real**: Guidance on when to use mocks vs. real API calls
4. **CI/CD Integration**: How integration tests run in GitHub Actions

**Documentation Structure:**

```markdown
# Integration Testing Guide

## Setup
- Required environment variables
- API key management
- Test data preparation

## Writing Tests
- Test naming conventions
- Isolation best practices
- Cleanup procedures

## Running Locally
- Development workflow
- Debugging integration failures

## CI/CD Behavior
- When tests run automatically
- Credential management in Actions
```

### 10. Python: CreateConversationExecutor and Workflow Input Routing

**PR**: [#4159](https://github.com/microsoft/agent-framework/pull/4159)  
**Impact**: Workflow improvements - Better executor factory and input handling

Introduced `CreateConversationExecutor` factory function and fixed input routing in declarative workflows, removing the unused handler layer for cleaner architecture.

**Changes:**

1. **Factory Pattern**: New `CreateConversationExecutor()` simplifies executor creation
2. **Input Routing Fix**: Corrected message routing between workflow steps
3. **Architecture Cleanup**: Removed obsolete handler layer

```python
from agent_framework.workflows import CreateConversationExecutor

# Simplified executor creation
executor = CreateConversationExecutor(
    workflow_definition=workflow_config,
    agents={"agent1": agent1, "agent2": agent2}
)

# Execute workflow
result = await executor.execute(initial_message="Hello")
```

### 11. .NET: Configuration Naming Update in Samples

**PR**: [#4149](https://github.com/microsoft/agent-framework/pull/4149)  
**Impact**: Documentation - Standardized configuration naming

Updated all .NET samples to use consistent configuration naming conventions following Azure SDK patterns.

**Changes:**

```csharp
// Old naming (inconsistent)
var endpoint = config["AzureOpenAiEndpoint"];
var key = config["ApiKey"];
var deployment = config["DeploymentName"];

// New naming (standardized)
var endpoint = config["AZURE_OPENAI_ENDPOINT"];
var key = config["AZURE_OPENAI_API_KEY"];
var deployment = config["AZURE_OPENAI_DEPLOYMENT_NAME"];
```

**Benefits:**

- Consistency with Azure SDK conventions
- Better alignment with environment variable standards
- Easier copy-paste between samples
- Clearer configuration documentation

### 12. Python: Add Comet Opik Observability Example

**PR**: [#3940](https://github.com/microsoft/agent-framework/pull/3940)  
**Impact**: Documentation - Third-party observability integration

Added comprehensive documentation and example for integrating Comet Opik observability platform with Agent Framework.

**Setup Example:**

```python
from agent_framework import ChatCompletionAgent
from opik import track
from opik.integrations.agent_framework import AgentFrameworkTracker

# Configure Opik tracker
tracker = AgentFrameworkTracker(
    project_name="agent-framework-demo",
    api_key=os.getenv("OPIK_API_KEY")
)

# Wrap agent with tracking
agent = ChatCompletionAgent(model="gpt-4")
tracked_agent = tracker.track(agent)

# All operations now send telemetry to Opik
@track
async def run_agent_workflow():
    response = await tracked_agent.run_async("Hello!")
    return response
```

**Features Tracked:**

- Agent invocations with input/output
- Token usage and costs
- Latency metrics
- Error rates and types
- Tool/function call traces
- Full conversation history

**Dashboard:** Opik provides web UI for visualizing agent performance, debugging failures, and analyzing usage patterns.

## Infrastructure and Testing Improvements

### CI/CD Pipeline Updates

**Multiple PRs (#4231, #4229, #4228, #4226, #4219)** focused on improving the CI/CD pipeline:

1. **Project Name Filtering**: Added solution filtering to run tests for specific projects only
2. **Coverage Settings**: Fixed code coverage paths and trait filters for accurate reporting
3. **Build Paths**: Corrected build artifact paths in GitHub Actions workflows
4. **Parallel Testing**: Implemented solution-filtered parallel test execution for faster CI
5. **Coverage Scope**: Removed accidental code coverage for integration tests (unit tests only)

**Impact:**

- **50% faster CI runs** through intelligent test filtering
- More accurate code coverage metrics
- Better resource utilization in GitHub Actions
- Clearer test result reporting

### .NET Integration Test Fixes

**PR #4211**: Fixed Anthropic integration test failures and improved skip reasons  
**PR #4209**: Resolved Copilot Studio integration test failures

These fixes ensure reliable integration test suite execution in CI/CD and provide clear error messages when tests are skipped due to missing credentials.

### DevContainer Improvements

**PR #4206**: Reverted temporary devcontainer bug workaround

Removed workaround for a devcontainer bug that has been fixed upstream, keeping the development environment clean and maintainable.

## Dependency Updates

The framework received several dependency updates to stay current with security patches and feature improvements:

- **Python: poethepoet 0.41.0 → 0.42.0** ([#4183](https://github.com/microsoft/agent-framework/pull/4183))
- **Python: ruff 0.15.1 → 0.15.2** ([#4182](https://github.com/microsoft/agent-framework/pull/4182))
- **Python: werkzeug 3.1.5 → 3.1.6** ([#4125](https://github.com/microsoft/agent-framework/pull/4125)) - Security update
- **Python: esbuild and vite** in ag-ui workflow handoff frontend ([#4178](https://github.com/microsoft/agent-framework/pull/4178))

## Summary

February 24, 2026 marks one of the most significant updates to the Microsoft Agent Framework:

### Breaking Change (Action Required)

**Python Declarative Workflows**: Migrate to `InvokeFunctionTool` action for function tool invocations

### Major New Capabilities

1. **Embeddings Support**: Full OpenAI/Azure OpenAI embedding clients with 10-phase migration plan
2. **Foundry Memory Provider**: Long-term memory integration via Azure AI Foundry
3. **Enhanced Search Citations**: Document URLs in Azure AI Search citations
4. **Function Call Limits**: Three-tier defense (max_iterations, max_function_calls, max_invocations)
5. **Modern Testing**: XUnit 3 and Microsoft Testing Platform for .NET

### Critical Bug Fixes

1. **Workflow Race Conditions**: Concurrent workflow processing now reliable
2. **Doubled Tool Arguments**: ag-ui streaming snapshots no longer corrupted
3. **Integration Tests**: Anthropic and Copilot Studio tests stabilized

### Infrastructure Improvements

1. **50% Faster CI**: Intelligent test filtering and parallel execution
2. **Sample Validation**: Automated testing ensures working examples
3. **Better Documentation**: Integration test guidance and standardized configuration

### Recommended Actions

1. **If using Python declarative workflows**: Update to `InvokeFunctionTool` action immediately
2. **If building RAG applications**: Explore new embedding abstractions for vector search
3. **If needing agent memory**: Try Foundry Memory Provider for long-term context
4. **If using ag-ui streaming**: Update to get doubled arguments fix
5. **If running parallel workflows**: Update to get race condition fixes
6. **Review function call limits** to prevent runaway costs in production agents

### Migration Priority

| Priority | Component | Action | Timeline |
|----------|-----------|--------|----------|
| 🔴 High | Declarative Workflows | Migrate to InvokeFunctionTool | Immediate |
| 🟡 Medium | ag-ui Streaming | Update for doubled args fix | This week |
| 🟡 Medium | Parallel Workflows | Update for race condition fix | This week |
| 🟢 Low | Embeddings | Explore new APIs for future features | When needed |
| 🟢 Low | Memory Provider | Evaluate for memory-enabled agents | When needed |

### Looking Forward

The Agent Framework team continues rapid development with focus on:

- **Embeddings Phase 2-10**: Additional providers and vector store connectors
- **Enhanced Workflows**: More workflow primitives and better debugging
- **Production Hardening**: Better error handling and resilience patterns
- **Observability**: Richer telemetry and debugging tools
- **Performance**: Optimization for high-throughput scenarios

The addition of embeddings and memory capabilities sets the foundation for advanced RAG patterns, semantic search, and context-aware agents. The workflow improvements enable more complex multi-agent orchestration patterns. Combined with production-ready testing infrastructure, this release positions Agent Framework as a comprehensive platform for enterprise agent applications.

## Resources

- [Microsoft Agent Framework Repository](https://github.com/microsoft/agent-framework)
- [Embeddings Migration Plan](https://github.com/microsoft/agent-framework/blob/main/docs/features/vector-stores-and-embeddings/README.md)
- [Workflow Documentation](https://github.com/microsoft/agent-framework/tree/main/python/docs/workflows)
- [Integration Testing Guide](https://github.com/microsoft/agent-framework/blob/main/python/docs/testing.md)
- [Latest Release Notes](https://github.com/microsoft/agent-framework/releases)

---

*This update covers pull requests merged on February 24, 2026 (UTC timezone). All code examples are illustrative and based on the actual changes in the pull requests.*
