# Agent Framework Updates - February 26, 2026

The Microsoft Agent Framework concluded another highly productive day with **19 merged pull requests** on February 26, 2026. This update brings a major samples restructuring initiative, critical bug fixes across Python implementations, enhanced .NET features for chat history management and skill execution, plus important improvements to workflow continuity and tool handling.

## 🔄 Major Restructuring: Samples Learning Path

### 1. Python/.NET Samples - Comprehensive Restructure (#4092)

The largest PR of the day represents a **massive overhaul** of the sample organization across both Python and .NET, creating structured learning paths for developers.

**New Learning Path Structure:**

The samples have been reorganized into progressive learning steps:

```
samples/
├── 01-getting-started/
│   └── Basic agent creation and configuration
├── 02-agents/
│   ├── Step01_SimpleAgent
│   ├── Step02_AgentWithTools
│   ├── Step03_MultiAgent
│   └── ...
├── 03-workflows/
│   ├── Step01_BasicWorkflow
│   ├── Step02_StateManagement
│   └── ...
├── 04-hosting/
│   ├── ConsoleApps/
│   └── AzureFunctions/
└── 05-advanced/
    └── Enterprise integration patterns
```

**Key Improvements:**

- **Progressive Learning**: Samples now start from Step01 instead of scattered numbering
- **Consistent Naming**: Configuration settings standardized across all samples
- **Documentation Updates**: Fixed broken markdown links throughout documentation
- **Parity Restoration**: AzureFunctions and ConsoleApps samples now have identical coverage
- **Script Organization**: Moved scripts to dedicated scripts folder for better project structure

**Migration Impact:**

```csharp
// Old path structure (deprecated)
samples/Durable/Agent_Step04_WithMemory

// New path structure
samples/02-agents/Agent_Step04_AgentWithMemory
```

All internal documentation links have been updated to reflect the new structure. This restructuring significantly improves the onboarding experience for new developers learning the framework.

## 🐛 Critical Python Bug Fixes

### 2. Python: Fix WorkflowAgent Not Persisting Response Messages (#4319)

**Issue**: Multi-turn conversations with WorkflowAgent were broken because response messages were never stored in session history.

`WorkflowAgent._run_impl()` and `_run_stream_impl()` did not set `session_context._response` before calling `_run_after_providers()`. This caused `InMemoryHistoryProvider.after_run()` to see `context.response` as None, preventing response messages from being stored.

**Before (Broken):**
```python
class WorkflowAgent(Agent):
    async def _run_impl(self, session, messages, **kwargs):
        result = await self.workflow.run(...)
        
        # BUG: Missing response assignment before after_run providers
        await self._run_after_providers(session_context)
        
        return result
```

On subsequent runs, the workflow only received prior user inputs without assistant responses, breaking conversation continuity.

**After (Fixed):**
```python
class WorkflowAgent(Agent):
    async def _run_impl(self, session, messages, **kwargs):
        result = await self.workflow.run(...)
        
        # FIX: Set response before running after providers
        session_context._response = result
        await self._run_after_providers(session_context)
        
        return result
```

This fix ensures WorkflowAgent matches the behavior of the regular Agent class, properly persisting conversation history across turns.

### 3. Python: Preserve File Citations and Annotations in Assistants API Streaming (#4320)

**Issue**: During Assistants API streaming, file citation and file path annotations were ignored, causing raw placeholder strings to appear instead of resolved metadata.

**Before (Broken):**
```python
# Output seen by downstream consumers (including AG-UI):
"According to the documentation【4:0†source】, the API requires authentication."
```

The streaming implementation ignored `TextDeltaBlock.text.annotations` when creating Content objects, passing through raw placeholders like `【4:0†source】` instead of resolving them to citation metadata.

