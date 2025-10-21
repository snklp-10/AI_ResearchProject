import json
import time
import os
import re
import pandas as pd
from pathlib import Path
from google import genai


os.environ["GEMINI_API_KEY"] = "AIzaSyAdd8u-SbuX8RXLFZPGYXlp5zVrfOKANLU"
client = genai.Client()


with open("canine_thorax_prompt.json", "r") as file:
    initial_prompt = json.load(file)

input_file = Path(
    r"C:\Users\snklp\Downloads\Research Student Assignments\Research Student Assignments\Input Data 1 - canine_thorax_scoring.xlsx"
)


# read from excel
df_input = pd.read_excel(
    input_file,
    usecols=["Findings (original radiologist report)", "Findings (AI report)"],
)

# use only 1st 10 columns
df_input = df_input.head(10)


output_json_path = Path(
    r"C:\Users\snklp\Downloads\ResearchProject\ai_classification.json"
)

# ensure folder exists
output_json_path.parent.mkdir(parents=True, exist_ok=True)

if not output_json_path.exists():
    # Create empty JSON file if not present
    with open(output_json_path, "w") as f:
        json.dump([], f, indent=4)
    all_results = []
else:
    with open(output_json_path, "r") as f:
        try:
            all_results = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Existing JSON is invalid, starting fresh.")
            all_results = []


def clean_ai_json(ai_text: str):
    if not ai_text:
        return None
    # Remove code block markers like ```json ... ```
    ai_text = re.sub(r"```(?:json)?", "", ai_text, flags=re.IGNORECASE).strip()
    # Extract first JSON object
    match = re.search(r"\{.*\}", ai_text, flags=re.DOTALL)
    if match:
        return match.group(0)
    return None


# iterate over every row
for idx, row in df_input.iterrows():
    radiologist_report = str(row["Findings (original radiologist report)"])
    ai_report = str(row["Findings (AI report)"])

    print(f"\nProcessing row {idx+1}:")
    # print("Radiologist Report:", radiologist_report)
    # print("Ai Report: ", ai_report)

    final_prompt = f"""
    Role:{initial_prompt['role']}
    Description: {initial_prompt["description"]}

    Objective:
    -{";".join(initial_prompt["objective"])}

    Conditions to identify:
    - {"; ".join(initial_prompt['conditions_to_identify'])}

    Classification rules:
    - {"; ".join(initial_prompt['classification_rules'])}

    Radiologist Report: {radiologist_report}
    AI Report: {ai_report}

    Output format (JSON only):
    {{
    "tp": [],
    "fp": [],
    "tn": [],
    "fn": []
    }}

    Strict instruction:
    {initial_prompt['strict_output_instruction']}

    Example output:
    {json.dumps(initial_prompt['example_output'], indent=2)}
    """

    try:
        # access gemini api
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt,
        )

        ai_output_text = response.text.strip()

        # if no response is provided by ai
        if not ai_output_text:
            print(f"⚠️ Row {idx+1}: AI returned empty response. Skipping.")
            continue

        # handle extra text
        cleaned_text = clean_ai_json(ai_output_text)
        if not cleaned_text:
            print(f"⚠️ Row {idx+1}: Could not extract JSON. Skipping.")
            continue

    except Exception as e:
        print(f"⚠️ Error calling Gemini API: {e}")
        continue

    try:
        ai_output = json.loads(cleaned_text)
    except json.JSONDecodeError:
        print(f"⚠️ Row {idx+1}: Invalid JSON returned by AI. Skipping row.")
        print("Output was:", ai_output_text)
        continue

    # Append result
    entry = {
        "row_id": idx + 1,
        "radiologist_report": radiologist_report,
        "ai_report": ai_report,
        "results": ai_output,
    }

    all_results.append(entry)

    # append json formatted output in json file
    with open(output_json_path, "w") as f:
        json.dump(all_results, f, indent=4)

    print(f"✅ Row {idx+1} saved to {output_json_path}")
    time.sleep(1)

print("\n✅ All rows processed successfully")
