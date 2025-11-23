import pandas as pd
from pathlib import Path

# ====== Path to your Excel file ======
excel_path = Path(
    r"C:\Users\snklp\Downloads\Abdomen_classification.xlsx"
)  # <-- change this

# ====== Master list of all conditions ======
MASTER_CONDITIONS = [
    "gastritis",
    "ascites",
    "colitis",
    "liver_mass",
    "pancreatitis",
    "microhepatia",
    "small_intestinal_obstruction",
    "splenic_mass",
    "splenomegaly",
    "hepatomegaly",
]

MASTER_SET = set(MASTER_CONDITIONS)


def parse_cell(cell):
    """Convert a cell into a set of conditions, separated by commas/newlines/semicolons."""
    if pd.isna(cell):
        return set()
    if not isinstance(cell, str):
        cell = str(cell)

    # Normalize separators to commas
    for sep in ["\n", ";", "/", "|"]:
        cell = cell.replace(sep, ",")

    parts = [p.strip() for p in cell.split(",")]
    return {p for p in parts if p}


def compute_pos_neg_for_row(row):
    tp = parse_cell(row.get("tp", ""))
    tn = parse_cell(row.get("tn", ""))
    fp = parse_cell(row.get("fp", ""))
    fn = parse_cell(row.get("fn", ""))

    # Radiologist logic
    rad_pos = tp | fn
    labeled = tp | tn | fp | fn
    missing = MASTER_SET - labeled
    rad_neg = tn | fp | missing

    # NEW LINE-SEPARATED output
    pos_str = "\n".join(sorted(rad_pos))
    neg_str = "\n".join(sorted(rad_neg))

    return pd.Series({"pos": pos_str, "neg": neg_str})


# ====== Load Excel ======
df = pd.read_excel(excel_path)

# ====== Compute per-row pos/neg ======
pos_neg_df = df.apply(compute_pos_neg_for_row, axis=1)

# Add row numbering
df_with_pos_neg = df.copy()
df_with_pos_neg.insert(0, "row_number", range(1, len(df) + 1))
df_with_pos_neg = pd.concat([df_with_pos_neg, pos_neg_df], axis=1)

# ====== Write to same Excel (new sheet) ======
with pd.ExcelWriter(
    excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
) as writer:
    df_with_pos_neg.to_excel(writer, sheet_name="with_rad_pos_neg", index=False)

print("✅ Done! Sheet 'with_rad_pos_neg' created with POS/NEG (newline-separated).")
