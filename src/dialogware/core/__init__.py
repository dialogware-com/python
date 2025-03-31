# src/dialogware/core/__init__.py
"""
DialogWare: Text-to-Software - rdzeń systemu
============================================

Ten moduł zawiera podstawowe klasy abstrakcyjne definiujące architekturę systemu.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic

T = TypeVar('T')
U = TypeVar('U')

