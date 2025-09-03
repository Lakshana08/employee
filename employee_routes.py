from flask import Blueprint, jsonify, request
from db import employees
from compute import calculate_age, calculate_experience, calculate_work_hours,calculate_salary, get_amenities, calculate_leaves, mark_attendance
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity

#generate_password_hash() - encrypts passwords before storing.
#check_password_hash() - checks entered password against stored hash.

# Create a blueprint object
employee_bp = Blueprint("employee_bp", __name__)

def build_employee_profile(emp):
    emp_copy = emp.copy()
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["salary_computed"] = calculate_salary(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["amenities"] = get_amenities(emp_copy["experience"])
    emp_copy["leave_info"] = calculate_leaves(emp_copy)
    return emp_copy

#login
@employee_bp.post("/login")
def login():
    data = request.get_json()
    emp_id = int(data.get("id"))
    password = data.get("password")

    emp = employees.get(emp_id)
    if not emp or not emp.get("password"):
        return jsonify({"message": "Invalid credentials"}), 401

    if not check_password_hash(emp["password"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(
    identity=str(emp_id),   # subject must be string
    additional_claims={"role": emp["role"]}
    )

    return jsonify({"access_token": token})

# GET all or one employee - HR only
@employee_bp.get("/employees")
@jwt_required()
def get_employees():
    if get_jwt():
        claims = get_jwt()
        if claims.get("role") != "HR":
            return jsonify({"message": "Only HR can view employee details"}), 403

        emp_id = request.args.get("id")
        if emp_id:
            emp_id = int(emp_id)
            employee = employees.get(emp_id)
            if employee:
                emp_copy = build_employee_profile(employees[emp_id])
                return jsonify({str(emp_id): emp_copy})
            else:
                return jsonify({"error": "Employee not found"}), 404

        employees_with_extra = {}
        for emp_id, emp in employees.items():
            emp_copy = build_employee_profile(employees[emp_id])
            employees_with_extra[str(emp_id)] = emp_copy
        return jsonify(employees_with_extra)
    
    else:
        return {"msg": "token not sent"}

# POST add employee
@employee_bp.post("/add_employee")
@jwt_required()
def add_employee():
    claims = get_jwt()
    if claims.get("role") != "HR":   # only HR can add
        return jsonify({"message": "HR only!"}), 403
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
        "role": data["role"],
        "department": data["department"],
        "date_of_joining": data["date_of_joining"],
        "ongoing_project": data.get("ongoing_project", []),
        "completed_project": data.get("completed_project", []),
        "in_time": data.get("in_time"),
        "out_time": data.get("out_time"),
        "present_days": [],
        "password": hashed_password,
        "address": data.get("address", ""),
        "email": data.get("email", "")
    }


    mark_attendance(employees[emp_id], data.get("in_time"), data.get("out_time"))
    emp_copy = build_employee_profile(employees[emp_id])
    return jsonify({
    "message": "Employee added successfully",
    "employee": emp_copy,
    }), 201


# PUT update employee
@employee_bp.put("/update_employee/<int:emp_id>")
@jwt_required()
def update_employee(emp_id):
    if emp_id not in employees:
        return jsonify({"error": "Employee not found"}), 404
    
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    if claims.get("role") != "HR" and current_user_id != emp_id:
        return jsonify({"message": "Not authorized to update other employees"}), 403

    data = request.get_json()
    if "password" in data:
        data["password"] = generate_password_hash(data["password"])
    employees[emp_id].update(data)
    mark_attendance(employees[emp_id], data.get("in_time"), data.get("out_time"))

    emp_copy = build_employee_profile(employees[emp_id])

    return jsonify({"message": "Employee updated successfully", "employee": emp_copy})

# DELETE employee
@employee_bp.delete("/delete_employee/<int:emp_id>")
@jwt_required()
def delete_employee(emp_id):
    claims = get_jwt()
    if claims.get("role") != "HR":   # only HR can add
        return jsonify({"message": "HR only!"}), 403
    if emp_id in employees:
        employees.pop(emp_id)
        return jsonify({"message": "Employee deleted successfully"})
    else:
        return jsonify({"message": "Employee not found"}), 404

#  GET employee with sections
@employee_bp.get("/employee/<int:emp_id>", defaults={"section": None})
@employee_bp.get("/employee/<int:emp_id>/<section>")
@jwt_required()
def get_employee_sections(emp_id, section):
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())

    # Restrict personal details
    if section == "personal":
        if claims.get("role") != "HR" and current_user_id != emp_id:
            return jsonify({"message": "Not authorized to view other employee's personal details"}), 403
    if emp_id not in employees:
        return jsonify({"error": "Employee not found"}), 404
    
    # Restrict professional details
    if section == "professional":
        allowed_roles = ["HR", "Manager", "Team Leader"]
        if claims.get("role") not in allowed_roles and current_user_id != emp_id:
            return jsonify({"message": "Not authorized to view other employee's professional details"}), 403


    emp_copy = build_employee_profile(employees[emp_id])

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
        "amenities": emp_copy["amenities"],
        "in_time": emp_copy.get("in_time"),
        "out_time": emp_copy.get("out_time"),
        "work_hours": emp_copy["work_hours"],
        "salary":emp_copy["salary_computed"],
        "leave_info": emp_copy["leave_info"],
        "ongoing_project": emp_copy.get("ongoing_project", []),
        "completed_project": emp_copy.get("completed_project", []),
    }

    if section == "personal":
        return jsonify({"personal": personal_fields})
    elif section == "professional":
        return jsonify({"professional": professional_fields})
    else:
        personal_allowed = claims.get("role") == "HR" or current_user_id == emp_id
        professional_allowed = claims.get("role") in ["HR", "Manager", "Team Leader"] or current_user_id == emp_id

        result = {}
        if personal_allowed:
            result["personal"] = personal_fields
        if professional_allowed:
            result["professional"] = professional_fields

        if not result:
            return jsonify({"message": "Not authorized to view this employee's details"}), 403

        return jsonify(result)

