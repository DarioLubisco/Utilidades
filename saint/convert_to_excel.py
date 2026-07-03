import pandas as pd
import io

input_file = r"C:\Users\DARIO LUBISCO\.gemini\antigravity\brain\3b632898-e8f4-40d7-b1b2-4ffacc42ff22\.system_generated\steps\510\output.txt"
output_file = r"c:\source\Precios_Corregidos_822_Productos.xlsx"

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = 0
for i, line in enumerate(lines):
    if line.startswith("codigo,descripcion,costo_anterior"):
        start_idx = i
        break

data = []
for line in lines[start_idx+1:]:
    line = line.strip()
    if not line:
        continue
    # Split from right max 5 times to get the 5 numeric columns
    parts = line.rsplit(",", 5)
    if len(parts) == 6:
        # The first part is "codigo,descripcion"
        code_desc = parts[0]
        code_desc_parts = code_desc.split(",", 1)
        if len(code_desc_parts) == 2:
            codigo = code_desc_parts[0]
            desc = code_desc_parts[1]
        else:
            codigo = code_desc
            desc = ""
        
        data.append([
            codigo, 
            desc, 
            float(parts[1]), 
            float(parts[2]), 
            float(parts[3]), 
            float(parts[4]),
            float(parts[5]) # stock_actual
        ])

df = pd.DataFrame(data, columns=["codigo", "descripcion", "costo_anterior", "precio_anterior", "costo_actual", "precio_actual", "stock_actual"])

df.to_excel(output_file, index=False)
print(f"Excel updated successfully at: {output_file}")
