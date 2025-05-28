# Dataset-Tools/debug_imports.py
import sys
import traceback # Ensure traceback is imported to be used in except blocks

print("--- Python Import Debug Script ---")
print(f"Python version: {sys.version}")
print("Current sys.path:")
for p in sys.path:
    print(f"  - {p}")
print("-------------------------------------\n")

print("1. Importing dataset_tools.correct_types directly...")
try:
    from dataset_tools import correct_types
    print("   OK: dataset_tools.correct_types imported.")
    print(f"   Content of correct_types: {dir(correct_types)[:5]} ... (first 5 names)") # Show a few names
except Exception as e:
    print(f"   FAIL: Could not import dataset_tools.correct_types: {e}")
    traceback.print_exc()
    sys.exit(1) # Exit if this critical import fails

print("\n2. Importing dataset_tools.logger directly...")
try:
    from dataset_tools import logger
    print("   OK: dataset_tools.logger imported.")
    print(f"   Content of logger: {dir(logger)[:5]} ...")
except Exception as e:
    print(f"   FAIL: Could not import dataset_tools.logger: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n3. Importing dataset_tools.model_parsers.base_model_parser directly...")
try:
    from dataset_tools.model_parsers import base_model_parser
    print("   OK: dataset_tools.model_parsers.base_model_parser module imported.")
    # print(f"   Content of base_model_parser: {dir(base_model_parser)}") # Can be very verbose
    from dataset_tools.model_parsers.base_model_parser import BaseModelParser, ModelParserStatus
    print("   OK: BaseModelParser and ModelParserStatus imported from base_model_parser.")
    print(f"      BaseModelParser: {BaseModelParser}")
    print(f"      ModelParserStatus: {ModelParserStatus}")
except Exception as e:
    print(f"   FAIL: Error with model_parsers.base_model_parser: {e}")
    traceback.print_exc()
    sys.exit(1) # Likely critical if base parser fails

print("\n4. Importing dataset_tools.model_parsers.safetensors_parser directly...")
try:
    from dataset_tools.model_parsers import safetensors_parser
    print("   OK: dataset_tools.model_parsers.safetensors_parser module imported.")
    # print(f"   Content of safetensors_parser: {dir(safetensors_parser)}")
    from dataset_tools.model_parsers.safetensors_parser import SafetensorsParser as DirectSafetensorsParser
    print("   OK: SafetensorsParser imported directly from safetensors_parser.py.")
    print(f"      SafetensorsParser (direct): {DirectSafetensorsParser}")
except Exception as e:
    print(f"   FAIL: Error with model_parsers.safetensors_parser: {e}")
    traceback.print_exc()
    sys.exit(1) # If this fails, the __init__.py import will also fail

print("\n5. Importing SafetensorsParser from dataset_tools.model_parsers package (via __init__.py)...")
try:
    from dataset_tools.model_parsers import SafetensorsParser as PkgSParser # Changed alias
    print("   OK: SafetensorsParser imported via model_parsers package.")
    print(f"      SafetensorsParser (from package): {PkgSParser}")
except Exception as e:
    print(f"   FAIL: Could not import SafetensorsParser via model_parsers package: {e}")
    traceback.print_exc()
    sys.exit(1) # This is the import failing in model_tool.py

print("\n6. Attempting the import as done in model_tool.py (which imports model_parsers)...")
try:
    from dataset_tools.model_tool import ModelTool 
    print("   OK: Successfully imported ModelTool (implies its internal imports worked).")
    print(f"      ModelTool: {ModelTool}")
except Exception as e:
    print(f"   FAIL: Could not import ModelTool: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n--- All attempted imports finished. ---")