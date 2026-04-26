#!/usr/bin/env python3
"""Test script to verify the message bubble module syntax and structure."""

import ast
import sys

# Check syntax of both files
files_to_check = [
    '/workspace/message_bubble.py',
    '/workspace/deepagents_gui.py'
]

all_ok = True
for filepath in files_to_check:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f"✓ {filepath}: Syntax OK")
        
        # Check for key components
        if 'message_bubble' in filepath:
            # Check MessageBubble class exists
            tree = ast.parse(source)
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            if 'MessageBubble' in classes:
                print(f"  ✓ MessageBubble class found")
            else:
                print(f"  ✗ MessageBubble class NOT found")
                all_ok = False
                
            if 'calculate_text_height' in functions:
                print(f"  ✓ calculate_text_height function found")
            else:
                print(f"  ✗ calculate_text_height function NOT found")
                all_ok = False
                
            # Check for key methods
            required_methods = ['_estimate_line_count', '_adjust_layout', 'update_message', '_copy_to_clipboard']
            for method in required_methods:
                if method in functions:
                    print(f"  ✓ Method {method} found")
                else:
                    print(f"  ✗ Method {method} NOT found")
                    all_ok = False
                    
    except SyntaxError as e:
        print(f"✗ {filepath}: Syntax Error - {e}")
        all_ok = False
    except Exception as e:
        print(f"✗ {filepath}: Error - {e}")
        all_ok = False

# Check deepagents_gui.py imports
print("\nChecking deepagents_gui.py imports:")
with open('/workspace/deepagents_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'from message_bubble import MessageBubble' in content:
    print("  ✓ Import of MessageBubble found")
else:
    print("  ✗ Import of MessageBubble NOT found")
    all_ok = False

if 'from message_bubble import calculate_text_height' in content:
    print("  ✓ Import of calculate_text_height found")
else:
    print("  ⚠ Import of calculate_text_height NOT found (optional)")

# Check that old MessageBubble class is removed
if 'class MessageBubble(ctk.CTkFrame):' not in content:
    print("  ✓ Old MessageBubble class removed from deepagents_gui.py")
else:
    print("  ⚠ Old MessageBubble class still exists in deepagents_gui.py")

print("\n" + "="*50)
if all_ok:
    print("All checks passed! ✓")
    sys.exit(0)
else:
    print("Some checks failed! ✗")
    sys.exit(1)
