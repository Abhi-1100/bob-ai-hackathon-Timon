import os
import re

API_DIR = r"c:\SupplySense\SupplySense_Backend\backend\app\api\v1"

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add imports if not present
    if "UserResponse" not in content and "get_current_user" not in content:
        if "from backend.app.api.deps import" in content:
            content = content.replace("from backend.app.api.deps import", "from backend.app.api.deps import get_current_user,")
            content = content.replace("from backend.app.schemas", "from backend.app.schemas.auth import UserResponse\nfrom backend.app.schemas")
        else:
            content = "from backend.app.api.deps import get_current_user\nfrom backend.app.schemas.auth import UserResponse\n" + content

    # Add current_user to function signatures
    # Find all async def that take db: AsyncSession
    pattern = re.compile(r'(async def \w+\([^)]*)(db: AsyncSession = Depends\(get_db\))([^)]*\):)')
    
    def repl(m):
        pre = m.group(1)
        db_arg = m.group(2)
        post = m.group(3)
        if "current_user" not in pre and "current_user" not in post:
            return pre + db_arg + ", current_user: UserResponse = Depends(get_current_user)" + post
        return m.group(0)

    content = pattern.sub(repl, content)

    # Now for each query, try to inject the where clause.
    # This is tricky with regex. Let's look for common patterns.
    # select(Product
    # select(Warehouse
    # select(Supplier
    # select(PurchaseOrder
    # select(Inventory
    
    models = ["Product", "Warehouse", "Supplier", "PurchaseOrder", "Inventory", "Shipment", "StockTransfer", "DemandHistory", "ForecastHistory", "SalesOrder", "Category", "Brand", "AIRiskAlert"]
    
    for model in models:
        # select(Model)
        select_pattern = re.compile(r'select\(' + model + r'([^)]*)\)')
        
        # We need to find the variable it's assigned to.
        # usually `stmt = select(Model...`
        stmt_pattern = re.compile(r'(stmt\s*=\s*select\(' + model + r'[^)]*\)[^\n]*)')
        
        def stmt_repl(m):
            stmt_line = m.group(1)
            if f"{model}.company_id == current_user.company_id" not in stmt_line:
                if ".where(" in stmt_line:
                    # Insert into existing where
                    return stmt_line.replace(".where(", f".where({model}.company_id == current_user.company_id, ")
                else:
                    return stmt_line + f".where({model}.company_id == current_user.company_id)"
            return m.group(0)
            
        content = stmt_pattern.sub(stmt_repl, content)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(API_DIR):
    for file in files:
        if file.endswith(".py") and file != "auth.py" and file != "__init__.py":
            patch_file(os.path.join(root, file))
print("Patching complete.")
