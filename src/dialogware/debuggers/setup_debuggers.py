
# Funkcje pomocnicze
def setup_debuggers(plugin_manager=None):
    """
    Konfiguruje i rejestruje debugery.

    Args:
        plugin_manager: Opcjonalny zarządca wtyczek

    Returns:
        Słownik z debugerami
    """
    nlp_debugger = NLPDebugger()
    dsl_debugger = DSLDebugger()
    pipeline_debugger = PipelineDebugger()
    execution_debugger = ExecutionDebugger()

    # Rejestrowanie komponentów w debugerach, jeśli mamy zarządcę wtyczek
    if plugin_manager:
        for domain, parser in plugin_manager.parsers.items():
            nlp_debugger.register_parser(domain, parser)

        for domain, translator in plugin_manager.translators.items():
            dsl_debugger.register_translator(domain, translator)

    return {
        "nlp": nlp_debugger,
        "dsl": dsl_debugger,
        "pipeline": pipeline_debugger,
        "execution": execution_debugger
    }