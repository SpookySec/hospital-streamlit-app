import streamlit as st
import db
from datetime import datetime

st.set_page_config(page_title="Hospital System", layout="wide")

# Top-level page selector
page = st.sidebar.radio("Page", ["Home", "Manage"])


def home_page():
    st.title("Hospital System")
    if st.button("Init DB (create tables)"):
        db.init_db()
        st.success("Database initialized (schema applied).")

    with st.sidebar.expander("Quick add"):
        st.subheader("Add patient")
        fn = st.text_input("First name", key="q_fn")
        ln = st.text_input("Last name", key="q_ln")
        if st.button("Add patient (quick)"):
            if fn and ln:
                pid = db.add_patient(fn, ln)
                st.success(f"Added patient id={pid}")
            else:
                st.error("Provide first and last name")

    st.header("Patients")
    patients = db.list_patients()
    if patients:
        for p in patients:
            st.write(f"{p['id']}: {p['first_name']} {p['last_name']} — {p.get('dob')} — {p.get('email')}")
    else:
        st.info("No patients yet. Add one from Manage -> Patients")

    # Show doctors
    st.header("Doctors")
    doctors = db.list_doctors()
    if doctors:
        for d in doctors:
            st.write(f"{d['id']}: Dr. {d['first_name']} {d['last_name']} — {d.get('department_name')} — {d.get('email')}")
    else:
        st.info("No doctors yet. Add one from Manage -> Doctors")

    # Schedule appointment form
    st.header("Schedule Appointment")
    patients = db.list_patients()
    doctors = db.list_doctors()
    dept_list = db.list_departments()

    with st.form("schedule_appointment"):
        if patients:
            patient_options = {f"{p['id']}: {p['first_name']} {p['last_name']}": p['id'] for p in patients}
            patient_label = st.selectbox("Patient", list(patient_options.keys()))
            pid = patient_options[patient_label]
        else:
            st.warning("Create a patient first.")
            pid = None

        if doctors:
            doctor_options = {f"{d['id']}: Dr. {d['first_name']} {d['last_name']}": d['id'] for d in doctors}
            doctor_label = st.selectbox("Doctor (optional)", [""] + list(doctor_options.keys()))
            doc_id = doctor_options[doctor_label] if doctor_label and doctor_label != "" else None
        else:
            doc_id = None

        dept_opts = {f"{d['id']}: {d['name']}": d['id'] for d in dept_list}
        dept_label = st.selectbox("Department (optional)", [""] + list(dept_opts.keys()))
        dept_id = dept_opts[dept_label] if dept_label and dept_label != "" else None

        start_date = st.date_input("Start date")
        start_time = st.time_input("Start time")
        reason = st.text_input("Reason")
        submit_appt = st.form_submit_button("Schedule")
        if submit_appt:
            if not pid:
                st.error("No patient selected.")
            else:
                dt_start = datetime.combine(start_date, start_time).isoformat()
                aid = db.add_appointment(pid, doc_id, dept_id, dt_start, None, reason or None)
                st.success(f"Appointment scheduled (id={aid})")

    st.header("Appointments")
    appts = db.list_appointments()
    if appts:
        # Render as table for compact view
        rows = []
        for a in appts:
            rows.append({
                "id": a["id"],
                "patient": f"{a['patient_first']} {a['patient_last']}",
                "doctor": (f"Dr. {a['doctor_first']} {a['doctor_last']}" if a.get('doctor_first') else "(none)"),
                "department": a.get('department_name') or '(none)',
                "start_time": a['start_time'],
                "status": a['status'],
                "reason": a.get('reason') or "",
            })
        st.table(rows)
    else:
        st.info("No appointments yet.")


