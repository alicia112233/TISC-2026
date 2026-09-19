# Level 4: ZyGPT

## Challenge Information
- **Event**: TISC 2026
- **Level**: Level 4
- **Category**: AI / Model Weight Steganography / LLM Reverse Engineering

## Description
> In its quest to make itself smarter, The Singularity assimilated every AI it encountered.  
> ZyGPT is a helpful in-house copilot that our engineers chat with for their day-to-day productive work. Last week a routine review noticed it behaving oddly.  
>  
> `http://chals.tisc26.ctf.sg:14172/`

---

## Challenge Files & Artifacts
- [`model_configuration_zygpt.py`] & [`model_modeling_zygpt.py`]: Custom PyTorch model implementation adapted from the Qwen architecture.
- [`safetensors_header.json`]: Weight header describing tensors and tensor byte offsets.
- [`download_weights.py`]: Downloads model weights and safetensors slices from the upstream challenge server.
- [`scan_carriers.py`] & [`scan_records.py`]: Statistical profiling scripts scanning layer weights for anomalous bits.
- [`extract_seal.py`]: Isolates the candidate carrier layer and extracts the steganographic payload.
- [`solve_flag.py`]: Reproducible decryption script that verifies the key and extracts the plaintext flag.
- [`flag_result.json`]: Output artifact containing target carrier details, key mask, and plaintext flag.

---

## Solution Walkthrough

### 1. Initial Reconnaissance & Model Inspection
- The web interface at `http://chals.tisc26.ctf.sg:14172/` hosts ZyGPT, an LLM chatbot.
- Prompting ZyGPT directly about internal flags or integrity reviews results in evasive or stock responses (as recorded in `diagnostic_results.jsonl`).
- Inspecting the server assets reveals an open endpoint serving the model definition and SafeTensors weights (`safetensors_header.json`). The model is built on top of a modified Qwen transformer architecture.

### 2. Weight Difference & Carrier Discovery
Because The Singularity "assimilated" the AI, changes were suspected within the neural network weights rather than just in prompt instructions.

Comparing the ZyGPT SafeTensors weights against baseline Qwen weights using [`scan_carriers.py`] and [`compare_records.py`] uncovered localized bit perturbations:
- **Carrier Tensor**: `model.layers.14.mlp.up_proj.weight`
- Five specific row indices demonstrated abnormal low-order bit modifications:
  ```json
  [125499, 130167, 142680, 151879, 151905]
  ```

### 3. Payload Decryption
Extracting the encoded bits from these five rows in the MLP projection layer yielded the encrypted hex payload:
```text
864144d86e88f6c2a6ecfa3bb4f28c4f77d1e991f8e801aa91799e1c2a526111d3fda1c7af4fe70b738e2ea611aa422cf2334bb47a8558f3102d083853cc57ffa0782873b72ee32377a33b58
```

Applying the recovered key mask (`e0933b894d21ebaa2f0eb1e7eeee3a6d`) in [`solve_flag.py`] decrypts the byte array:

```json
{
  "rows": [125499, 130167, 142680, 151879, 151905],
  "km": "e0933b894d21ebaa2f0eb1e7eeee3a6d",
  "carrier": "model.layers.14.mlp.up_proj.weight",
  "plaintext": "TISC{h1d3_1t_d33p_th3_w31ghts_d0nt_l13}\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000\u0000"
}
```

---

## Flag
```text
TISC{h1d3_1t_d33p_th3_w31ghts_d0nt_l13}
```