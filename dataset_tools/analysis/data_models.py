# dataset_tools/analysis/data_models.py
"""Pydantic models for ensuring data integrity throughout the application.

This file acts as the single source of truth for the "shape" of our data.
"""

from typing import Literal

from pydantic import BaseModel, Field


# This is the "blueprint" for the final output of our feature analysis.
class FeatureAnalysisResult(BaseModel):
    """Defines the structured result of a feature analysis check."""

    # Using Field() allows us to add descriptions, which is great for documentation.
    is_flux: bool = Field(..., description="True if the generation used a FLUX model.")
    is_ponyx: bool = Field(..., description="True if the generation used a PonyXL finetune.")
    is_illustriousxl: bool = Field(..., description="True if the generation used an IllustriousXL finetune.")
    has_lora: bool = Field(..., description="True if a LoRA was detected in the generation.")

    # Using Literal forces the value to be one of these specific strings.
    # This prevents typos and guarantees the architecture is a known value.
    architecture: Literal["SD1.5", "SDXL/Other", "Unknown"] = Field(
        ..., description="The detected base architecture of the model."
    )

    has_known_finetune_or_lora: bool = Field(
        ...,
        description="A summary boolean that is True if any specific feature was found.",
    )