def manage_page():
    st.title("Manage — Hospital Data")
    tabs = st.tabs(["Patients", "Doctors", "Departments", "Appointments"])  # 4 tabs

    # Patients tab
    with tabs[0]:
        st.header("Patients")
        patients = db.list_patients()
        st.dataframe(patients)

        with st.expander("Add patient"):
            fn = st.text_input("First name", key="m_fn")
            ln = st.text_input("Last name", key="m_ln")
            dob = st.text_input("DOB (YYYY-MM-DD)", key="m_dob")
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], key="m_gender")
            phone = st.text_input("Phone", key="m_phone")
            email = st.text_input("Email", key="m_email")
            if st.button("Add patient", key="m_add_patient"):
                if fn and ln:
                    db.add_patient(fn, ln, dob or None, gender or None, phone or None, email or None)
                    st.rerun()
                else:
                    st.error("First and last name required")

        with st.expander("Update / Delete patient"):
            patients = db.list_patients()
            options = {f"{p['id']}: {p['first_name']} {p['last_name']}": p['id'] for p in patients}
            sel = st.selectbox("Select patient", [""] + list(options.keys()), key="m_sel_patient")
            if sel:
                pid = options[sel]
                p = db.get_patient(pid)
                new_fn = st.text_input("First name", value=p['first_name'], key="u_fn")
                new_ln = st.text_input("Last name", value=p['last_name'], key="u_ln")
                new_dob = st.text_input("DOB (YYYY-MM-DD)", value=p.get('dob') or "", key="u_dob")
                new_gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=(0), key="u_gender")
                new_phone = st.text_input("Phone", value=p.get('phone') or "", key="u_phone")
                new_email = st.text_input("Email", value=p.get('email') or "", key="u_email")
                if st.button("Update patient"):
                    db.update_patient(pid, new_fn, new_ln, new_dob or None, new_gender or None, new_phone or None, new_email or None)
                    st.success("Updated")
                    st.rerun()
                if st.button("Delete patient"):
                    db.delete_patient(pid)
                    st.success("Deleted")
                    st.rerun()

    # Doctors tab
    with tabs[1]:
        st.header("Doctors")
        st.dataframe(db.list_doctors())
        with st.expander("Add doctor"):
            d_fn = st.text_input("First name", key="ad_fn")
            d_ln = st.text_input("Last name", key="ad_ln")
            depts = db.list_departments()
            dept_map = {f"{d['id']}: {d['name']}": d['id'] for d in depts}
            dept_sel = st.selectbox("Department (optional)", [""] + list(dept_map.keys()), key="ad_dept")
            d_email = st.text_input("Email", key="ad_email")
            if st.button("Add doctor", key="ad_add"):
                dept_id = dept_map[dept_sel] if dept_sel else None
                db.add_doctor(d_fn, d_ln, dept_id, d_email or None)
                st.rerun()

        with st.expander("Update / Delete doctor"):
            docs = db.list_doctors()
            opts = {f"{d['id']}: Dr. {d['first_name']} {d['last_name']}": d['id'] for d in docs}
            sel = st.selectbox("Select doctor", [""] + list(opts.keys()), key="ud_sel")
            if sel:
                did = opts[sel]
                doc = db.get_doctor(did)
                nf = st.text_input("First name", value=doc['first_name'], key="ud_fn")
                nl = st.text_input("Last name", value=doc['last_name'], key="ud_ln")
                dept_map = {f"{d['id']}: {d['name']}": d['id'] for d in db.list_departments()}
                dept_choice = st.selectbox("Department", [""] + list(dept_map.keys()), key="ud_dept")
                ne = st.text_input("Email", value=doc.get('email') or "", key="ud_email")
                if st.button("Update doctor"):
                    dept_id = dept_map[dept_choice] if dept_choice else None
                    db.update_doctor(did, nf, nl, dept_id, ne or None)
                    st.success("Updated")
                    st.rerun()
                if st.button("Delete doctor"):
                    db.delete_doctor(did)
                    st.success("Deleted")
                    st.rerun()

    # Departments tab
    with tabs[2]:
        st.header("Departments")
        st.dataframe(db.list_departments())
        with st.expander("Add department"):
            dn = st.text_input("Name", key="adn")
            if st.button("Add department", key="adn_add"):
                if dn:
                    db.add_department(dn)
                    st.rerun()
                else:
                    st.error("Name required")

        with st.expander("Update / Delete department"):
            deps = db.list_departments()
            opts = {f"{d['id']}: {d['name']}": d['id'] for d in deps}
            sel = st.selectbox("Select department", [""] + list(opts.keys()), key="upd_dep")
            if sel:
                did = opts[sel]
                dep = db.get_department(did)
                new_name = st.text_input("Name", value=dep['name'], key="upd_dep_name")
                if st.button("Update department"):
                    db.update_department(did, new_name)
                    st.success("Updated")
                    st.rerun()
                if st.button("Delete department"):
                    db.delete_department(did)
                    st.success("Deleted")
                    st.rerun()

    # Appointments tab
    with tabs[3]:
        st.header("Appointments")
        appts = db.list_appointments()
        # Present full table
        st.dataframe([{
            'id': a['id'],
            'patient': f"{a['patient_first']} {a['patient_last']}",
            'doctor': (f"Dr. {a['doctor_first']} {a['doctor_last']}" if a.get('doctor_first') else '(none)'),
            'department': a.get('department_name') or '(none)',
            'start_time': a['start_time'],
            'status': a['status'],
            'reason': a.get('reason') or ''
        } for a in appts])

        with st.expander("Add appointment"):
            pats = db.list_patients()
            docs = db.list_doctors()
            deps = db.list_departments()
            pat_map = {f"{p['id']}: {p['first_name']} {p['last_name']}": p['id'] for p in pats}
            doc_map = {f"{d['id']}: Dr. {d['first_name']} {d['last_name']}": d['id'] for d in docs}
            dep_map = {f"{d['id']}: {d['name']}": d['id'] for d in deps}
            pat_sel = st.selectbox("Patient", list(pat_map.keys()), key="ap_pat")
            doc_sel = st.selectbox("Doctor (optional)", [""] + list(doc_map.keys()), key="ap_doc")
            dep_sel = st.selectbox("Department (optional)", [""] + list(dep_map.keys()), key="ap_dep")
            start = st.text_input("Start datetime (ISO)", value=datetime.now().isoformat(), key="ap_start")
            reason = st.text_input("Reason", key="ap_reason")
            if st.button("Add appointment", key="ap_add"):
                pid = pat_map[pat_sel]
                did = doc_map[doc_sel] if doc_sel else None
                didep = dep_map[dep_sel] if dep_sel else None
                db.add_appointment(pid, did, didep, start, None, reason or None)
                st.rerun()

        with st.expander("Update / Delete appointment"):
            ap = db.list_appointments()
            opts = {f"{a['id']}: {a['patient_first']} {a['patient_last']} @ {a['start_time']}": a['id'] for a in ap}
            sel = st.selectbox("Select appointment", [""] + list(opts.keys()), key="up_ap")
            if sel:
                aid = opts[sel]
                a = db.get_appointment(aid)
                pats = db.list_patients(); pat_map = {f"{p['id']}: {p['first_name']} {p['last_name']}": p['id'] for p in pats}
                docs = db.list_doctors(); doc_map = {f"{d['id']}: Dr. {d['first_name']} {d['last_name']}": d['id'] for d in docs}
                deps = db.list_departments(); dep_map = {f"{d['id']}: {d['name']}": d['id'] for d in deps}
                pat_choice = st.selectbox("Patient", list(pat_map.keys()), index=0, key="up_ap_pat")
                doc_choice = st.selectbox("Doctor (optional)", [""] + list(doc_map.keys()), key="up_ap_doc")
                dep_choice = st.selectbox("Department (optional)", [""] + list(dep_map.keys()), key="up_ap_dep")
                start = st.text_input("Start datetime (ISO)", value=a['start_time'], key="up_ap_start")
                status = st.text_input("Status", value=a.get('status') or 'scheduled', key="up_ap_status")
                reason = st.text_input("Reason", value=a.get('reason') or '', key="up_ap_reason")
                if st.button("Update appointment"):
                    pid = pat_map[pat_choice]
                    did = doc_map[doc_choice] if doc_choice else None
                    depid = dep_map[dep_choice] if dep_choice else None
                    db.update_appointment(aid, pid, did, depid, start, None, status or 'scheduled', reason or None)
                    st.success("Updated")
                    st.rerun()
                if st.button("Delete appointment"):
                    db.delete_appointment(aid)
                    st.success("Deleted")
                    st.rerun()


if page == "Home":
    home_page()
else:
    manage_page()
