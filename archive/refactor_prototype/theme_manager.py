# refactor_prototype/theme_manager.py

from qtpy import QtWidgets
from qt_material import apply_stylesheet

class ThemeManager(QtWidgets.QMenu):
    """A menu to control the application theme."""

    def __init__(self, parent=None):
        super().__init__("&Themes", parent)

        self.app = QtWidgets.QApplication.instance()

        # Get the list of available themes
        self.themes = [
            'dark_amber.xml',
            'dark_blue.xml',
            'dark_cyan.xml',
            'dark_lightgreen.xml',
            'dark_pink.xml',
            'dark_purple.xml',
            'dark_red.xml',
            'dark_teal.xml',
            'dark_yellow.xml',
            'light_amber.xml',
            'light_blue.xml',
            'light_cyan.xml',
            'light_cyan_500.xml',
            'light_lightgreen.xml',
            'light_pink.xml',
            'light_purple.xml',
            'light_red.xml',
            'light_teal.xml',
            'light_yellow.xml',
        ]

        # Create an action for each theme
        for theme_file in self.themes:
            theme_name = theme_file.replace('.xml', '').replace('_', ' ').title()
            action = self.addAction(theme_name)
            action.triggered.connect(lambda _, t=theme_file: self.apply_theme(t))

    def apply_theme(self, theme_file):
        """Apply the selected theme to the application."""
        print(f"[ThemeManager] Applying theme: {theme_file}")
        apply_stylesheet(self.app, theme=theme_file)
