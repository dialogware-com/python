"""
execution_debugger.py
"""



# src/dialogware/debuggers/execution_debugger.py
"""
Debuger dla warstwy wykonania komend.
"""

import time
import traceback
from typing import Any, Dict, List, Optional, Callable, Union


class ExecutionDebugger:
    """
    Narzędzie do debugowania wykonania komend.
    """

    def capture(self, func: Callable, *args, **kwargs) -> 'ExecutionLog':
        """
        Przechwytuje wykonanie funkcji.

        Args:
            func: Funkcja do wykonania
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            Log wykonania
        """
        log = ExecutionLog()

        # Rozpoczęcie logowania
        log.start()

        try:
            # Wykonanie funkcji
            result = func(*args, **kwargs)
            log.set_result(result)
        except Exception as e:
            # Logowanie błędu
            log.log_error(e)
            raise
        finally:
            # Zakończenie logowania
            log.stop()

        return log

