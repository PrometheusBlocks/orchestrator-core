"""Utility Contract — shared schema for all PrometheusBlocks utilities."""

from pydantic import BaseModel, Field
from typing import List

MAX_UTILITY_TOKENS = 200_000


class Dependency(BaseModel):
    package: str
    version: str = Field(..., pattern=r"^[^\s]+$")


class EntryPoint(BaseModel):
    name: str
    description: str
    parameters_schema: dict
    return_schema: dict


class UtilityContract(BaseModel):
    name: str
    version: str
    language: str = Field(..., description="e.g. python, swift")
    description: str
    size_budget: int = MAX_UTILITY_TOKENS
    entrypoints: List[EntryPoint]
    deps: List[Dependency] = []
    tests: List[str] = []

    class Config:
        title = "PrometheusBlocks Utility Contract"
        anystr_strip_whitespace = True
