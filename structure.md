dialogware-text-to-software/
├── LICENSE
├── README.md
├── pyproject.toml
├── setup.cfg
├── src/
│   └── dialogware/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── parser.py
│       │   ├── translator.py
│       │   ├── pipeline.py
│       │   └── executor.py
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── file_operations/
│       │   ├── sql_operations/
│       │   ├── browser_operations/
│       │   └── code_generation/
│       ├── debuggers/
│       │   ├── __init__.py
│       │   ├── nlp_debugger.py
│       │   ├── dsl_debugger.py
│       │   ├── pipeline_debugger.py
│       │   └── execution_debugger.py
│       ├── designers/
│       │   └── pipeline_designer.py
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── anthropic_client.py
│       │   └── ollama_client.py
│       └── utils/
│           ├── __init__.py
│           ├── logging.py
│           ├── visualization.py
│           └── storage.py
└── tests/
    ├── __init__.py
    ├── test_core/
    ├── test_plugins/
    ├── test_debuggers/
    └── test_llm/