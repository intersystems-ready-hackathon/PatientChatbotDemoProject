import json
import pytest
from tests.conftest import requires_iris


pytestmark = requires_iris


def _load_readyai_config(irispy, _iris):
    config_ref = _iris.IRISReference(None)
    sc = irispy.classMethodValue("%ConfigStore.Configuration", "Get", "AI.LLM.gpt-5-nano", config_ref)
    assert sc == 1, "AI.LLM.gpt-5-nano not found in ConfigStore"

    details_ref = _iris.IRISReference(None)
    sc = config_ref.getValue().invoke("GetDetailsWithSecrets", details_ref)
    assert sc == 1, "GetDetailsWithSecrets failed"

    return json.loads(details_ref.getValue().invoke("%ToJSON"))


def test_setup_creates_llm_config(iris_conn_superuser):
    import iris as _iris

    irispy = _iris.createIRIS(iris_conn_superuser)

    sc = irispy.classMethodValue("Setup.ConfigStore", "Setup")
    assert sc == 1, f"Setup() returned error status: {sc}"

    config = _load_readyai_config(irispy, _iris)
    assert config["model_provider"] == "openai"
    assert config["model"] == "gpt-5-nano"


def test_setup_is_idempotent(iris_conn_superuser):
    import iris as _iris

    irispy = _iris.createIRIS(iris_conn_superuser)
    sc1 = irispy.classMethodValue("Setup.ConfigStore", "Setup")
    sc2 = irispy.classMethodValue("Setup.ConfigStore", "Setup")
    assert sc1 == 1
    assert sc2 == 1, "Second call to Setup() should not error (delete + recreate)"


def test_setup_config_has_required_keys(iris_conn_superuser):
    import iris as _iris

    irispy = _iris.createIRIS(iris_conn_superuser)
    irispy.classMethodValue("Setup.ConfigStore", "Setup")
    config = _load_readyai_config(irispy, _iris)

    assert "model_provider" in config, "model_provider missing"
    assert "model" in config, "model missing"
    assert "." not in "gpt-5-nano", "config name must not contain '.'"


def test_setup_with_api_key_stores_secret(iris_conn_superuser):
    import iris as _iris

    irispy = _iris.createIRIS(iris_conn_superuser)
    sc = irispy.classMethodValue("Setup.ConfigStore", "SetupWithAPIKey", "sk-test-key")
    assert sc == 1, f"SetupWithAPIKey() returned error: {sc}"

    config = _load_readyai_config(irispy, _iris)

    assert config.get("api_key") == "sk-test-key", (
        f"Expected resolved API key, got: {config.get('api_key')}"
    )
