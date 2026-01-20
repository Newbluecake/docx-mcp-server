import sys

def main():
    # Check for server mode argument
    if "--server-mode" in sys.argv:
        # Remove the flag so it doesn't confuse the server argument parser
        sys.argv.remove("--server-mode")

        # Import and run server directly
        try:
            from docx_mcp_server.server import main as server_main
            server_main()
        except ImportError as e:
            print(f"Error importing server module: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # GUI Mode
    from PyQt6.QtWidgets import QApplication
    from docx_server_launcher.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Docx Server Launcher")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
