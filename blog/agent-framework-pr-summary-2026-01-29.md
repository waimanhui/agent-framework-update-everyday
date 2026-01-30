# Agent Framework Updates - January 29, 2026

On January 29, 2026, the Microsoft Agent Framework merged 5 significant pull requests, all focused on **improving test coverage and code quality** across both .NET and Python ecosystems. This release represents a major push toward achieving 85-90% unit test coverage for core packages, with no breaking changes but substantial improvements to reliability and developer confidence. The updates include over 1,200 new lines of test code, better documentation organization, and enhanced observability testing.

---

## 📊 Overview

**No Breaking Changes** - This release focuses entirely on quality improvements and developer experience enhancements.

**Key Improvements:**
- 🧪 Python core package test coverage increased from ~72% to ~95%
- 📝 Reorganized .NET durable agent samples for better discoverability
- 🔍 Comprehensive observability module testing (72% → 86% coverage)
- ✅ Enhanced Azure AI package test coverage

---

## Major Updates

### 1. Python: Comprehensive Core Utilities Unit Tests

**PR**: [#3487](https://github.com/microsoft/agent-framework/pull/3487)  
**Author**: [@giles17](https://github.com/giles17)  
**Impact**: MEDIUM - Improves reliability of core framework utilities  
**Coverage Improvement**: 81% → 96% (memory), 81% → 94% (serialization), 85% → 98% (threads)

This PR adds 35+ new unit tests covering critical functionality in three core utility modules: `_memory.py`, `_serialization.py`, and `_threads.py`.

#### Serialization Enhancements

The new tests ensure robust serialization behavior for complex scenarios:

**Nested Serialization Protocol Objects:**
```python
class InnerClass(SerializationMixin):
    def __init__(self, inner_value: str):
        self.inner_value = inner_value

class OuterClass(SerializationMixin):
    def __init__(self, outer_value: str, inner: Any = None):
        self.outer_value = outer_value
        self.inner = inner

# Properly serializes nested objects
inner = InnerClass(inner_value="inner_test")
outer = OuterClass(outer_value="outer_test", inner=inner)
data = outer.to_dict()

# Result: {'outer_value': 'outer_test', 'inner': {'inner_value': 'inner_test'}}
```

**Advanced Dependency Injection:**
```python
class TestClass(SerializationMixin):
    INJECTABLE = {"config"}
    
    def __init__(self, name: str, config: Any = None):
        self.name = name
        self.config = config

# Instance-specific dependency injection
dependencies = {
    "test_class": {
        "name:special_instance": {"config": "special_config"},
    }
}

obj = TestClass.from_dict(
    {"type": "test_class", "name": "special_instance"}, 
    dependencies=dependencies
)
# obj.config == "special_config"
```

**Dict Dependency Merging:**
```python
# Existing options in data
data = {
    "type": "test_class", 
    "value": "test", 
    "options": {"existing": "value"}
}

# Additional options from dependencies
dependencies = {
    "test_class": {"options": {"injected": "option"}}
}

obj = TestClass.from_dict(data, dependencies=dependencies)
# obj.options == {"existing": "value", "injected": "option"}
```

#### Thread Management Tests

New tests validate edge cases in `AgentThread` and `ChatMessageStore`:

```python
# Thread initialization states
thread = AgentThread(service_thread_id="test-thread-123")
assert thread.service_thread_id == "test-thread-123"

# ChatMessageStore deserialization
serialized_state = {
    "service_thread_id": None,
    "chat_message_store_state": {
        "messages": [{"role": "user", "text": "Hello"}],
    },
}

thread = await agent.deserialize_thread(serialized_state)
messages = await thread.message_store.list_messages()
assert len(messages) == 1
assert messages[0].text == "Hello"
```

#### Context Provider Tests

Tests ensure proper behavior of context providers:

```python
class TestContextProvider(ContextProvider):
    async def invoking(self, messages, **kwargs):
        return Context()

# Tests verify thread_created, invoked, and async context manager behavior
```

**Benefits:**
- Catches edge cases in serialization with nested objects and datetime handling
- Validates dependency injection patterns work correctly
- Ensures thread state management is robust
- Improves reliability of context provider lifecycle

---

### 2. Python: Core Types and Agents Unit Tests

**PR**: [#3470](https://github.com/microsoft/agent-framework/pull/3470)  
**Author**: [@giles17](https://github.com/giles17)  
**Impact**: MEDIUM - Validates core agent behaviors and content handling  

This PR adds comprehensive tests for content handling, agent initialization, and option merging logic.

#### Content Type Tests

New tests validate `Content` behaviors and internal helpers:

```python
# Usage aggregation - tracks content statistics
# Media type detection - identifies content types correctly
# Argument parsing - handles various input formats
# Data URI decoding - processes base64-encoded data
# Content list parsing - handles multiple content items
# URI validation - ensures valid resource references
```

#### Agent Option Merging

Tests ensure proper option merging behavior:

```python
def test_merge_options_tools_combined():
    """Test _merge_options combines tool lists without duplicates."""
    
    class MockTool:
        def __init__(self, name):
            self.name = name
    
    tool1 = MockTool("tool1")
    tool2 = MockTool("tool2")
    tool3 = MockTool("tool1")  # Duplicate name
    
    base = {"tools": [tool1]}
    override = {"tools": [tool2, tool3]}
    
    result = _merge_options(base, override)
    
    # Should have tool1 and tool2, but not duplicate tool3
    assert len(result["tools"]) == 2
    tool_names = [t.name for t in result["tools"]]
    assert "tool1" in tool_names
    assert "tool2" in tool_names
```

**Instructions Concatenation:**
```python
def test_merge_options_instructions_concatenated():
    """Test _merge_options concatenates instructions."""
    base = {"instructions": "First instruction."}
    override = {"instructions": "Second instruction."}
    
    result = _merge_options(base, override)
    
    assert "First instruction." in result["instructions"]
    assert "Second instruction." in result["instructions"]
    assert "\n" in result["instructions"]
```

**Metadata and Logit Bias Merging:**
```python
# logit_bias dicts are merged
base = {"logit_bias": {"token1": 1.0}}
override = {"logit_bias": {"token2": 2.0}}
result = _merge_options(base, override)
# result["logit_bias"] == {"token1": 1.0, "token2": 2.0}

# metadata dicts are merged similarly
```

#### Agent Name Sanitization

```python
def test_sanitize_agent_name_replaces_invalid_chars():
    """Test _sanitize_agent_name replaces invalid characters."""
    result = _sanitize_agent_name("Agent Name!")
    # Should replace spaces and special chars with underscores
    assert " " not in result
    assert "!" not in result
```

#### ChatAgent Initialization Edge Cases

**Conversation ID Validation:**
```python
@pytest.mark.asyncio
async def test_chat_agent_raises_with_both_conversation_id_and_store():
    """Test ChatAgent raises error with both conversation_id and chat_message_store_factory."""
    mock_client = MagicMock()
    mock_store_factory = MagicMock()
    
    with pytest.raises(AgentInitializationError, match="Cannot specify both"):
        ChatAgent(
            chat_client=mock_client,
            default_options={"conversation_id": "test_id"},
            chat_message_store_factory=mock_store_factory,
        )
```

**Context Provider Integration:**
```python
@pytest.mark.asyncio
async def test_chat_agent_context_provider_adds_tools_when_agent_has_none():
    """Test that context provider tools are used when agent has no default tools."""
    
    @tool
    def context_tool(text: str) -> str:
        """A tool provided by context."""
        return text
    
    class ToolContextProvider(ContextProvider):
        async def invoking(self, messages, **kwargs):
            return Context(tools=[context_tool])
    
    provider = ToolContextProvider()
    agent = ChatAgent(chat_client=chat_client_base, context_provider=provider)
    
    # Agent starts with empty tools list
    assert agent.default_options.get("tools") == []
    
    # After preparation, context tools are added
    _, options, _ = await agent._prepare_thread_and_messages(
        thread=None,
        input_messages=[ChatMessage(role=Role.USER, text="Hello")]
    )
    
    # The context tools should now be in the options
    assert len(options["tools"]) == 1
```

**Benefits:**
- Prevents duplicate tools in merged options
- Ensures agent names are properly sanitized
- Validates conversation ID consistency
- Tests context provider integration thoroughly

---

### 3. Python: Observability Unit Tests

**PR**: [#3469](https://github.com/microsoft/agent-framework/pull/3469)  
**Author**: [@giles17](https://github.com/giles17)  
**Impact**: HIGH - Critical for production monitoring and debugging  
**Coverage Improvement**: 72% → 86%  
**Lines Added**: 1,169 lines of test code

This massive PR adds comprehensive testing for the observability module, ensuring telemetry and monitoring features work correctly in production environments.

#### Coverage Areas

**OpenTelemetry (OTel) Attributes:**
- Validates proper attribute naming and formatting
- Tests semantic conventions compliance
- Ensures attributes are correctly attached to spans

**Metric Views:**
- Tests metric collection and aggregation
- Validates metric export formats
- Ensures metric naming consistency

**Instrumentation Decorators:**
- Tests `@instrument` decorator behavior
- Validates automatic span creation
- Ensures proper context propagation

**Span Creation:**
```python
# Tests ensure spans are created correctly for:
# - Agent invocations
# - Chat client calls
# - Tool executions
# - Workflow steps
```

**Exception Handling:**
```python
# Observability tests validate that:
# - Exceptions are properly recorded in spans
# - Error attributes are set correctly
# - Stack traces are captured when appropriate
# - Span status is set to ERROR on exceptions
```

**Configuration Tests:**
- Tests enabled vs disabled instrumentation scenarios
- Validates sampler configuration
- Ensures proper exporter setup

**Agent Instrumentation:**
```python
# Tests cover:
# - Agent lifecycle spans (creation, execution, completion)
# - Tool call tracing
# - Message processing spans
# - Context provider spans
```

**Chat Client Telemetry:**
```python
# Tests validate:
# - Request/response tracking
# - Token usage metrics
# - Latency measurements
# - Model attribution
```

**Workflow Spans:**
```python
# Tests ensure:
# - Workflow step tracing
# - Parent-child span relationships
# - Workflow state transitions
# - Conditional branch tracking
```

**Benefits:**
- Production-ready observability with 86% test coverage
- Confidence in monitoring and debugging capabilities
- Early detection of telemetry regressions
- Better visibility into agent behavior in production

---

### 4. Python: Improved Azure AI Package Test Coverage

**PR**: [#3452](https://github.com/microsoft/agent-framework/pull/3452)  
**Author**: [@giles17](https://github.com/giles17)  
**Impact**: MEDIUM - Ensures Azure AI integrations work correctly

This PR adds extensive tests for Azure AI-specific functionality including tools, MCP integration, and response format handling.

#### Test Coverage Areas

**Shared Conversion Functions:**
```python
# python/packages/azure-ai/tests/test_shared.py
# Tests for:
# - Tool conversion to Azure AI format
# - MCP (Model Context Protocol) conversions
# - Response format transformations
```

**Provider Tests:**
```python
# python/packages/azure-ai/tests/test_provider.py
# Ensures tool-merge behavior:
# - Skips dict function tools
# - Preserves hosted tools
# - Handles tool conflicts correctly
```

**Azure AI Client Tests:**
```python
# python/packages/azure-ai/tests/test_azure_ai_client.py
# Tests for:
# - Azure Monitor configuration paths
# - MCP tool preparation
# - Client initialization edge cases
```

**Azure AI Agent Client Tests:**
```python
# python/packages/azure-ai/tests/test_azure_ai_agent_client.py
# Validates:
# - response_format handling
# - Tool resources configuration
# - MCP resources setup
# - Message preparation logic
# - Tool preparation workflows
```

**Agent Provider Validation:**
```python
# python/packages/azure-ai/tests/test_agent_provider.py
# Tests that:
# - Dict-format function tools require implementations
# - Integration test imports work correctly
# - Provider initialization is validated
```

**Benefits:**
- Ensures Azure-specific features work reliably
- Validates MCP integration correctness
- Tests response format handling edge cases
- Improves confidence in Azure AI deployments

---

### 5. .NET: Consolidated Durable Agent Samples

**PR**: [#3471](https://github.com/microsoft/agent-framework/pull/3471)  
**Author**: [@kshyju](https://github.com/kshyju)  
**Impact**: LOW - Documentation and samples organization (no code changes)

This PR reorganizes durable agent samples into a cleaner folder structure for better discoverability and maintainability.

#### New Folder Structure

**Before:**
```
dotnet/samples/Durable/
├── Various scattered samples
└── Mixed console and Azure Functions samples
```

**After:**
```
dotnet/samples/Durable/Agents/
├── ConsoleApps/
│   ├── 01_SingleAgent/
│   ├── 02_AgentOrchestration_Chaining/
│   ├── 03_AgentOrchestration_Concurrency/
│   ├── 04_AgentOrchestration_Conditionals/
│   ├── 05_AgentOrchestration_HITL/
│   ├── 06_LongRunningTools/
│   └── 07_ReliableStreaming/
└── AzureFunctions/
    ├── 01_SingleAgent/
    ├── 02_AgentOrchestration_Chaining/
    ├── 03_AgentOrchestration_Concurrency/
    ├── 04_AgentOrchestration_Conditionals/
    ├── 05_AgentOrchestration_HITL/
    ├── 06_LongRunningTools/
    ├── 07_AgentAsMcpTool/
    └── 08_ReliableStreaming/
```

#### Samples Included

**Console Applications:**
1. **01_SingleAgent** - Basic single agent setup
2. **02_AgentOrchestration_Chaining** - Sequential agent workflows
3. **03_AgentOrchestration_Concurrency** - Parallel agent execution
4. **04_AgentOrchestration_Conditionals** - Conditional branching logic
5. **05_AgentOrchestration_HITL** - Human-in-the-loop patterns
6. **06_LongRunningTools** - Durable tool execution
7. **07_ReliableStreaming** - Streaming with Redis persistence

**Azure Functions:**
1. **01_SingleAgent** - Serverless single agent
2. **02-06** - Same patterns as console apps
3. **07_AgentAsMcpTool** - Agent exposed as MCP tool
4. **08_ReliableStreaming** - Serverless reliable streaming

#### Configuration Updates

**Directory.Build.props:**
```xml
<!-- Overrides parent props to remove `Environment` alias for Durable samples -->
```

**Solution File Updates:**
```xml
<!-- dotnet/agent-framework-dotnet.slnx -->
<!-- Updated solution folder/project paths to new sample hierarchy -->
```

**Each Sample Includes:**
- `README.md` - Setup and usage instructions
- `Program.cs` - Main application code
- `.csproj` - Project file with updated references
- `Models.cs` - Data models (where applicable)
- `demo.http` - HTTP test requests (Azure Functions)
- `local.settings.json` - Local configuration (Azure Functions)
- `host.json` - Function host config (Azure Functions)

**Benefits:**
- Easier to find relevant samples by scenario
- Clear separation between console and serverless patterns
- Better documentation organization
- Improved developer onboarding experience
- Consistent project structure across samples

---

## Summary

January 29, 2026 represents a significant **quality and reliability milestone** for the Microsoft Agent Framework. With over 1,200 lines of new test code added across five PRs, the framework now has substantially better coverage and more robust validation of critical functionality.

### Key Achievements

✅ **Python Core Coverage**: 81-85% → 94-98% across core utilities  
✅ **Observability Coverage**: 72% → 86% with 1,169 new test lines  
✅ **Azure AI Testing**: Comprehensive coverage for Azure-specific features  
✅ **Better Documentation**: Reorganized samples for easier discovery  
✅ **Zero Breaking Changes**: All improvements are backward compatible

### Recommended Actions

**For All Developers:**
1. ✅ **No immediate action required** - this release has no breaking changes
2. 🔄 Update to the latest version to benefit from improved reliability
3. 📖 Explore the reorganized samples in `dotnet/samples/Durable/Agents/`

**For Python Developers:**
1. 🧪 Review the new test patterns if you're contributing to the framework
2. 🔍 Leverage improved observability for production debugging
3. ☁️ Validate Azure AI integrations with the new test coverage

**For .NET Developers:**
1. 📚 Check out the reorganized durable agent samples
2. 🚀 Try the Azure Functions samples for serverless patterns
3. 🛠️ Explore MCP tool integration (sample 07_AgentAsMcpTool)

### What's Next?

The framework continues toward the **85-90% test coverage goal** (issue [#3356](https://github.com/microsoft/agent-framework/issues/3356)). Future PRs will likely focus on:
- Additional test coverage for remaining modules
- Performance testing and benchmarks
- Integration test improvements
- End-to-end scenario validation

---

**Related Issue**: [#3356 - Achieve 85-90% unit test coverage for core package](https://github.com/microsoft/agent-framework/issues/3356)

**Contributors**: [@giles17](https://github.com/giles17), [@kshyju](https://github.com/kshyju)

**Total PRs Merged**: 5  
**Total Lines Added**: 1,200+ (primarily tests)  
**Breaking Changes**: 0  
**Impact Level**: MEDIUM to HIGH (quality improvements)
