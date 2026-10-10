import json
import os
from pathlib import Path

import docx
import PyPDF2
from flask import Flask, render_template, request, redirect, session, url_for
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

from db import Base, engine, SessionLocal
import model
from ai import analyze_resume

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")

# Create tables when the application starts.
Base.metadata.create_all(bind=engine)


def extract_resume_text(uploaded_file):
    """Extract text from an uploaded PDF or DOCX file."""
    filename = (uploaded_file.filename or "").lower()
    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if filename.endswith(".docx"):
        document = docx.Document(uploaded_file)
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    raise ValueError("Please upload a PDF or DOCX file.")


@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not email or not password:
                return render_template("signup.html", error="Email and password are required.")
            if db.query(model.User).filter_by(email=email).first():
                return render_template("signup.html", error="An account with this email already exists.")
            db.add(model.User(email=email, password=password))
            db.commit()
            return redirect(url_for("login"))
        return render_template("signup.html")
    except SQLAlchemyError:
        db.rollback()
        app.logger.exception("Signup database error")
        return render_template("signup.html", error="Could not create the account. Check the database connection.")
    finally:
        db.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = db.query(model.User).filter_by(email=email, password=password).first()
            if user:
                session["user"] = user.email
                return redirect(url_for("dashboard"))
            return render_template("login.html", error="Invalid email or password.")
        return render_template("login.html")
    except SQLAlchemyError:
        app.logger.exception("Login database error")
        return render_template("login.html", error="Could not connect to the database.")
    finally:
        db.close()


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    result = None
    if request.method == "POST":
        user_goal = request.form.get("role", "").strip()
        resume_text = request.form.get("resume", "").strip()
        uploaded_file = request.files.get("file")

        if uploaded_file and uploaded_file.filename:
            try:
                resume_text = extract_resume_text(uploaded_file)
            except Exception as exc:
                result = {"error": str(exc)}

        if not result and (not resume_text or not user_goal):
            result = {"error": "Paste your resume or upload a PDF/DOCX, and enter your target role."}

        if not result:
            result = analyze_resume(resume_text, user_goal)
            if "error" not in result:
                db = SessionLocal()
                try:
                    user = db.query(model.User).filter_by(email=session["user"]).first()
                    if user is None:
                        session.pop("user", None)
                        return redirect(url_for("login"))
                    report = model.Reports(
                        user_id=user.id,
                        resume_text=resume_text,
                        result=json.dumps(result),
                    )
                    db.add(report)
                    db.commit()
                except SQLAlchemyError:
                    db.rollback()
                    app.logger.exception("Could not save report")
                    result["save_warning"] = "Analysis completed, but the report could not be saved. Check your database connection."
                finally:
                    db.close()

    return render_template("dashboard.html", user=session["user"], result=result)


@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))

    db = SessionLocal()
    try:
        user = db.query(model.User).filter_by(email=session["user"]).first()
        if user is None:
            session.pop("user", None)
            return redirect(url_for("login"))
        reports = db.query(model.Reports).filter_by(user_id=user.id).order_by(model.Reports.id.desc()).all()
        parsed_reports = []
        for report in reports:
            try:
                parsed_result = json.loads(report.result or "{}")
            except (json.JSONDecodeError, TypeError):
                parsed_result = {}
            parsed_reports.append({"resume": report.resume_text or "", "result": parsed_result})
        return render_template("history.html", reports=parsed_reports)
    except SQLAlchemyError:
        app.logger.exception("History database error")
        return render_template("history.html", reports=[], error="Could not load history. Check the database connection.")
    finally:
        db.close()


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
