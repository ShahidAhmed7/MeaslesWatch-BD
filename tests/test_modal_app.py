import inspect
import json
import tomllib
from pathlib import Path

import modal
import pytest

import modal_app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG = tomllib.loads((PROJECT_ROOT / ".devin" / "study.toml").read_text())
MODAL_CONFIG = CONFIG["modal"]


def test_config_is_authoritative_study_toml():
    assert modal_app.CONFIG_PATH == PROJECT_ROOT / ".devin" / "study.toml"
    assert modal_app.MODAL_CONFIG == MODAL_CONFIG
    assert modal_app.PILOT_CONFIG == CONFIG["pilot"]


def test_import_makes_no_rpc():
    assert modal_app.MODEL_VOLUME._is_hydrated is False
    assert modal_app.pilot._is_hydrated is False


def test_private_app_no_entrypoint_or_endpoint():
    assert modal_app.app._local_state.local_entrypoints == {}
    assert modal_app.app._local_state.web_endpoints == []
    assert modal_app.app.name == MODAL_CONFIG["app_name"] == "measleswatch-pilot"
    assert isinstance(modal_app.pilot, modal.Function)


def test_resources_match_config_bounds():
    assert modal_app.PILOT_RESOURCES == {
        "gpu": "L40S",
        "cpu": 2.0,
        "memory": 16384,
        "max_containers": 1,
        "min_containers": 0,
        "scaledown_window": 60,
        "timeout": 7200,
        "retries": 0,
    }
    for key, config_key in (("gpu", "gpu"), ("cpu", "cpu"),
                            ("memory", "memory_mib"),
                            ("max_containers", "max_containers"),
                            ("min_containers", "min_containers"),
                            ("scaledown_window", "scaledown_window_seconds"),
                            ("timeout", "timeout_seconds")):
        assert modal_app.PILOT_RESOURCES[key] == MODAL_CONFIG[config_key]


def test_volume_and_cache_named_and_bounded():
    assert modal_app.MODEL_VOLUME_NAME == "measleswatch-model-cache-v1"
    assert isinstance(modal_app.MODEL_VOLUME, modal.Volume)


def test_gpu_image_pins():
    assert modal_app.GPU_IMAGE_PACKAGES == [
        "torch==2.7.1",
        "transformers==4.53.3",
        "accelerate==1.8.1",
        "safetensors==0.5.3",
    ]
    assert isinstance(modal_app.IMAGE, modal.Image)


def test_model_pinned_revision():
    assert MODAL_CONFIG["model_id"] == "Qwen/Qwen3-4B"
    assert MODAL_CONFIG["model_revision"] == "1cfa9a7208912126459214e8b04321603b3df60c"


def test_generation_bounds_match_config():
    assert MODAL_CONFIG["context_window_tokens"] == 131072
    assert MODAL_CONFIG["max_input_tokens"] == 98304
    assert MODAL_CONFIG["max_new_tokens"] == 32768
    assert MODAL_CONFIG["max_input_tokens"] + MODAL_CONFIG["max_new_tokens"] <= \
        MODAL_CONFIG["context_window_tokens"]
    assert MODAL_CONFIG["rope_scaling_type"] == "yarn"
    assert MODAL_CONFIG["rope_scaling_factor"] == 4.0
    assert MODAL_CONFIG["seed"] == 2026
    assert MODAL_CONFIG["enable_thinking"] is True
    assert MODAL_CONFIG["temperature"] == 0.6
    assert MODAL_CONFIG["top_p"] == 0.95
    assert MODAL_CONFIG["top_k"] == 20
    assert MODAL_CONFIG["min_p"] == 0.0


def test_model_loading_kwargs_wiring():
    from measleswatch.generation_limits import model_loading_kwargs
    assert model_loading_kwargs(MODAL_CONFIG) == {
        "attn_implementation": "sdpa",
        "max_position_embeddings": 131072,
        "rope_scaling": {
            "rope_type": "yarn",
            "factor": 4.0,
            "original_max_position_embeddings": 32768,
        },
    }
    body = inspect.getsource(modal_app.pilot._raw_f_)
    assert "**model_loading_kwargs(modal_config)" in body
    assert "separate_thinking_tokens(" in body
    assert 'convert_tokens_to_ids("<think>")' in body
    assert 'convert_tokens_to_ids("</think>")' in body


