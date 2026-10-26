import json
import time
import tomllib
from pathlib import Path

import modal

from measleswatch.generation_limits import (
    finish_details,
    model_loading_kwargs,
    separate_thinking_tokens,
    validate_generation_limits,
)

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / ".devin" / "study.toml"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

with CONFIG_PATH.open("rb") as handle:
    CONFIG = tomllib.load(handle)
with PYPROJECT_PATH.open("rb") as handle:
    DEPENDENCY_EXCLUDE_NEWER = tomllib.load(handle)["tool"]["uv"]["exclude-newer"]

MODAL_CONFIG = CONFIG["modal"]
PILOT_CONFIG = CONFIG["pilot"]
validate_generation_limits(MODAL_CONFIG)

MODEL_VOLUME_NAME = "measleswatch-model-cache-v1"
MODEL_CACHE_MOUNT = "/model-cache"
CONTAINER_CONFIG_PATH = "/root/.devin/study.toml"
CONTAINER_PYPROJECT_PATH = "/root/pyproject.toml"
GPU_IMAGE_PACKAGES = [
    "torch==2.7.1",
    "transformers==4.53.3",
    "accelerate==1.8.1",
    "safetensors==0.5.3",
]

IMAGE = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        *GPU_IMAGE_PACKAGES,
        uv_version="0.8.22",
        extra_options=f"--exclude-newer {DEPENDENCY_EXCLUDE_NEWER}",
    )
    .env({"HF_HOME": MODEL_CACHE_MOUNT})
    .add_local_file(CONFIG_PATH, CONTAINER_CONFIG_PATH)
    .add_local_file(PYPROJECT_PATH, CONTAINER_PYPROJECT_PATH)
    .add_local_python_source("measleswatch")
)

MODEL_VOLUME = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

app = modal.App(MODAL_CONFIG["app_name"])

PILOT_RESOURCES = {
    "gpu": MODAL_CONFIG["gpu"],
    "cpu": MODAL_CONFIG["cpu"],
    "memory": MODAL_CONFIG["memory_mib"],
    "max_containers": MODAL_CONFIG["max_containers"],
    "min_containers": MODAL_CONFIG["min_containers"],
    "scaledown_window": MODAL_CONFIG["scaledown_window_seconds"],
    "timeout": MODAL_CONFIG["timeout_seconds"],
    "retries": 0,
}


@app.function(image=IMAGE, volumes={MODEL_CACHE_MOUNT: MODEL_VOLUME}, **PILOT_RESOURCES)
def pilot(messages):
    function_started = time.perf_counter()
    import torch
    from importlib.metadata import version
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    if not isinstance(messages, list) or not all(
        isinstance(message, dict) and "role" in message and "content" in message
        for message in messages
    ):
        raise ValueError("messages must be a list of {'role': ..., 'content': ...} dicts")

    with Path(CONTAINER_CONFIG_PATH).open("rb") as handle:
        modal_config = tomllib.load(handle)["modal"]
    validate_generation_limits(modal_config)

    torch.cuda.reset_peak_memory_stats()
    tokenizer = AutoTokenizer.from_pretrained(
        modal_config["model_id"],
        revision=modal_config["model_revision"],
        trust_remote_code=False,
    )
    encoded = encode_messages(tokenizer, messages, modal_config)
    model = AutoModelForCausalLM.from_pretrained(
        modal_config["model_id"],
        revision=modal_config["model_revision"],
        trust_remote_code=False,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        **model_loading_kwargs(modal_config),
    )

    input_ids = encoded["input_ids"].to("cuda")
    attention_mask = encoded["attention_mask"].to("cuda")
    input_tokens = int(input_ids.shape[-1])

    set_seed(modal_config["seed"])
    torch.cuda.synchronize()
    started = time.perf_counter()
    output_ids = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=modal_config["max_new_tokens"],
        do_sample=True,
        temperature=modal_config["temperature"],
        top_p=modal_config["top_p"],
        top_k=modal_config["top_k"],
        min_p=modal_config["min_p"],
    )
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started

    generated = output_ids[0][input_tokens:]
    output_token_ids = [int(token) for token in generated]
    output_tokens = len(output_token_ids)
    eos_token_ids = model.generation_config.eos_token_id
    if eos_token_ids is None:
        eos_token_ids = tokenizer.eos_token_id
    think_start_token_id = tokenizer.convert_tokens_to_ids("<think>")
    think_end_token_id = tokenizer.convert_tokens_to_ids("</think>")
    if modal_config["enable_thinking"] and (
        think_start_token_id is None or think_end_token_id is None
    ):
        raise ValueError("Thinking mode requires resolvable <think> and </think> token IDs")
    partition = separate_thinking_tokens(
        output_token_ids,
        enable_thinking=modal_config["enable_thinking"],
        think_start_token_id=think_start_token_id,
        think_end_token_id=think_end_token_id,
    )

    result = {
        "text": tokenizer.decode(generated, skip_special_tokens=True),
        "raw_text": tokenizer.decode(output_token_ids, skip_special_tokens=False),
        "reasoning_text": tokenizer.decode(
            partition["reasoning_token_ids"], skip_special_tokens=True).strip("\n"),
        "final_text": tokenizer.decode(
            partition["final_token_ids"], skip_special_tokens=True).strip("\n"),
        "enable_thinking": modal_config["enable_thinking"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "output_token_ids": output_token_ids,
        **finish_details(output_token_ids, eos_token_ids, modal_config["max_new_tokens"]),
        **partition,
        "context_window_tokens": modal_config["context_window_tokens"],
        "max_input_tokens": modal_config["max_input_tokens"],
        "max_new_tokens": modal_config["max_new_tokens"],
        "total_tokens": input_tokens + output_tokens,
        "elapsed_seconds": elapsed,
        "timing_scope": "elapsed_seconds measures synchronized generation only; "
                        "function_elapsed_seconds includes imports and model loading but "
                        "excludes image building and container startup",
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu_name": torch.cuda.get_device_name(),
        "model_id": modal_config["model_id"],
        "model_revision": modal_config["model_revision"],
        "torch_version": version("torch"),
        "transformers_version": version("transformers"),
    }
    result["function_elapsed_seconds"] = time.perf_counter() - function_started
    return result


def encode_messages(tokenizer, messages, settings):
    validate_generation_limits(settings)
    encoded = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        enable_thinking=settings["enable_thinking"],
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    )
    if "input_ids" not in encoded or "attention_mask" not in encoded:
        raise ValueError("Chat template output must include input_ids and attention_mask")
    input_tokens = int(encoded["input_ids"].shape[-1])
    if input_tokens > settings["max_input_tokens"]:
        raise ValueError(
            f"Prompt has {input_tokens} tokens; bound is {settings['max_input_tokens']}"
        )
    if input_tokens + settings["max_new_tokens"] > settings["context_window_tokens"]:
        raise ValueError("Prompt plus output reservation exceeds the shared context window")
    return encoded


def parse_pilot_response(text):
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Pilot response is not a JSON object")
    if set(parsed) != {"status"}:
        raise ValueError(f"Pilot response keys must be exactly {{'status'}}; got {sorted(parsed)}")
    if parsed["status"] != PILOT_CONFIG["expected_status"]:
        raise ValueError(
            f"Pilot status must be {PILOT_CONFIG['expected_status']!r}; got {parsed['status']!r}"
        )
    return parsed
