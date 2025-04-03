#!/usr/bin/env python3
"""
Fix indentation issues in app/routes.py
"""

def fix_indentation():
    filename = 'app/routes.py'
    print(f"Fixing indentation in {filename}")
    
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    # Fix the indentation issue at line 922
    for i in range(len(lines)):
        if "message = translate('reset_email_sent')" in lines[i]:
            # Look for lines with extra indentation
            leading_spaces = len(lines[i]) - len(lines[i].lstrip())
            if leading_spaces > 16:  # If indentation is more than 16 spaces
                lines[i] = ' ' * 16 + lines[i].lstrip()  # Fix indentation to 16 spaces
                
                # Also check the next line for "category = 'success'"
                if i+1 < len(lines) and "category = 'success'" in lines[i+1]:
                    lines[i+1] = ' ' * 16 + lines[i+1].lstrip()
                    
                print(f"Fixed indentation at lines {i+1} and {i+2}")
    
    # Write the fixed content back to the file
    with open(filename, 'w') as file:
        file.writelines(lines)
    
    print(f"Indentation fixed in {filename}")

if __name__ == "__main__":
    fix_indentation() 