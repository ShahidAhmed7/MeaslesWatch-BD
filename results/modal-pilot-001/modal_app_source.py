import json
import time
import tomllib
from pathlib import Path

import modal

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / ".devin" / "study.toml"

with CONFIG_PATH.open("rb") as handle:
    CONFIG = tomllib.load(handle)

MODAL_CONFIG = CONFIG["modal"]
PILOT_CONFIG = CONFIG["pilot"]

MODEL_VOLUME_NAME = "measleswatch-model-cache-v1"
MODEL_CACHE_MOUNT = "/model-cache"
CONTAINER_CONFIG_PATH = "/root/.devin/study.toml"
GPU_IMAGE_PACKAGES = [
    "torch==2.7.1",
    "transformers==4.53.3",
    "accelerate==1.8.1",
    "safetensors==0.5.3",
]

IMAGE = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(*GPU_IMAGE_PACKAGES)
    .env({"HF_HOME": MODEL_CACHE_MOUNT})
    .add_local_file(CONFIG_PATH, CONTAINER_CONFIG_PATH)
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

    torch.cuda.reset_peak_memory_stats()
    tokenizer = AutoTokenizer.from_pretrained(
        modal_config["model_id"],
        revision=modal_config["model_revision"],
        trust_remote_code=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        modal_config["model_id"],
        revision=modal_config["model_revision"],
        trust_remote_code=False,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
    )

    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        enable_thinking=modal_config["enable_thinking"],
        return_tensors="pt",
    ).to("cuda")
    input_tokens = int(input_ids.shape[-1])
    if input_tokens > modal_config["max_input_tokens"]:
        raise ValueError(
            f"Prompt has {input_tokens} tokens; bound is {modal_config['max_input_tokens']}"
        )

    set_seed(modal_config["seed"])
    torch.cuda.synchronize()
    started = time.perf_counter()
    output_ids = model.generate(
        input_ids,
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
    output_tokens = int(generated.shape[-1])
    finished = output_tokens > 0 and int(generated[-1]) == tokenizer.eos_token_id

    result = {
        "text": tokenizer.decode(generated, skip_special_tokens=True),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "output_token_ids": [int(token) for token in generated],
        "truncated": not finished,
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
