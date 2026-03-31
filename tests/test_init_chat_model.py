from unittest.mock import MagicMock, patch
import json

import pytest
from tests.conftest import requires_iris


def _mock_chat_config(mock_iris, config_payload: dict, get_status: int = 1):
    config_ref = MagicMock()
    details_ref = MagicMock()
    details_ref.getValue.return_value.invoke.return_value = json.dumps(config_payload)
    config_ref.getValue.return_value.invoke.return_value = 1

    mock_irispy = MagicMock()
    mock_irispy.classMethodValue.return_value = get_status
    mock_iris.createIRIS.return_value = mock_irispy
    mock_iris.IRISReference.side_effect = [config_ref, details_ref]


class TestInitChatModelUnit:
    def test_raises_on_dot_in_config_name(self):
        from langchain_intersystems.chat_models import init_chat_model

        with pytest.raises(ValueError, match="must not contain '.'"):
            init_chat_model("AI.LLM.readyai", MagicMock())

    def test_raises_if_model_missing_from_config(self):
        from langchain_intersystems.chat_models import _get_chat_config

        conn = MagicMock()
        with patch("langchain_intersystems.chat_models.iris") as mock_iris:
            _mock_chat_config(mock_iris, {"model_provider": "openai"})

            with pytest.raises(ValueError, match="model is missing"):
                _get_chat_config("readyai", conn)

    def test_raises_if_model_provider_missing_from_config(self):
        from langchain_intersystems.chat_models import _get_chat_config

        conn = MagicMock()
        with patch("langchain_intersystems.chat_models.iris") as mock_iris:
            _mock_chat_config(mock_iris, {"model": "gpt-4o-mini"})

            with pytest.raises(ValueError, match="model_provider is missing"):
                _get_chat_config("readyai", conn)

    def test_returns_base_chat_model_on_valid_config(self):
        from langchain_intersystems.chat_models import init_chat_model
        from langchain_core.language_models.chat_models import BaseChatModel

        conn = MagicMock()
        with patch("langchain_intersystems.chat_models.iris") as mock_iris, \
             patch("langchain_intersystems.chat_models._init_chat_model") as mock_init:
            _mock_chat_config(mock_iris, {"model_provider": "openai", "model": "gpt-4o-mini"})

            fake_model = MagicMock(spec=BaseChatModel)
            mock_init.return_value = fake_model

            result = init_chat_model("readyai", conn)

            mock_init.assert_called_once_with(model_provider="openai", model="gpt-4o-mini")
            assert result is fake_model

    def test_config_store_error_raises_runtime_error(self):
        from langchain_intersystems.chat_models import _get_chat_config

        conn = MagicMock()
        with patch("langchain_intersystems.chat_models.iris") as mock_iris:
            config_ref = MagicMock()
            mock_irispy = MagicMock()
            mock_irispy.classMethodValue.side_effect = lambda cls, method, *args: (
                0 if method == "Get" else "Config not found"
            )
            mock_iris.createIRIS.return_value = mock_irispy
            mock_iris.IRISReference.return_value = config_ref

            with pytest.raises(RuntimeError):
                _get_chat_config("nosuchconfig", conn)


@requires_iris
class TestInitChatModelIntegration:
    def test_init_chat_model_resolves_from_configstore(self, iris_conn_superuser):
        import iris as _iris
        from langchain_intersystems.chat_models import init_chat_model
        from langchain_core.language_models.chat_models import BaseChatModel

        irispy = _iris.createIRIS(iris_conn_superuser)
        irispy.classMethodValue("ReadyAI.ConfigStoreSetup", "Setup")

        model = init_chat_model("readyai", iris_conn_superuser)
        assert isinstance(model, BaseChatModel), f"Expected BaseChatModel, got {type(model)}"

    def test_init_chat_model_unknown_config_raises(self, iris_conn_superuser):
        from langchain_intersystems.chat_models import init_chat_model

        with pytest.raises((RuntimeError, Exception)):
            init_chat_model("no_such_config_xyz", iris_conn_superuser)

    def test_init_chat_model_returns_openai_model(self, iris_conn_superuser):
        import iris as _iris
        from langchain_intersystems.chat_models import init_chat_model

        irispy = _iris.createIRIS(iris_conn_superuser)
        irispy.classMethodValue("ReadyAI.ConfigStoreSetup", "Setup")

        model = init_chat_model("readyai", iris_conn_superuser)
        assert "openai" in type(model).__module__.lower() or "openai" in type(model).__name__.lower(), (
            f"Expected an OpenAI model, got {type(model)}"
        )
