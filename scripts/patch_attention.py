#!/usr/bin/env python3
"""
Patch WAN 2.2 attention.py to make flash-attn optional
Falls back to PyTorch's scaled_dot_product_attention if flash-attn is unavailable
"""

file_path = '/workspace/Wan2.2/wan/modules/attention.py'

with open(file_path, 'r') as f:
    content = f.read()

# Replace the assertion with a fallback
old_code = '    assert FLASH_ATTN_2_AVAILABLE'
new_code = '''    # Fallback if flash-attn not available
    if not FLASH_ATTN_2_AVAILABLE:
        import torch.nn.functional as F
        q_t = q.transpose(1, 2)  # [B, H, N, D]
        k_t = k.transpose(1, 2)
        v_t = v.transpose(1, 2)
        out = F.scaled_dot_product_attention(q_t, k_t, v_t, attn_mask=None, dropout_p=0.0)
        return out.transpose(1, 2).contiguous()
    # assert FLASH_ATTN_2_AVAILABLE - using fallback instead'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print('✅ Applied flash-attn fallback patch')
else:
    print('⚠️ Could not find assertion line to patch')
    exit(1)
