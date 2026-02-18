# Agent Framework Updates - February 17, 2026

The Microsoft Agent Framework saw exceptional development activity on February 17, 2026, with 20 merged pull requests bringing critical improvements across both .NET and Python implementations. This update introduces 2 breaking changes, major feature enhancements, comprehensive testing improvements, and numerous bug fixes that significantly enhance the framework's reliability and developer experience.

## ⚠️ BREAKING CHANGES

### 1. Python: Scope Provider State by source_id and Standardize Source IDs

**Impact**: High - Requires updates to context provider implementations and state access patterns

**PR**: [#3995](https://github.com/microsoft/agent-framework/pull/3995)

This breaking change introduces session-scoped provider state management, requiring providers to explicitly scope their state by `source_id` and standardizing source ID naming conventions across the framework.

**Key Changes:**

1. **Session State Scoping**: Provider state must now be accessed with explicit source_id scoping:

**Before:**
```python
await provider.before_run(
    agent=None, 
    session=session, 
    context=ctx, 
    state=session.state
)
```

**After:**
```python
await provider.before_run(
    agent=None, 
    session=session, 
    context=ctx, 
    state=session.state.setdefault(provider.source_id, {})
)
```

2. **Standardized Source IDs**: Context messages now use provider source_id instead of hardcoded strings:

**Before:**
```python
msgs = ctx.context_messages.get("aisearch", [])
assert ctx.context_messages.get("aisearch") is None
```

**After:**
```python
msgs = ctx.context_messages.get(provider.source_id, [])
assert ctx.context_messages.get(provider.source_id) is None
```

3. **Default Source ID Constants**: Providers now define their default source IDs as class constants:

```python
# Using the default source ID constant
provider = AzureAISearchContextProvider(
    source_id=AzureAISearchContextProvider.DEFAULT_SOURCE_ID,
    endpoint="https://test.search.windows.net",
    index_name="test-index"
)
```

**Migration Guide:**

- Update all `before_run` calls to scope state by `provider.source_id`
- Replace hardcoded source ID strings with provider instance properties
- Use `DEFAULT_SOURCE_ID` constants where appropriate
- Review session state access patterns to ensure proper scoping

### 2. .NET: Replace Typed Base Providers with Composition

**Impact**: High - Requires refactoring of custom provider implementations

**PR**: [#3988](https://github.com/microsoft/agent-framework/pull/3988)

This architectural change replaces typed generic base providers with a composition-based approach, simplifying provider implementations and improving flexibility.

**Key Changes:**

1. **Simplified Base Class**: Providers no longer require generic type parameters:

**Before:**
```csharp
public sealed class InMemoryChatHistoryProvider 
    : ChatHistoryProvider<InMemoryChatHistoryProvider.State>
{
    public InMemoryChatHistoryProvider(InMemoryChatHistoryProviderOptions? options = null)
        : base(
            options?.StateInitializer ?? (_ => new State()),
            options?.StateKey,
            options?.JsonSerializerOptions,
            options?.ProvideOutputMessageFilter,
            options?.StorageInputMessageFilter)
    {
        this.ChatReducer = options?.ChatReducer;
    }
}
```

**After:**
```csharp
public sealed class InMemoryChatHistoryProvider : ChatHistoryProvider
{
    private readonly ProviderSessionState<State> _sessionState;
    
    public InMemoryChatHistoryProvider(InMemoryChatHistoryProviderOptions? options = null)
    {
        this._sessionState = new ProviderSessionState<State>(
            options?.StateInitializer ?? (_ => new State()),
            options?.StateKey ?? this.GetType().Name,
            options?.JsonSerializerOptions);
        this.ChatReducer = options?.ChatReducer;
    }
    
    public override string StateKey => this._sessionState.StateKey;
}
```

2. **Composition-Based State Management**: Session state is now managed through a dedicated `ProviderSessionState<T>` component:

```csharp
// State access through composition
var state = this._sessionState.GetOrInitializeState(session);
state.Messages = messages;
```

**Before:**
```csharp
protected override async ValueTask<IEnumerable<ChatMessage>> ProvideChatHistoryAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default)
{
    var state = this.GetOrInitializeState(context.Session);
    // Use state...
}
```

**After:**
```csharp
protected override async ValueTask<IEnumerable<ChatMessage>> ProvideChatHistoryAsync(
    InvokingContext context, 
    CancellationToken cancellationToken = default)
{
    var state = this._sessionState.GetOrInitializeState(context.Session);
    // Use state...
}
```

**Migration Guide:**

- Remove generic type parameters from provider base classes
- Create a `ProviderSessionState<T>` field in your provider
- Replace `this.GetOrInitializeState()` calls with `this._sessionState.GetOrInitializeState()`
- Implement `StateKey` property to return `_sessionState.StateKey`
- Move state initialization logic from base constructor to session state component

## Major Updates

### Python: Fix Anthropic Option Conflicts and Manager Parse Retries

**PR**: [#4000](https://github.com/microsoft/agent-framework/pull/4000)

This PR addresses critical bugs in the Anthropic client implementation, fixing parameter conflicts and adding robust retry logic for group chat parsing failures.

**Key Changes:**

1. **Stripped Unsupported Anthropic Parameters**: The client now properly filters out unsupported kwargs while preserving provider-specific mappings.

2. **Stream Mode Conflict Resolution**: Prevents duplicate `stream` kwarg conflicts at Anthropic SDK call sites:

```python
# Stream mode is now explicitly managed
# Prevents conflicts between provider options and SDK parameters
```

3. **Bounded Default Retries**: Added retry logic with strict prompts for agent-based group chat manager parse failures:

```python
# Addresses issues #3371, #3827, and #3078
# Adds bounded retries with explicit retry prompts
```

**Impact**: Resolves runtime errors when using Anthropic with certain parameter combinations and improves reliability of group chat parsing.

### Python: Add Missing System Instruction Attribute to invoke_agent Span

**PR**: [#4012](https://github.com/microsoft/agent-framework/pull/4012)

This observability fix ensures system instructions from `default_options` are properly captured in telemetry spans.

**Bug Fix:**

**Before:**
```python
# System instructions from default_options were silently dropped
instructions = _get_instructions_from_options(options)
```

**After:**
```python
# Now uses merged_options containing both default and runtime options
instructions = _get_instructions_from_options(merged_options)
```

**Key Improvements:**

- Fixed system instruction extraction in telemetry to use merged options
- Added comprehensive test coverage for instruction merging scenarios
- Covers both streaming and non-streaming modes
- Updated observability sample to demonstrate the fix

### Python: Improve Azure AI Search Package Test Coverage

**PR**: [#4019](https://github.com/microsoft/agent-framework/pull/4019)

This PR achieves 97% test coverage for the Azure AI Search package, enforcing a minimum 85% threshold through CI.

**Coverage Improvements:**

```python
# Added 880+ lines of comprehensive unit tests covering:
# - Initialization and credential resolution
# - Async context manager lifecycle
# - Vector field discovery
# - Semantic search functionality
# - Agentic search patterns
# - Document text extraction
# - Edge cases and error handling
```

**CI Integration:**

```python
# .github/workflows/python-check-coverage.py
# Added azure-ai-search to enforced modules list
enforced_modules = [
    "azure-ai-search",  # New entry
    # ... other modules
]
```

**Impact**: Significantly improves code quality and reliability for Azure AI Search integration.

### Python: MCP Sample Bugbash Fixes

**PR**: [#4001](https://github.com/microsoft/agent-framework/pull/4001)

Corrects API usage errors in MCP sample files discovered during testing.

**Before:**
```python
# Incorrect parameter names (internal dict keys)
get_mcp_tool(
    server_label="github",
    server_url="https://github.com/...",
    require_approval="never"
)
```

**After:**
```python
# Correct API parameters
get_mcp_tool(
    name="github",
    url="https://github.com/...",
    approval_mode="never_require"
)
```

**Additional Changes:**

```python
# Added standard execution block for direct script running
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Python: Track and Enforce 85%+ Unit Test Coverage for Anthropic Package

**PR**: [#3926](https://github.com/microsoft/agent-framework/pull/3926)

Establishes comprehensive test coverage standards for the Anthropic package with CI enforcement.

**Key Achievements:**

- Achieved 90%+ test coverage for Anthropic client
- Added extensive unit tests for streaming and non-streaming modes
- Implemented CI checks to maintain minimum 85% coverage
- Tests cover error handling, retries, and edge cases

## .NET Major Updates

### Update Microsoft.Agents.ObjectModel Packages to 2026.2.2.1

**PR**: [#4003](https://github.com/microsoft/agent-framework/pull/4003)

Updates the ObjectModel packages across the framework to the latest version, bringing bug fixes and improvements for declarative workflows.

**Updated Packages:**

```xml
<PackageReference Include="Microsoft.Agents.ObjectModel" Version="2026.2.2.1" />
<PackageReference Include="Microsoft.Agents.ObjectModel.Serialization" Version="2026.2.2.1" />
```

**Impact**: Ensures compatibility with latest workflow features and fixes.

### Open Active Item in Solution Explorer Automatically

**PR**: [#3992](https://github.com/microsoft/agent-framework/pull/3992)

Improves VS Code developer experience by enabling automatic synchronization with the active item in Solution Explorer.

**Configuration Added:**

```json
{
  "explorer.autoReveal": true,
  "workbench.view.alwaysShowHeaderActions": true
}
```

**Impact**: Better navigation experience when working with .NET projects in VS Code.

### Add Additional Build, Test and Project Structure Skills

**PR**: [#3987](https://github.com/microsoft/agent-framework/pull/3987)

Enhances Copilot skills for better understanding of .NET project structure, build systems, and testing patterns.

**New Skills Include:**

- Build system comprehension for .sln and .csproj files
- Test project identification and execution patterns
- Project dependency graph understanding
- Sample project navigation

**Impact**: Improves AI-assisted development experience in the repository.

## Minor Updates and Bug Fixes

### .NET: Improve Session Cast Error Message Quality and Consistency

**PR**: [#3973](https://github.com/microsoft/agent-framework/pull/3973)

Enhances error messages when session type casting fails in workflow contexts:

```csharp
// More descriptive error messages help developers quickly identify type mismatches
// Consistent formatting across all session-related errors
```

### General Durable Agents Documentation

**PR**: [#3972](https://github.com/microsoft/agent-framework/pull/3972)

Adds comprehensive documentation for durable agents, including:

- Overview of durable agent architecture
- Technical implementation details
- Usage examples and patterns
- Agent instructions for maintaining documentation

**Impact**: Provides centralized reference for developers building durable agents.

### .NET: Surface Downstream Experimental Flags

**PR**: [#3968](https://github.com/microsoft/agent-framework/pull/3968)

Properly surfaces experimental API warnings from downstream dependencies and removes unnecessary warning suppressions:

```csharp
// Experimental APIs are now properly marked
// Developers get appropriate warnings when using experimental features
```

### .NET: Fixing Small Issues from Bugbash

**PR**: [#3961](https://github.com/microsoft/agent-framework/pull/3961)

Multiple small fixes identified during bug bash:

1. **Updated MCP Inspector Command**:

```bash
# Before
dotnet run

# After
dotnet run --framework net10.0
```

2. **Fixed RAG Sample Configuration**:

```csharp
// Added proper chat history filtering
var chatHistoryProvider = new InMemoryChatHistoryProvider(
    new InMemoryChatHistoryProviderOptions
    {
        StorageInputMessageFilter = ChatHistoryProvider.ExcludeAIContextProviderAndChatHistory
    }
);
```

3. **Corrected Documentation Comments**: Fixed comment to match actual code behavior (5 messages instead of 4).

### .NET: Fix Sample Resource Path Resolution

**PR**: [#3952](https://github.com/microsoft/agent-framework/pull/3952)

Fixes resource loading in workflow samples to work correctly with `dotnet run`:

**Before:**
```csharp
var content = File.ReadAllText("Resources/file.txt");
```

**After:**
```csharp
var content = File.ReadAllText(
    Path.Combine(AppContext.BaseDirectory, "Resources", "file.txt")
);
```

**Impact**: Samples now work reliably regardless of working directory.

## Summary

February 17, 2026 was a highly productive day for the Agent Framework, with significant improvements across multiple areas:

### Breaking Changes Impact
- **Python**: Session state scoping requires careful migration but provides better isolation and consistency
- **.NET**: Provider composition pattern simplifies implementations and improves maintainability

### Quality Improvements
- **Test Coverage**: Azure AI Search and Anthropic packages now have >85% coverage with CI enforcement
- **Bug Fixes**: Critical fixes for Anthropic client conflicts and observability instrumentation
- **Documentation**: New durable agents documentation and improved code comments

### Developer Experience
- **Better Tooling**: VS Code integration improvements and enhanced Copilot skills
- **Sample Fixes**: Multiple sample issues resolved for better learning experience
- **Clearer Errors**: Improved error messages for faster debugging

### Recommended Actions

1. **For Python Users**:
   - Review PR #3995 migration guide for state scoping changes
   - Update Anthropic client usage if experiencing parameter conflicts
   - Test observability instrumentation to ensure system instructions are captured

2. **For .NET Users**:
   - Plan migration for custom provider implementations (PR #3988)
   - Update to Microsoft.Agents.ObjectModel 2026.2.2.1
   - Review and apply sample fixes if using similar patterns

3. **For All Users**:
   - Review test coverage for custom provider implementations
   - Update MCP sample usage to match corrected API patterns
   - Read new durable agents documentation if working with persistence

### Statistics

- **Total PRs Merged**: 20
- **Breaking Changes**: 2
- **Major Features**: 8
- **Bug Fixes**: 10
- **Languages**: Python, C#
- **Test Coverage Improvements**: +15% for Azure AI Search, +10% for Anthropic
- **Documentation Additions**: 3 PRs

This release demonstrates the framework's continued evolution toward production readiness, with a strong focus on reliability, testability, and developer experience. The breaking changes, while requiring migration effort, provide better foundations for scalable agent applications.
