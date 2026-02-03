# Agent Framework Updates - February 2, 2026

On February 2, 2026, the Microsoft Agent Framework merged **1 documentation update** that corrects API method names in the README examples. This release contains **no breaking changes** but addresses important discrepancies between the README examples and the current API, helping new users get started with the correct method names.

---

## 📊 Overview

**Documentation Update** - Updates README with correct API method names.

**Key Improvements:**
- 📝 Corrected Python API method from `create_agent()` to `as_agent()`
- 📝 Corrected .NET API method from `CreateAIAgent()` to `AsAIAgent()`
- ✅ Ensures README examples align with current API
- 📚 Improves new user onboarding experience

**Impact**: MEDIUM - This update helps new users avoid confusion when following the README examples.

---

## 📚 Documentation Updates

### README API Method Name Corrections

**PR**: [#3576](https://github.com/microsoft/agent-framework/pull/3576)  
**Author**: [@dmytrostruk](https://github.com/dmytrostruk)  
**Impact**: MEDIUM - Documentation consistency improvement  
**Labels**: `documentation`

#### The Issue

The README file contained outdated method names in the quickstart examples. The documented methods (`create_agent()` in Python and `CreateAIAgent()` in .NET) did not match the actual API methods (`as_agent()` and `AsAIAgent()` respectively), causing confusion for developers following the getting started guide.

#### What Changed

The PR updates all README examples to use the correct current API method names:

**Python API Update:**

Before:
```python
agent = AzureOpenAIClient(
    # endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    # api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    # api_key=os.environ["AZURE_OPENAI_API_KEY"],  # Optional if using AzureCliCredential
    credential=AzureCliCredential(), # Optional, if using api_key
).create_agent(  # ❌ Outdated method name
    name="HaikuBot",
    instructions="You are an upbeat assistant that writes beautifully.",
)
```

After:
```python
agent = AzureOpenAIClient(
    # endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    # api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    # api_key=os.environ["AZURE_OPENAI_API_KEY"],  # Optional if using AzureCliCredential
    credential=AzureCliCredential(), # Optional, if using api_key
).as_agent(  # ✅ Correct method name
    name="HaikuBot",
    instructions="You are an upbeat assistant that writes beautifully.",
)
```

**.NET API Update (OpenAI):**

Before:
```csharp
using OpenAI;

// Replace the <apikey> with your OpenAI API key.
var agent = new OpenAIClient("<apikey>")
    .GetOpenAIResponseClient("gpt-4o-mini")
    .CreateAIAgent(  // ❌ Outdated method name
        name: "HaikuBot", 
        instructions: "You are an upbeat assistant that writes beautifully."
    );

Console.WriteLine(await agent.RunAsync("Write a haiku about Microsoft Agent Framework."));
```

After:
```csharp
using OpenAI;

// Replace the <apikey> with your OpenAI API key.
var agent = new OpenAIClient("<apikey>")
    .GetOpenAIResponseClient("gpt-4o-mini")
    .AsAIAgent(  // ✅ Correct method name
        name: "HaikuBot", 
        instructions: "You are an upbeat assistant that writes beautifully."
    );

Console.WriteLine(await agent.RunAsync("Write a haiku about Microsoft Agent Framework."));
```

**.NET API Update (Azure OpenAI):**

Before:
```csharp
using Azure.Identity;
using Microsoft.Extensions.AI;
using OpenAI;

var agent = new OpenAIClient(
    new BearerTokenPolicy(new AzureCliCredential(), "https://ai.azure.com/.default"),
    new OpenAIClientOptions() { Endpoint = new Uri("https://<resource>.openai.azure.com/openai/v1") })
    .GetOpenAIResponseClient("gpt-4o-mini")
    .CreateAIAgent(  // ❌ Outdated method name
        name: "HaikuBot", 
        instructions: "You are an upbeat assistant that writes beautifully."
    );

Console.WriteLine(await agent.RunAsync("Write a haiku about Microsoft Agent Framework."));
```

After:
```csharp
using Azure.Identity;
using Microsoft.Extensions.AI;
using OpenAI;

var agent = new OpenAIClient(
    new BearerTokenPolicy(new AzureCliCredential(), "https://ai.azure.com/.default"),
    new OpenAIClientOptions() { Endpoint = new Uri("https://<resource>.openai.azure.com/openai/v1") })
    .GetOpenAIResponseClient("gpt-4o-mini")
    .AsAIAgent(  // ✅ Correct method name
        name: "HaikuBot", 
        instructions: "You are an upbeat assistant that writes beautifully."
    );

Console.WriteLine(await agent.RunAsync("Write a haiku about Microsoft Agent Framework."));
```

#### Why This Matters

Documentation accuracy is crucial for developer experience, especially in README files that serve as the first point of contact for new users. This update:

- ✅ **Prevents Confusion**: New developers following the README will now use the correct API methods
- ✅ **Reduces Support Burden**: Fewer issues filed due to incorrect method names in examples
- ✅ **Improves First Impressions**: Accurate documentation demonstrates quality and attention to detail
- ✅ **Saves Developer Time**: No need to search for the correct method names when the README is wrong

#### API Method Naming Convention

The change from `create_agent()` → `as_agent()` and `CreateAIAgent()` → `AsAIAgent()` reflects the framework's API design pattern where:

- **`as_agent()`/`AsAIAgent()`**: Wraps an existing chat client as an agent with specified instructions and name
- The "as" prefix indicates a conversion/adapter pattern rather than creation of a new resource

This naming convention makes the API more intuitive by clearly indicating that you're treating an existing client as an agent, rather than creating a new agent from scratch.

---

## Files Changed

**Modified:**
- `README.md` (3 method name corrections)
  - Python example: `create_agent()` → `as_agent()`
  - .NET OpenAI example: `CreateAIAgent()` → `AsAIAgent()`
  - .NET Azure OpenAI example: `CreateAIAgent()` → `AsAIAgent()`

---

## Summary

February 2, 2026 delivers a **documentation accuracy update** that ensures the README examples use the correct current API method names. While this is a documentation-only change with no code modifications, it significantly improves the new user experience.

### Key Achievements

✅ **Documentation Accuracy**: README now reflects the current API  
✅ **Improved Developer Experience**: New users can follow examples without errors  
✅ **Consistency**: All language examples use the correct method names  
✅ **Zero Breaking Changes**: No code changes required

### Recommended Actions

**For New Users:**
1. 📚 Follow the updated README with confidence - examples are now accurate
2. 🚀 Use `as_agent()` in Python and `AsAIAgent()` in .NET when creating agents
3. 🔗 Refer to the README for the latest getting started examples

**For Existing Users:**
1. ✅ No action required - this is a documentation-only update
2. 📖 Review the README if you want to see the latest example patterns
3. 🔍 Verify your code already uses the correct `as_agent()`/`AsAIAgent()` methods

**For Contributors:**
1. 📝 Use the README as the canonical reference for API examples
2. ✅ Ensure future examples use `as_agent()`/`AsAIAgent()` method names
3. 🔄 Keep documentation in sync with API changes

### Who Should Update?

**UPDATE DOCUMENTATION REFERENCES IF:**
- ✅ You maintain internal documentation referencing the Agent Framework README
- ✅ You teach or train others on the Agent Framework API
- ✅ You reference the old method names in blog posts or tutorials
- ✅ You're writing new examples or documentation

**No action required for:**
- ❌ Users already using the correct API methods in their code
- ❌ Applications already in production (no code changes needed)

---

**Related Documentation**: [Microsoft Agent Framework README](https://github.com/microsoft/agent-framework/blob/main/README.md)

**Contributor**: [@dmytrostruk](https://github.com/dmytrostruk)

**Total PRs Merged**: 1  
**Total Lines Changed**: 3 (documentation only)  
**Breaking Changes**: 0  
**Impact Level**: MEDIUM (documentation accuracy improvement)
