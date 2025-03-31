
class ExecutionLog:
    """
    Log wykonania komendy.
    """

    def __init__(self):
        """
        Inicjalizacja logu.
        """
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.result = None
        self.error = None
        self.error_traceback = None
        self.events = []
        self.resource_usage = {
            "cpu": [],
            "memory": []
        }

    def start(self) -> None:
        """
        Rozpoczyna logowanie.
        """
        self.start_time = time.time()
        self.log_event("Execution started")

    def stop(self) -> None:
        """
        Zatrzymuje logowanie.
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.log_event("Execution completed")

    def log_event(self, message: str, data: Any = None) -> None:
        """
        Loguje zdarzenie.

        Args:
            message: Komunikat
            data: Dodatkowe dane
        """
        event_time = time.time()
        relative_time = event_time - (self.start_time or event_time)

        self.events.append({
            "timestamp": event_time,
            "relative_time": relative_time,
            "message": message,
            "data": data
        })

    def set_result(self, result: Any) -> None:
        """
        Ustawia wynik wykonania.

        Args:
            result: Wynik
        """
        self.result = result
        self.log_event("Result produced", result)

    def log_error(self, error: Exception) -> None:
        """
        Loguje błąd.

        Args:
            error: Błąd
        """
        self.error = str(error)
        self.error_traceback = traceback.format_exc()
        self.log_event("Error occurred", str(error))

    def print_timeline(self) -> None:
        """
        Wyświetla oś czasu wykonania.
        """
        print("=== Execution Timeline ===")
        print(f"Total duration: {self.duration:.4f} seconds")

        for event in self.events:
            print(f"[{event['relative_time']:.4f}s] {event['message']}")
            if event['data'] is not None:
                print(f"  Data: {event['data']}")

        if self.error:
            print("\n=== Error ===")
            print(self.error)
            print("\n=== Traceback ===")
            print(self.error_traceback)

    def show_resource_usage(self) -> None:
        """
        Wyświetla użycie zasobów.
        """
        # TODO: Implementacja monitorowania zasobów
        print("Resource usage monitoring not implemented yet")

