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

    def test_packaged_environment_uses_system_python(self, server_manager):
        """
        Test that in packaged environment (frozen=True),
        the server uses system Python from PATH, not the .exe itself.

        This is the key bugfix: prevents launching the GUI .exe again.
        """
        # Mock QProcess to prevent actual process start
        with patch.object(server_manager.process, 'start') as mock_start, \
             patch.object(server_manager.process, 'state', return_value=QProcess.ProcessState.NotRunning), \
             patch.object(server_manager.process, 'setWorkingDirectory'), \
             patch.object(server_manager.process, 'processEnvironment'), \
             patch.object(server_manager.process, 'setProcessEnvironment'), \
             patch('shutil.which', return_value='/usr/bin/python3'):

            # Simulate packaged environment
            sys.frozen = True

            try:
                # Start server
                server_manager.start_server('127.0.0.1', 8000, '/tmp')

                # Verify start was called with system Python
                mock_start.assert_called_once()
                call_args = mock_start.call_args
                program = call_args[0][0]
                args = call_args[0][1]

                # Key assertion: should NOT use sys.executable in frozen state
                assert program != sys.executable, \
                    "In frozen state, should use system Python, not sys.executable"

                # Should use the Python found via shutil.which
                assert program == '/usr/bin/python3', \
                    f"Expected program to be /usr/bin/python3, got {program}"

                assert "-m" in args
                assert "docx_mcp_server.server" in args
            finally:
                # Clean up
                if hasattr(sys, 'frozen'):
                    delattr(sys, 'frozen')

    def test_packaged_environment_no_python_shows_error(self, server_manager):
        """
        Test that when Python is not found in PATH in packaged environment,
        a clear error message is emitted.
        """
        # Mock signal to capture error
        error_emitted = []
        server_manager.server_error.connect(lambda msg: error_emitted.append(msg))

        with patch.object(server_manager.process, 'state', return_value=QProcess.ProcessState.NotRunning), \
             patch('shutil.which', return_value=None):

            # Simulate packaged environment
            sys.frozen = True

            try:
                # Start server (should fail gracefully)
                server_manager.start_server('127.0.0.1', 8000, '/tmp')

                # Verify error was emitted
                assert len(error_emitted) > 0, "Expected error to be emitted"
                assert "Cannot find Python interpreter" in error_emitted[0]
                assert "PATH" in error_emitted[0]
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
