import os
import re

API_DIR = r"c:\SupplySense\SupplySense_Backend\backend\app\api\v1"

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find `db: AsyncSession = Depends(get_db)` and replace with `db: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)`
    # BUT only if it's inside `def `
    # Let's split by lines and look for it.
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'db: AsyncSession = Depends(get_db)' in line and 'current_user' not in line:
            # check if it ends with `,` or `)`
            if 'db: AsyncSession = Depends(get_db),' in line:
                lines[i] = line.replace('db: AsyncSession = Depends(get_db),', 'db: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user),')
            elif 'db: AsyncSession = Depends(get_db)' in line:
                lines[i] = line.replace('db: AsyncSession = Depends(get_db)', 'db: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

for root, _, files in os.walk(API_DIR):
    for file in files:
        if file.endswith(".py") and file != "auth.py" and file != "__init__.py":
            patch_file(os.path.join(root, file))
print("Signature patching complete.")
