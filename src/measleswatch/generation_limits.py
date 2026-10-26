import math


def validate_generation_limits(settings):
    for key in ("context_window_tokens", "max_input_tokens", "max_new_tokens"):
        if type(settings.get(key)) is not int or settings[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    context = settings["context_window_tokens"]
    if context > 131072:
        raise ValueError("Context exceeds Qwen3's documented 131072-token extended context")
    if context > 32768:
        factor = settings.get("rope_scaling_factor")
        if (settings.get("rope_scaling_type") != "yarn"
                or type(factor) not in (int, float) or not math.isfinite(factor)
                or factor < context / 32768 or factor > 4):
            raise ValueError("Extended context requires valid YaRN scaling from the native 32768 tokens")
    if settings["max_input_tokens"] + settings["max_new_tokens"] > settings["context_window_tokens"]:
        raise ValueError("Input budget plus output reservation exceeds the shared context window")


def model_loading_kwargs(settings):
    validate_generation_limits(settings)
    result = {"attn_implementation": "sdpa"}
    if settings["context_window_tokens"] > 32768:
        result["max_position_embeddings"] = settings["context_window_tokens"]
        result["rope_scaling"] = {
            "rope_type": "yarn", "factor": settings["rope_scaling_factor"],
            "original_max_position_embeddings": 32768,
        }
    return result


def separate_thinking_tokens(output_token_ids, *, enable_thinking,
                             think_start_token_id, think_end_token_id):
    ids = list(output_token_ids)
    if not enable_thinking:
        boundary, status = 0, "disabled"
    elif think_end_token_id is not None and think_end_token_id in ids:
        boundary = len(ids) - ids[::-1].index(think_end_token_id)
        status = "complete"
    elif think_start_token_id is not None and think_start_token_id in ids:
        boundary, status = len(ids), "incomplete"
    else:
        boundary, status = 0, "no_explicit_thinking_block"
    return {
        "reasoning_token_ids": ids[:boundary],
        "final_token_ids": ids[boundary:],
        "reasoning_tokens": boundary,
        "final_tokens": len(ids) - boundary,
        "thinking_status": status,
        "reasoning_token_counts_include_markers": True,
    }


def finish_details(output_token_ids, eos_token_ids, max_new_tokens):
    if eos_token_ids is None:
        eos_token_ids = []
    if isinstance(eos_token_ids, int):
        eos_token_ids = [eos_token_ids]
    finished = bool(output_token_ids) and output_token_ids[-1] in eos_token_ids
    capped = not finished and len(output_token_ids) >= max_new_tokens
    return {
        "finish_reason": "eos" if finished else "length" if capped else "unknown",
        "output_limit_reached": capped,
        "truncated": not finished,
    }
