"""
pipeline_debugger.py
"""


# src/dialogware/debuggers/pipeline_debugger.py
"""
Debuger dla warstwy pipeline.
"""

import time
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic

T = TypeVar('T')


class PipelineDebugger:
    """
    Narzędzie do debugowania pipeline'ów.
    """

    def trace(self, pipeline, input_data: Any) -> 'PipelineTrace':
        """
        Śledzi wykonanie pipeline'u.

        Args:
            pipeline: Pipeline do śledzenia
            input_data: Dane wejściowe

        Returns:
            Ślad wykonania pipeline'u
        """
        # Włączenie trybu debugowania
        original_debug_mode = pipeline.debug_mode
        pipeline.debug_mode = True

        # Pomiar czasu wykonania
        start_time = time.time()
        result = pipeline.execute(input_data)
        total_time = time.time() - start_time

        # Przywrócenie oryginalnego trybu
        pipeline.debug_mode = original_debug_mode

        # Utworzenie śladu
        trace = PipelineTrace(
            pipeline_name=pipeline.name,
            execution_trace=pipeline.execution_trace.copy(),
            input_data=input_data,
            output_data=result,
            total_time=total_time
        )

        return trace

