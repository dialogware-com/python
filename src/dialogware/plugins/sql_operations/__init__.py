# src/dialogware/plugins/sql_operations/__init__.py
"""
DialogWare: Text-to-Software - Moduł Text-to-SQL
================================================

Ten moduł zawiera komponenty potrzebne do konwersji poleceń w języku naturalnym
na zapytania SQL z obsługą fuzzy matching dla tabel i kolumn.
"""

import re
import sqlite3
import json
import datetime
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from difflib import SequenceMatcher
import logging

from dialogware.core import AbstractParser, AbstractTranslator, AbstractExecutor, CommandResult

logger = logging.getLogger(__name__)


class SQLSchema:
    """
    Klasa reprezentująca schemat bazy danych.
    """
