

class PipelineElement(Generic[T, U]):
    """
    Element pipeline'u, który przetwarza dane wejściowe i zwraca wynik.
    """

    def __init__(self, function: Callable[[T], U], name: Optional[str] = None):
        self.function = function
        self.name = name or function.__name__

    def __call__(self, input_data: T) -> U:
        return self.function(input_data)


