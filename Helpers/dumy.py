import json

with open("radio_canine_report.json", "r") as f:
    data = json.load(f)

print(data[1])
