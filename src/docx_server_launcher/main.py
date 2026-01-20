import sys
from PyQt6.QtWidgets import QApplication
from docx_server_launcher.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Docx Server Launcher")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
