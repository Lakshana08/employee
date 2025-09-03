from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash

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

# Calculate salary
def calculate_salary(in_time, out_time, rate_per_hour=250):
    work_hours = calculate_work_hours(in_time, out_time)
    salary = round(work_hours["hours_worked"] * rate_per_hour, 2)
    return salary

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


#print(generate_password_hash("admin@123"))