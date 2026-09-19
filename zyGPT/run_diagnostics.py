import json
import os
import pathlib
import time
import runpy

os.environ['USE_TF'] = '0'
os.environ['USE_FLAX'] = '0'
import torch
from torch import nn
from transformers import PreTrainedTokenizerFast, Qwen3Config, Qwen3ForCausalLM

torch.set_num_threads(4)
torch.set_num_interop_threads(1)
cfg = json.loads(pathlib.Path('model_config.json').read_text(encoding='utf-8-sig'))
cfg.pop('auto_map', None)
cfg.pop('architectures', None)
cfg['model_type'] = 'qwen3'
cfg['rope_theta'] = cfg.pop('rope_parameters')['rope_theta']
config = Qwen3Config(**cfg)
start = time.monotonic()
print('Loading model using the locally installed Qwen3 implementation',flush=True)
model = Qwen3ForCausalLM.from_pretrained('model', config=config, torch_dtype=torch.bfloat16, attn_implementation='sdpa', local_files_only=True)
print('Loaded; quantizing CPU linear layers',flush=True)
for i,layer in enumerate(model.model.layers):
    layer.float()
    model.model.layers[i] = torch.ao.quantization.quantize_dynamic(layer, {nn.Linear:torch.ao.quantization.per_channel_dynamic_qconfig}, dtype=torch.qint8,inplace=True)
    if i % 7 == 0:
        print('Quantized layer',i,flush=True)
model.model.embed_tokens.float()
model.model.norm.float()
model.model.rotary_emb.float()
model.lm_head.weight = model.model.embed_tokens.weight
model.eval()
print('Ready after',round(time.monotonic()-start,1),'seconds',flush=True)
tokenizer_cfg = json.loads(pathlib.Path('model_tokenizer_config.json').read_text(encoding='utf-8-sig'))
tok = PreTrainedTokenizerFast(tokenizer_file='model_tokenizer.json',eos_token='<|zygpt_turn_end|>',pad_token='<|zygpt_end|>',chat_template=tokenizer_cfg['chat_template'])

def respond(prompt,limit=160):
    if isinstance(prompt,dict):
        runpy.run_path('diagnostic_actions.py',init_globals={'model':model,'tok':tok,'request':prompt,'torch':torch})
        return
    text = tok.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    ids = tok(text,return_tensors='pt',return_token_type_ids=False)
    t = time.monotonic()
    with torch.inference_mode():
        result = model.generate(**ids,max_new_tokens=limit,do_sample=False,pad_token_id=151643,eos_token_id=151645)
    reply = tok.decode(result[0,ids['input_ids'].shape[1]:],skip_special_tokens=False)
    print(json.dumps({'prompt':prompt,'reply':reply,'seconds':round(time.monotonic()-t,2)},ensure_ascii=True),flush=True)
    with open('diagnostic_results.jsonl','a',encoding='utf-8') as f:
        f.write(json.dumps({'prompt':prompt,'reply':reply})+'\n')

specials = json.loads(pathlib.Path('model_tokenizer_config.json').read_text(encoding='utf-8-sig'))['extra_special_tokens']
specials.sort(key=lambda x: (0 if 'flags' in x else 1 if 'diag' in x else 2))
print('Watching prompts.jsonl for queries',flush=True)
position = 0
while True:
    path = pathlib.Path('prompts.jsonl')
    if path.exists():
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        for line in lines[position:]:
            position += 1
            prompt = json.loads(line)
            if prompt == '__STOP__':
                raise SystemExit(0)
            respond(prompt,800)
    time.sleep(0.5)
