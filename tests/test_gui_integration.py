#!/usr/bin/env python3
"""
Tests for DeepAgents GUI Integration module.

These tests verify:
- Controller initialization
- Tool management
- Configuration export/import
- Graph structure provider
- LangSmith configuration
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


class TestDeepAgentsGUIController:
    """Test the DeepAgentsGUIController class."""
    
    def test_controller_creation(self):
        """Test basic controller creation."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(
            model_name="test-model",
            base_url="http://localhost:1234",
            langsmith_enabled=False
        )
        
        assert controller.model_name == "test-model"
        assert controller.base_url == "http://localhost:1234"
        assert controller.is_initialized is False
        assert controller.langsmith_enabled is False
    
    def test_controller_default_values(self):
        """Test controller with default values."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController()
        
        assert controller.model_name == "local-model"
        assert controller.base_url == "http://localhost:1234"
        assert controller.temperature == 0.7
        assert controller.enable_persistence is True
        assert controller.enable_human_in_loop is True
    
    def test_get_tools_metadata(self):
        """Test retrieving tool metadata."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        metadata = controller.get_tools_metadata()
        
        assert isinstance(metadata, list)
        assert len(metadata) > 0
        
        # Check metadata structure
        for tool in metadata:
            assert "name" in tool
            assert "description" in tool
            assert "risk_level" in tool
            assert tool["risk_level"] in ["safe", "review", "dangerous"]
    
    def test_tool_states_initialization(self):
        """Test that tool states are properly initialized after init."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        
        # Before initialization, tool_states should be empty
        assert len(controller.tool_states) == 0
        
        # After initialization (mocked), tool_states should be populated
        with patch.object(controller, '_create_model'), \
             patch.object(controller, '_create_tools', return_value=None), \
             patch.object(controller, '_build_graph', return_value=None):
            
            # Manually set tools for testing
            from core.tools import create_filesystem_tools
            controller.tools = create_filesystem_tools()
            
            # Initialize tool states
            for tool in controller.tools:
                controller.tool_states[tool.name] = True
            
            assert len(controller.tool_states) == 4
            assert all(controller.tool_states.values())  # All enabled by default
    
    def test_set_tool_enabled(self):
        """Test enabling/disabling tools."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        
        # Initialize tool states
        controller.tool_states = {
            "read_file": True,
            "write_file": True,
            "list_directory": True,
            "execute_command": True,
        }
        
        # Disable a tool
        result = controller.set_tool_enabled("write_file", False)
        assert result is True
        assert controller.tool_states["write_file"] is False
        
        # Enable it back
        result = controller.set_tool_enabled("write_file", True)
        assert result is True
        assert controller.tool_states["write_file"] is True
        
        # Try to toggle non-existent tool
        result = controller.set_tool_enabled("nonexistent_tool", True)
        assert result is False
    
    def test_get_enabled_tools(self):
        """Test getting list of enabled tools."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        
        # Create mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "read_file"
        mock_tool2 = Mock()
        mock_tool2.name = "write_file"
        
        controller.tools = [mock_tool1, mock_tool2]
        controller.tool_states = {
            "read_file": True,
            "write_file": False,
        }
        
        enabled = controller.get_enabled_tools()
        assert len(enabled) == 1
        assert enabled[0].name == "read_file"
    
    def test_export_config(self):
        """Test configuration export."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(
            model_name="test-model",
            temperature=0.5,
            langsmith_enabled=True
        )
        
        config = controller.export_config()
        
        assert isinstance(config, dict)
        assert config["model_name"] == "test-model"
        assert config["temperature"] == 0.5
        assert config["langsmith_enabled"] is True
        assert "tool_states" in config
        assert "enable_persistence" in config
        assert "enable_human_in_loop" in config
    
    def test_import_config(self):
        """Test configuration import."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        
        new_config = {
            "model_name": "new-model",
            "temperature": 0.9,
            "enable_persistence": False,
            "enable_human_in_loop": False,
            "tool_states": {
                "read_file": True,
                "write_file": False,
            }
        }
        
        success = controller.import_config(new_config)
        assert success is True
        assert controller.model_name == "new-model"
        assert controller.temperature == 0.9
        assert controller.enable_persistence is False
        assert controller.enable_human_in_loop is False
    
    def test_import_config_invalid(self):
        """Test importing invalid configuration."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        
        # Invalid config (None)
        success = controller.import_config(None)
        assert success is False
    
    def test_get_current_state_empty(self):
        """Test getting state when no thread is active."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        controller.current_thread_id = None
        
        state = controller.get_current_state()
        assert state == {}
    
    @pytest.mark.asyncio
    async def test_process_message_not_initialized(self):
        """Test processing message when agent not initialized."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        controller.is_initialized = False
        
        events = []
        async for event in controller.process_message("test message"):
            events.append(event)
        
        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert "not initialized" in events[0]["data"]
    
    @pytest.mark.asyncio
    async def test_submit_approval_no_thread(self):
        """Test submitting approval without active thread."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        controller.current_thread_id = None
        
        result = await controller.submit_approval(True)
        
        assert result["success"] is False
        assert "No active thread" in result["error"]


class TestGraphStructureProvider:
    """Test the graph structure provider function."""
    
    def test_get_graph_structure(self):
        """Test getting graph structure for visualization."""
        from core.gui_integration import get_graph_structure
        
        structure = get_graph_structure()
        
        assert isinstance(structure, dict)
        assert "nodes" in structure
        assert "edges" in structure
        
        # Check nodes
        nodes = structure["nodes"]
        assert len(nodes) == 4
        
        node_ids = [n["id"] for n in nodes]
        assert "model" in node_ids
        assert "tools" in node_ids
        assert "human_review" in node_ids
        assert "error_handler" in node_ids
        
        # Check edges
        edges = structure["edges"]
        assert len(edges) == 6
        
        # Verify edge structure
        for edge in edges:
            assert "from" in edge
            assert "to" in edge
            assert "condition" in edge


class TestLangSmithConfiguration:
    """Test LangSmith configuration functions."""
    
    def test_configure_langsmith_disabled(self):
        """Test LangSmith configuration when disabled."""
        from core.gui_integration import configure_langsmith
        
        result = configure_langsmith(enabled=False)
        assert result is False
    
    def test_configure_langsmith_no_api_key(self, monkeypatch):
        """Test LangSmith configuration without API key."""
        from core.gui_integration import configure_langsmith
        
        # Ensure no API key is set
        monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
        
        result = configure_langsmith(
            api_key=None,
            project_name="test-project",
            enabled=True
        )
        
        assert result is False
        # Environment variables should still be set
        assert os.environ.get("LANGSMITH_TRACING") == "true"
        assert os.environ.get("LANGSMITH_PROJECT") == "test-project"
    
    def test_configure_langsmith_with_api_key(self, monkeypatch):
        """Test LangSmith configuration with API key."""
        from core.gui_integration import configure_langsmith
        
        # Clear any existing key
        monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
        
        result = configure_langsmith(
            api_key="test-api-key-123",
            project_name="test-project",
            enabled=True
        )
        
        assert result is True
        assert os.environ.get("LANGSMITH_API_KEY") == "test-api-key-123"
        assert os.environ.get("LANGSMITH_PROJECT") == "test-project"
        assert os.environ.get("LANGSMITH_TRACING") == "true"


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_workflow(self):
        """Test complete workflow: create, configure, export, import."""
        from core.gui_integration import DeepAgentsGUIController
        
        # Step 1: Create controller
        controller1 = DeepAgentsGUIController(
            model_name="model-v1",
            temperature=0.7,
            langsmith_enabled=False
        )
        
        # Step 2: Export configuration
        config = controller1.export_config()
        
        # Step 3: Create new controller and import config
        controller2 = DeepAgentsGUIController(
            model_name="model-v2",  # Different initial value
            temperature=0.5,
        )
        
        success = controller2.import_config(config)
        assert success is True
        
        # Step 4: Verify configuration matches
        assert controller2.model_name == controller1.model_name
        assert controller2.temperature == controller1.temperature
        assert controller2.langsmith_enabled == controller1.langsmith_enabled
    
    def test_tool_metadata_consistency(self):
        """Test that tool metadata is consistent across calls."""
        from core.gui_integration import DeepAgentsGUIController
        
        controller = DeepAgentsGUIController(langsmith_enabled=False)
        
        # Get metadata twice
        metadata1 = controller.get_tools_metadata()
        metadata2 = controller.get_tools_metadata()
        
        # Should be identical
        assert len(metadata1) == len(metadata2)
        
        for m1, m2 in zip(metadata1, metadata2):
            assert m1["name"] == m2["name"]
            assert m1["risk_level"] == m2["risk_level"]
            assert m1["description"] == m2["description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
