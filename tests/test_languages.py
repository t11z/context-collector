"""Tests for language detection."""

from llm_context_collector.languages import detect_language


class TestDetectLanguage:
    def test_python(self) -> None:
        assert detect_language("app.py") == "python"

    def test_javascript(self) -> None:
        assert detect_language("index.js") == "javascript"
        assert detect_language("module.mjs") == "javascript"
        assert detect_language("require.cjs") == "javascript"

    def test_typescript(self) -> None:
        assert detect_language("app.ts") == "typescript"
        assert detect_language("App.tsx") == "tsx"

    def test_go(self) -> None:
        assert detect_language("main.go") == "go"

    def test_rust(self) -> None:
        assert detect_language("lib.rs") == "rust"

    def test_yaml(self) -> None:
        assert detect_language("config.yml") == "yaml"
        assert detect_language("config.yaml") == "yaml"

    def test_dockerfile(self) -> None:
        assert detect_language("Dockerfile") == "dockerfile"
        assert detect_language("app.dockerfile") == "dockerfile"

    def test_unknown_extension(self) -> None:
        assert detect_language("data.xyz") == ""

    def test_no_extension(self) -> None:
        assert detect_language("README") == ""

    def test_makefile(self) -> None:
        assert detect_language("Makefile") == "makefile"

    def test_c_and_cpp(self) -> None:
        assert detect_language("main.c") == "c"
        assert detect_language("header.h") == "c"
        assert detect_language("main.cpp") == "cpp"
        assert detect_language("header.hpp") == "cpp"