def test_pilot_signature_requires_messages_no_default_prompt():
    signature = inspect.signature(modal_app.pilot._raw_f_)
    parameters = list(signature.parameters.values())
    assert [p.name for p in parameters] == ["messages"]
    assert parameters[0].default is inspect.Parameter.empty


def test_no_secrets_or_local_llm_imports():
    source = inspect.getsource(modal_app)
    assert "modal.Secret" not in source
    body = inspect.getsource(modal_app.pilot._raw_f_)
    assert "import torch" in body and "from transformers import" in body
    module_head = source.split("@app.function")[0]
    assert "import torch" not in module_head
    assert "import transformers" not in module_head
    assert "from transformers" not in module_head


def test_parse_pilot_response_accepts_exact_object():
    assert modal_app.parse_pilot_response('{"status": "ok"}') == {"status": "ok"}


def test_parse_pilot_response_rejects_invalid():
    for text in (
        '{"status": "ok"',
        "not json",
        '["status", "ok"]',
        '"ok"',
        '{"status": "ok", "extra": 1}',
        "{}",
        '{"status": "failed"}',
        '```json\n{"status": "ok"}\n```',
        'Here is the object: {"status": "ok"}',
    ):
        with pytest.raises(ValueError):
            modal_app.parse_pilot_response(text)


class FakeTensor:
    def __init__(self, length):
        self.shape = (1, length)

    def to(self, device):
        return self


class RecordingTokenizer:
    def __init__(self, length, include_mask=True):
        self.length = length
        self.include_mask = include_mask
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        encoded = {"input_ids": FakeTensor(self.length)}
        if self.include_mask:
            encoded["attention_mask"] = FakeTensor(self.length)
        return encoded


MESSAGES = [{"role": "user", "content": CONFIG["pilot"]["user_message"]}]


def test_encode_messages_template_args_and_mask():
    tokenizer = RecordingTokenizer(45)
    encoded = modal_app.encode_messages(tokenizer, MESSAGES, MODAL_CONFIG)
    messages, kwargs = tokenizer.calls[0]
    assert messages is MESSAGES
    assert kwargs == {
        "add_generation_prompt": True,
        "enable_thinking": True,
        "tokenize": True,
        "return_dict": True,
        "return_tensors": "pt",
    }
    assert set(encoded) == {"input_ids", "attention_mask"}
    assert encoded["attention_mask"].shape == (1, 45)


def test_encode_messages_input_bound_no_truncation():
    accepted = RecordingTokenizer(98304)
    encoded = modal_app.encode_messages(accepted, MESSAGES, MODAL_CONFIG)
    assert encoded["input_ids"].shape[-1] == 98304
    with pytest.raises(ValueError):
        modal_app.encode_messages(RecordingTokenizer(98305), MESSAGES, MODAL_CONFIG)


def test_encode_messages_shared_context_budget_rejected():
    with pytest.raises(ValueError):
        modal_app.encode_messages(RecordingTokenizer(98305), MESSAGES, MODAL_CONFIG)


def test_encode_messages_invalid_limits_rejected_before_tokenizer():
    for key, value in (("max_new_tokens", 0), ("max_input_tokens", -5),
                       ("context_window_tokens", True), ("max_input_tokens", True),
                       ("max_new_tokens", "4096")):
        settings = dict(MODAL_CONFIG)
        settings[key] = value
        tokenizer = RecordingTokenizer(10)
        with pytest.raises(ValueError):
            modal_app.encode_messages(tokenizer, MESSAGES, settings)
        assert tokenizer.calls == []


def test_encode_messages_requires_mask_key():
    tokenizer = RecordingTokenizer(10, include_mask=False)
    with pytest.raises(ValueError):
        modal_app.encode_messages(tokenizer, MESSAGES, MODAL_CONFIG)


def test_dependency_exclusion_matches_pyproject():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    cutoff = pyproject["tool"]["uv"]["exclude-newer"]
    assert modal_app.DEPENDENCY_EXCLUDE_NEWER == cutoff == "2026-10-20T00:00:00Z"
    assert modal_app.PYPROJECT_PATH == PROJECT_ROOT / "pyproject.toml"
    assert modal_app.CONTAINER_PYPROJECT_PATH == "/root/pyproject.toml"
    source = inspect.getsource(modal_app)
    assert "uv_pip_install" in source
    assert 'uv_version="0.8.22"' in source
    assert f"--exclude-newer {cutoff}" in source or "--exclude-newer {DEPENDENCY_EXCLUDE_NEWER}" in source
    assert "extra_options" in source