**After (Fixed):**
```python
# Now properly maps annotations from streaming delta blocks
def _create_content_from_delta(delta_block):
    content = TextContent(text=delta_block.text.value)
    
    # Map FileCitationDeltaAnnotation and FilePathDeltaAnnotation
    if delta_block.text.annotations:
        content.annotations = [
            _map_annotation(ann) 
            for ann in delta_block.text.annotations
        ]
    
    return content

# Output with resolved citations:
{
    "text": "According to the documentation, the API requires authentication.",
    "annotations": [{
        "type": "file_citation",
        "file_id": "file-abc123",
        "quote": "authentication required"
    }]
}
```

The fix maps `FileCitationDeltaAnnotation` and `FilePathDeltaAnnotation` to Annotation objects on the Content, consistent with existing patterns in `_responses_client.py` and `_chat_client.py`.

### 4. Python: Fix Agent Option Merge for Dict-Defined Tools (#4314)

**Issue**: Dictionary-style tool definitions were silently dropped during option merging due to incorrect tool name extraction.

`_merge_options` used `getattr(tool, 'name', None)` to de-duplicate tools, which returns None for dict-style tool definitions. This caused all override dict tools to be treated as duplicates of each other and of any base dict tools, silently dropping them.

**Before (Broken):**
```python
def _merge_options(base_options, override_options):
    existing_names = {getattr(tool, 'name', None) for tool in base_tools}
    # BUG: All dict tools return None, treated as same tool
    
    # Result: Only one dict tool survives, rest silently dropped
```

**After (Fixed):**
```python
def _get_tool_name(tool) -> str | None:
    """Extract name from both object-style and dict-style tools."""
    if hasattr(tool, 'name'):
        return tool.name  # Object-style: tool.name
    elif isinstance(tool, dict):
        # Dict-style: tool['function']['name']
        func = tool.get('function')
        if isinstance(func, dict):
            return func.get('name')
    return None

def _merge_options(base_options, override_options):
    existing_names = {
        _get_tool_name(tool) 
        for tool in base_tools 
        if _get_tool_name(tool) is not None
    }
    # Now correctly handles both dict and object tools
```

**Example Usage:**
```python
# Both styles now work correctly in agent options
agent_options = AgentOptions(
    tools=[
        # Object-style
        FunctionTool(name="search", ...),
        
        # Dict-style
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform calculations"
            }
        }
    ]
)
```

The fix also excludes None from `existing_names` set so nameless/malformed tools are not silently deduplicated against each other.

### 5. Python: Fix Single-Tool Input Handling in OpenAI Responses Client (#4312)

**Issue**: Passing a single tool (not wrapped in a list) to OpenAI Responses Client caused iteration failures.

**Fix**: Use `normalize_tools()` in `_prepare_tools_for_openai` to wrap single tools (FunctionTool or dict) in a list before iteration, consistent with the chat client implementation.

**Before:**
```python
def _prepare_tools_for_openai(tools):
    if not tools:
        return []
    
    # BUG: Assumes tools is always iterable
    return [_convert_tool(t) for t in tools]
```

**After:**
```python
from semantic_kernel.utils.tool_utils import normalize_tools

def _prepare_tools_for_openai(tools: ToolTypes) -> list[dict]:
    # Normalize single tools to list format
    tools = normalize_tools(tools)
    
    if not tools:
        return []
    
    return [_convert_tool(t) for t in tools]
```

### 6. Python: Strip Reserved Kwargs in AgentExecutor (#4298)

**Issue**: Passing `session=` through `workflow.run()` caused TypeError due to duplicate keyword arguments.

`workflow.run(session=...)` passed 'session' through to `agent.run()` via `**run_kwargs` while `AgentExecutor` also passes `session=self._session` explicitly, causing:
```python
TypeError: got multiple values for keyword argument 'session'
```

**Fix**: `_prepare_agent_run_args` now strips reserved params (session, stream, messages) from run_kwargs and logs a warning:

```python
_RESERVED_RUN_PARAMS = frozenset(['session', 'stream', 'messages'])

def _prepare_agent_run_args(self, run_kwargs):
    # Strip reserved parameters
    stripped = {
        k: v for k, v in run_kwargs.items() 
        if k not in _RESERVED_RUN_PARAMS
    }
    
    if len(stripped) < len(run_kwargs):
        logger.warning(
            f"Stripped reserved parameters from run kwargs: "
            f"{set(run_kwargs) - set(stripped)}"
        )
    
    return {
        'session': self._session,  # Always use executor's session
        'stream': self.stream,
        **stripped  # Custom kwargs without conflicts
    }
```

