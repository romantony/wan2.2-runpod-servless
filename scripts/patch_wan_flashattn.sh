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
import re

file_path = "/workspace/Wan2.2/wan/modules/attention.py"

with open(file_path, 'r') as f:
    content = f.read()

# Find the flash_attention function and patch the assertion
# Replace: assert FLASH_ATTN_2_AVAILABLE
# With: if not FLASH_ATTN_2_AVAILABLE: return F.scaled_dot_product_attention(...)

pattern = r'def flash_attention\((.*?)\):(.*?)assert FLASH_ATTN_2_AVAILABLE'
replacement = r'''def flash_attention(\1):\2# Fallback if flash-attn not available
    if not FLASH_ATTN_2_AVAILABLE:
        import torch.nn.functional as F
        # Use PyTorch's native attention as fallback
        q_reshaped = q.transpose(1, 2)  # [B, H, N, D]
        k_reshaped = k.transpose(1, 2)
        v_reshaped = v.transpose(1, 2)
        out = F.scaled_dot_product_attention(q_reshaped, k_reshaped, v_reshaped, attn_mask=None, dropout_p=0.0, is_causal=False)
        return out.transpose(1, 2).contiguous()  # Back to [B, N, H, D]
    #assert FLASH_ATTN_2_AVAILABLE'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

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
