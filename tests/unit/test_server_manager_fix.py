"""
Unit tests for server_manager.py bugfix.

Tests the fix for the window popup issue when starting server in packaged environment.
Bug: Clicking "Start Server" would pop up another window in Windows .exe build.
Root Cause: sys.executable points to the .exe itself when frozen, causing recursive launch.
Fix: Detect frozen state and use system Python interpreter instead.
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QProcess

# Import the module to test
from docx_server_launcher.core.server_manager import ServerManager


class TestServerManagerBugFix:
    """Test the bugfix for preventing window popup in packaged environment."""

    @pytest.fixture
    def server_manager(self):
        """Create a ServerManager instance for testing."""
        return ServerManager()

    def test_development_environment_uses_sys_executable(self, server_manager):
        """
        Test that in development environment (not frozen),
        the server uses sys.executable (current Python interpreter).
        """
        # Mock QProcess to prevent actual process start
        with patch.object(server_manager.process, 'start') as mock_start, \
             patch.object(server_manager.process, 'state', return_value=QProcess.ProcessState.NotRunning), \
             patch.object(server_manager.process, 'setWorkingDirectory'), \
             patch.object(server_manager.process, 'processEnvironment'), \
             patch.object(server_manager.process, 'setProcessEnvironment'):

            # Ensure sys.frozen is not set (development environment)
            if hasattr(sys, 'frozen'):
                delattr(sys, 'frozen')

            # Start server
            server_manager.start_server('127.0.0.1', 8000, '/tmp')

            # Verify start was called with sys.executable
            mock_start.assert_called_once()
            call_args = mock_start.call_args
            program = call_args[0][0]
            args = call_args[0][1]

            assert program == sys.executable, \
                f"Expected program to be sys.executable, got {program}"
            assert "-m" in args
            assert "docx_mcp_server.server" in args

    def test_packaged_environment_uses_self_executable_in_server_mode(self, server_manager):
        """
        Test that in packaged environment (frozen=True),
        the server uses the executable itself with --server-mode flag.
        """
        # Mock QProcess
        with patch.object(server_manager.process, 'start') as mock_start, \
             patch.object(server_manager.process, 'state', return_value=QProcess.ProcessState.NotRunning), \
             patch.object(server_manager.process, 'setWorkingDirectory'), \
             patch.object(server_manager.process, 'processEnvironment'), \
             patch.object(server_manager.process, 'setProcessEnvironment'):

            # Simulate packaged environment
            sys.frozen = True

            try:
                # Start server
                server_manager.start_server('127.0.0.1', 8000, '/tmp')

                # Verify start was called
                mock_start.assert_called_once()
                call_args = mock_start.call_args
                program = call_args[0][0]
                args = call_args[0][1]

                # Key assertion: should use sys.executable (the exe itself)
                assert program == sys.executable, \
                    f"Expected program to be sys.executable ({sys.executable}), got {program}"

                # Key assertion: should include --server-mode flag
                assert "--server-mode" in args, "Args must include --server-mode"
                assert "--transport" in args
                assert "sse" in args

            finally:
                # Clean up
                if hasattr(sys, 'frozen'):
                    delattr(sys, 'frozen')

    def test_regression_normal_operation_still_works(self, server_manager):
        """
        Regression test: Ensure the fix doesn't break normal operation.
        Test that all expected arguments are still passed correctly.
        """
        with patch.object(server_manager.process, 'start') as mock_start, \
             patch.object(server_manager.process, 'state', return_value=QProcess.ProcessState.NotRunning), \
             patch.object(server_manager.process, 'setWorkingDirectory') as mock_set_cwd, \
             patch.object(server_manager.process, 'processEnvironment'), \
             patch.object(server_manager.process, 'setProcessEnvironment'):

            # Ensure development environment
            if hasattr(sys, 'frozen'):
                delattr(sys, 'frozen')

            # Start server with custom parameters
            server_manager.start_server('0.0.0.0', 9000, '/custom/path')

            # Verify working directory was set
            mock_set_cwd.assert_called_once_with('/custom/path')

            # Verify all parameters in args
            call_args = mock_start.call_args
            args = call_args[0][1]

            assert "--transport" in args
            assert "sse" in args
            assert "--port" in args
            assert "9000" in args
            assert "--host" in args
            assert "0.0.0.0" in args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
