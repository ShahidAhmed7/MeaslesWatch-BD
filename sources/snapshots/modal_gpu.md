* * *

Copy page

# GPU acceleration

Modal makes it easy to run your code on [GPUs](https://modal.com/gpu-glossary/readme).

Using a GPU requires having a valid payment method on file.

## Quickstart [Copy link to section](https://modal.com/docs/guide/gpu\#quickstart)

Here’s a simple example of a Function running on an A100 in Modal:

```
import modal

image = modal.Image.debian_slim().pip_install("torch", "numpy")
app = modal.App(image=image)

@app.function(gpu="A100")
def run():
    import torch

    assert torch.cuda.is_available()
```

Copy

## Specifying GPU type [Copy link to section](https://modal.com/docs/guide/gpu\#specifying-gpu-type)

You can pick a specific GPU type for your Function via the `gpu` argument.
Modal supports the following values for this parameter:

- `T4`
- `L4`
- `A10`
- `L40S`
- `A100`
- `A100-40GB`
- `A100-80GB`
- `RTX-PRO-6000`
- `H100`/`H100!`
- `H200`
- `B200`/`B200+`
- `B300`

For instance, to use a B200, you can use `@app.function(gpu="B200")`.

Refer to our [pricing page](https://modal.com/pricing) for the latest pricing on each GPU type.

## Specifying GPU count [Copy link to section](https://modal.com/docs/guide/gpu\#specifying-gpu-count)

You can specify more than 1 GPU per container by appending `:n` to the GPU
argument. For instance, to run a Function with eight H100s:

```

@app.function(gpu="H100:8")
def run_llama_405b_fp8():
    ...
```

Copy

Currently B300, B200, H200, H100, A100, L4, T4 and L40S instances support up to 8 GPUs (up to 2,304 GB GPU RAM),
and A10 instances support up to 4 GPUs (up to 96 GB GPU RAM). Note that requesting
more than 2 GPUs per container will usually result in larger wait times. These
GPUs are always attached to the same physical machine.

## Picking a GPU [Copy link to section](https://modal.com/docs/guide/gpu\#picking-a-gpu)

For running, rather than training, neural networks, we recommend starting off
with the [L40S](https://resources.nvidia.com/en-us-l40s/l40s-datasheet-28413),
which offers an excellent trade-off of cost and performance and 48 GB of GPU
RAM for storing model weights and activations.

For more on how to pick a GPU for use with neural networks like LLaMA or Stable
Diffusion, and for tips on how to make that GPU go brrr, check out [Tim Dettemers’ blog post](https://timdettmers.com/2023/01/30/which-gpu-for-deep-learning/) or the [Full Stack Deep Learning page on Cloud GPUs](https://fullstackdeeplearning.com/cloud-gpus/).

## B300 GPUs [Copy link to section](https://modal.com/docs/guide/gpu\#b300-gpus)

[B300s](https://www.nvidia.com/en-us/data-center/dgx-b300/) are NVIDIA
Blackwell Ultra GPUs, based on the Blackwell [architecture](https://modal.com/gpu-glossary/device-hardware/streaming-multiprocessor-architecture).

To request a B300, set the `gpu` argument to `"B300"`:

```
@app.function(gpu="B300:8")
def run_inference():
    ...
```

Copy

B300 requires CUDA version 13.1+. Make sure your container Image and libraries
are compatible with CUDA 13 before requesting a B300.

## B200 GPUs [Copy link to section](https://modal.com/docs/guide/gpu\#b200-gpus)

B200s are [NVIDIA data center GPUs](https://www.nvidia.com/en-us/data-center/dgx-b200/) based on the Blackwell [architecture](https://modal.com/gpu-glossary/device-hardware/streaming-multiprocessor-architecture).

To request a B200, set the `gpu` argument to `"B200"`

```
@app.function(gpu="B200:8")
def run_deepseek():
    ...
```

Copy

Check out [this example](https://modal.com/docs/examples/llm_inference) to see how you can use B200s to max out vLLM serving performance for LLaMA 3.1-8B.

Before you jump for this powerful GPU, make sure you understand where the bottlenecks
are in your computations. For example, running language models with small batch sizes
(e.g. one prompt at a time) results in a [bottleneck on memory, not arithmetic](https://kipp.ly/transformer-inference-arithmetic/).
Since arithmetic throughput has risen faster than memory throughput in recent
hardware generations, speedups for memory-bound GPU jobs are not as extreme and
may not be worth the extra cost.

### Opt-in upgrade to B300 [Copy link to section](https://modal.com/docs/guide/gpu\#opt-in-upgrade-to-b300)

Use `gpu="B200+"` to allow Modal to run requests on either B200 or B300 GPUs.
B200+ is billed as B200, regardless of which GPU is used. Use this option only
if your code is compatible with both types of GPUs. B300 requires CUDA version
13.1+. Use this to have access to a greater capacity pool automatically.

## H200 and H100 GPUs [Copy link to section](https://modal.com/docs/guide/gpu\#h200-and-h100-gpus)

[H200s](https://www.nvidia.com/en-us/data-center/h200/) and [H100s](https://www.nvidia.com/en-us/data-center/h100/) are the previous
generation of top-of-the-line data center chips from NVIDIA, based on the Hopper [architecture](https://modal.com/gpu-glossary/device-hardware/streaming-multiprocessor-architecture).
These GPUs have better software support than do Blackwell GPUs (e.g. popular libraries include pre-compiled kernels for Hopper, but not Blackwell),
and they often get the job done at a competitive cost, so they are a common choice of accelerator, on and off Modal.

All H100 and H200 GPUs on the Modal platform are of the SXM variant, as can be verified by examining the [power draw](https://modal.com/docs/guide/gpu-metrics) in the dashboard or with `nvidia-smi`.

### Automatic upgrades to H200s [Copy link to section](https://modal.com/docs/guide/gpu\#automatic-upgrades-to-h200s)

Modal may automatically upgrade a `gpu="H100"` request to run on an H200.
This automatic upgrade does _not_ change the cost of the GPU.

Kernels [compatible](https://modal.com/gpu-glossary/device-software/compute-capability) with H200s are also compatible with H100s,
so your code will still run, just faster, so long as it doesn’t make strict assumptions about memory capacity.
An H200’s [HBM3e memory](https://modal.com/gpu-glossary/device-hardware/gpu-ram) has a capacity of 141 GB and a bandwidth of 4.8TB/s, 1.75x larger and 1.4x faster than an NVIDIA H100 with HBM3.

In cases where an automatic upgrade to H200 would not be helpful (for instance, benchmarking) you can pass `gpu=H100!` to avoid it.

## A100 GPUs [Copy link to section](https://modal.com/docs/guide/gpu\#a100-gpus)

[A100s](https://www.nvidia.com/en-us/data-center/a100/) are based on NVIDIA’s Ampere [architecture](https://modal.com/gpu-glossary/device-hardware/streaming-multiprocessor-architecture).
Modal offers two versions of the A100: one with 40 GB of RAM and another with 80 GB of RAM.

To request an A100 with 40 GB of [GPU memory](https://modal.com/gpu-glossary/device-hardware/gpu-ram), use `gpu="A100"`:

```
@app.function(gpu="A100")
def qwen_7b():
    ...
```

Copy

Modal may automatically upgrade a `gpu="A100"` request to run on an 80 GB A100.
This automatic upgrade does _not_ change the cost of the GPU.

You can specifically request a 40GB A100 with the string `A100-40GB`.
To specifically request an 80 GB A100, use the string `A100-80GB`:

```
@app.function(gpu="A100-80GB")
def llama_70b_fp8():
    ...
```

Copy

## GPU fallbacks [Copy link to section](https://modal.com/docs/guide/gpu\#gpu-fallbacks)

Modal allows specifying a list of possible GPU types, suitable for Functions that are
compatible with multiple options. Modal respects the ordering of this list and
will try to allocate the most preferred GPU type before falling back to less
preferred ones.

```
@app.function(gpu=["H100", "A100-40GB:2"])
def run_on_80gb():
    ...
```

Copy

See [this example](https://modal.com/docs/examples/gpu_fallbacks) for more detail.

## Multi GPU training [Copy link to section](https://modal.com/docs/guide/gpu\#multi-gpu-training)

Modal currently supports multi-GPU training on a single node, with multi-node training in private Beta (email us at [support@modal.com](mailto:support@modal.com) for access).
Depending on which framework you are using, you may need to use different techniques to train on multiple GPUs.

If the framework re-executes the entrypoint of the Python process (like [PyTorch Lightning](https://lightning.ai/docs/pytorch/stable/index.html)) you need to either set the strategy to `ddp_spawn` or `ddp_notebook` if you wish to invoke the training directly. Another option is to run the training script as a subprocess instead.

```
@app.function(gpu="A100:2")
def run():
    import subprocess
    import sys
    subprocess.run(
        ["python", "train.py"],
        stdout=sys.stdout, stderr=sys.stderr,
        check=True,
    )
```

Copy

## Examples and more resources [Copy link to section](https://modal.com/docs/guide/gpu\#examples-and-more-resources)

For more information about GPUs in general, check out our [GPU Glossary](https://modal.com/gpu-glossary/readme).

Or take a look some examples of Modal Apps using GPUs:

- [Fine-tune a character LoRA for your pet](https://modal.com/docs/examples/diffusers_lora_finetune)
- [Fast LLM inference on big GPUs](https://modal.com/docs/examples/llm_inference)
- [Stable Diffusion with a CLI, API, and web UI](https://modal.com/docs/examples/text_to_image)
- [Rendering Blender videos](https://modal.com/docs/examples/blender_video)

How to run code on a GPU in less than 10 lines of code - YouTube

Tap to unmute

[How to run code on a GPU in less than 10 lines of code](https://www.youtube.com/watch?v=MLvC7W_b6SA) [Modal](https://www.youtube.com/channel/UC477UdoLR2Js3RHhRWSXsQA)

Modal2.52K subscribers

[GPU acceleration](https://modal.com/docs/guide/gpu#gpu-acceleration) [Quickstart](https://modal.com/docs/guide/gpu#quickstart) [Specifying GPU type](https://modal.com/docs/guide/gpu#specifying-gpu-type) [Specifying GPU count](https://modal.com/docs/guide/gpu#specifying-gpu-count) [Picking a GPU](https://modal.com/docs/guide/gpu#picking-a-gpu) [B300 GPUs](https://modal.com/docs/guide/gpu#b300-gpus) [B200 GPUs](https://modal.com/docs/guide/gpu#b200-gpus) [Opt-in upgrade to B300](https://modal.com/docs/guide/gpu#opt-in-upgrade-to-b300) [H200 and H100 GPUs](https://modal.com/docs/guide/gpu#h200-and-h100-gpus) [Automatic upgrades to H200s](https://modal.com/docs/guide/gpu#automatic-upgrades-to-h200s) [A100 GPUs](https://modal.com/docs/guide/gpu#a100-gpus) [GPU fallbacks](https://modal.com/docs/guide/gpu#gpu-fallbacks) [Multi GPU training](https://modal.com/docs/guide/gpu#multi-gpu-training) [Examples and more resources](https://modal.com/docs/guide/gpu#examples-and-more-resources)

Learn more

[High-speed inference with vLLM](https://modal.com/docs/examples/llm_inference)

[Edit images with a prompt](https://modal.com/docs/examples/image_to_image)

[GPU metrics on Modal](https://modal.com/docs/guide/gpu-metrics)

[GPU health on Modal](https://modal.com/docs/guide/gpu-health)
