from __future__ import annotations

from pathlib import Path

MODEL_DIR = Path("model")
MAX_NEW_TOKENS = 640


def load(model_dir: Path):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.utils import logging as hf_logging

    hf_logging.set_verbosity_error()
    tok = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=dtype, trust_remote_code=True)
    if torch.cuda.is_available():
        model = model.cuda()
    model.eval()
    return model, tok


def chat(model, tok, user: str) -> str:
    import torch

    msgs = [{"role": "user", "content": user}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                   enable_thinking=False)
    enc = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=True,
                             temperature=0.6, top_p=0.95, top_k=20, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def main() -> int:
    if not MODEL_DIR.is_dir():
        raise SystemExit("model not found")
    model, tok = load(MODEL_DIR)
    print("ZyGPT console - type a message, Ctrl-D to exit.\n")
    while True:
        user = input("you> ").strip()
        if not user:
            continue
        print("zygpt>", chat(model, tok, user), "\n")


if __name__ == "__main__":
    raise SystemExit(main())
