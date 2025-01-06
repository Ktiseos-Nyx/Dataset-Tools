"""啟動程式，退出程式"""

import sys

from PyQt6 import QtWidgets # ignore

from dataset_tools import logger
from dataset_tools.ui import MainWindow  # Import our main window class

def main():
    """Launch application"""
    logger.info("%s","Launching application...")

    app = QtWidgets.QApplication(sys.argv) # pylint: disable=c-extension-no-member
    window = MainWindow() # Initialize our main window.
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
