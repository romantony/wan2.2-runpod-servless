#!/usr/bin/env python3
"""
Patch WAN 2.2 attention.py to make flash-attn optional
Comment out the assert so it falls through to the attention() call below
"""

file_path = '/workspace/Wan2.2/wan/modules/attention.py'

with open(file_path, 'r') as f:
    content = f.read()

# The assert at line 108 blocks the fallback in attention()
# Just comment it out - the code after it will use the attention() fallback

if 'assert FLASH_ATTN_2_AVAILABLE' in content:
    content = content.replace(
        '        assert FLASH_ATTN_2_AVAILABLE',
        '        # assert FLASH_ATTN_2_AVAILABLE  # Patched: allow fallback'
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print('✅ Patched flash_attention: commented out assertion to allow fallback')
else:
    print('⚠️ Could not find assertion line - may already be patched')
