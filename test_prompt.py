import json
import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_AI_APIKEY"))

# Load compact prompt JSON
with open("feline_thorax_prompt.json", "r") as file:
    initial_prompt = json.load(file)

# Input Excel
input_file = Path(
    r"C:\Users\snklp\Downloads\Research Student Assignments1\Research Student Assignments\Input Data 2 - feline_thorax_scoring.xlsx"
)

df_input = pd.read_excel(
    input_file,
    usecols=["Findings (original radiologist report)", "Findings (AI report)"],
)
df_input = df_input.head(1)


# ✅ New classification output
classification_output_path = Path(
    r"C:\Users\snklp\Downloads\ResearchProject\classification_files\classification_feline.json"
)
classification_output_path.parent.mkdir(parents=True, exist_ok=True)


try:
    with open(classification_output_path, "r") as f:
        all_classifications = json.load(f)
except:
    all_classifications = []


# ✅ Build system prompt once
SYSTEM_PROMPT = f"""
You are an expert veterinary radiologist.

Conditions:
{", ".join(initial_prompt["conditions_to_identify"])}

Synonyms:
{json.dumps(initial_prompt["synonyms_mapping"])}

Rules:
{json.dumps(initial_prompt["tagging_rules"])}

strict_output_instruction: "{...}\n{...}"

Strictly Return only 2 JSON dictionaries on separate lines:
1) Radiologist
2) AI
"""


# ✅ Classification function
def classify(row_id, rad, ai):
    tp, tn, fp, fn = [], [], [], []

    for cond, r_val in rad.items():
        a_val = ai.get(cond)

        if r_val == "pos" and a_val == "pos":
            tp.append(cond)
        elif r_val == "neg" and a_val == "neg":
            tn.append(cond)
        elif r_val == "pos" and a_val == "neg":
            fn.append(cond)
        elif r_val == "neg" and a_val == "pos":
            fp.append(cond)

    return {"row_id": row_id, "tp": tp, "tn": tn, "fp": fp, "fn": fn}


# ✅ Process rows
for idx, row in df_input.iterrows():
    row_num = idx + 1
    print(f"Processing row {row_num}")

    user_prompt = f"""
Radiologist Report:
{row['Findings (original radiologist report)']}

AI Report:
{row['Findings (AI report)']}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )

        output = response.choices[0].message.content
        lines = [l.strip() for l in output.split("\n") if l.strip()]

        if len(lines) < 2:
            print(f"⚠️ Row {row_num}: Bad output")
            continue

        rad_dict = json.loads(lines[0])
        ai_dict = json.loads(lines[1])

    except Exception as e:
        print(f"❌ Error row {row_num}: {e}")
        continue

    class_entry = classify(row_num, rad_dict, ai_dict)
    all_classifications.append(class_entry)

    # ✅ Save classification JSON after each append
    with open(classification_output_path, "w") as f:
        json.dump(all_classifications, f, indent=4)

# print(f"✅ Classification results saved → {classification_output_path}")
print("\n✅ All rows processed & saved successfully")