### 7. Python: Align HandoffBuilder Type Signatures with Runtime Requirements (#4302)

**Issue**: `HandoffBuilder.participants()` accepted `SupportsAgentRun` by API contract, but `build()` failed at runtime because `_prepare_agent_with_handoffs()` requires Agent instances.

**Fix**: Update all public type hints, docstrings, and validation to require Agent explicitly:

```python
# Before (misleading API)
class HandoffBuilder:
    def participants(
        self, 
        *agents: SupportsAgentRun  # Too permissive
    ) -> HandoffBuilder:
        ...

# After (correct API)
class HandoffBuilder:
    def participants(
        self, 
        *agents: Agent  # Matches runtime requirement
    ) -> HandoffBuilder:
        # Early validation with clear error
        for agent in agents:
            if not isinstance(agent, Agent):
                raise TypeError(
                    f"HandoffBuilder requires Agent instances for "
                    f"cloning, tool injection, and middleware. "
                    f"Got {type(agent).__name__}"
                )
        ...
```

The isinstance check is now performed early in `participants()` with a clear error message explaining why Agent is required (for cloning, tool injection, and middleware support).

### 8. Python: Preserve Workflow Run Kwargs on Continuation (#4296)

**Issue**: When continuing a paused workflow with `run(responses=...)`, the existing run kwargs stored in state were unconditionally overwritten with an empty dict, losing custom context.

**Before (Broken):**
```python
# Initial run with custom data
await workflow.run(session, input, custom_data={"user_id": 123})

# Workflow pauses for input

# Continue (BUG: custom_data is lost!)
await workflow.run(session, responses=user_response)
# agent.run() now called without custom_data
```

**After (Fixed):**
```python
def _prepare_run_kwargs(self, run_kwargs, reset_context):
    if run_kwargs is not None:
        # New kwargs explicitly provided - override
        self.set_state(WORKFLOW_RUN_KWARGS_KEY, run_kwargs)
    elif reset_context:
        # Fresh run - initialize to empty
        self.set_state(WORKFLOW_RUN_KWARGS_KEY, {})
    # else: preserve existing kwargs from state
    
    return self.get_state(WORKFLOW_RUN_KWARGS_KEY, {})
```

Now kwargs are only overwritten when:
- New kwargs are explicitly provided (override), or  
- State was just cleared for a fresh run (initialize to {})

On continuation without new kwargs, existing kwargs are preserved across workflow invocations.

### 9. Python: Fix response_format Resolution in Streaming Finalizer (#4291)

**Issue**: When `response_format` was set in `default_options` rather than runtime options, streaming responses had `value=None` because the finalizer didn't see the merged options.

**Before (Broken):**
```python
class BaseAgent:
    def __init__(self, default_options=AgentOptions(response_format=JsonSchema)):
        self.default_options = default_options
    
    async def run(self, session, messages, options=None):
        # Streaming path bug
        return self._create_stream(
            messages,
            options=options  # BUG: Not merged with default_options!
        )
```

**After (Fixed):**
```python
async def run(self, session, messages, options=None):
    # Merge options early
    ctx_holder = {'chat_options': self._merge_options(options)}
    
    return self._create_stream(
        messages,
        options=ctx_holder['chat_options']  # Use merged options
    )
```

The streaming finalizer now uses the merged `chat_options` from the run context, matching the non-streaming path which already uses `ctx['chat_options']`.

### 10. Python: Fix AG-UI Approval Payloads Being Re-processed (#4232)

Fixed a bug in the agent UI where approval payloads were being re-processed on subsequent conversation turns, causing duplicate approvals.

### 11. Python: Fix Bedrock Embedding Test Stub (#4287)

Added missing `meta` attribute to Bedrock embedding test stub to prevent test failures.

