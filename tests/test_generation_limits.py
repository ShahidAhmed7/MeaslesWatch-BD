from copy import deepcopy

import pytest

from measleswatch.generation_limits import (
    finish_details, model_loading_kwargs, separate_thinking_tokens, validate_generation_limits,
)


LIMITS = {"context_window_tokens": 32768, "max_input_tokens": 28672, "max_new_tokens": 4096}


def test_shared_context_budget_is_reserved():
    validate_generation_limits(LIMITS)
    for key, value in (("max_input_tokens", 28673), ("max_new_tokens", 4097),
                       ("context_window_tokens", 32769), ("max_new_tokens", 0),
                       ("max_input_tokens", True)):
        settings = deepcopy(LIMITS)
        settings[key] = value
        with pytest.raises(ValueError):
            validate_generation_limits(settings)


def test_generation_stop_reason_distinguishes_cap_from_eos():
    assert finish_details([1, 2, 3], 3, 3) == {
        "finish_reason": "eos", "output_limit_reached": False, "truncated": False}
    assert finish_details([1, 2, 3], [4, 5], 3) == {
        "finish_reason": "length", "output_limit_reached": True, "truncated": True}
    assert finish_details([1], 3, 4096)["finish_reason"] == "unknown"
    assert finish_details([], None, 4096)["truncated"] is True


def test_extended_context_has_explicit_yarn_and_shared_reservation():
    settings = {
        "context_window_tokens": 131072, "max_input_tokens": 98304,
        "max_new_tokens": 32768, "rope_scaling_type": "yarn", "rope_scaling_factor": 4.0,
    }
    assert model_loading_kwargs(settings) == {
        "attn_implementation": "sdpa", "max_position_embeddings": 131072,
        "rope_scaling": {"rope_type": "yarn", "factor": 4.0,
                         "original_max_position_embeddings": 32768},
    }
    for key, value in (("rope_scaling_factor", 1.0), ("rope_scaling_factor", True),
                       ("rope_scaling_factor", float("nan")), ("rope_scaling_type", "linear"),
                       ("context_window_tokens", 131073), ("max_new_tokens", 32769)):
        invalid = {**settings, key: value}
        with pytest.raises(ValueError):
            validate_generation_limits(invalid)


def test_thinking_partition_preserves_every_token_and_final_boundary():
    result = separate_thinking_tokens(
        [10, 20, 30, 40, 50], enable_thinking=True,
        think_start_token_id=10, think_end_token_id=30)
    assert result["reasoning_token_ids"] == [10, 20, 30]
    assert result["final_token_ids"] == [40, 50]
    assert result["reasoning_tokens"] + result["final_tokens"] == 5
    assert result["thinking_status"] == "complete"
    incomplete = separate_thinking_tokens(
        [10, 20], enable_thinking=True, think_start_token_id=10, think_end_token_id=30)
    assert incomplete["final_token_ids"] == []
    assert incomplete["thinking_status"] == "incomplete"
    absent = separate_thinking_tokens(
        [40, 50], enable_thinking=True, think_start_token_id=10, think_end_token_id=30)
    assert absent["final_token_ids"] == [40, 50]
    assert absent["thinking_status"] == "no_explicit_thinking_block"
    disabled = separate_thinking_tokens(
        [10, 30, 40], enable_thinking=False, think_start_token_id=10, think_end_token_id=30)
    assert disabled["reasoning_tokens"] == 0
    assert disabled["final_token_ids"] == [10, 30, 40]
