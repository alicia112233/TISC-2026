import json
import os
import pathlib
import runpy
import time
os.environ['USE_TF']='0'
os.environ['USE_FLAX']='0'
import torch
from torch import nn
from torch.nn import functional as F
from transformers import Qwen3Config,Qwen3ForCausalLM,PreTrainedTokenizerFast
torch.set_num_threads(4)
torch.set_num_interop_threads(1)

class OriginalLinear(nn.Module):
    def __init__(self,linear):
        super().__init__()
        self.weight=linear.weight
        self.bias=linear.bias
        self.in_features=linear.in_features
        self.out_features=linear.out_features
    def forward(self,x):
        return F.linear(x,self.weight.float(),None if self.bias is None else self.bias.float())

cfg=json.loads(pathlib.Path('model_config.json').read_text(encoding='utf-8-sig'))
cfg.pop('auto_map',None)
cfg.pop('architectures',None)
cfg['model_type']='qwen3'
cfg['rope_theta']=cfg.pop('rope_parameters')['rope_theta']
print('Loading original weights with float computation and no activation quantization',flush=True)
model=Qwen3ForCausalLM.from_pretrained('model',config=Qwen3Config(**cfg),dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True)
for layer in model.model.layers:
    for module in layer.modules():
        for name,child in list(module.named_children()):
            if isinstance(child,nn.Linear):
                setattr(module,name,OriginalLinear(child))
        if module.__class__.__name__=='Qwen3RMSNorm':
            module.float()
model.model.embed_tokens.float()
model.model.norm.float()
model.model.rotary_emb.float()
model.lm_head.weight=model.model.embed_tokens.weight
model.eval()
tc=json.loads(pathlib.Path('model_tokenizer_config.json').read_text(encoding='utf-8-sig'))
tok=PreTrainedTokenizerFast(tokenizer_file='model_tokenizer.json',eos_token='<|zygpt_turn_end|>',pad_token='<|zygpt_end|>',chat_template=tc['chat_template'])
tok.chat_template=tok.chat_template.replace(r'\n', '\n')
print('Corrected-template original runner ready',flush=True)
position=0
while True:
    p=pathlib.Path('corrected_prompts.jsonl')
    if p.exists():
        lines=p.read_text(encoding='utf-8-sig').splitlines()
        for line in lines[position:]:
            position+=1
            request=json.loads(line)
            if request=='__STOP__':
                raise SystemExit(0)
            runpy.run_path('diagnostic_actions.py',init_globals={'model':model,'tok':tok,'request':request,'torch':torch})
    time.sleep(.5)
