
class CommandResult:
    """
    Klasa reprezentująca wynik wykonania komendy.
    """

    def __init__(self,
                 success: bool,
                 data: Any = None,
                 error: Optional[str] = None,
                 generated_code: Optional[str] = None,
                 execution_log: Optional[List[Dict[str, Any]]] = None,
                 sql: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
        self.generated_code = generated_code
        self.execution_log = execution_log or []
        self.sql = sql

    def __repr__(self) -> str:
        if self.success:
            return f"CommandResult(success=True, data={self.data})"
        return f"CommandResult(success=False, error={self.error})"
