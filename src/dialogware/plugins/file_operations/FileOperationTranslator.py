import os
import shutil
import glob
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import fnmatch

from dialogware.core import AbstractParser, AbstractTranslator, AbstractExecutor, CommandResult



class FileOperationTranslator(AbstractTranslator):
    """
    Translator dla operacji na plikach.
    """

    def translate(self, parsed_data: Dict[str, Any]) -> str:
        """
        Tłumaczy sparsowane dane na DSL dla operacji na plikach.

        Args:
            parsed_data: Dane po parsowaniu

        Returns:
            Reprezentacja w DSL
        """
        operation = parsed_data.get("operation", "find")
        params = parsed_data.get("params", {})

        # Tworzenie DSL dla operacji na plikach
        dsl_parts = []

        # Bazowa operacja
        if operation == "find":
            dsl_parts.append("find(")
        elif operation == "list":
            dsl_parts.append("list(")
        elif operation == "create":
            dsl_parts.append("create(")
        elif operation == "delete":
            dsl_parts.append("delete(")
        elif operation == "copy":
            dsl_parts.append("copy(")
        elif operation == "move":
            dsl_parts.append("move(")
        elif operation == "modify":
            dsl_parts.append("modify(")

        # Dodawanie ścieżek i wzorców
        paths = params.get("paths", [])
        patterns = params.get("patterns", [])

        if paths and patterns:
            path_str = ', '.join([f'"{p}"' for p in paths])
            pattern_str = ', '.join([f'"{p}"' for p in patterns])
            dsl_parts.append(f"paths=[{path_str}], patterns=[{pattern_str}]")
        elif paths:
            path_str = ', '.join([f'"{p}"' for p in paths])
            dsl_parts.append(f"paths=[{path_str}]")
        elif patterns:
            pattern_str = ', '.join([f'"{p}"' for p in patterns])
            dsl_parts.append(f"patterns=[{pattern_str}]")
        else:
            dsl_parts.append('"*"')  # Domyślny wzorzec

        dsl_parts.append(")")

        # Dodawanie filtrów
        size_filters = params.get("size_filters", [])
        for filt in size_filters:
            operator = filt.get("operator")
            value = filt.get("value")
            dsl_parts.append(f".where(size {operator} {value})")

        date_filters = params.get("date_filters", [])
        for filt in date_filters:
            if "period" in filt:
                period = filt.get("period")
                dsl_parts.append(f".where(modified_in('{period}'))")
            else:
                operator = filt.get("operator")
                value = filt.get("value")
                unit = filt.get("unit")
                dsl_parts.append(f".where(modified {operator} {value} {unit})")

        content_filters = params.get("content_filters", [])
        for filt in content_filters:
            filter_type = filt.get("filter_type")
            value = filt.get("value")
            if filter_type == "contains":
                dsl_parts.append(f".where(content_contains('{value}'))")
            elif filter_type == "not_contains":
                dsl_parts.append(f".where(not content_contains('{value}'))")

        # Dodawanie dodatkowych akcji
        additional_actions = params.get("additional_actions", [])
        for action in additional_actions:
            action_type = action.get("action")
            if action_type == "copy":
                destination = action.get("destination")
                dsl_parts.append(f".copy_to('{destination}')")
            elif action_type == "move":
                destination = action.get("destination")
                dsl_parts.append(f".move_to('{destination}')")
            elif action_type == "convert":
                format_to = action.get("format")
                dsl_parts.append(f".convert_to('{format_to}')")

        return "".join(dsl_parts)