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

import itertools
prefix=tok('<|zygpt_turn_start|>user\n',add_special_tokens=False)['input_ids']
suffix=tok('<|zygpt_turn_end|>\n<|zygpt_turn_start|>assistant\n<think>\n\n</think>\n\n',add_special_tokens=False)['input_ids']
queries=[]
for record in [127340,130167,151828,151831]:
    for command in [151675,151684,151689]:
        for content in [[151669,record,command],[record,151669,command],[151669,command,record]]:
            queries.append(content)
for start in range(0,len(queries),6):
    batch=queries[start:start+6]
    ids=torch.tensor([prefix+q+suffix for q in batch])
    with torch.inference_mode():
        probs=torch.softmax(model(input_ids=ids,logits_to_keep=1).logits[:,-1].float(),dim=-1)
    vals,tokens=torch.topk(probs,3)
    for q,ts,vs in zip(batch,tokens.tolist(),vals.tolist()):
        print(json.dumps({'tokens':q,'top':[(t,tok.decode([t]),v) for t,v in zip(ts,vs)]}),flush=True)
