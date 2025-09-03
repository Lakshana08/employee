from flask import Blueprint, jsonify, request,session
from db import employees
from functools import wraps
from utils import token_required
from compute import calculate_age, calculate_experience, calculate_work_hours,calculate_salary, get_amenities, calculate_leaves, mark_attendance
from werkzeug.security import generate_password_hash, check_password_hash
import secrets, hashlib

#generate_password_hash() - encrypts passwords before storing.
#check_password_hash() - checks entered password against stored hash.

# Create a blueprint object
employee_bp = Blueprint("employee_bp", __name__)

# GET all or one employee
@employee_bp.get("/employees")
def get_employees():
    emp_id = request.args.get("id")
    if emp_id:
        emp_id = int(emp_id)
        employee = employees.get(emp_id)
        if employee:
            emp_copy = employees[emp_id].copy() 
            emp_copy["age"] = calculate_age(emp_copy["dob"])
            emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
            emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
            emp_copy["salary_computed"] = calculate_salary(emp_copy.get("in_time"), emp_copy.get("out_time"))
            emp_copy["amenities"] = get_amenities(emp_copy["experience"])
            emp_copy["leave_info"] = calculate_leaves(emp_copy)
            return jsonify({str(emp_id): emp_copy})
        else:
            return jsonify({"error": "Employee not found"}), 404

    employees_with_extra = {}
    for emp_id, emp in employees.items():
        emp_copy = employees[emp_id].copy() 
        emp_copy["age"] = calculate_age(emp_copy["dob"])
        emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
        emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
        emp_copy["salary_computed"] = calculate_salary(emp_copy.get("in_time"), emp_copy.get("out_time"))
        emp_copy["amenities"] = get_amenities(emp_copy["experience"])
        emp_copy["leave_info"] = calculate_leaves(emp_copy)
        employees_with_extra[emp_id] = emp_copy
    return jsonify(employees_with_extra)

# POST add employee
@employee_bp.post("/add_employee")
@token_required(required_role="HR")
def add_employee():
    data = request.get_json()
    emp_id = int(data["id"])
    if emp_id in employees:
        return jsonify({"error": "Employee with this ID already exists"}), 400

    # Hash password
    password = data.get("password")
    hashed_password = generate_password_hash(password) if password else None

    raw_token = secrets.token_hex(16)  # generate raw token
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()  # hash it


    employees[emp_id] = {
        "id": emp_id,
        "name": data["name"],
        "dob": data["dob"],
        "department": data["department"],
        "date_of_joining": data["date_of_joining"],
        "ongoing_project": data.get("ongoing_project", []),
        "completed_project": data.get("completed_project", []),
        "employee_of_month_count": data.get("employee_of_month_count", 0),
        "in_time": data.get("in_time"),
        "out_time": data.get("out_time"),
        "present_days": [],
        "password": hashed_password,
        "token_hash": token_hash,
        "address": data.get("address", ""),
        "email": data.get("email", "")
    }

    mark_attendance(employees[emp_id], data.get("in_time"), data.get("out_time"))

    emp_copy = employees[emp_id].copy() 
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["salary_computed"] = calculate_salary(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["amenities"] = get_amenities(emp_copy["experience"])
    emp_copy["leave_info"] = calculate_leaves(emp_copy)

    return jsonify({
        "message": "Employee added successfully",
        "employee": emp_copy,
        "token": raw_token
    }), 201

# PUT update employee
@employee_bp.put("/update_employee/<int:emp_id>")
@token_required(required_role=None)
def update_employee(emp_id):
    if emp_id not in employees:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json()
    employees[emp_id].update(data)
    mark_attendance(employees[emp_id], data.get("in_time"), data.get("out_time"))

    emp_copy = employees[emp_id].copy() 
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["salary_computed"] = calculate_salary(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["amenities"] = get_amenities(emp_copy["experience"])
    emp_copy["leave_info"] = calculate_leaves(emp_copy)

    return jsonify({"message": "Employee updated successfully", "employee": emp_copy})

# DELETE employee
@employee_bp.delete("/delete_employee/<int:emp_id>")
@token_required(required_role="HR")
def delete_employee(emp_id):
    if emp_id in employees:
        employees.pop(emp_id)
        return jsonify({"message": "Employee deleted successfully"})
    else:
        return jsonify({"message": "Employee not found"}), 404

#  GET employee with sections
@employee_bp.get("/employee/<int:emp_id>", defaults={"section": None})
@employee_bp.get("/employee/<int:emp_id>/<section>")
@token_required(required_role=None)
def get_employee_sections(emp_id, section):
    if emp_id not in employees:
        return jsonify({"error": "Employee not found"}), 404

    emp_copy = employees[emp_id].copy() 
    emp_copy["age"] = calculate_age(emp_copy["dob"])
    emp_copy["experience"] = calculate_experience(emp_copy["date_of_joining"])
    emp_copy["work_hours"] = calculate_work_hours(emp_copy.get("in_time"), emp_copy.get("out_time"))
    emp_copy["salary_computed"] = calculate_salary(emp_copy.get("in_time"), emp_copy.get("out_time"))
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
        "amenities": emp_copy["amenities"],
        "in_time": emp_copy.get("in_time"),
        "out_time": emp_copy.get("out_time"),
        "work_hours": emp_copy["work_hours"],
        "salary":emp_copy["salary_computed"],
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
