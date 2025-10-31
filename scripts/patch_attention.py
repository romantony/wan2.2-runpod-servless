#!/usr/bin/env python3
"""
Patch WAN 2.2 attention.py to make flash-attn optional
Falls back to PyTorch's scaled_dot_product_attention if flash-attn is unavailable
"""

file_path = '/workspace/Wan2.2/wan/modules/attention.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# Find and replace the assertion line, preserving indentation
patched = False
new_lines = []
for i, line in enumerate(lines):
    if 'assert FLASH_ATTN_2_AVAILABLE' in line:
        # Get the indentation of the assert line
        indent = line[:len(line) - len(line.lstrip())]
        
        # Replace with fallback code, maintaining proper indentation
        new_lines.append(f"{indent}# Fallback if flash-attn not available\n")
        new_lines.append(f"{indent}if not FLASH_ATTN_2_AVAILABLE:\n")
        new_lines.append(f"{indent}    import torch.nn.functional as F\n")
        new_lines.append(f"{indent}    q_t = q.transpose(1, 2)  # [B, H, N, D]\n")
        new_lines.append(f"{indent}    k_t = k.transpose(1, 2)\n")
        new_lines.append(f"{indent}    v_t = v.transpose(1, 2)\n")
        new_lines.append(f"{indent}    out = F.scaled_dot_product_attention(q_t, k_t, v_t, attn_mask=None, dropout_p=0.0)\n")
        new_lines.append(f"{indent}    return out.transpose(1, 2).contiguous()\n")
        new_lines.append(f"{indent}# Original: assert FLASH_ATTN_2_AVAILABLE\n")
        patched = True
    else:
        new_lines.append(line)

if patched:
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    print('✅ Applied flash-attn fallback patch')
else:
    print('⚠️ Could not find assertion line to patch')
    exit(1)
