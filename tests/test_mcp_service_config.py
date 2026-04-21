from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READYAI_SRC = ROOT / "ReadyAI-demo" / "iris" / "projects" / "src" / "ReadyAI"


def test_mcp_dispatch_classes_extend_mcp_service():
    dispatch_classes = {
        "BasicMCP.cls": "%AI.MCP.Service",
        "AdvancedMCP.cls": "%AI.MCP.Service",
    }

    for file_name, expected_base in dispatch_classes.items():
        declaration = (READYAI_SRC / file_name).read_text(encoding="utf-8").splitlines()[0].strip()
        assert f"Extends {expected_base}" in declaration, (
            f"{file_name} must extend {expected_base} to serve an MCP web application, got: {declaration}"
        )