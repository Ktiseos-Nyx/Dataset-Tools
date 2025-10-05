# dataset_tools/vendored_sdpr/format/forge_format.py

__author__ = "receyuki & Ktiseos Nyx"
__filename__ = "forge_format.py"
__copyright__ = "Copyright 2023, Receyuki; Modified 2025, Ktiseos Nyx"
__email__ = "receyuki@gmail.com; your_email@example.com"

import re

from .a1111 import A1111


class ForgeFormat(A1111):
    """Parser for Forge/ReForge.

    Inherits from A1111 to use its helper methods
    but provides its own independent _process logic.
    """

    tool = "Forge"

    def _process(self) -> None:
        """Process and identify Forge/ReForge-specific metadata.

        This method DOES NOT call super()._process(). It performs its own
        checks and then uses helper methods inherited from A1111.
        """
        self._logger.debug("Attempting to parse as %s.", self.tool)

        # We need the full A1111-style text block to check for markers.
        if not self._raw:
            self._raw = self._extract_raw_data_from_info()

        if not self._raw:
            raise self.NotApplicableError("No raw text data found to check for Forge markers.")

        # --- THE DEFINITIVE SIGNATURE CHECK (ON THE ENTIRE RAW STRING) ---
        # A file is considered Forge/ReForge if it has ANY of these unique markers.
        # We use a regex for the version check to be precise.

        forge_version_match = re.search(r"Version:\s*f", self._raw, re.IGNORECASE)
        has_auto_scheduler = "Schedule type: Automatic" in self._raw
        has_hires_module = "Hires Module 1:" in self._raw

        is_unambiguously_forge = forge_version_match or has_auto_scheduler or has_hires_module

        if not is_unambiguously_forge:
            raise self.NotApplicableError("No definitive Forge/ReForge markers found in raw text.")
        # --- END OF CHECK ---

        # --- IT IS FORGE! NOW WE PARSE IT FULLY ---
        self._logger.info("Identified as Forge by signature in raw text.")

        # Now that we know it's Forge, we can use the inherited A1111 helper
        # to do the heavy lifting of parsing the prompts and parameters.
        self._parse_a1111_text_format()

        # The tool name is already 'Forge'. The BaseFormat.parse() method will
        # set the final status to READ_SUCCESS because we didn't raise an error.