### 12. Python: Update Workflow Orchestration Samples (#4285)

Updated workflow orchestration samples to use `AzureOpenAIResponsesClient` for consistency with latest best practices.

## 🔧 .NET Enhancements

### 13. .NET: Add ChatHistory Helpers and Configurable Provider Management (#4224)

Major improvement to chat history management with new extension methods and configurable conflict resolution.

**New Extension Methods:**
```csharp
using Microsoft.Agents.AI.Abstractions;

// Convenient access to in-memory chat history
public static class AgentSessionExtensions
{
    // Get chat history if provider is InMemoryChatHistoryProvider
    public static ChatHistory? GetInMemoryChatHistory(
        this AgentSession session)
    {
        var provider = session.GetChatHistoryProvider();
        return (provider as InMemoryChatHistoryProvider)?.ChatHistory;
    }
    
    // Same with TryGet pattern
    public static bool TryGetInMemoryChatHistory(
        this AgentSession session,
        out ChatHistory? chatHistory)
    {
        chatHistory = session.GetInMemoryChatHistory();
        return chatHistory is not null;
    }
}
```

**Configurable Conflict Handling:**
```csharp
public class ChatClientAgentOptions
{
    // Control ChatHistoryProvider conflict resolution
    
    // Log warning when provider conflict detected (default: true)
    public bool WarnOnChatHistoryProviderConflict { get; set; } = true;
    
    // Throw exception on provider conflict (default: false)
    public bool ThrowOnChatHistoryProviderConflict { get; set; } = false;
    
    // Prefer agent's provider over session's (default: true)
    public bool PreferAgentChatHistoryProvider { get; set; } = true;
}
```

**Updated Sample Usage:**
```csharp
// Agent_Step16_ChatReduction sample now uses extension method
if (session.TryGetInMemoryChatHistory(out var chatHistory))
{
    Console.WriteLine($"Chat history: {chatHistory.Count} messages");
    
    // Perform chat reduction if needed
    if (chatHistory.Count > MAX_HISTORY_SIZE)
    {
        await chatReductionService.ReduceAsync(chatHistory);
    }
}
```

**Key Changes:**
- Changed ChatHistoryProvider initialization from lazy to eager
- Updated conflict detection logic to check options instead of instance property  
- Added warning log message for provider conflicts
- Comprehensive tests for all conflict resolution scenarios

### 14. .NET: Support Hosted Code Interpreter for Skill Script Execution (#4192)

Added support for using a hosted code interpreter service to execute skill scripts, improving security and isolation.

**New Capability:**
```csharp
using Microsoft.Agents.Skills;

// Configure skill executor with hosted code interpreter
var skillExecutor = SkillExecutor.CreateHostedCodeInterpreter(
    endpoint: "https://code-interpreter.example.com",
    apiKey: configuration["CodeInterpreter:ApiKey"]
);

// Skills are executed in isolated hosted environment
var result = await skillExecutor.ExecuteAsync(
    skillCode,
    context,
    cancellationToken
);
```

**Benefits:**
- **Security**: Script execution isolated from main process
- **Resource Control**: Memory and CPU limits enforced by hosted service
- **Multi-tenancy**: Shared interpreter service across agents
- **Monitoring**: Centralized execution logging and metrics

The PR includes comprehensive documentation and samples demonstrating both local and hosted execution modes.

### 15. .NET: AgentThread Serialization Alternatives ADR (#3062)

Added Architecture Decision Record (ADR) documenting the evaluation and decision process for AgentThread serialization approaches.

**Evaluated Options:**
1. **JSON Serialization**: Simple but lossy for complex types
2. **Protocol Buffers**: Efficient but requires schema management
3. **Custom Binary Format**: Maximum control but maintenance overhead
4. **Hybrid Approach**: JSON for structure, binary for blobs

**Decision**: Hybrid approach using JSON for thread metadata and structure with binary attachments stored separately.

### 16. .NET: Revert Parallel Disable (#4324)

Reverted the parallel test execution disable introduced in PR #4313 after identifying and fixing the root cause of test instability.

