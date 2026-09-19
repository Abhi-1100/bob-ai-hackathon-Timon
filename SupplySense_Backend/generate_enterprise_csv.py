import csv
import random
import uuid

# Configuration
NUM_ROWS_A = 2500  # Electronics
NUM_ROWS_B = 2500  # Apparel

# Electronics Data Generators
ELECTRONIC_PREFIXES = ["SKU-EL", "PRD-HW", "COMP", "MOD", "PWR"]
ELECTRONIC_TYPES = ["Power Supply", "Monitor", "Keyboard", "Mouse", "RAM", "CPU", "GPU", "Motherboard", "SSD", "HDD", "Cooling Fan", "Case", "Cable"]
ELECTRONIC_SPECS = ["850W Gold", "27-inch 4K", "Mechanical RGB", "Wireless", "32GB DDR5", "Intel Core i7", "RTX 4070", "ATX", "1TB NVMe", "2TB 7200RPM", "120mm PWM", "Mid-Tower", "USB-C 2m"]
ELECTRONIC_WAREHOUSES = ["Central Hub (WH-01)", "Regional Depot (WH-02)", "Express Logistics (WH-03)", "West Coast Dist", "East Coast Fulfillment"]

def generate_electronics_row():
    sku = f"{random.choice(ELECTRONIC_PREFIXES)}-{random.randint(1000, 99999)}"
    name = f"{random.choice(ELECTRONIC_TYPES)} - {random.choice(ELECTRONIC_SPECS)}"
    warehouse = random.choice(ELECTRONIC_WAREHOUSES)
    stock = random.randint(0, 5000)
    reorder = random.randint(10, 500)
    cost = round(random.uniform(5.0, 800.0), 2)
    return [sku, name, warehouse, stock, reorder, f"${cost:.2f}"]

# Apparel Data Generators
APPAREL_PREFIXES = ["SKU-AP", "TSHIRT", "PANTS", "JCKT", "SHOE"]
APPAREL_TYPES = ["Cotton T-Shirt", "Slim Fit Jeans", "Puffer Jacket", "Running Sneakers", "Beanie Hat", "Hoodie", "Athletic Shorts", "Socks", "Sweater", "Polo Shirt"]
APPAREL_SPECS = ["Small (S)", "Medium (M)", "Large (L)", "Extra Large (XL)", "US 9", "US 10", "US 11", "One Size", "32x32", "34x32"]
APPAREL_WAREHOUSES = ["Surat Central Warehouse", "Regional Depot North", "South Fulfillment Center", "Mumbai Hub", "Delhi Distribution"]

def generate_apparel_row():
    sku = f"{random.choice(APPAREL_PREFIXES)}-{random.randint(1000, 99999)}"
    name = f"{random.choice(APPAREL_TYPES)} - {random.choice(APPAREL_SPECS)}"
    warehouse = random.choice(APPAREL_WAREHOUSES)
    stock = random.randint(0, 10000)
    reorder = random.randint(50, 1000)
    cost = round(random.uniform(2.0, 150.0), 2)
    return [sku, name, warehouse, stock, reorder, f"${cost:.2f}"]

# Write Company A (Electronics)
print("Generating Company A CSV...")
with open('c:\\SupplySense\\SupplySense_Backend\\CompanyA_Electronics.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["sku", "name", "warehouse", "stock", "reorder", "cost"])
    # Ensure unique SKUs
    skus_a = set()
    rows_generated = 0
    while rows_generated < NUM_ROWS_A:
        row = generate_electronics_row()
        if row[0] not in skus_a:
            skus_a.add(row[0])
            writer.writerow(row)
            rows_generated += 1

# Write Company B (Apparel)
print("Generating Company B CSV...")
with open('c:\\SupplySense\\SupplySense_Backend\\CompanyB_Apparel.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["sku", "name", "warehouse", "stock", "reorder", "cost"])
    skus_b = set()
    rows_generated = 0
    while rows_generated < NUM_ROWS_B:
        row = generate_apparel_row()
        if row[0] not in skus_b:
            skus_b.add(row[0])
            writer.writerow(row)
            rows_generated += 1

print("Done generating large enterprise CSVs.")
