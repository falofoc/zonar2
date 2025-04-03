#!/usr/bin/env python3
"""
Fix indentation issues in app/routes.py
"""

def fix_file(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.readlines()
    
    fixed_content = []
    in_try_block = False
    indent_level = 0
    
    for line in content:
        stripped = line.strip()
        
        # Detect indentation issues in verify_email function
        if stripped == 'try:':
            in_try_block = True
            indent_level = len(line) - len(line.lstrip())
        
        # Fix the indentation for 'flash' and 'db.session.commit()' statements
        if stripped.startswith('flash(translate(\'verification_') and in_try_block and not line.strip().startswith('#'):
            leading_spaces = ' ' * (indent_level + 4)  # Add 4 spaces for indent level inside try block
            fixed_line = leading_spaces + stripped + '\n'
            fixed_content.append(fixed_line)
        elif stripped.startswith('db.session.commit()') and in_try_block and not line.strip().startswith('#'):
            leading_spaces = ' ' * (indent_level + 4)  # Add 4 spaces for indent level inside try block
            fixed_line = leading_spaces + stripped + '\n'
            fixed_content.append(fixed_line)
        else:
            fixed_content.append(line)
        
        # Reset try block tracking when encountering 'except' or 'finally'
        if stripped.startswith('except') or stripped.startswith('finally'):
            in_try_block = False
    
    with open(output_file, 'w') as f:
        f.writelines(fixed_content)

if __name__ == '__main__':
    fix_file('app/routes.py', 'app/routes_fixed.py')
    print("Fixed file written to app/routes_fixed.py") 