### 17. .NET: Disable Parallelization for WorkflowRunActivityStopTests (#4313)

Temporarily disabled parallel execution for `WorkflowRunActivityStopTests` to prevent test flakiness while investigating timing-sensitive Activity disposal.

### 18. .NET: Fix Encoding (#4309)

Fixed character encoding issues in file I/O operations to properly handle UTF-8 with BOM and other encodings.

### 19. .NET: Merge and Move Scripts (#4308)

Consolidated and reorganized build/deployment scripts into a dedicated scripts folder, improving maintainability across both Python and .NET codebases.

## 📊 Impact Summary

**By the Numbers:**
- 19 PRs merged in a single day
- 1 massive samples restructuring (800+ files affected)
- 10 Python bug fixes improving reliability
- 4 .NET feature enhancements
- Multiple documentation and infrastructure improvements

**Key Takeaways:**

1. **Developer Experience Transformed**: The samples restructuring creates a clear learning path from basic to advanced concepts, significantly improving onboarding for new developers.

2. **Python Reliability Improvements**: Critical fixes to WorkflowAgent session persistence, tool handling, and streaming behavior eliminate common pitfalls that broke multi-turn conversations.

3. **.NET Chat History Management**: New extension methods and configurable provider conflict resolution give developers fine-grained control over conversation state.

4. **Type Safety and Validation**: Multiple PRs tightened type contracts between API signatures and runtime requirements, catching errors earlier with clearer messages.

5. **Workflow Continuity**: Fixes to kwargs preservation and response_format resolution ensure workflows maintain context across pause/resume cycles.

## 🚨 Migration Notes

### For All Developers:

**Samples Structure Changed**: If you've bookmarked or referenced sample paths, update them:
```bash
# Old paths (broken)
samples/Durable/Agent_Step04_WithMemory
samples/ConsoleApps/BasicWorkflow

# New paths (current)
samples/02-agents/Agent_Step04_AgentWithMemory
samples/03-workflows/Step01_BasicWorkflow
```

### For Python Developers:

**Update to rc2**: If using workflows, update immediately for critical fixes:
```bash
pip install --upgrade semantic-kernel-agents-core>=1.0.0rc2
```

**Check Tool Definitions**: If using dict-style tool definitions, verify they're not being silently dropped:
```python
# Verify your tools after merge
merged_options = agent._merge_options(base_options, override_options)
assert len(merged_options.tools) == expected_count
```

**Review Workflow Kwargs**: If passing custom context through workflows, test continuation:
```python
# Ensure kwargs persist across pauses
await workflow.run(session, input, custom_data={"tenant_id": 123})
# ... workflow pauses ...
await workflow.run(session, responses=response)
# custom_data should still be available to agents
```

### For .NET Developers:

**ChatHistory Access**: Migrate to new extension methods:
```csharp
// Old pattern (still works but verbose)
var provider = session.GetChatHistoryProvider();
if (provider is InMemoryChatHistoryProvider memProvider)
{
    var history = memProvider.ChatHistory;
}

// New pattern (recommended)
if (session.TryGetInMemoryChatHistory(out var history))
{
    // Use history
}
```

**Provider Conflict Handling**: Review options if you have custom providers:
```csharp
var options = new ChatClientAgentOptions
{
    WarnOnChatHistoryProviderConflict = true,   // Log conflicts
    ThrowOnChatHistoryProviderConflict = false, // Don't fail
    PreferAgentChatHistoryProvider = true       // Use agent's provider
};
```

## 🔗 Resources

- [Microsoft Agent Framework Repository](https://github.com/microsoft/agent-framework)
- [Agent Skills Specification](https://agentskills.io/)
- [Samples Documentation](https://github.com/microsoft/agent-framework/tree/main/samples)
- [OpenTelemetry .NET SDK](https://github.com/open-telemetry/opentelemetry-dotnet)

---

*This summary covers PRs merged on February 26, 2026. For detailed code changes and discussions, refer to individual pull requests linked above.*
