from flask import Flask 
from flask_jwt_extended import JWTManager
from employee_routes import employee_bp   # import blueprint

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "123890"
jwt = JWTManager(app)

app.register_blueprint(employee_bp, url_prefix="/employee")

if __name__ == "__main__":
    app.run(debug=True)
