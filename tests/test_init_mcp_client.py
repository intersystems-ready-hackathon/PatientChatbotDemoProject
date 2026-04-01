import json
from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import requires_iris, MCP_URL, MCP_TRANSPORT


def _mock_mcp_config(mock_iris, config_payload: dict, repeats: int = 1):
    config_ref = MagicMock()
    details_ref = MagicMock()
    details_ref.getValue.return_value.invoke.return_value = json.dumps(config_payload)
    config_ref.getValue.return_value.invoke.return_value = 1

    mock_irispy = MagicMock()
    mock_irispy.classMethodValue.return_value = 1
    mock_iris.createIRIS.return_value = mock_irispy
    mock_iris.IRISReference.side_effect = [config_ref, details_ref] * repeats


class TestInitMCPClientUnit:
    def test_raises_on_dot_in_config_name(self):
        from langchain_intersystems.mcp import init_mcp_client

        with pytest.raises(ValueError, match="must not contain '.'"):
            init_mcp_client(["AI.MCP.readyai"], MagicMock())

    def test_raises_on_duplicate_config_name(self):
        from langchain_intersystems.mcp import init_mcp_client

        conn = MagicMock()
        cfg = {"transport": "http", "url": "http://iris:8888/mcp/readyai"}
        with patch("langchain_intersystems.mcp.iris") as mock_iris:
            _mock_mcp_config(mock_iris, cfg, repeats=2)

            with pytest.raises(ValueError, match="duplicate"):
                init_mcp_client(["readyai", "readyai"], conn)

    def test_raises_if_transport_missing(self):
        from langchain_intersystems.mcp import _get_mcp_config

        conn = MagicMock()
        with patch("langchain_intersystems.mcp.iris") as mock_iris:
            _mock_mcp_config(mock_iris, {"url": "http://localhost:8888/mcp/readyai"})

            with pytest.raises(ValueError, match="transport is missing"):
                _get_mcp_config("readyai", conn)

    def test_raises_on_invalid_transport(self):
        from langchain_intersystems.mcp import _get_mcp_config

        conn = MagicMock()
        with patch("langchain_intersystems.mcp.iris") as mock_iris:
            _mock_mcp_config(mock_iris, {"transport": "ftp", "url": "ftp://nowhere"})

            with pytest.raises(ValueError, match="Invalid transport"):
                _get_mcp_config("readyai", conn)

    def test_returns_multi_server_client_on_valid_config(self):
        from langchain_intersystems.mcp import init_mcp_client
        from langchain_mcp_adapters.client import MultiServerMCPClient

        conn = MagicMock()
        with patch("langchain_intersystems.mcp.iris") as mock_iris:
            _mock_mcp_config(mock_iris, {"transport": "http", "url": "http://iris:8888/mcp/readyai"})

            result = init_mcp_client(["readyai"], conn)

        assert isinstance(result, MultiServerMCPClient)

    def test_multi_server_client_has_correct_connections(self):
        from langchain_intersystems.mcp import init_mcp_client
        from langchain_mcp_adapters.client import MultiServerMCPClient

        conn = MagicMock()
        cfg = {"transport": "http", "url": "http://iris:8888/mcp/readyai"}
        with patch("langchain_intersystems.mcp.iris") as mock_iris, \
             patch("langchain_intersystems.mcp.MultiServerMCPClient") as mock_cls:
            _mock_mcp_config(mock_iris, cfg)

            init_mcp_client(["readyai"], conn)

            mock_cls.assert_called_once_with({"readyai": cfg})

    def test_configstore_error_raises_runtime_error(self):
        from langchain_intersystems.mcp import _get_mcp_config

        conn = MagicMock()
        with patch("langchain_intersystems.mcp.iris") as mock_iris:
            config_ref = MagicMock()
            mock_irispy = MagicMock()
            mock_irispy.classMethodValue.side_effect = lambda cls, method, *args: (
                0 if method == "Get" else "not found"
            )
            mock_iris.createIRIS.return_value = mock_irispy
            mock_iris.IRISReference.return_value = config_ref

            with pytest.raises(RuntimeError):
                _get_mcp_config("nosuch", conn)


@requires_iris
class TestInitMCPClientIntegration:
    def test_init_mcp_client_resolves_from_configstore(self, iris_conn_superuser):
        import iris as _iris
        from langchain_intersystems.mcp import _get_mcp_config
        from langchain_mcp_adapters.client import MultiServerMCPClient

        irispy = _iris.createIRIS(iris_conn_superuser)

        irispy.classMethodValue("%ConfigStore.Configuration", "Delete", "AI.MCP.readyai")
        cfg_obj = irispy.classMethodObject("%Library.DynamicObject", "%New")
        cfg_obj.invoke("%Set", "transport", MCP_TRANSPORT)
        cfg_obj.invoke("%Set", "url", MCP_URL)
        sc = irispy.classMethodValue(
            "%ConfigStore.Configuration", "Create",
            "AI", "MCP", "", "readyai", cfg_obj
        )
        assert sc == 1, f"ConfigStore Create failed: sc={sc}"

        result = _get_mcp_config("readyai", iris_conn_superuser)
        assert result["transport"] == MCP_TRANSPORT
        assert result["url"] == MCP_URL

    def test_init_mcp_client_unknown_config_raises(self, iris_conn_superuser):
        from langchain_intersystems.mcp import init_mcp_client

        with pytest.raises((RuntimeError, Exception)):
            init_mcp_client(["no_such_mcp_config_xyz"], iris_conn_superuser)
