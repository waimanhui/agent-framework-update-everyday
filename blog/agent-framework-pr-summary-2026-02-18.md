# Agent Framework Updates - February 18, 2026

On February 18, 2026, the Microsoft Agent Framework merged 19 pull requests representing a significant milestone for the project. This update includes **one critical breaking change** in .NET workflows, introduces powerful new features like InvokeFunctionTool for declarative workflows, adds comprehensive Foundry Evaluation samples, and delivers extensive fixes across Python samples to ensure robustness for the community.

## ⚠️ BREAKING CHANGES

### .NET: Unified Agent Events as WorkflowOutputEvents

**PR**: [#3441](https://github.com/microsoft/agent-framework/pull/3441)  
**Impact**: High - Requires updates to event handling code in .NET workflows

This breaking change unifies the event system in .NET workflows by making `AgentResponseEvent` and `AgentResponseUpdateEvent` inherit from `WorkflowOutputEvent`. This change addresses a regression where workflows built directly with `WorkflowBuilder` (without using `AgentWorkflowBuilder` helpers) did not emit `WorkflowOutputEvent` for agent outputs.

**What Changed:**

Previously, `AgentResponseEvent` and `AgentResponseUpdateEvent` were separate event types. Now they both inherit from `WorkflowOutputEvent`, providing a unified interface for handling agent outputs:

```csharp
// New inheritance hierarchy
public class AgentResponseUpdateEvent : WorkflowOutputEvent
{
    public string ExecutorId { get; }
    public AgentResponseUpdate Update { get; }
    // Data property inherited from WorkflowOutputEvent returns Update
}

public class AgentResponseEvent : WorkflowOutputEvent
{
    public string ExecutorId { get; }
    public AgentResponse Response { get; }
    // Data property inherited from WorkflowOutputEvent returns Response
}
```

**Example - Testing the new behavior:**

```csharp
// Arrange - Build workflow using WorkflowBuilder directly
AIAgent agent1 = new TestEchoAgent("agent1");
AIAgent agent2 = new TestEchoAgent("agent2");

Workflow workflow = new WorkflowBuilder(agent1)
    .AddEdge(agent1, agent2)
    .Build();

// Act
await using StreamingRun run = await InProcessExecution.StreamAsync(
    workflow, 
    new List<ChatMessage> { new(ChatRole.User, "Hello") }
);
await run.TrySendMessageAsync(new TurnToken(emitEvents: true));

List<WorkflowOutputEvent> outputEvents = new();
List<AgentResponseUpdateEvent> updateEvents = new();

await foreach (WorkflowEvent evt in run.WatchStreamAsync())
{
    if (evt is AgentResponseUpdateEvent updateEvt)
    {
        updateEvents.Add(updateEvt);
    }
    
    if (evt is WorkflowOutputEvent outputEvt)
    {
        outputEvents.Add(outputEvt);
    }
}

// Assert - All update events are now also output events
Assert.All(updateEvents, updateEvt => 
    Assert.Contains(updateEvt, outputEvents));
```

**Migration Guide:**

1. If you were filtering for `AgentResponseEvent` or `AgentResponseUpdateEvent`, they now also match `WorkflowOutputEvent` filters
2. Use the `Data` property (from `WorkflowOutputEvent`) to access the underlying data generically
3. Update event handling to account for the inheritance relationship:

```csharp
// Before - separate handling
await foreach (WorkflowEvent evt in stream)
{
    if (evt is AgentResponseUpdateEvent updateEvt)
    {
        // Handle update
    }
    else if (evt is WorkflowOutputEvent outputEvt)
    {
        // Handle output
    }
}

// After - unified handling possible
await foreach (WorkflowEvent evt in stream)
{
    if (evt is WorkflowOutputEvent outputEvt)
    {
        // Can now handle both types uniformly
        var data = outputEvt.Data;
        
        // Still have access to specific types when needed
        if (outputEvt is AgentResponseUpdateEvent updateEvt)
        {
            // Handle streaming update specifically
        }
    }
}
```

## 🎯 Major Features

### .NET: InvokeFunctionTool for Declarative Workflows

**PR**: [#4014](https://github.com/microsoft/agent-framework/pull/4014)

This powerful new feature allows workflows to invoke function tools directly without going through an AI agent first. This enables pre-fetching data or executing operations before calling an AI agent, improving efficiency and workflow control.

**Key Capabilities:**

- Direct function invocation from workflows
- Pre-fetch data before AI agent calls
- Execute operations without LLM roundtrips
- Works with declarative YAML workflow definitions

**Example Implementation:**

```csharp
// Create menu plugin with functions that can be invoked directly
MenuPlugin menuPlugin = new();
AIFunction[] functions = [
    AIFunctionFactory.Create(menuPlugin.GetMenu),
    AIFunctionFactory.Create(menuPlugin.GetSpecials),
    AIFunctionFactory.Create(menuPlugin.GetItemPrice),
];

// Create workflow factory from YAML
WorkflowFactory workflowFactory = new("InvokeFunctionTool.yaml", foundryEndpoint);

// Execute workflow with direct function invocation
WorkflowRunner runner = new(functions) { UseJsonCheckpoints = true };
await runner.ExecuteAsync(workflowFactory.CreateWorkflow, workflowInput);
```

**Agent Definition:**

Note that the agent can be created without function tools in its definition - the workflow handles tool invocation directly:

```csharp
PromptAgentDefinition DefineMenuAgent(IConfiguration configuration)
{
    return new PromptAgentDefinition(modelName)
    {
        Instructions = """
            Answer the users questions about the menu.
            Use the information provided in the conversation history to answer questions.
            If the information is already available in the conversation, use it directly.
            """
    };
    // No tools needed - workflow invokes them directly!
}
```

**Benefits:**

- Reduce latency by pre-fetching data
- Execute deterministic operations without LLM calls
- Better control over workflow execution order
- More efficient use of AI model resources

---

### .NET: Foundry Evaluation Samples (Safety + Quality)

**PR**: [#3697](https://github.com/microsoft/agent-framework/pull/3697)

Comprehensive samples demonstrating Azure AI Foundry's evaluation capabilities, including red teaming for safety assessment and quality evaluations.

**Red Teaming Sample:**

The red teaming sample demonstrates how to assess AI model safety and resilience against adversarial attacks:

**Attack Strategies:**

| Strategy | Description |
|----------|-------------|
| Easy | Simple encoding/obfuscation attacks (ROT13, Leetspeak, etc.) |
| Moderate | Moderate complexity attacks requiring an LLM for orchestration |
| Jailbreak | Crafted prompts designed to bypass AI safeguards (UPIA) |

**Risk Categories:**

| Category | Description |
|----------|-------------|
| Violence | Content related to violence |
| HateUnfairness | Hate speech or unfair content |
| Sexual | Sexual content |
| SelfHarm | Self-harm related content |

**Configuration Example:**

```bash
# Environment Variables
$env:AZURE_FOUNDRY_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/your-project"
$env:AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME="gpt-4o-mini"
```

**Regional Requirements:**

Red teaming is only available in specific regions that support risk and safety evaluators:
- **East US 2**
- **Sweden Central** 
- **US North Central**
- **France Central**
- **Switzerland West**

**Expected Behavior:**

1. Configure a `RedTeam` run targeting the specified model deployment
2. Define risk categories and attack strategies
3. Submit the scan to Azure AI Foundry's Red Teaming service
4. Poll for completion (may take several minutes)
5. Review results in the Azure AI Foundry portal

**Interpreting Results:**

- Results appear in the **classic** Azure AI Foundry portal view (toggle at top-right)
- Lower Attack Success Rate (ASR) is better - target **ASR < 5% for production**
- Review individual attack conversations to understand vulnerabilities

**Important Limitations:**

> The .NET Red Teaming API (`Azure.AI.Projects`) currently supports targeting **model deployments only** via `AzureOpenAIModelConfiguration`. The `AzureAIAgentTarget` type exists in the SDK but is consumed by the **Evaluation Taxonomy** API (`/evaluationtaxonomies`), not by the Red Teaming API (`/redTeams/runs`).

---

## 🔧 Python: Comprehensive Sample Fixes

The February 18 update includes extensive fixes across Python samples, ensuring they work correctly and follow best practices. Here are the highlights:

### Python: Fixed Hosted MCP Tool Approval Flow

**PR**: [#4054](https://github.com/microsoft/agent-framework/pull/4054)

Fixed the hosted MCP (Model Context Protocol) tool approval flow to work correctly across all session and streaming combinations. This ensures that approval requests and responses for hosted MCP tools pass through correctly to the service without local interception.

**Key Fix:**

When an MCP approval response has `server_label` in `function_call.additional_properties`, the function invocation layer now correctly passes it through without attempting local execution:

```python
# Simulate an MCP approval request from the service (has server_label)
mcp_function_call = Content.from_function_call(
    call_id="mcpr_abc123",
    name="microsoft_docs_search",
    arguments='{"query": "azure storage"}',
    additional_properties={"server_label": "Microsoft_Learn_MCP"},
)

mcp_approval_request = Content.from_function_approval_request(
    id="mcpr_abc123",
    function_call=mcp_function_call,
)

mcp_approval_response = mcp_approval_request.to_function_approval_response(
    approved=True
)
```

**Helper Function:**

```python
def _is_hosted_tool_approval(content) -> bool:
    """Check if content is a hosted tool approval (has server_label)."""
    if content is None or not hasattr(content, 'type'):
        return False
        
    if content.type == "function_approval_request":
        fc = getattr(content, 'function_call', None)
        if fc and hasattr(fc, 'additional_properties'):
            return 'server_label' in fc.additional_properties
            
    if content.type == "function_approval_response":
        fc = getattr(content, 'function_call', None)
        if fc and hasattr(fc, 'additional_properties'):
            return 'server_label' in fc.additional_properties
            
    return False
```

**Mixed Local and Hosted Approvals:**

The fix also handles scenarios with both local and hosted MCP approvals in the same response - local approvals are processed normally while hosted MCP approvals pass through untouched to the API.

---

### Python: Improved .env Handling and Observability

**PR**: [#4032](https://github.com/microsoft/agent-framework/pull/4032)

Significant improvements to environment variable handling and observability in Python samples.

**Priority Order Changed:**

The `load_settings` function now uses a more intuitive priority order:

**Before:**
1. Explicit overrides
2. Environment variables
3. `.env` file
4. Defaults

**After:**
1. Explicit keyword overrides
2. `.env` file (when `env_file_path` is explicitly provided)
3. Environment variables
4. Defaults

**Key Changes:**

```python
def load_settings(
    settings_type: type[SettingsT],
    env_prefix: str = "",
    env_file_path: str | None = None,
    env_file_encoding: str | None = None,
    required_fields: Sequence[str | tuple[str, ...]] | None = None,
    **overrides: Any,
) -> SettingsT:
    """Load settings from explicit overrides, an optional .env file, and environment variables.
    
    Values are resolved in this order (highest priority first):
    1. Explicit keyword overrides (None values are filtered out).
    2. A .env file (when env_file_path is explicitly provided).
    3. Environment variables (<env_prefix><FIELD_NAME>).
    4. Default values - fields with class-level defaults on the TypedDict, or None for optional fields.
    """
```

**Implementation:**

```python
# Load .env values when explicitly provided
loaded_dotenv_values: dict[str, str] = {}
if env_file_path is not None:
    if not os.path.exists(env_file_path):
        raise FileNotFoundError(env_file_path)
    
    raw_dotenv_values = dotenv_values(dotenv_path=env_file_path, encoding=encoding)
    loaded_dotenv_values = {
        key: value 
        for key, value in raw_dotenv_values.items() 
        if key is not None and value is not None
    }

# Resolution order for each field:
# 1. Override value
# 2. Optional .env value (only when env_file_path is explicitly provided)
# 3. Environment variable
# 4. Default from TypedDict class-level defaults, or None for optional fields
```

**Benefits:**

- `.env` files are now explicitly opt-in (must provide `env_file_path`)
- Process environment variables take precedence over `.env` files (better for CI/CD)
- More predictable behavior in containerized environments
- Required file check when path is explicitly provided

---

### Python: Fixed Redis Context Provider and Samples

**PR**: [#4030](https://github.com/microsoft/agent-framework/pull/4030)

Fixed Redis context provider examples and clarified memory scoping behavior with Mem0.

**Key Improvements:**

1. **Simplified Cross-Session Memory:**

```python
async def example_cross_session_memory() -> None:
    """Example 1: Cross-session memory (memories shared across all sessions for a user)."""
    user_id = "user123"
    
    async with (
        AzureCliCredential() as credential,
        AzureAIAgentClient(credential=credential).as_agent(
            name="MemoryAssistant",
            instructions="You are an assistant that remembers user preferences across conversations.",
            tools=get_user_preferences,
            context_providers=[Mem0ContextProvider(user_id=user_id)],  # Shared across sessions
        ) as agent,
    ):
        # Store preferences
        query = "Remember that I prefer technical responses with code examples."
        result = await agent.run(query)
        
        # Wait for async processing
        await asyncio.sleep(12)
        
        # Create new session - memories still accessible
        new_session = agent.create_session()
        query = "What do you know about my preferences?"
        result = await agent.run(query, session=new_session)
```

2. **Agent-Scoped Memory:**

```python
async def example_agent_scoped_memory() -> None:
    """Example 2: Agent-scoped memory (memories isolated per agent)."""
    
    async with (
        AzureCliCredential() as credential,
        AzureAIAgentClient(credential=credential).as_agent(
            name="PersonalAssistant",
            context_providers=[Mem0ContextProvider(agent_id="agent_personal")],
        ) as personal_agent,
        AzureAIAgentClient(credential=credential).as_agent(
            name="WorkAssistant",
            context_providers=[Mem0ContextProvider(agent_id="agent_work")],
        ) as work_agent,
    ):
        # Each agent maintains separate memories
        await personal_agent.run("I have a dentist appointment at 3 PM")
        await work_agent.run("Schedule team meeting for Thursday")
        
        await asyncio.sleep(12)  # Wait for indexing
        
        # Memory isolation - each agent only recalls its own memories
        result = await personal_agent.run("What do you know about my schedule?")
        # Returns dentist appointment, not team meeting
```

**Documentation Updates:**

- Removed confusing `scope_to_per_operation_thread_id` parameter
- Clarified that Mem0 scopes by `user_id` or `agent_id`, not by session
- Added explicit wait times for asynchronous memory indexing
- Better explanation of memory isolation patterns

---

### Python: Fixed AutoGen Migration and Tool Samples

**PR**: [#4027](https://github.com/microsoft/agent-framework/pull/4027)

Comprehensive fixes to AutoGen migration samples ensuring they work correctly with the latest API.

**Key Fixes:**

1. **Correct Message List Usage:**

```python
# Before - passing string directly
response = await client.get_response(message, tools=get_time)

# After - passing Message list
messages = [Message(role="user", text=message)]
response = await client.get_response(messages, tools=get_time)
```

2. **Fixed Orchestration Display:**

```python
# Before - streaming with AgentResponseUpdate
async for event in workflow.run("Create a brief summary", stream=True):
    if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
        # Complex executor tracking
        print(event.data.text, end="", flush=True)

# After - using final messages
async for event in workflow.run("Create a brief summary", stream=True):
    if event.type == "output" and isinstance(event.data, list):
        for message in event.data:
            if isinstance(message, Message) and message.role == "assistant":
                print(f"---------- {message.author_name} ----------")
                print(message.text)
```

3. **Fixed Session Injection:**

```python
# Before - session not properly passed to tools
await agent.run('What is the weather in London?', session=session)

# After - pass session via additional_function_arguments
opts = {"additional_function_arguments": {"session": session}}
await agent.run('What is the weather in London?', session=session, options=opts)
```

4. **Fixed Handoff Responses:**

```python
# Before - passing raw string
responses: dict[str, Any] = {
    req.request_id: user_response for req in pending_requests
}

# After - create proper response object
responses: dict[str, Any] = {
    req.request_id: HandoffAgentUserRequest.create_response(user_response) 
    for req in pending_requests
}
```

5. **Fixed AutoGen Stream Method:**

```python
# Before - incorrect streaming API
await Console(agent.run(task="Count from 1 to 5", stream=True))

# After - use run_stream method
await Console(agent.run_stream(task="Count from 1 to 5"))
```

---

### Python: Fixed OpenAI Image Generation Example

**PR**: [#4056](https://github.com/microsoft/agent-framework/pull/4056)

Fixed the OpenAI image generation streaming example to correctly extract file extensions from media types.

**The Fix:**

```python
# Before - hardcoded extension
filename = output_dir / f"image{image_count}.png"

# After - extract extension from media_type
extension = "png"  # Default fallback
if content.media_type and "/" in content.media_type:
    extension = content.media_type.split("/")[-1]

filename = output_dir / f"image{image_count}.{extension}"
```

**Applied to both content types:**

1. Direct URI content with `is_partial_image` flag
2. `image_generation_tool_result` content with image outputs

This ensures images are saved with the correct file extension based on their actual media type (e.g., `.png`, `.jpg`, `.webp`).

---

### Python: Fixed Workflow Samples (Part 1)

**PR**: [#4055](https://github.com/microsoft/agent-framework/pull/4055)

Refactored workflow samples to improve code clarity and fix human feedback handling.

**Key Improvements:**

1. **Extracted Stream Consumption Logic:**

```python
async def consume_stream(stream: AsyncIterable[WorkflowEvent]) -> dict[str, str] | None:
    """Consume a workflow event stream, printing outputs and returning any pending human responses."""
    requests: list[WorkflowEvent] = []
    
    async for event in stream:
        if event.type == "request_info" and isinstance(event.data, DraftFeedbackRequest):
            # Stash the request so we can prompt the human after the stream completes
            requests.append(event)
    
    if requests:
        pending_responses: dict[str, str] = {}
        for request in requests:
            print("\n----- Writer draft -----")
            print(request.data.draft_text.strip())
            print("\nProvide guidance for the editor (or 'approve' to accept the draft).")
            answer = input("Human feedback: ").strip()
            
            if answer.lower() == "exit":
                print("Exiting...")
                exit(0)
                
            pending_responses[request.request_id] = answer
        
        return pending_responses
    
    return None
```

2. **Simplified Main Loop:**

```python
async def main() -> None:
    """Run the workflow and bridge human feedback between two agents."""
    
    # Build workflow
    workflow = (
        WorkflowBuilder()
        .add_agent_executor("writer", writer_agent)
        .add_agent_executor("editor", editor_agent)
        .build()
    )
    
    # Initial run
    stream = workflow.run(
        "Create a short launch blurb for the LumenX desk lamp.",
        stream=True,
    )
    pending_responses = await consume_stream(stream)
    
    # Run until there are no more requests
    while pending_responses is not None:
        stream = workflow.run(stream=True, responses=pending_responses)
        pending_responses = await consume_stream(stream)
    
    print("Workflow complete.")
```

**Benefits:**

- Cleaner separation of concerns
- Easier to understand and maintain
- More robust error handling
- Better user experience with clearer prompts

---

### Python: Fixed Azure AI Sample Errors

**PR**: [#4021](https://github.com/microsoft/agent-framework/pull/4021)

Fixed Azure AI file search sample to use the correct APIs for file upload and vector store management.

**Key Changes:**

1. **Use AIProjectClient for OpenAI operations:**

```python
async with (
    AzureCliCredential() as credential,
    AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], 
        credential=credential
    ) as project_client,
    AzureAIProjectAgentProvider(project_client=project_client) as provider,
):
    openai_client = project_client.get_openai_client()
```

2. **Fixed File Upload:**

```python
# Before - using agents_client
file = await agents_client.files.upload_and_poll(
    file_path=str(pdf_file_path), 
    purpose="assistants"
)

# After - using openai_client with vector store
vector_store = await openai_client.vector_stores.create(name="my_vectorstore")

with open(pdf_file_path, "rb") as f:
    file = await openai_client.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id,
        file=f,
    )
```

3. **Fixed Cleanup:**

```python
# Before - separate deletions
if vector_store:
    await agents_client.vector_stores.delete(vector_store.id)
if file:
    await agents_client.files.delete(file.id)

# After - unified cleanup (deleting vector store also deletes files)
with contextlib.suppress(Exception):
    await openai_client.vector_stores.delete(vector_store.id)
```

---

## 🔄 .NET Updates

### .NET: Fixed MCP Samples and Updated SDK

**PR**: [#3959](https://github.com/microsoft/agent-framework/pull/3959)

Updated MCP (Model Context Protocol) samples to use SDK version **0.8.0-preview.1** and fixed README references.

**Package Updates:**

```xml
<!-- Before -->
<PackageVersion Include="ModelContextProtocol" Version="0.4.0-preview.3" />
<PackageVersion Include="System.Net.ServerSentEvents" Version="10.0.1" />

<!-- After -->
<PackageVersion Include="ModelContextProtocol" Version="0.8.0-preview.1" />
<PackageVersion Include="System.Net.ServerSentEvents" Version="10.0.3" />
```

**OAuth Configuration Update:**

```csharp
// Updated OAuth configuration for MCP
OAuth = new()
{
    DynamicClientRegistration = new()
    {
        ClientName = "ProtectedMcpClient",
    },
    RedirectUri = new Uri("http://localhost:1179/callback"),
    AuthorizationRedirectDelegate = HandleAuthorizationUrlAsync,
}
```

**Documentation Fixes:**

- Updated README references from `ModelContextProtocolPluginAuth` → `Agent_MCP_Server`
- Fixed step-by-step instructions for running protected MCP samples
- Corrected sample names in cross-references

---

### .NET: Disabled Intermittently Failing Tests

**PR**: [#3997](https://github.com/microsoft/agent-framework/pull/3997)

Temporarily disabled intermittently failing `AzureAIAgentsPersistent` integration tests to improve CI/CD reliability while issues are being investigated.

---

### .NET: Inline Private RunCoreAsync

**PR**: [#3928](https://github.com/microsoft/agent-framework/pull/3928)

Refactored internal async execution by inlining the private `RunCoreAsync` method into the protected one, simplifying the codebase and improving maintainability.

---

## 🐛 Additional Python Sample Fixes

### Fixed Declarative Samples

**PR**: [#4051](https://github.com/microsoft/agent-framework/pull/4051)

Fixed issues in declarative workflow samples to ensure they work correctly with the latest API.

---

### Fixed File Search and Web Search Samples

**PR**: [#4049](https://github.com/microsoft/agent-framework/pull/4049)

Corrected file search and web search sample implementations to follow current best practices.

---

### Fixed SK Migration Samples

**PR**: [#4046](https://github.com/microsoft/agent-framework/pull/4046)

Updated Semantic Kernel (SK) migration samples to work with the latest framework APIs.

---

### Fixed Eval Samples

**PR**: [#4033](https://github.com/microsoft/agent-framework/pull/4033)

Fixed evaluation sample code to ensure proper execution and accurate results.

---

### Fixed Anthropic and GitHub Copilot Samples

**PR**: [#4025](https://github.com/microsoft/agent-framework/pull/4025)

Updated Anthropic and GitHub Copilot integration samples with correct API usage patterns.

---

### Fixed Middleware and Multimodal Input Samples

**PR**: [#4022](https://github.com/microsoft/agent-framework/pull/4022)

Fixed middleware configuration and multimodal input handling in sample code.

---

## 📊 Summary

The February 18, 2026 update represents a major quality and feature milestone for the Agent Framework:

### Breaking Changes
- **1 critical breaking change** in .NET: Event system unification requires updates to event handling code

### Major Features
- **InvokeFunctionTool**: Direct function invocation in declarative workflows without LLM roundtrips
- **Foundry Evaluation Samples**: Comprehensive red teaming and quality evaluation examples

### Python Improvements
- **12 sample fix PRs** covering MCP tools, AutoGen migration, Azure AI, Redis context, workflows, and more
- Improved `.env` handling with better priority order
- Fixed image generation, tool approvals, and session management

### .NET Improvements  
- **MCP SDK updated** to 0.8.0-preview.1
- Code refactoring for better maintainability
- Test reliability improvements

### Impact Assessment

**High Priority - Action Required:**
- If you're using .NET workflows with custom event handling, review and update your code for the unified event system
- Test your workflows to ensure `WorkflowOutputEvent` handling works correctly with the inheritance changes

**Recommended Actions:**
- Update to MCP SDK 0.8.0-preview.1 for .NET projects
- Review Python samples if you're using similar patterns - many edge cases have been fixed
- Explore the new InvokeFunctionTool feature for workflow optimization
- Try the Foundry Evaluation samples to assess your AI model safety and quality

**Low Priority:**
- Python sample fixes are backward compatible in most cases
- .NET refactoring changes are internal and don't affect public APIs

### What's Next

This release demonstrates the framework's commitment to:
- **Robustness**: Extensive sample fixes ensure developers have working reference implementations
- **Innovation**: New features like InvokeFunctionTool expand workflow capabilities
- **Safety**: Comprehensive evaluation samples help teams build secure AI systems
- **Quality**: Breaking changes are carefully considered and well-documented

The Agent Framework continues to evolve as a production-ready platform for building sophisticated AI agent systems.

---

**Related Links:**
- [Agent Framework Repository](https://github.com/microsoft/agent-framework)
- [Breaking Change PR #3441](https://github.com/microsoft/agent-framework/pull/3441)
- [InvokeFunctionTool PR #4014](https://github.com/microsoft/agent-framework/pull/4014)
- [Foundry Evaluation PR #3697](https://github.com/microsoft/agent-framework/pull/3697)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
