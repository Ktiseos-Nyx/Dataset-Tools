
import sys
from dataset_tools.ui import MainWindow  # Import our main window class

def main():
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow() # Initialize our main window.
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
