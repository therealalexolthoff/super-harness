""" Tool registry: stores tools, generates schemas, dispatches calls."""

from dataclasses import dataclass
from typing import Any, Callable
from pydantic import TypeAdapter
import inspect

@dataclass
class Tool:
    """ A registered tool - wraps a Python function with its metadata."""
    name: str
    description: str
    function: Callable
    schema: dict

class ToolRegistry:
    """Holds tools, exposes their schemas, dispatches incoming calls."""

    def __init__(self) -> None:
        # Tools indexed by name for 0(1) dispatch look up.
        self._tools: dict[str,Tool] = {}

    def register(self, tool: Tool) -> None:
        # Last-write-wins if the same name is registered twice.
        self._tools[tool.name] = tool

    def get_schemas(self) -> list[dict]:
        """Return the list of tool schemas in the OpenAI tools= format."""
        # Wrap each tool's schema in OpenAI's required {"type": "function"} envelope.
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameter": 
                    t.schema,
                }
            }
        ]

    