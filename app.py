from flask import Flask, request, jsonify
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash, check_password_hash

#generate_password_hash() - encrypts passwords before storing.
#check_password_hash() - checks entered password against stored hash.

app = Flask(__name__)

employees = {}

PUBLIC_HOLIDAYS = {
    date(2025, 1, 26),
    date(2025, 8, 15),
    date(2025, 10, 2),
}

#  Calculate age from DOB
def calculate_age(dob_str):
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    diff = relativedelta(today, dob)
    return diff.years

#  Calculate experience from date of joining
def calculate_experience(doj_str):
    doj = datetime.strptime(doj_str, "%Y-%m-%d").date()
    today = date.today()
    diff = relativedelta(today, doj)
    return {"years": diff.years, "months": diff.months, "days": diff.days}

#  Calculate work hours and overtime
def calculate_work_hours(in_time, out_time):
    if not in_time or not out_time:
        return {"hours_worked": 0, "overtime": 0}
    try:
        in_t = datetime.strptime(in_time, "%H:%M")
        out_t = datetime.strptime(out_time, "%H:%M")
        worked_hours = (out_t - in_t).seconds / 3600
        overtime = max(0, worked_hours - 8)
        return {"hours_worked": round(worked_hours, 2), "overtime": round(overtime, 2)}
    except:
        return {"hours_worked": 0, "overtime": 0}

#  Provide amenities based on experience
def get_amenities(experience):
    if experience["years"] >= 2:
        return ["Laptop", "Bag", "Mouse", "Headphone"]
    else:
        return ["No amenities provided"]

#  Calculate leaves
def calculate_leaves(emp):
    today = date.today()
    year, month = today.year, today.month
    first_day = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    days_in_month = (next_month - first_day).days

    working_days = []
    for i in range(days_in_month):
        day = first_day + timedelta(days=i)
        if day.weekday() < 5 and day not in PUBLIC_HOLIDAYS:
            if day <= date.today():
                working_days.append(day.strftime("%Y-%m-%d"))

    present_days = emp.get("present_days", [])
    leaves = len(set(working_days) - set(present_days))

    return {"month": f"{year}-{month}", "total_working_days": len(working_days),
            "present_days": len(present_days), "leaves": leaves}

#  Auto mark attendance
def mark_attendance(emp, in_time, out_time):
    if in_time and out_time:
        today_str = date.today().strftime("%Y-%m-%d")
        if "present_days" not in emp:
            emp["present_days"] = []
        if today_str not in emp["present_days"]:
            emp["present_days"].append(today_str)

#  Helper to mask password
def mask_password(emp):
    emp_copy = emp.copy()
    emp_copy["password"] = "-"
    return emp_copy

# GET all or one employee
@app.get("/employees")
def get_employees():
    emp_id = request.args.get("id")
    if emp_id:
        emp_id = int(emp_id)
        employee = employees.get(emp_id)
        if employee:
            emp_copy = mask_password(employee)
            emp_copy["age"] = calculate_age(emp_copy["dob"])
            emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
            emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
            emp_copy["amenities"] = get_amenities(emp_copy["experience"])
            emp_copy["leave_info"] = calculate_leaves(emp_copy)
            return jsonify({str(emp_id): emp_copy})
        else:
            return jsonify({"error": "Employee not found"}), 404

    employees_with_extra = {}
    for emp_id, emp in employees.items():
        emp_copy = mask_password(emp)
        emp_copy["age"] = calculate_age(emp_copy["dob"])
        emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
        emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
        emp_copy["amenities"] = get_amenities(emp_copy["experience"])
        emp_copy["leave_info"] = calculate_leaves(emp_copy)
        employees_with_extra[emp_id] = emp_copy
    return jsonify(employees_with_extra)

