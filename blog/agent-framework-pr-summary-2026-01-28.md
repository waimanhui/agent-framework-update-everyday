# Agent Framework Updates - January 28, 2026

On January 28, 2026, the Microsoft Agent Framework merged 9 significant pull requests that reshape the developer experience with **multiple breaking changes** affecting both .NET and Python ecosystems. This release emphasizes standardization, better naming conventions, enhanced type safety, and improved development workflows. All developers should review the breaking changes section carefully before upgrading.

---

## ⚠️ BREAKING CHANGES

### 1. .NET & Python: GitHub Brand Naming Correction

**PR**: [#3486](https://github.com/microsoft/agent-framework/pull/3486)  
**Impact**: HIGH - Requires code changes in all GitHub Copilot integrations  
**Author**: [@dmytrostruk](https://github.com/dmytrostruk)  
**Affects**: .NET and Python

The framework has corrected the branding from "Github" to "GitHub" (with proper capitalization) across all namespaces, class names, and packages.

#### .NET Changes

**Namespace Renamed:**
```csharp
// Before
using Microsoft.Agents.AI.GithubCopilot;

// After
using Microsoft.Agents.AI.GitHub.Copilot;
```

**Class Names Updated:**
```csharp
// Before
var agent = new GithubCopilotAgent(
    copilotClient,
    sessionConfig,
    ownsClient: false
);

var session = new GithubCopilotAgentSession();

// After
var agent = new GitHubCopilotAgent(
    copilotClient,
    sessionConfig,
    ownsClient: false
);

var session = new GitHubCopilotAgentSession();
```

**Package Name Changed:**
```xml
<!-- Before -->
<PackageReference Include="Microsoft.Agents.AI.GithubCopilot" Version="1.2.0" />

<!-- After -->
<PackageReference Include="Microsoft.Agents.AI.GitHub.Copilot" Version="1.2.0" />
```

#### Python Changes

Similar naming corrections applied to Python packages and imports.

#### Migration Guide

**For .NET:**
1. Update package references in your `.csproj` files
2. Update all `using` statements
3. Rename all class instantiations
4. Rebuild your project - the compiler will catch all remaining references

```bash
# Find and replace in your codebase
find . -type f -name "*.cs" -exec sed -i 's/GithubCopilot/GitHub.Copilot/g' {} +
find . -type f -name "*.csproj" -exec sed -i 's/GithubCopilot/GitHub.Copilot/g' {} +
```

**For Python:**
```bash
# Update package installations
pip uninstall agent-framework-github-copilot
pip install agent-framework-github-copilot  # New version with corrected naming
```

---

### 2. Python: AIFunction → FunctionTool and @ai_function → @tool

**PR**: [#3413](https://github.com/microsoft/agent-framework/pull/3413)  
**Impact**: HIGH - Requires code changes in all Python tool implementations  
**Author**: [@eavanvalkenburg](https://github.com/eavanvalkenburg)  
**Fixes**: [#3247](https://github.com/microsoft/agent-framework/issues/3247), [#3368](https://github.com/microsoft/agent-framework/issues/3368)

The Python SDK has renamed `AIFunction` to `FunctionTool` and the `@ai_function` decorator to `@tool` for better alignment with industry standards and improved clarity.

#### Core Changes

**1. Class Rename:**
```python
# Before
from agent_framework import AIFunction

def my_function(param: str) -> str:
    return f"Result: {param}"

func: AIFunction[str, str] = AIFunction(
    name="my_function",
    description="Does something",
    func=my_function,
    parameters={"param": "string"}
)

# After
from agent_framework import FunctionTool

def my_function(param: str) -> str:
    return f"Result: {param}"

func: FunctionTool[str, str] = FunctionTool(
    name="my_function",
    description="Does something",
    func=my_function,
    parameters={"param": "string"}
)
```

**2. Decorator Rename:**
```python
# Before
from agent_framework import ai_function

@ai_function
async def fetch_weather(location: str) -> dict:
    """Fetch weather data for a location."""
    return {"location": location, "temp": 72}

# After
from agent_framework import tool

@tool
async def fetch_weather(location: str) -> dict:
    """Fetch weather data for a location."""
    return {"location": location, "temp": 72}
```

**3. Type Annotations:**
```python
# Before
from agent_framework import AIFunction
from typing import Any

tools: list[AIFunction[Any, Any]] = []

# After
from agent_framework import FunctionTool
from typing import Any

tools: list[FunctionTool[Any, Any]] = []
```

#### Why This Change?

- **Industry Alignment**: `@tool` is more common in AI frameworks (LangChain, Semantic Kernel)
- **Clarity**: "FunctionTool" better describes what it is - a tool that wraps a function
- **Brevity**: Shorter decorator name improves code readability

#### Migration Strategy

**Automated Migration:**
```bash
# Update all imports
find . -name "*.py" -exec sed -i 's/from agent_framework import AIFunction/from agent_framework import FunctionTool/g' {} +
find . -name "*.py" -exec sed -i 's/from agent_framework import ai_function/from agent_framework import tool/g' {} +

# Update decorator usage
find . -name "*.py" -exec sed -i 's/@ai_function/@tool/g' {} +

# Update type annotations
find . -name "*.py" -exec sed -i 's/AIFunction\[/FunctionTool[/g' {} +
find . -name "*.py" -exec sed -i 's/: AIFunction/: FunctionTool/g' {} +
```

**Manual Review Required:**
- Comments and docstrings mentioning "AIFunction"
- Variable names containing "ai_function" or "ai_func"
- External documentation references

---

### 3. Python: GroupChat and Magentic Factory Pattern Updates

**PR**: [#3224](https://github.com/microsoft/agent-framework/pull/3224)  
**Impact**: MEDIUM - Requires code changes in GroupChat and Magentic orchestrations  
**Author**: [@TaoChenOSU](https://github.com/TaoChenOSU)  
**Completes**: [#429](https://github.com/microsoft/agent-framework/issues/429)

This PR introduces factory patterns for GroupChat and Magentic orchestrations and renames key APIs for consistency.

#### Breaking API Changes

**1. `with_standard_manager` → `with_manager`**

The Magentic API no longer uses "standard" in the method name since it supports both standard and custom manager implementations.

```python
# Before
from agent_framework.orchestrations import MagenticBuilder

builder = MagenticBuilder()
builder.with_standard_manager(manager_agent)

# After
from agent_framework.orchestrations import MagenticBuilder

builder = MagenticBuilder()
builder.with_manager(manager_agent)
```

**2. `participant_factories()` → `register_participants()`**

Renamed for consistency with other orchestration APIs.

```python
# Before
from agent_framework.orchestrations import HandoffBuilder

builder = HandoffBuilder()
builder.participant_factories({
    "agent1": lambda: create_agent_1(),
    "agent2": lambda: create_agent_2()
})

# After
from agent_framework.orchestrations import HandoffBuilder

builder = HandoffBuilder()
builder.register_participants({
    "agent1": lambda: create_agent_1(),
    "agent2": lambda: create_agent_2()
})
```

#### New Factory Pattern Features

**GroupChat with Participant Factory:**
```python
from agent_framework.orchestrations import GroupChatBuilder

def create_moderator():
    return ChatAgent(name="Moderator", instructions="Moderate the discussion")

def create_expert():
    return ChatAgent(name="Expert", instructions="Provide expertise")

# Factory pattern allows lazy instantiation
builder = GroupChatBuilder()
builder.register_participant("moderator", create_moderator)
builder.register_participant("expert", create_expert)
builder.with_orchestrator_factory(lambda agents: RoundRobinOrchestrator(agents))

group_chat = builder.build()
```

**Magentic with Manager Factory:**
```python
from agent_framework.orchestrations import MagenticBuilder

def create_manager():
    return ChatAgent(
        name="Manager",
        instructions="Coordinate the team",
        model="gpt-4"
    )

builder = MagenticBuilder()
builder.register_participants({
    "coder": lambda: ChatAgent(name="Coder"),
    "reviewer": lambda: ChatAgent(name="Reviewer")
})
builder.with_manager_factory(create_manager)

workflow = builder.build()
```

#### Benefits of Factory Pattern

1. **Lazy Initialization**: Agents created only when needed
2. **Testability**: Easier to inject mock agents
3. **Resource Efficiency**: Avoid creating expensive resources upfront
4. **Flexibility**: Different agent configurations per environment

#### Migration Checklist

- [ ] Replace `with_standard_manager()` with `with_manager()`
- [ ] Replace `participant_factories()` with `register_participants()`
- [ ] Update error handling for renamed exceptions
- [ ] Update unit tests referencing old API names

---

### 4. .NET: Declarative Object Model Namespace Migration

**PR**: [#3017](https://github.com/microsoft/agent-framework/pull/3017)  
**Impact**: HIGH - Requires namespace and package updates  
**Author**: [@crickman](https://github.com/crickman)  
**Fixes**: [#3018](https://github.com/microsoft/agent-framework/issues/3018)

The Declarative Object Model packages have been migrated from `Microsoft.Bot.ObjectModel.*` to `Microsoft.Agents.ObjectModel.*` to align with the Agent Framework branding.

#### Package Changes

```xml
<!-- Before -->
<PackageReference Include="Microsoft.Bot.ObjectModel" Version="1.2025.1106.1" />
<PackageReference Include="Microsoft.Bot.ObjectModel.Json" Version="1.2025.1106.1" />
<PackageReference Include="Microsoft.Bot.ObjectModel.PowerFx" Version="1.2025.1106.1" />

<!-- After -->
<PackageReference Include="Microsoft.Agents.ObjectModel" Version="2026.1.2.3" />
<PackageReference Include="Microsoft.Agents.ObjectModel.Json" Version="2026.1.2.3" />
<PackageReference Include="Microsoft.Agents.ObjectModel.PowerFx" Version="2026.1.2.3" />
```

#### Namespace Changes

```csharp
// Before
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Json;
using Microsoft.Bot.ObjectModel.PowerFx;

// After
using Microsoft.Agents.ObjectModel;
using Microsoft.Agents.ObjectModel.Json;
using Microsoft.Agents.ObjectModel.PowerFx;
```

#### New Features in 2026.1.2.3

The updated packages include:
- **Media Type Support**: Image and file-based message content now includes media type information
- **Enhanced JSON Serialization**: Improved JSON handling for declarative agents
- **PowerFx Integration**: Better Power Fx expression support

#### Migration Steps

1. **Update Package References:**
```bash
dotnet remove package Microsoft.Bot.ObjectModel
dotnet remove package Microsoft.Bot.ObjectModel.Json
dotnet remove package Microsoft.Bot.ObjectModel.PowerFx

dotnet add package Microsoft.Agents.ObjectModel --version 2026.1.2.3
dotnet add package Microsoft.Agents.ObjectModel.Json --version 2026.1.2.3
dotnet add package Microsoft.Agents.ObjectModel.PowerFx --version 2026.1.2.3
```

2. **Update Namespaces:**
```bash
find . -name "*.cs" -exec sed -i 's/using Microsoft.Bot.ObjectModel/using Microsoft.Agents.ObjectModel/g' {} +
```

3. **Test Thoroughly**: The version jump from 1.x to 2026.x may include additional changes

#### New Media Type Feature

```csharp
using Microsoft.Agents.ObjectModel;

var message = new Message
{
    Content = new MessageContent
    {
        Type = MessageContentType.Image,
        MediaType = "image/png",  // NEW: Media type specification
        Url = "https://example.com/image.png"
    }
};
```

---

## Major Updates

### .NET: Improved Unit Test Coverage for Azure AI (85.6%)

**PR**: [#3383](https://github.com/microsoft/agent-framework/pull/3383)  
**Impact**: MEDIUM - Better reliability and documentation  
**Author**: [@Copilot](https://github.com/Copilot)  
**Fixes**: [#3337](https://github.com/microsoft/agent-framework/issues/3337)

The `Microsoft.Agents.AI.AzureAI` package now has 85.6% test coverage (up from 64.5%), meeting the project's quality standards.

#### Coverage Improvements

| Component | Before | After | Change |
|-----------|--------|-------|--------|
| `AzureAIProjectChatClientExtensions.cs` | 73.99% | 90.08% | +16.09% |
| Overall `Microsoft.Agents.AI.AzureAI` | ~64.5% | 85.6% | +21.1% |

#### New Test Areas

**1. Name Validation:**
```csharp
[Fact]
public async Task GetAIAgentAsync_EmptyName_ThrowsArgumentException()
{
    var client = CreateMockClient();
    
    await Assert.ThrowsAsync<ArgumentException>(
        async () => await client.GetAIAgentAsync(string.Empty)
    );
}

[Fact]
public async Task CreateAIAgentAsync_NullName_ThrowsArgumentNullException()
{
    var client = CreateMockClient();
    
    await Assert.ThrowsAsync<ArgumentNullException>(
        async () => await client.CreateAIAgentAsync(null, "instructions")
    );
}
```

**2. Response Format Handling:**
```csharp
[Fact]
public async Task ChatWithTextResponseFormat_ReturnsPlainText()
{
    var client = CreateMockClient();
    var options = new ChatOptions
    {
        ResponseFormat = ChatResponseFormatText.Instance
    };
    
    var response = await client.GetCompletionAsync("Hello", options);
    
    Assert.NotNull(response);
    Assert.IsType<string>(response.Content);
}

[Fact]
public async Task ChatWithJsonResponseFormat_ReturnsStructuredJson()
{
    var client = CreateMockClient();
    var options = new ChatOptions
    {
        ResponseFormat = new ChatResponseFormatJson
        {
            Schema = MySchema.JsonSchema,
            StrictMode = true
        }
    };
    
    var response = await client.GetCompletionAsync("Generate JSON", options);
    
    Assert.NotNull(response);
    var json = JsonSerializer.Deserialize<MySchema>(response.Content);
    Assert.NotNull(json);
}
```

**3. Tool Validation:**
```csharp
[Fact]
public async Task CallAgent_WithMissingRequiredTools_ThrowsInvalidOperationException()
{
    var agent = CreateAgent(requiredTools: ["tool1", "tool2"]);
    var providedTools = new[] { CreateTool("tool1") }; // Missing tool2
    
    await Assert.ThrowsAsync<InvalidOperationException>(
        async () => await agent.RunAsync("query", tools: providedTools)
    );
}

[Fact]
public async Task CallAgent_WithWrongToolNames_ThrowsArgumentException()
{
    var agent = CreateAgent(requiredTools: ["calculator"]);
    var providedTools = new[] { CreateTool("weather") }; // Wrong tool
    
    await Assert.ThrowsAsync<ArgumentException>(
        async () => await agent.RunAsync("query", tools: providedTools)
    );
}
```

**4. Options Preservation:**
```csharp
[Fact]
public async Task CreateAgent_WithCustomContextProvider_PreservesOptions()
{
    var customProvider = new CustomAIContextProvider();
    var options = new AgentOptions
    {
        AIContextProviderFactory = () => customProvider
    };
    
    var agent = await client.CreateAgentAsync("Agent", options);
    
    // Verify the custom provider is used
    var context = await agent.GetContextAsync();
    Assert.Same(customProvider, context.Provider);
}
```

#### What This Means for You

- **Higher Reliability**: More edge cases are tested and documented
- **Better Error Messages**: Validation tests ensure clear exceptions
- **Code Examples**: Tests serve as usage documentation
- **Regression Prevention**: Future changes less likely to break existing behavior

---

### .NET: Codespaces Enhanced with GitHub Copilot CLI

**PR**: [#3479](https://github.com/microsoft/agent-framework/pull/3479)  
**Impact**: MEDIUM - Improved developer experience  
**Author**: [@rogerbarreto](https://github.com/rogerbarreto)

GitHub Codespaces configuration now includes GitHub Copilot CLI and additional development tools for a better out-of-the-box experience.

#### Updated Codespaces Configuration

```json
{
  "name": "Agent Framework Dev Container",
  "build": {
    "dockerfile": "dotnet.Dockerfile"
  },
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {
      "version": "2"
    },
    "ghcr.io/devcontainers/features/powershell:1": {
      "version": "latest"
    },
    "ghcr.io/azure/azure-dev/azd:0": {
      "version": "latest"
    },
    "ghcr.io/devcontainers/features/dotnet:2": {
      "version": "none",
      "dotnetRuntimeVersions": "10.0",
      "aspNetCoreRuntimeVersions": "10.0"
    },
    "ghcr.io/devcontainers/features/copilot-cli:1": {}  // NEW!
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "GitHub.copilot",
        "GitHub.vscode-github-actions",
        "ms-dotnettools.csdevkit",
        "vscode-icons-team.vscode-icons",
        "ms-windows-ai-studio.windows-ai-studio"
      ]
    }
  }
}
```

#### What You Get

**1. GitHub Copilot CLI Integration:**
```bash
# In your Codespace terminal
gh copilot suggest "how do I run all tests"
# Copilot suggests: dotnet test

gh copilot explain "dotnet build -c Release"
# Copilot explains the command
```

**2. Pre-installed Tools:**
- **GitHub CLI v2**: Interact with GitHub from the terminal
- **Azure Developer CLI (azd)**: Deploy to Azure seamlessly
- **PowerShell**: Cross-platform scripting
- **.NET 10.0 Runtime**: Latest runtime pre-installed

**3. Enhanced VS Code:**
- GitHub Copilot extension pre-installed
- C# Dev Kit for .NET development
- GitHub Actions extension for workflow editing
- Windows AI Studio integration

#### Quick Start with Codespaces

1. **Open in Codespace:**
   ```bash
   # From the repository
   gh cs create -r microsoft/agent-framework
   ```

2. **Start Coding Immediately:**
   - All dependencies pre-installed
   - Copilot CLI ready to assist
   - No local setup required

3. **Use Copilot CLI:**
   ```bash
   # Get help with commands
   gh copilot suggest "build and test the project"
   
   # Explain complex commands
   gh copilot explain "dotnet test --filter Category=Integration"
   ```

---

## Minor Updates and Maintenance

### Python: Updated DurableTask Package

**PR**: [#3492](https://github.com/microsoft/agent-framework/pull/3492)  
**Author**: [@larohra](https://github.com/larohra)

Updated the Python `durabletask` package to the latest version with bug fixes and improvements.

```bash
# Update to latest
pip install --upgrade agent-framework-durabletask
```

---

### Python: Updated Code Owners for DurableTask

**PR**: [#3491](https://github.com/microsoft/agent-framework/pull/3491)  
**Author**: [@larohra](https://github.com/larohra)

Updated `CODEOWNERS` file to reflect the correct maintainers for the `durabletask` package, ensuring proper review assignments.

```
# CODEOWNERS update
/python/packages/agent-framework-durabletask/ @larohra @microsoft/durabletask-team
```

---

### Python: Enhanced Generic Types for ChatOptions and Response Formats

**PR**: [#3305](https://github.com/microsoft/agent-framework/pull/3305)  
**Author**: [@eavanvalkenburg](https://github.com/eavanvalkenburg)  
**Fixes**: [#3091](https://github.com/microsoft/agent-framework/issues/3091)

Added generic type support to `ChatOptions`, `ChatResponse`, and `AgentResponse` for better type inference with response formats.

#### Improved Type Safety

**Before (Type: Any):**
```python
agent = OpenAIResponsesClient().as_agent(name="Agent", instructions="...")
result = await agent.run("Generate data")
# result has type: AgentResponse[Any]
# result.value has type: Any | None
```

**After (Type Inferred):**
```python
from pydantic import BaseModel

class OutputModel(BaseModel):
    name: str
    age: int
    email: str

agent = OpenAIResponsesClient().as_agent(name="Agent", instructions="...")
result = await agent.run("Generate data", options={"response_format": OutputModel})
# result has type: AgentResponse[OutputModel]  ✅ Type inferred!
# result.value has type: OutputModel | None     ✅ Properly typed!

# IDE autocomplete works
print(result.value.name)   # ✅ Autocomplete knows it's a string
print(result.value.age)    # ✅ Autocomplete knows it's an int
```

#### With Streaming:
```python
result = await AgentResponse.from_agent_response_generator(
    agent.run_stream(query, options={"response_format": OutputModel}),
    output_format_type=OutputModel,  # Explicit type for streaming
)
# result has type: AgentResponse[OutputModel]  ✅
```

#### Benefits
- **Better IDE Support**: Full autocomplete for response properties
- **Type Checking**: Catch errors at development time, not runtime
- **Clearer Intent**: Response format is part of the type signature

---

## Summary

This release brings significant breaking changes focused on standardization and best practices:

### Breaking Changes Summary

| Change | Impact | Migration Effort |
|--------|--------|------------------|
| GitHub Naming Correction | **HIGH** | **MEDIUM** - Find and replace across codebase |
| AIFunction → FunctionTool | **HIGH** | **MEDIUM** - Automated with sed, manual review needed |
| GroupChat/Magentic API Rename | **MEDIUM** | **LOW** - Simple method renames |
| Bot.ObjectModel → Agents.ObjectModel | **HIGH** | **MEDIUM** - Package and namespace updates |

### Recommended Actions

#### For .NET Developers (URGENT)

**1. Update GitHub Copilot Integration:**
```bash
dotnet remove package Microsoft.Agents.AI.GithubCopilot
dotnet add package Microsoft.Agents.AI.GitHub.Copilot

# Update all namespaces
find . -name "*.cs" -exec sed -i 's/Microsoft.Agents.AI.GithubCopilot/Microsoft.Agents.AI.GitHub.Copilot/g' {} +
find . -name "*.cs" -exec sed -i 's/GithubCopilot/GitHubCopilot/g' {} +
```

**2. Migrate Object Model Packages:**
```bash
dotnet remove package Microsoft.Bot.ObjectModel
dotnet add package Microsoft.Agents.ObjectModel --version 2026.1.2.3

# Update namespaces
find . -name "*.cs" -exec sed -i 's/Microsoft.Bot.ObjectModel/Microsoft.Agents.ObjectModel/g' {} +
```

**3. Rebuild and Test:**
```bash
dotnet build
dotnet test
```

#### For Python Developers (URGENT)

**1. Migrate from AIFunction to FunctionTool:**
```bash
# Automated migration
find . -name "*.py" -exec sed -i 's/from agent_framework import AIFunction/from agent_framework import FunctionTool/g' {} +
find . -name "*.py" -exec sed -i 's/@ai_function/@tool/g' {} +
find . -name "*.py" -exec sed -i 's/AIFunction\[/FunctionTool[/g' {} +
```

**2. Update GroupChat/Magentic Code:**
```python
# Replace in your code:
# - .with_standard_manager() → .with_manager()
# - .participant_factories() → .register_participants()
```

**3. Update Dependencies:**
```bash
pip install --upgrade agent-framework agent-framework-durabletask
```

**4. Run Tests:**
```bash
pytest tests/
```

#### For All Developers

**Use Codespaces for Easy Development:**
```bash
gh cs create -r microsoft/agent-framework
# Everything pre-configured with Copilot CLI!
```

### Migration Timeline

We recommend completing migration within **2 weeks** as the old APIs and packages will be deprecated in the next release.

### Testing Considerations

- **Breaking Changes**: All breaking changes have comprehensive test coverage
- **Azure AI Tests**: 85.6% coverage ensures reliability
- **Type Safety**: Python generic types reduce runtime errors
- **CI/CD**: Codespaces improvements streamline contributor experience

### Impact Assessment

| Category | Impact Level | Migration Required |
|----------|-------------|-------------------|
| GitHub Copilot Integration | **CRITICAL** | **YES** - Namespace/class renames |
| Python Function Tools | **CRITICAL** | **YES** - Decorator and class renames |
| GroupChat/Magentic | **HIGH** | **YES** - Method renames |
| Object Model Migration | **CRITICAL** | **YES** - Package migration |
| Azure AI Test Coverage | **LOW** | **NO** - Internal improvements |
| Codespaces Configuration | **LOW** | **NO** - Optional upgrade |
| DurableTask Updates | **LOW** | **NO** - Drop-in replacement |
| Type Safety Enhancements | **LOW** | **NO** - Opt-in improvement |

---

**Contributors**: [@dmytrostruk](https://github.com/dmytrostruk), [@eavanvalkenburg](https://github.com/eavanvalkenburg), [@TaoChenOSU](https://github.com/TaoChenOSU), [@crickman](https://github.com/crickman), [@Copilot](https://github.com/Copilot), [@rogerbarreto](https://github.com/rogerbarreto), [@larohra](https://github.com/larohra)

**Total PRs Merged**: 9  
**Breaking Changes**: 4  
**Files Changed**: 200+ files  
**Lines Changed**: ~8,000 additions, ~3,000 deletions  

For detailed code changes, visit the individual PRs linked above.
