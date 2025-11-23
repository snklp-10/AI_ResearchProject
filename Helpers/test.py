import pandas as pd
import json
from typing import List, Dict, Set, Any, Optional


def parse_cell_to_set(cell: Any) -> Set[str]:
    """
    Convert cell content into a set of normalized (lowercase, stripped) conditions.
    Supports comma, semicolon, pipe, and newline separators.
    Returns an empty set for NaN/None/empty strings.
    """
    if pd.isna(cell) or cell is None:
        return set()
    # normalize separators to comma, then split
    text = str(cell)
    for sep in [";", "|", "\n", "\r"]:
        text = text.replace(sep, ",")
    items = [itm.strip().lower() for itm in text.split(",") if itm.strip() != ""]
    return set(items)


def row_to_condition_object(
    pos_set: Set[str],
    neg_set: Set[str],
    master_list: List[str],
    default_when_missing: str = "neg",
) -> Dict[str, str]:
    """
    Build a dictionary mapping each condition in master_list to 'pos'/'neg' (or default).
    Matching is case-insensitive (pos_set/neg_set expected to be lowercase).
    The output keys are the original master_list entries (preserved case).
    """
    obj: Dict[str, str] = {}
    # prepare lowercase lookup for faster checks
    for cond in master_list:
        cond_lc = cond.lower()
        if cond_lc in pos_set:
            obj[cond] = "pos"
        elif cond_lc in neg_set:
            obj[cond] = "neg"
        else:
            obj[cond] = default_when_missing
    return obj


def excel_rows_to_json_objects(
    file_path: str,
    master_list: List[str],
    sheet_name: Optional[Any] = None,
    pos: str = "pos",
    neg: str = "neg",
    default_when_missing: str = "neg",
    output_json_path: Optional[str] = None,
    append_json_array_path: Optional[str] = None,  # NEW
) -> List[Dict[str, str]]:

    if not master_list:
        raise ValueError("master_list must be a non-empty list of condition keys.")

    try:
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            usecols=[pos, neg],
            engine="openpyxl",
        )
    except ValueError as e:
        raise ValueError(f"Error reading Excel file: {e}")

    for col in (pos, neg):
        if col not in df.columns:
            raise KeyError(
                f"Expected column '{col}' not found in sheet '{sheet_name}' of file '{file_path}'."
            )

    results: List[Dict[str, str]] = []

    # If append path is given, load or initialize JSON array
    json_array = []
    if append_json_array_path:
        try:
            with open(append_json_array_path, "r", encoding="utf-8") as f:
                json_array = json.load(f)
                if not isinstance(json_array, list):
                    raise ValueError("Append file is not a JSON array.")
        except FileNotFoundError:
            json_array = []
        except json.JSONDecodeError:
            # File exists but invalid JSON → reset
            json_array = []

    for _, row in df.iterrows():
        pos_data = parse_cell_to_set(row[pos])
        neg_data = parse_cell_to_set(row[neg])

        obj = row_to_condition_object(
            pos_data, neg_data, master_list, default_when_missing
        )
        results.append(obj)

        if append_json_array_path:
            json_array.append(obj)

    # Re-write appended JSON array safely
    if append_json_array_path:
        with open(append_json_array_path, "w", encoding="utf-8") as f:
            json.dump(json_array, f, indent=2, ensure_ascii=False)

    # Write standard JSON output if requested
    if output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def list_sheet_names(file_path: str) -> List[str]:
    """
    Return list of sheet names available in the given Excel file.
    Useful to discover valid sheet_name values.
    """
    xls = pd.ExcelFile(file_path, engine="openpyxl")
    return xls.sheet_names


# -------------------------
# Example usage (adjust values for your environment)
# -------------------------
if __name__ == "__main__":
    master_list = [
        "pulmonary_nodules",
        "esophagitis",
        "pneumonia",
        "bronchitis",
        "interstitial",
        "diseased_lungs",
        "hypo_plastic_trachea",
        "cardiomegaly",
        "pleural_effusion",
        "perihilar_infiltrate",
        "rtm",
        "focal_caudodorsal_lung",
        "right_sided_cardiomegaly",
        "focal_perihilar",
        "left_sided_cardiomegaly",
        "bronchiectasis",
        "pulmonary_vessel_enlargement",
        "thoracic_lymphadenopathy",
        "pulmonary_hypoinflation",
        "pericardial_effusion",
        "Fe_Alveolar",
    ]

    file_path = r"C:\Users\snklp\Downloads\Feline.xlsx"

    # Optional: list sheet names first to confirm which to use
    try:
        sheets = list_sheet_names(file_path)
        print("Available sheets:", sheets)
    except Exception as e:
        print("Could not read sheet names:", e)
        sheets = []

    # choose sheet_name either by string or index (e.g., "Sheet1" or 0). Use None to use the first sheet.
    sheet_name_to_use = "with_rad_pos_neg" if "with_rad_pos_neg" in sheets else None

    output = excel_rows_to_json_objects(
        file_path=file_path,
        master_list=master_list,
        sheet_name=sheet_name_to_use,
        pos="pos",
        neg="neg",
        default_when_missing="neg",
        output_json_path=None,  # or provide a path like r"output.json"
        append_json_array_path=r"C:\Users\snklp\Downloads\ResearchProject\radio_feline_reports.json",
    )

    for i, row_obj in enumerate(output, 1):
        print(f"Row {i}:")
        print(json.dumps(row_obj, indent=2))
        print()
