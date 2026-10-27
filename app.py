import os
from datetime import date, datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from database import (
    init_db, create_patient, list_patients, get_patient, update_patient,
    delete_patient, log_import_result, list_import_logs, patient_exists
)
from validation import validate_patient, validate_import_row, calculate_age
from ai_service import generate_health_remarks

load_dotenv()
init_db()

st.set_page_config(page_title="Health Prediction Application", page_icon="🩺", layout="wide")

st.title("🩺 Health Prediction Application")
st.caption("Patient blood-test record management with AI-assisted informational remarks")

st.warning(
    "Educational demonstration only. This application does not diagnose disease or replace a qualified "
    "health professional. AI-generated remarks may be inaccurate and must not be used for treatment decisions."
)

def render_patient_table(rows):
    if not rows:
        st.info("No patient records have been saved yet.")
        return
    df = pd.DataFrame(rows)
    display_cols = ["id", "full_name", "date_of_birth", "email", "glucose", "haemoglobin", "cholesterol", "remarks", "created_at", "updated_at"]
    df = df[[c for c in display_cols if c in df.columns]]
    df = df.rename(columns={
        "id": "ID", "full_name": "Full Name", "date_of_birth": "Date of Birth",
        "email": "Email Address", "glucose": "Glucose", "haemoglobin": "Haemoglobin",
        "cholesterol": "Cholesterol", "remarks": "Remarks (AI-generated)",
        "created_at": "Created At", "updated_at": "Updated At"
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

tab_create, tab_read, tab_edit, tab_delete, tab_test = st.tabs(
    ["➕ Create", "📋 Read records", "✏️ Update", "🗑️ Delete", "🧪 Assignment test data"]
)

with tab_create:
    st.subheader("Create a patient record")
    with st.form("create_patient_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full Name")
            dob_text = st.text_input("Date of Birth (dd/mm/yyyy)", placeholder="28/01/1960")
            email = st.text_input("Email Address")
        with c2:
            glucose_text = st.text_input("Glucose", placeholder="e.g. 94")
            haemoglobin_text = st.text_input("Haemoglobin", placeholder="e.g. 13.5")
            cholesterol_text = st.text_input("Cholesterol", placeholder="e.g. 200")
        submitted = st.form_submit_button("Validate, generate remarks & save", type="primary", use_container_width=True)

    if submitted:
        raw = {
            "full_name": full_name.strip(),
            "date_of_birth": dob_text.strip(),
            "email": email.strip(),
            "glucose": glucose_text.strip(),
            "haemoglobin": haemoglobin_text.strip(),
            "cholesterol": cholesterol_text.strip(),
        }
        errors, clean = validate_patient(raw, input_date_format="slash")
        if errors:
            st.error("The record was not saved. Please fix these issues:")
            for error in errors:
                st.write(f"- {error}")
        elif patient_exists(clean):
            st.error("A matching patient record already exists. Duplicate records are not added.")
        else:
            with st.spinner("Requesting informational remarks from Gemini..."):
                remarks, ai_status = generate_health_remarks(clean)
            patient_id = create_patient(clean, remarks)
            st.success(f"Patient record saved successfully (ID {patient_id}).")
            if ai_status != "ok":
                st.info(f"AI remarks could not be generated: {ai_status}. The record was saved with a clear status message in Remarks.")
            st.rerun()

with tab_read:
    st.subheader("All saved patient records")
    rows = list_patients()
    st.metric("Saved records", len(rows))
    render_patient_table(rows)
    if rows:
        csv_data = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
        st.download_button("Download records as CSV", csv_data, "patient_records.csv", "text/csv")

with tab_edit:
    st.subheader("Update an existing patient")
    rows = list_patients()
    if not rows:
        st.info("Create or import a valid record before editing.")
    else:
        options = {f"ID {r['id']} — {r['full_name']} ({r['email']})": r["id"] for r in rows}
        chosen_label = st.selectbox("Choose a record", list(options.keys()), key="edit_choice")
        selected = get_patient(options[chosen_label])
        with st.form("edit_patient_form"):
            new_name = st.text_input("Full Name", value=selected["full_name"])
            new_dob = st.text_input("Date of Birth (dd/mm/yyyy)", value=selected["date_of_birth"])
            new_email = st.text_input("Email Address", value=selected["email"])
            c1, c2, c3 = st.columns(3)
            with c1:
                new_glucose = st.text_input("Glucose", value=str(selected["glucose"]))
            with c2:
                new_hb = st.text_input("Haemoglobin", value=str(selected["haemoglobin"]))
            with c3:
                new_chol = st.text_input("Cholesterol", value=str(selected["cholesterol"]))
            regenerate = st.checkbox("Regenerate AI remarks using current blood-test values", value=True)
            update_submit = st.form_submit_button("Save changes", type="primary")
        if update_submit:
            raw = {"full_name": new_name.strip(), "date_of_birth": new_dob.strip(), "email": new_email.strip(),
                   "glucose": new_glucose.strip(), "haemoglobin": new_hb.strip(), "cholesterol": new_chol.strip()}
            errors, clean = validate_patient(raw, input_date_format="slash")
            if errors:
                st.error("Update not saved:")
                for error in errors:
                    st.write(f"- {error}")
            else:
                with st.spinner("Updating record..."):
                    if regenerate:
                        remarks, ai_status = generate_health_remarks(clean)
                    else:
                        remarks, ai_status = selected["remarks"], "unchanged"
                    update_patient(selected["id"], clean, remarks)
                st.success("Record updated successfully.")
                if ai_status not in ("ok", "unchanged"):
                    st.info(f"AI remarks were not regenerated: {ai_status}")
                st.rerun()

with tab_delete:
    st.subheader("Delete a patient record")
    rows = list_patients()
    if not rows:
        st.info("There are no records to delete.")
    else:
        options = {f"ID {r['id']} — {r['full_name']} ({r['email']})": r["id"] for r in rows}
        chosen_label = st.selectbox("Choose a record to delete", list(options.keys()), key="delete_choice")
        target_id = options[chosen_label]
        target = get_patient(target_id)
        st.write(f"You selected **{target['full_name']}**, email **{target['email']}**.")
        confirm = st.checkbox("I understand this permanently deletes the selected record.", key="confirm_delete")
        if st.button("Delete selected record", type="primary", disabled=not confirm):
            delete_patient(target_id)
            st.success("Record deleted.")
            st.rerun()
        st.caption("After deletion, open the Read records tab to see the remaining records.")

with tab_test:
    st.subheader("Run the assignment's supplied test data")
    st.write(
        "This imports the ten rows exactly as supplied in the assignment. Dates in this test-data file use "
        "the original dd.mm.yyyy notation; the normal entry form uses the required dd/mm/yyyy notation. "
        "The original values are not silently corrected."
    )
    st.info(
        "Expected validation outcomes: Test 2 has an invalid email; Test 4 has an impossible calendar date; "
        "Test 6 duplicates Test 1; Test 8 has a future date of birth and an invalid email. Other numeric "
        "values are accepted as entered, even when they may be medically unusual."
    )
    if st.button("Process supplied 10 test rows", type="primary"):
        import csv
        from pathlib import Path
        test_path = Path(__file__).parent / "test_data.csv"
        results = []
        with test_path.open("r", encoding="utf-8-sig", newline="") as f:
            test_rows = list(csv.DictReader(f))
        for row in test_rows:
            test_no = row["test_no"]
            raw = {
                "full_name": row["full_name"],
                "date_of_birth": row["date_of_birth"],
                "email": row["email"],
                "glucose": row["glucose"],
                "haemoglobin": row["haemoglobin"],
                "cholesterol": row["cholesterol"],
            }
            errors, clean = validate_import_row(raw)
            if errors:
                message = "; ".join(errors)
                log_import_result(test_no, raw, "Rejected", message)
                results.append({"Test #": test_no, "Name": raw["full_name"], "Result": "Rejected", "Reason": message})
                continue
            if patient_exists(clean):
                message = "Duplicate record: matching name, date of birth and email already exists."
                log_import_result(test_no, raw, "Rejected", message)
                results.append({"Test #": test_no, "Name": raw["full_name"], "Result": "Rejected", "Reason": message})
                continue
            remarks, ai_status = generate_health_remarks(clean)
            new_id = create_patient(clean, remarks)
            message = f"Saved as record ID {new_id}"
            if ai_status != "ok":
                message += f"; AI service status: {ai_status}"
            log_import_result(test_no, raw, "Created", message)
            results.append({"Test #": test_no, "Name": raw["full_name"], "Result": "Created", "Reason": message})
        st.session_state["last_import_results"] = results
        st.rerun()

    if "last_import_results" in st.session_state:
        st.subheader("Latest import results")
        st.dataframe(pd.DataFrame(st.session_state["last_import_results"]), use_container_width=True, hide_index=True)
    st.subheader("Persistent import / validation log")
    logs = list_import_logs()
    if logs:
        log_df = pd.DataFrame(logs).rename(columns={
            "test_no": "Test #", "full_name": "Full Name", "status": "Status",
            "message": "Validation / Processing Result", "created_at": "Logged At",
            "raw_date_of_birth": "Original DOB", "raw_email": "Original Email"
        })
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No test-data import has been run yet.")

st.divider()
st.caption("Gemini remarks are informational, not a medical diagnosis. Do not enter real patient data into a demo without appropriate privacy and security controls.")
