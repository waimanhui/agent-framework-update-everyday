# Agent Framework Updates - February 1, 2026

On February 1, 2026, the Microsoft Agent Framework merged **1 critical bug fix** that resolves a significant issue affecting sequential workflows in Azure AI Agent implementations. This release addresses a **high-severity bug** where agent instructions were being silently dropped, causing agents in multi-step workflows to completely ignore their configured instructions and behave unpredictably.

---

## 📊 Overview

**Critical Bug Fix** - Restores proper instruction handling in Azure AI sequential workflows.

**Key Improvements:**
- 🐛 Fixed silent instruction dropping in `AzureAIAgentClient`
- ✅ Added comprehensive unit tests for instruction handling
- 🔧 Restored correct behavior for `as_agent(instructions=...)` API
- 🔄 Fixed sequential workflow agent orchestration

**Impact**: HIGH - This bug affected all developers using Azure AI agents in sequential workflows, causing unpredictable agent behavior and workflow failures.

---

## ⚠️ CRITICAL BUG FIX

### Python: AzureAIAgentClient Silently Dropped Agent Instructions

**PR**: [#3563](https://github.com/microsoft/agent-framework/pull/3563)  
**Author**: [@evan.mattson](https://github.com/evan-mattson)  
**Impact**: HIGH - Critical fix for sequential workflow reliability  
**Closes**: [#3507 - Agents in workflow do not follow instructions](https://github.com/microsoft/agent-framework/issues/3507)

#### The Problem

The `AzureAIAgentClient._prepare_options()` method was **silently dropping** agent instructions passed via the `as_agent(instructions=...)` API. The `instructions` key was included in the `exclude_keys` set with a comment "handled via messages", but the instructions from options were **never actually extracted and added** to the final instructions list. Only instructions from system/developer messages were being processed.

This caused a **severe breakdown** in sequential workflows where agents would:
- ❌ Completely ignore their configured instructions
- ❌ Produce unexpected outputs unrelated to their role
- ❌ Fail to perform their designated tasks in the workflow

#### Real-World Impact Example

Before the fix, a sequential workflow with specialized agents would produce **incorrect results**:

```python
# Define specialized agents with specific instructions
writer = chat_client.as_agent(
    instructions="You are a concise copywriter. Provide a single, punchy marketing sentence.",
    name="writer",
)

reviewer = chat_client.as_agent(
    instructions="You are a thoughtful reviewer. Give brief feedback on the previous message.",
    name="reviewer",
)

# Build sequential workflow: writer → reviewer
workflow = SequentialBuilder().participants([writer, reviewer]).build()

# Run workflow
async for event in workflow.run_stream("Write a tagline for a budget-friendly eBike."):
    if isinstance(event, WorkflowOutputEvent):
        print_results(event.data)
```

**Broken Output (Before Fix):**
```
01 [user]
Write a tagline for a budget-friendly eBike.
------------------------------------------------------------
02 [writer]
"Ride Far. Spend Less. Go Electric."
------------------------------------------------------------
03 [reviewer]
"Electric Freedom, Wallet Friendly."  ❌ WRONG! Reviewer wrote a tagline instead of reviewing!
```

The **reviewer agent completely ignored** its instruction to "give brief feedback" and instead wrote another tagline, behaving identically to the writer agent.

#### The Root Cause

In `_prepare_options()`, the code structure was:

```python
# _chat_client.py (BEFORE FIX)
async def _prepare_options(
    self,
    messages: Sequence[ChatMessage],
    options: ChatOptions,
) -> tuple[dict[str, Any], list[ChatMessage]]:
    # ...
    exclude_keys = {
        "instructions",  # ❌ Excluded but never re-added!
        "messages",
        # ... other keys
    }
    
    # Build run_options by copying everything EXCEPT exclude_keys
    run_options = {k: v for k, v in options.items() if k not in exclude_keys}
    
    # Process system/developer message instructions
    instructions = []
    for msg in messages:
        if msg.role in (Role.SYSTEM, Role.DEVELOPER):
            instructions.append(msg.text)
    
    # ❌ BUG: Never extracted options.get("instructions") and added it!
    # The instructions from as_agent() were silently dropped
    
    if instructions:
        run_options["instructions"] = "\n\n".join(instructions)
```

The intent was to exclude `instructions` from the initial copy, then manually construct the final instructions list from multiple sources. However, **the code only extracted instructions from messages** and completely forgot to include instructions from the options dict.

#### The Fix

The fix is elegant and minimal - just **4 lines of code**:

```python
# _chat_client.py (AFTER FIX)
async def _prepare_options(
    self,
    messages: Sequence[ChatMessage],
    options: ChatOptions,
) -> tuple[dict[str, Any], list[ChatMessage]]:
    # ... (exclude_keys and run_options setup same as before)
    
    # Process system/developer message instructions
    instructions = []
    for msg in messages:
        if msg.role in (Role.SYSTEM, Role.DEVELOPER):
            instructions.append(msg.text)
    
    # ✅ FIX: Add instructions from options (agent's instructions set via as_agent())
    if options_instructions := options.get("instructions"):
        instructions.append(options_instructions)
    
    # Add instruction from existing agent definition (if any)
    if agent_definition is not None and agent_definition.instructions:
        instructions.insert(0, agent_definition.instructions)
    
    if instructions:
        run_options["instructions"] = "\n\n".join(instructions)
```

**What Changed:**
1. ✅ Extract instructions from `options.get("instructions")`
2. ✅ Append to the instructions list
3. ✅ Ensures instructions from `as_agent(instructions=...)` are properly included
4. ✅ Maintains correct order: agent definition → message instructions → options instructions

#### Comprehensive Test Coverage

Two new unit tests ensure this bug never resurfaces:

**Test 1: Instructions from Options Only**

```python
async def test_azure_ai_chat_client_prepare_options_with_instructions_from_options(
    mock_agents_client: MagicMock,
) -> None:
    """Test _prepare_options includes instructions passed via options.
    
    This verifies that agent instructions set via as_agent(instructions=...)
    are properly included in the API call.
    """
    chat_client = create_test_azure_ai_chat_client(mock_agents_client, agent_id="test-agent")
    mock_agents_client.get_agent = AsyncMock(return_value=None)
    
    messages = [ChatMessage(role=Role.USER, text="Hello")]
    chat_options: ChatOptions = {
        "instructions": "You are a thoughtful reviewer. Give brief feedback.",
    }
    
    run_options, _ = await chat_client._prepare_options(messages, chat_options)
    
    # ✅ Verify instructions are present
    assert "instructions" in run_options
    assert "reviewer" in run_options["instructions"].lower()
```

**Test 2: Merging Instructions from Multiple Sources**

```python
async def test_azure_ai_chat_client_prepare_options_merges_instructions_from_messages_and_options(
    mock_agents_client: MagicMock,
) -> None:
    """Test _prepare_options merges instructions from both system messages and options.
    
    When instructions come from both system/developer messages AND from options,
    both should be included in the final instructions.
    """
    chat_client = create_test_azure_ai_chat_client(mock_agents_client, agent_id="test-agent")
    mock_agents_client.get_agent = AsyncMock(return_value=None)
    
    messages = [
        ChatMessage(role=Role.SYSTEM, text="Context: You are reviewing marketing copy."),
        ChatMessage(role=Role.USER, text="Review this tagline"),
    ]
    chat_options: ChatOptions = {
        "instructions": "Be concise and constructive in your feedback.",
    }
    
    run_options, _ = await chat_client._prepare_options(messages, chat_options)
    
    assert "instructions" in run_options
    instructions_text = run_options["instructions"]
    
    # ✅ Both instruction sources should be present
    assert "marketing" in instructions_text.lower()
    assert "concise" in instructions_text.lower()
```

These tests validate:
- ✅ Instructions from `options` are included
- ✅ Instructions from system messages are included
- ✅ Both sources are properly merged when present
- ✅ The final instructions string contains content from all sources

---

## Expected Behavior After Fix

With the fix applied, the sequential workflow now produces **correct results**:

```
01 [user]
Write a tagline for a budget-friendly eBike.
------------------------------------------------------------
02 [writer]
"Ride farther, spend less—your affordable eBike adventure starts here."
------------------------------------------------------------
03 [reviewer]
This tagline clearly communicates affordability and the benefit of extended 
travel, making it appealing to budget-conscious consumers. It has a friendly 
and motivating tone, though it could be slightly shorter for more punch. 
Overall, a strong and effective suggestion!
```

✅ **Correct!** The reviewer now properly follows its instruction to "give brief feedback" instead of generating another tagline.

---

## Files Changed

**Modified:**
- `python/packages/azure-ai/agent_framework_azure_ai/_chat_client.py` (+4 lines)
  - Added extraction of instructions from options dict
  - Fixed instruction merging logic

**Test Coverage:**
- `python/packages/azure-ai/tests/test_azure_ai_agent_client.py` (+50 lines)
  - Added `test_azure_ai_chat_client_prepare_options_with_instructions_from_options()`
  - Added `test_azure_ai_chat_client_prepare_options_merges_instructions_from_messages_and_options()`

---

## Summary

February 1, 2026 delivers a **critical bug fix** that restores proper instruction handling in Azure AI agent workflows. This high-severity issue was causing silent failures in production workflows, where agents would ignore their configured instructions entirely.

### Key Achievements

✅ **Bug Fixed**: AzureAIAgentClient now properly includes instructions from `as_agent()`  
✅ **Test Coverage**: 2 new unit tests prevent regression  
✅ **Sequential Workflows**: Agents now correctly follow their designated roles  
✅ **Zero Breaking Changes**: Fix is backward compatible

### Recommended Actions

**For All Azure AI Agent Users:**
1. 🚨 **UPDATE IMMEDIATELY** if you use sequential workflows with `as_agent(instructions=...)`
2. ✅ Test your existing workflows - they should now work correctly
3. 🔍 Review any workflow outputs that seemed incorrect - this bug may have affected them

**For Developers Using Sequential Workflows:**
1. ✅ Upgrade to this version to fix instruction handling
2. 🧪 Verify your agents now follow their instructions properly
3. 📝 Review workflow definitions - instructions should now be respected

**For New Users:**
1. 📚 Check out the sequential workflow sample: [sequential_workflow_as_agent.py](https://github.com/microsoft/agent-framework/blob/main/python/samples/getting_started/workflows/agents/sequential_workflow_as_agent.py)
2. 🎯 Use `as_agent(instructions=...)` with confidence
3. 🔗 Build multi-agent workflows with specialized roles

### Who Should Update?

**UPDATE IMMEDIATELY IF:**
- ✅ You use `AzureAIAgentClient` with sequential workflows
- ✅ You use `as_agent(instructions=...)` to define agent behavior
- ✅ Your agents are not following their instructions
- ✅ Your workflow outputs are unexpected or incorrect

**This fix resolves:**
- ❌ Agents ignoring their configured instructions
- ❌ Sequential workflows producing unexpected outputs
- ❌ Multiple agents behaving identically despite different instructions
- ❌ Silent failures in agent orchestration

---

**Related Issue**: [#3507 - Python: [Bug]: Agents in workflow do not follow instructions](https://github.com/microsoft/agent-framework/issues/3507)

**Contributor**: [@evan.mattson](https://github.com/evan-mattson)

**Total PRs Merged**: 1  
**Total Lines Changed**: +54 (4 in source, 50 in tests)  
**Breaking Changes**: 0  
**Impact Level**: HIGH (critical bug fix)
