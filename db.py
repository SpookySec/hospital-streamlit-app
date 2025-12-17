import sqlite3
from typing import List, Dict, Any, Optional
import faker

DB_PATH = "hospital.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(schema_path: str = "schema.sql") -> None:
    conn = get_conn()
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    
    fake = faker.Faker()
    # Insert sample departments
    departments = ["Cardiology", "Neurology", "Pediatrics", "Oncology", "Emergency"]
    for dept in departments:
        conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))

    # Insert sample doctors
    for _ in range(10):
        first_name = fake.first_name()
        last_name = fake.last_name()
        department_id = conn.execute("SELECT id FROM departments ORDER BY RANDOM() LIMIT 1").fetchone()[0]
        email = fake.email()
        conn.execute(
            "INSERT INTO doctors (first_name, last_name, department_id, email) VALUES (?, ?, ?, ?)",
            (first_name, last_name, department_id, email),
        )

    # Insert sample patients
    for _ in range(20):
        first_name = fake.first_name()
        last_name = fake.last_name()
        dob = fake.date_of_birth(minimum_age=0, maximum_age=90).isoformat()
        gender = fake.random_element(elements=("Male", "Female"))
        phone = fake.phone_number()
        email = fake.email()
        conn.execute(
            "INSERT INTO patients (first_name, last_name, dob, gender, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, dob, gender, phone, email),
        )
    
    # Insert sample appointments
    patient_ids = [row["id"] for row in conn.execute("SELECT id FROM patients").fetchall()]
    doctor_ids = [row["id"] for row in conn.execute("SELECT id FROM doctors").fetchall()]
    department_ids = [row["id"] for row in conn.execute("SELECT id FROM departments").fetchall()]

    for _ in range(30):
        patient_id = fake.random_element(elements=patient_ids)
        doctor_id = fake.random_element(elements=doctor_ids)
        department_id = fake.random_element(elements=department_ids)
        start_time = fake.date_time_between(start_date='-30d')
        end_time = fake.date_time_between(start_date=start_time).isoformat()
        reason = fake.sentence(nb_words=6)
        conn.execute(
            "INSERT INTO appointments (patient_id, doctor_id, department_id, start_time, end_time, reason) VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, doctor_id, department_id, start_time, end_time, reason),
        )

    conn.commit()
    conn.close()


# Patients

def add_patient(first_name: str, last_name: str, dob: Optional[str] = None, gender: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO patients (first_name, last_name, dob, gender, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
        (first_name, last_name, dob, gender, phone, email),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def list_patients() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM patients ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_patient(patient_id: int, first_name: str, last_name: str, dob: Optional[str], gender: Optional[str], phone: Optional[str], email: Optional[str]) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE patients SET first_name = ?, last_name = ?, dob = ?, gender = ?, phone = ?, email = ? WHERE id = ?",
        (first_name, last_name, dob, gender, phone, email, patient_id),
    )
    conn.commit()
    conn.close()


def delete_patient(patient_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()


# Departments

def add_department(name: str) -> int:
    conn = get_conn()
    cur = conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
    conn.commit()
    # If it was ignored, fetch the id
    if cur.lastrowid:
        did = cur.lastrowid
    else:
        did = conn.execute("SELECT id FROM departments WHERE name = ?", (name,)).fetchone()[0]
    conn.close()
    return did


def list_departments() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM departments ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_department(department_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM departments WHERE id = ?", (department_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_department(department_id: int, name: str) -> None:
    conn = get_conn()
    conn.execute("UPDATE departments SET name = ? WHERE id = ?", (name, department_id))
    conn.commit()
    conn.close()


def delete_department(department_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM departments WHERE id = ?", (department_id,))
    conn.commit()
    conn.close()


# Doctors

def add_doctor(first_name: str, last_name: str, department_id: Optional[int] = None, email: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO doctors (first_name, last_name, department_id, email) VALUES (?, ?, ?, ?)",
        (first_name, last_name, department_id, email),
    )
    conn.commit()
    did = cur.lastrowid
    conn.close()
    return did


def list_doctors() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT d.*, dep.name as department_name FROM doctors d LEFT JOIN departments dep ON d.department_id = dep.id ORDER BY d.last_name"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_doctor(doctor_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_doctor(doctor_id: int, first_name: str, last_name: str, department_id: Optional[int], email: Optional[str]) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE doctors SET first_name = ?, last_name = ?, department_id = ?, email = ? WHERE id = ?",
        (first_name, last_name, department_id, email, doctor_id),
    )
    conn.commit()
    conn.close()


def delete_doctor(doctor_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
    conn.commit()
    conn.close()


# Appointments

def add_appointment(patient_id: int, doctor_id: Optional[int], department_id: Optional[int], start_time: str, end_time: Optional[str] = None, reason: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO appointments (patient_id, doctor_id, department_id, start_time, end_time, reason) VALUES (?, ?, ?, ?, ?, ?)",
        (patient_id, doctor_id, department_id, start_time, end_time, reason),
    )
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def list_appointments() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT a.*, p.first_name as patient_first, p.last_name as patient_last,
               d.first_name as doctor_first, d.last_name as doctor_last, dep.name as department_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN departments dep ON a.department_id = dep.id
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_appointment(appointment_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_appointment(appointment_id: int, patient_id: int, doctor_id: Optional[int], department_id: Optional[int], start_time: str, end_time: Optional[str], status: Optional[str], reason: Optional[str]) -> None:
    conn = get_conn()
    conn.execute(
        """
        UPDATE appointments SET patient_id = ?, doctor_id = ?, department_id = ?, start_time = ?, end_time = ?, status = ?, reason = ? WHERE id = ?
        """,
        (patient_id, doctor_id, department_id, start_time, end_time, status, reason, appointment_id),
    )
    conn.commit()
    conn.close()


def delete_appointment(appointment_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()
