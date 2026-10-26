"""Private model-resident inference. Only the explicit audited runner invokes this app."""
import time

import modal
import modal_app

from measleswatch.generation_limits import finish_details, model_loading_kwargs, separate_thinking_tokens

app = modal.App("measleswatch-research")
settings = modal_app.MODAL_CONFIG


SERVICE_IMAGE = modal_app.IMAGE.add_local_file(modal_app.PROJECT_ROOT / "modal_app.py", "/root/modal_app.py")


@app.cls(image=SERVICE_IMAGE, volumes={modal_app.MODEL_CACHE_MOUNT: modal_app.MODEL_VOLUME},
         gpu=settings["gpu"], cpu=settings["cpu"], memory=settings["memory_mib"],
         max_containers=1, min_containers=0, scaledown_window=60,
         timeout=settings["timeout_seconds"], retries=0)
class AnalystModel:
    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(settings["model_id"], revision=settings["model_revision"], trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            settings["model_id"], revision=settings["model_revision"], trust_remote_code=False,
            torch_dtype=torch.bfloat16, device_map="cuda", **model_loading_kwargs(settings))
        self.model.eval()

    @modal.method()
    def generate(self, messages, seed=2026):
        from transformers import set_seed
        if seed not in (2026, 2027, 2028):
            raise ValueError("Seed must be declared in the study protocol")
        encoded = modal_app.encode_messages(self.tokenizer, messages, settings)
        inputs = {k: v.to("cuda") for k, v in encoded.items()}
        tokens = int(inputs["input_ids"].shape[-1])
        self.torch.cuda.reset_peak_memory_stats()
        set_seed(seed)
        self.torch.cuda.synchronize()
        started = time.perf_counter()
        with self.torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=settings["max_new_tokens"],
                do_sample=True, temperature=settings["temperature"], top_p=settings["top_p"],
                top_k=settings["top_k"], min_p=settings["min_p"])
        self.torch.cuda.synchronize()
        ids = [int(v) for v in output[0][tokens:]]
        partition = separate_thinking_tokens(ids, enable_thinking=settings["enable_thinking"],
            think_start_token_id=self.tokenizer.convert_tokens_to_ids("<think>"),
            think_end_token_id=self.tokenizer.convert_tokens_to_ids("</think>"))
        return {"raw_text": self.tokenizer.decode(ids, skip_special_tokens=False),
                "reasoning_text": self.tokenizer.decode(partition["reasoning_token_ids"], skip_special_tokens=True),
                "final_text": self.tokenizer.decode(partition["final_token_ids"], skip_special_tokens=True).strip(),
                "input_tokens": tokens, "output_tokens": len(ids), "seed": seed,
                "reasoning_tokens": partition["reasoning_tokens"], "final_tokens": partition["final_tokens"],
                "thinking_status": partition["thinking_status"], "generation_seconds": time.perf_counter() - started,
                "peak_gpu_memory_bytes": int(self.torch.cuda.max_memory_allocated()),
                "gpu_name": self.torch.cuda.get_device_name(),
                **finish_details(ids, self.model.generation_config.eos_token_id, settings["max_new_tokens"])}
