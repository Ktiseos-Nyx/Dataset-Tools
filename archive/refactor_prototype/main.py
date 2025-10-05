# refactor_prototype/main.py

import sys
from qtpy import QtWidgets
from views import MainWindow

def main():
    """Main function to run the application."""
    app = QtWidgets.QApplication(sys.argv)

    # Import and apply theme after QApplication is created
    from qt_material import apply_stylesheet
    apply_stylesheet(app, theme='dark_teal.xml')

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
