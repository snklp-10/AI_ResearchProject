import json

# Path to your JSON file
json_path = (
    r"C:\Users\snklp\Downloads\ResearchProject\ai_classification_feline_thorax.json"
)

# Step 1: Read the JSON file
with open(json_path, "r") as f:
    data = json.load(f)

# Step 2: Sort the data by 'row_id'
sorted_data = sorted(data, key=lambda x: x.get("row_id", 0))

# Step 3: Write the sorted data back to the file
with open(json_path, "w") as f:
    json.dump(sorted_data, f, indent=4)

print("✅ JSON file sorted successfully by row_id.")
