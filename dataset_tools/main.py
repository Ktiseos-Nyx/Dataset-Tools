# // SPDX-License-Identifier: CC0-1.0
# // --<{ Ktiseos Nyx }>--

"""啟動程式，退出程式"""

import sys
from dataset_tools.ui import MainWindow  # Import our main window class
from PyQt6 import QtWidgets
from dataset_tools.logger import info_monitor as loginfo


def main():
    """Launch application"""
    loginfo("Launching application...")

    app = QtWidgets.QApplication(sys.argv)  # pylint: disable=c-extension-no-member
    window = MainWindow()  # Initialize our main window.
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # begin routine
    main()
