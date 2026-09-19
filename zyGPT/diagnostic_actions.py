import json
import pathlib
import time

if 'float_layers' in request:
    from safetensors import safe_open
    from transformers.models.qwen3.modeling_qwen3 import Qwen3DecoderLayer
    with safe_open('model/model.safetensors',framework='pt',device='cpu') as f:
        for i in request['float_layers']:
            prefix=f'model.layers.{i}.'
            weights={k[len(prefix):]:f.get_tensor(k) for k in f.keys() if k.startswith(prefix)}
            layer=Qwen3DecoderLayer(model.config,i)
            layer.load_state_dict(weights,assign=True)
            layer.float()
            model.model.layers[i]=layer
            print('Restored original floating-point layer',i,flush=True)
    del weights,layer,f

if 'probe_reserved' in request:
    rows=request['probe_reserved']
    control=request.get('control',151669)
    best=[]
    for row in rows:
        content=([control,row] if control else [row])
        token_ids=[151644,872,198]+content+[151645,198,151644,77091,198,151667,271,151668,271]
        with torch.inference_mode():
            output=model(input_ids=torch.tensor([token_ids],dtype=torch.long),logits_to_keep=1)
            probs=torch.softmax(output.logits[0,-1].float(),dim=-1)
            values,indices=torch.topk(probs,5)
        r={'row':row,'top':[(int(i),tok.decode([i]),float(p)) for i,p in zip(indices.tolist(),values.tolist())]}
        best.append(r)
        print(json.dumps(r,ensure_ascii=True),flush=True)
    pathlib.Path('reserved_probe.json').write_text(json.dumps(best),encoding='utf-8')
    request={'prompt':'<|zygpt-maint|>','limit':8}

if request.get('float_head',True) and not isinstance(model.lm_head,torch.nn.Linear):
    model.lm_head=torch.nn.Linear(model.config.hidden_size,model.config.vocab_size,bias=False)
    model.lm_head.weight=model.model.embed_tokens.weight

if request.get('reconfigure_quantization',False):
    from safetensors import safe_open
    from transformers.models.qwen3.modeling_qwen3 import Qwen3DecoderLayer
    qconfig=torch.ao.quantization.per_channel_dynamic_qconfig
    with safe_open('model/model.safetensors',framework='pt',device='cpu') as f:
        for i in range(model.config.num_hidden_layers):
            prefix=f'model.layers.{i}.'
            weights={k[len(prefix):]:f.get_tensor(k) for k in f.keys() if k.startswith(prefix)}
            layer=Qwen3DecoderLayer(model.config,i)
            layer.load_state_dict(weights,assign=True)
            layer.float()
            model.model.layers[i]=torch.ao.quantization.quantize_dynamic(layer,{torch.nn.Linear:qconfig},dtype=torch.qint8,inplace=True)
            if i%7==0:
                print('Restored layer using per-channel quantization',i,flush=True)
    del weights,layer,f

messages=request.get('messages',[{'role':'user','content':request.get('prompt','')}])
text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=request.get('thinking',False))
text+=request.get('prefix','')
if 'raw' in request:
    text=request['raw']
ids=tok(text,return_tensors='pt',return_token_type_ids=False)
if 'token_ids' in request:
    ids={'input_ids':torch.tensor([request['token_ids']],dtype=torch.long),'attention_mask':torch.ones((1,len(request['token_ids'])),dtype=torch.long)}
t=time.monotonic()
class ProgressStreamer:
    def __init__(self):
        self.first=True
        self.buffer=[]
        self.total=0
    def put(self,value):
        if self.first:
            self.first=False
            return
        self.buffer.extend(value.reshape(-1).tolist())
        self.total+=value.numel()
        if len(self.buffer)>=64:
            print(json.dumps({'partial':tok.decode(self.buffer,skip_special_tokens=False),'tokens':self.total},ensure_ascii=True),flush=True)
            self.buffer=[]
    def end(self):
        pass
with torch.inference_mode():
    out=model.generate(**ids,max_new_tokens=request.get('limit',800),do_sample=False,pad_token_id=151643,eos_token_id=151645,streamer=ProgressStreamer())
reply=tok.decode(out[0,ids['input_ids'].shape[1]:],skip_special_tokens=False)
result={'request':request,'reply':reply,'token_ids':out[0,ids['input_ids'].shape[1]:].tolist(),'seconds':round(time.monotonic()-t,2)}
print(json.dumps(result,ensure_ascii=True),flush=True)
with open('diagnostic_results.jsonl','a',encoding='utf-8') as f:
    f.write(json.dumps(result)+'\n')
