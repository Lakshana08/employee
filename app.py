from flask import Flask
from employee_routes import employee_bp   # import blueprint
app = Flask(__name__)

app.register_blueprint(employee_bp, url_prefix="/employee")

if __name__ == "__main__":
    app.run(debug=True) 