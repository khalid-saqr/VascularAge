import csv
from itertools import product
from pathlib import Path
import zipfile

import pytest

from vascularage.phase1 import audit_model_variations, audit_radial_archive


def write_configs(path: Path):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Subject Number", "age [years]"])
        w.writeheader()
        subject = 1
        for age in (25,35,45,55,65,75):
            for _ in range(729):
                w.writerow({"Subject Number": subject, "age [years]": age})
                subject += 1


def write_variations(path: Path):
    fields = ["SUBJECT NUMBER","AGE","DIA","HR","LVET","MBP","PWV","SV"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        subject = 1
        for age in (25,35,45,55,65,75):
            for hr,sv,lvet,dia,pwv,mbp in product((-1,0,1), repeat=6):
                w.writerow({"SUBJECT NUMBER":subject,"AGE":age,"DIA":dia,"HR":hr,"LVET":lvet,"MBP":mbp,"PWV":pwv,"SV":sv})
                subject += 1


def test_factorial_exact_8_column_source_contract(tmp_path):
    variations = tmp_path/"pwdb_model_variations.csv"
    configs = tmp_path/"pwdb_model_configs.csv"
    write_variations(variations)
    write_configs(configs)
    result = audit_model_variations(variations, configs)
    assert result["subjects"] == 4374
    assert result["map_to_source_mbp_explicit"] is True
    assert all(v["complete_3pow6"] for v in result["age_groups"].values())


def test_factorial_rejects_contextual_columns_not_in_canonical_artifact(tmp_path):
    variations = tmp_path/"pwdb_model_variations.csv"
    configs = tmp_path/"pwdb_model_configs.csv"
    write_variations(variations)
    write_configs(configs)
    rows = variations.read_text(encoding="utf-8").splitlines()
    rows[0] = rows[0] + ",LEN"
    variations.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="unexpected model variations header"):
        audit_model_variations(variations, configs)


def make_radial_zip(path: Path, *, internal_nan_subject: int | None = None):
    member = path.parent/"PWs_Radial_P.csv"
    with member.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Subject Number","pt1","pt2","pt3","pt4","pt5"])
        for subject in range(1,4375):
            if internal_nan_subject == subject:
                row = [subject,80.0,"NaN",90.0,"NaN","NaN"]
            else:
                row = [subject,80.0,90.0,85.0,"NaN","NaN"]
            w.writerow(row)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(member, arcname="PWs_Radial_P.csv")


def test_radial_nan_suffix_is_padding_not_corruption(tmp_path):
    archive = tmp_path/"PWs_csv.zip"
    make_radial_zip(archive)
    result = audit_radial_archive(archive, ("1","4374"))
    assert result["subjects"] == 4374
    assert result["internal_missing_total"] == 0
    assert result["min_active_samples"] == 3
    assert result["max_padding_samples"] == 2


def test_radial_internal_nan_is_rejected(tmp_path):
    archive = tmp_path/"PWs_csv.zip"
    make_radial_zip(archive, internal_nan_subject=11)
    with pytest.raises(AssertionError, match="internal missing"):
        audit_radial_archive(archive, ("1","4374"))
