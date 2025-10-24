"""Lightweight CLI parser for Dataset-Tools - NO GUI DEPENDENCIES.

This module provides a headless command-line interface for parsing image metadata.
Perfect for Discord bots, CI/CD pipelines, and serverless environments.

Key Features:
- NO PyQt6 imports - completely headless
- Full metadata extraction power (dispatcher + numpy scorers)
- JSON output for machine-readable integration
- Subprocess-friendly for Discord bot usage
- Memory efficient - parse and exit

Usage:
    dataset-tools-parse image.png --json
    dataset-tools-parse image.png --pretty
    dataset-tools-parse image.png  # Human-readable output
"""

import sys
import json
import argparse
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging for CLI usage.

    Args:
        verbose: Enable verbose debug output
        quiet: Suppress all logs except CRITICAL (for JSON output)
    """
    if quiet:
        level = logging.CRITICAL  # Only show critical errors in quiet mode
        # Set environment variable BEFORE importing to suppress session start logs
        os.environ['DATASET_TOOLS_CLI_QUIET'] = '1'
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    # Configure root logger to suppress everything
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Send logs to stderr, not stdout
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Parse AI image metadata (headless mode)",
        epilog="Perfect for Discord bots and serverless environments!"
    )

    parser.add_argument(
        'image_path',
        help="Path to image file"
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help="Output JSON format (machine-readable)"
    )

    parser.add_argument(
        '--pretty',
        action='store_true',
        help="Pretty-print JSON output (implies --json)"
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose debug output to stderr"
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help="Suppress all logs except critical errors (recommended for JSON parsing)"
    )

    parser.add_argument(
        '--compact',
        action='store_true',
        help="Compact JSON output (no indentation)"
    )

    return parser.parse_args()


def format_metadata_human(metadata: Dict[str, Any]) -> str:
    """Format metadata for human-readable output.

    Args:
        metadata: Parsed metadata dictionary

    Returns:
        Formatted string for terminal display
    """
    lines = ["=" * 60, "Image Metadata", "=" * 60, ""]

    # Basic info
    if 'ui_system' in metadata:
        lines.append(f"UI System: {metadata['ui_system']}")

    if 'model' in metadata:
        lines.append(f"Model: {metadata['model']}")

    # Prompts
    if 'positive_prompt' in metadata:
        lines.append("\nPositive Prompt:")
        lines.append("-" * 60)
        lines.append(metadata['positive_prompt'])

    if 'negative_prompt' in metadata:
        lines.append("\nNegative Prompt:")
        lines.append("-" * 60)
        lines.append(metadata['negative_prompt'])

    # Settings
    if 'settings' in metadata and metadata['settings']:
        lines.append("\nSettings:")
        lines.append("-" * 60)
        for key, value in metadata['settings'].items():
            lines.append(f"  {key}: {value}")

    # Resources (LoRAs, embeddings, etc.)
    if 'resources' in metadata and metadata['resources']:
        lines.append("\nResources:")
        lines.append("-" * 60)
        for resource in metadata['resources']:
            resource_type = resource.get('type', 'unknown')
            resource_name = resource.get('name', 'unnamed')
            lines.append(f"  [{resource_type}] {resource_name}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def cli_parse() -> None:
    """Main CLI entry point - parse image metadata and output results.

    Exit codes:
        0: Success
        1: File not found or invalid path
        2: No metadata found in image
        3: Parsing error
    """
    args = parse_args()

    # Auto-enable quiet mode for JSON output (unless verbose is explicitly set)
    auto_quiet = (args.json or args.pretty) and not args.verbose
    quiet_mode = args.quiet or auto_quiet

    setup_logging(args.verbose, quiet_mode)

    # Import AFTER logging setup to allow quiet mode to take effect
    from dataset_tools.metadata_engine import parse_file_metadata

    # Validate input file
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: File not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    if not image_path.is_file():
        print(f"Error: Not a file: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get parser definitions path (bundled with package)
        import dataset_tools
        package_dir = Path(dataset_tools.__file__).parent
        parser_definitions_path = package_dir / "parser_definitions"

        # Parse metadata using Dataset-Tools metadata engine
        result = parse_file_metadata(
            file_input=str(image_path),
            parser_definitions_path=str(parser_definitions_path),
            logger=None  # Use default logger setup
        )

        # Extract metadata dictionary from result
        if isinstance(result, dict):
            metadata = result
        elif hasattr(result, '__dict__'):
            # If it's a BaseFormat object, convert to dict
            metadata = vars(result)
        else:
            metadata = None

        if not metadata or not isinstance(metadata, dict):
            print("No metadata found in image", file=sys.stderr)
            sys.exit(2)

        # Output results
        if args.pretty or args.json:
            # JSON output
            if args.compact:
                indent = None
            elif args.pretty:
                indent = 2
            else:
                indent = None

            print(json.dumps(metadata, indent=indent))
        else:
            # Human-readable output
            print(format_metadata_human(metadata))

        sys.exit(0)

    except Exception as e:
        logging.exception("Error parsing metadata")
        print(f"Error parsing metadata: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    cli_parse()