# POST add employee
@app.post("/add_employee")
def add_employee():
    data = request.get_json()
    emp_id = int(data["id"])
    if emp_id in employees:
        return jsonify({"error": "Employee with this ID already exists"}), 400

    # Hash password
    password = data.get("password")
    hashed_password = generate_password_hash(password) if password else None

    employees[emp_id] = {
        "id": emp_id,
        "name": data["name"],
        "dob": data["dob"],
        "department": data["department"],
        "date_of_joining": data["date_of_joining"],
        "salary": data["salary"],
        "salary_credited_date": data["salary_credited_date"],
        "ongoing_project": data.get("ongoing_project", []),
        "completed_project": data.get("completed_project", []),
        "employee_of_month_count": data.get("employee_of_month_count", 0),
        "in_time": data.get("in_time"),
        "out_time": data.get("out_time"),
        "present_days": [],
        "password": hashed_password,
        "address": data.get("address", ""),
        "email": data.get("email", "")
    }

    mark_attendance(employees[emp_id], data.get("in_time"), data.get("out_time"))

    emp_copy = mask_password(employees[emp_id])
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["amenities"] = get_amenities(emp_copy["experience"])
    emp_copy["leave_info"] = calculate_leaves(emp_copy)

    return jsonify({"message": "Employee added successfully", "employee": emp_copy}), 201

# PUT update employee
@app.put("/update_employee/<int:emp_id>")
def update_employee(emp_id):
    if emp_id not in employees:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json()
    employees[emp_id].update(data)
    mark_attendance(employees[emp_id], data.get("in_time"), data.get("out_time"))

    emp_copy = mask_password(employees[emp_id])
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["amenities"] = get_amenities(emp_copy["experience"])
    emp_copy["leave_info"] = calculate_leaves(emp_copy)

    return jsonify({"message": "Employee updated successfully", "employee": emp_copy})

# DELETE employee
@app.delete("/delete_employee/<int:emp_id>")
def delete_employee(emp_id):
    if emp_id in employees:
        employees.pop(emp_id)
        return jsonify({"message": "Employee deleted successfully"})
    else:
        return jsonify({"message": "Employee not found"}), 404

#  GET employee with sections
@app.get("/employee/<int:emp_id>", defaults={"section": None})
@app.get("/employee/<int:emp_id>/<section>")
def get_employee_sections(emp_id, section):
    if emp_id not in employees:
        return jsonify({"error": "Employee not found"}), 404

    # Check password in headers for personal or combined access
    emp = employees[emp_id]
    if section in ["personal", None]:
        pw = request.headers.get("password")
        if not pw or not check_password_hash(emp["password"], pw):
            return jsonify({"error": "Password required or incorrect"}), 401

    emp_copy = mask_password(emp)
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["amenities"] = get_amenities(emp_copy["experience"])
    emp_copy["leave_info"] = calculate_leaves(emp_copy)

    personal_fields = {
        "id": emp_copy["id"],
        "name": emp_copy["name"],
        "dob": emp_copy["dob"],
        "age": emp_copy["age"],
        "department": emp_copy["department"],
        "date_of_joining": emp_copy["date_of_joining"],
        "experience": emp_copy["experience"],
        "address": emp_copy.get("address", ""),
        "email": emp_copy.get("email", "")
    }

    professional_fields = {
        "salary": emp_copy["salary"],
        "salary_credited_date": emp_copy["salary_credited_date"],
        "amenities": emp_copy["amenities"],
        "in_time": emp_copy.get("in_time"),
        "out_time": emp_copy.get("out_time"),
        "work_hours": emp_copy["work_hours"],
        "leave_info": emp_copy["leave_info"],
        "ongoing_project": emp_copy.get("ongoing_project", []),
        "completed_project": emp_copy.get("completed_project", []),
        "employee_of_month_count": emp_copy.get("employee_of_month_count", 0)
    }

    if section == "personal":
        return jsonify({"personal": personal_fields})
    elif section == "professional":
        return jsonify({"professional": professional_fields})
    else:
        return jsonify({"personal": personal_fields, "professional": professional_fields})

if __name__ == "__main__":
    app.run(debug=True)
