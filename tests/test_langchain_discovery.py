import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PATH = ROOT / "ReadyAI-demo" / "langchain_external" / "langchain_discovery.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("langchain_discovery", DISCOVERY_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_mcp_config_uses_single_proxy_connection():
    module = _load_module()

    config = module.build_mcp_config("token")

    assert list(config) == ["readyai"]
    assert config["readyai"]["transport"] == "http"
    assert config["readyai"]["url"] == module.MCP_PROXY_URL
    assert config["readyai"]["headers"] == {"Authorization": "Basic token"}