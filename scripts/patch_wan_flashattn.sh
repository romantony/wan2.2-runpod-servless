#!/bin/bash
# Patch WAN 2.2 to make flash-attn optional
# If flash-attn is not available, fallback to PyTorch's scaled_dot_product_attention

ATTENTION_FILE="/workspace/Wan2.2/wan/modules/attention.py"

if [ -f "$ATTENTION_FILE" ]; then
    echo "Patching $ATTENTION_FILE to make flash-attn optional..."
    
    # Backup original
    cp "$ATTENTION_FILE" "${ATTENTION_FILE}.orig"
    
    # Replace the assertion with a fallback
    python3 << 'EOF'
file_path = "/workspace/Wan2.2/wan/modules/attention.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

# Find and replace the assertion line
new_lines = []
for i, line in enumerate(lines):
    if 'assert FLASH_ATTN_2_AVAILABLE' in line and 'def flash_attention' in ''.join(lines[max(0,i-20):i]):
        # Get the indentation
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        
        # Replace assertion with conditional fallback
        new_lines.append(indent_str + '# Fallback if flash-attn not available\n')
        new_lines.append(indent_str + 'if not FLASH_ATTN_2_AVAILABLE:\n')
        new_lines.append(indent_str + '    import torch.nn.functional as F\n')
        new_lines.append(indent_str + '    # Use PyTorch native attention as fallback\n')
        new_lines.append(indent_str + '    q_t = q.transpose(1, 2)  # [B, H, N, D]\n')
        new_lines.append(indent_str + '    k_t = k.transpose(1, 2)\n')
        new_lines.append(indent_str + '    v_t = v.transpose(1, 2)\n')
        new_lines.append(indent_str + '    out = F.scaled_dot_product_attention(q_t, k_t, v_t, attn_mask=None, dropout_p=0.0)\n')
        new_lines.append(indent_str + '    return out.transpose(1, 2).contiguous()\n')
        new_lines.append(indent_str + '# Original assertion commented out\n')
        new_lines.append(indent_str + '# ' + line.lstrip())
    else:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("✅ Patched flash_attention to use fallback")
EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully patched attention.py"
    else
        echo "⚠️ Patch failed, restoring original"
        mv "${ATTENTION_FILE}.orig" "$ATTENTION_FILE"
    fi
else
    echo "⚠️ $ATTENTION_FILE not found, skipping patch"
fi
