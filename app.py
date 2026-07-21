"""
RSFM Enterprise Website
Roushni Security & Facility Management

Entry point: creates the Flask application, registers routes, and wires up
the database, live Excel workbooks, two-way email notifications, and the
admin panel for both enquiries and job applications.
"""
import functools
import os
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, send_file
)

from config import config_map
from extensions import db
from models import Enquiry, JobApplication, STATUS_CHOICES
from email_utils import send_enquiry_emails, send_application_emails
from excel_utils import (
    ensure_master_workbooks,
    append_enquiry_to_live_workbook,
    append_application_to_live_workbook,
    build_enquiries_workbook,
    build_applications_workbook,
    ENQUIRIES_XLSX_PATH,
    APPLICATIONS_XLSX_PATH,
)


def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["default"]))

    db.init_app(app)
    with app.app_context():
        db.create_all()

    ensure_master_workbooks()

    register_context(app)
    register_routes(app)
    register_admin_routes(app)
    register_error_handlers(app)

    return app


def register_context(app):
    """Make company-wide details available to every template without
    repeating them in each view function."""

    @app.context_processor
    def inject_company_details():
        return {
            "company_name": app.config["COMPANY_NAME"],
            "company_short": app.config["COMPANY_SHORT"],
            "company_tagline": app.config["COMPANY_TAGLINE"],
            "company_address_line1": app.config["COMPANY_ADDRESS_LINE1"],
            "company_address_line2": app.config["COMPANY_ADDRESS_LINE2"],
            "company_phone": app.config["COMPANY_PHONE"],
            "company_phone_2": app.config["COMPANY_PHONE_2"],
            "company_email": app.config["COMPANY_EMAIL"],
        }


def register_routes(app):

    @app.route("/")
    def home():
        return render_template("index.html", active_page="home")

    @app.route("/about")
    def about():
        return render_template("about.html", active_page="about")

    @app.route("/services")
    def services():
        return render_template("services.html", active_page="services")

    @app.route("/industries")
    def industries():
        return render_template("industries.html", active_page="industries")

    @app.route("/gallery")
    def gallery():
        return render_template("gallery.html", active_page="gallery")

    @app.route("/careers")
    def careers():
        return render_template("careers.html", active_page="careers")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            service = request.form.get("service", "").strip()
            message = request.form.get("message", "").strip()

            errors = []
            if not name:
                errors.append("Please tell us your name.")
            if not phone and not email:
                errors.append("Please share a phone number or email so we can reach you.")
            if not message:
                errors.append("Please add a short message about your requirement.")

            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template(
                    "contact.html",
                    active_page="contact",
                    form_data=request.form,
                )

            # 1. DATABASE STORAGE — every enquiry is permanently saved, no exceptions.
            enquiry = Enquiry(
                name=name,
                phone=phone or None,
                email=email or None,
                service=service or None,
                message=message,
                status="New",
                created_at=datetime.utcnow(),
            )
            db.session.add(enquiry)
            db.session.commit()

            # 2. LIVE EXCEL SHEET — a row is appended immediately to the master
            # workbook so it's always current when opened in Excel.
            append_enquiry_to_live_workbook(enquiry)

            # 3. EMAIL — company notification + confirmation to the sender
            # (if they gave an email). Best-effort; never blocks the response.
            send_enquiry_emails(app, enquiry)

            flash(
                "Thank you, {0}. Your enquiry has been received and our team "
                "will contact you within one business day.".format(name),
                "success",
            )
            return redirect(url_for("contact"))

        return render_template("contact.html", active_page="contact", form_data={})

    @app.route("/careers/apply", methods=["POST"])
    def careers_apply():
        name = request.form.get("applicant_name", "").strip()
        phone = request.form.get("applicant_phone", "").strip()
        email = request.form.get("applicant_email", "").strip()
        role = request.form.get("applicant_role", "").strip()
        experience = request.form.get("applicant_experience", "").strip()
        message = request.form.get("applicant_message", "").strip()

        if not name:
            flash("Please enter your name to submit an application.", "error")
            return redirect(url_for("careers"))
        if not phone:
            flash("Please enter a phone number so recruitment can reach you.", "error")
            return redirect(url_for("careers"))

        # 1. DATABASE STORAGE
        application = JobApplication(
            name=name,
            phone=phone or None,
            email=email or None,
            role=role or None,
            experience=experience or None,
            message=message or None,
            status="New",
            created_at=datetime.utcnow(),
        )
        db.session.add(application)
        db.session.commit()

        # 2. LIVE EXCEL SHEET
        append_application_to_live_workbook(application)

        # 3. EMAIL — company notification + confirmation to the applicant
        send_application_emails(app, application)

        flash(
            "Thank you, {0}. Your application has been received. Our "
            "recruitment team will be in touch.".format(name),
            "success",
        )
        return redirect(url_for("careers"))


# ---------------------------------------------------------------------------
# Admin panel — secure enquiry & application management
# ---------------------------------------------------------------------------

def login_required(view_func):
    @functools.wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in to access the admin panel.", "error")
            return redirect(url_for("admin_login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


def register_admin_routes(app):

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if username == app.config["ADMIN_USERNAME"] and password == app.config["ADMIN_PASSWORD"]:
                session["is_admin"] = True
                session["admin_username"] = username
                flash("Welcome back, {0}.".format(username), "success")
                next_url = request.args.get("next") or url_for("admin_dashboard")
                return redirect(next_url)
            flash("Invalid username or password.", "error")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("is_admin", None)
        session.pop("admin_username", None)
        flash("You have been logged out.", "success")
        return redirect(url_for("admin_login"))

    # --- Enquiries ---

    @app.route("/admin")
    @app.route("/admin/enquiries")
    @login_required
    def admin_dashboard():
        filters = _read_filters(request)
        query = _filtered_enquiry_query(filters)
        enquiries = query.all()

        total_count = Enquiry.query.count()
        status_counts = {
            status: Enquiry.query.filter_by(status=status).count() for status in STATUS_CHOICES
        }
        services = [row[0] for row in db.session.query(Enquiry.service).distinct() if row[0]]

        return render_template(
            "admin/dashboard.html",
            enquiries=enquiries,
            statuses=STATUS_CHOICES,
            services=sorted(services),
            filters=filters,
            total_count=total_count,
            status_counts=status_counts,
        )

    @app.route("/admin/enquiries/<int:enquiry_id>/status", methods=["POST"])
    @login_required
    def admin_update_status(enquiry_id):
        enquiry = Enquiry.query.get_or_404(enquiry_id)
        new_status = request.form.get("status", "")
        if new_status in STATUS_CHOICES:
            enquiry.status = new_status
            db.session.commit()
            flash("Status updated for {0}.".format(enquiry.name), "success")
        else:
            flash("Invalid status.", "error")
        return redirect(url_for("admin_dashboard", **_read_filters(request, from_args=True)))

    @app.route("/admin/enquiries/export")
    @login_required
    def admin_export_excel():
        filters = _read_filters(request)
        enquiries = _filtered_enquiry_query(filters).all()
        workbook = build_enquiries_workbook(enquiries)
        filename = "rsfm-enquiries-{0}.xlsx".format(datetime.now().strftime("%Y%m%d-%H%M"))
        return send_file(
            workbook, as_attachment=True, download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @app.route("/admin/enquiries/live-workbook")
    @login_required
    def admin_download_live_enquiries():
        """Downloads the actual live master workbook — the same file that
        gets a new row appended every time someone submits the Contact form."""
        return send_file(ENQUIRIES_XLSX_PATH, as_attachment=True, download_name="rsfm-enquiries-live.xlsx")

    # --- Job Applications ---

    @app.route("/admin/applications")
    @login_required
    def admin_applications():
        filters = _read_application_filters(request)
        query = _filtered_application_query(filters)
        applications = query.all()

        total_count = JobApplication.query.count()
        status_counts = {
            status: JobApplication.query.filter_by(status=status).count() for status in STATUS_CHOICES
        }
        roles = [row[0] for row in db.session.query(JobApplication.role).distinct() if row[0]]

        return render_template(
            "admin/applications.html",
            applications=applications,
            statuses=STATUS_CHOICES,
            roles=sorted(roles),
            filters=filters,
            total_count=total_count,
            status_counts=status_counts,
        )

    @app.route("/admin/applications/<int:application_id>/status", methods=["POST"])
    @login_required
    def admin_update_application_status(application_id):
        application = JobApplication.query.get_or_404(application_id)
        new_status = request.form.get("status", "")
        if new_status in STATUS_CHOICES:
            application.status = new_status
            db.session.commit()
            flash("Status updated for {0}.".format(application.name), "success")
        else:
            flash("Invalid status.", "error")
        return redirect(url_for("admin_applications", **_read_application_filters(request, from_args=True)))

    @app.route("/admin/applications/export")
    @login_required
    def admin_export_applications_excel():
        filters = _read_application_filters(request)
        applications = _filtered_application_query(filters).all()
        workbook = build_applications_workbook(applications)
        filename = "rsfm-applications-{0}.xlsx".format(datetime.now().strftime("%Y%m%d-%H%M"))
        return send_file(
            workbook, as_attachment=True, download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @app.route("/admin/applications/live-workbook")
    @login_required
    def admin_download_live_applications():
        return send_file(APPLICATIONS_XLSX_PATH, as_attachment=True, download_name="rsfm-applications-live.xlsx")


def _read_filters(request_obj, from_args=False):
    source = request_obj.form if from_args else request_obj.args
    return {
        "q": (source.get("q") or "").strip(),
        "status": source.get("status") or "",
        "service": source.get("service") or "",
        "date": source.get("date") or "",
        "sort": source.get("sort") or "created_at",
        "direction": source.get("direction") or "desc",
    }


def _filtered_enquiry_query(filters):
    query = Enquiry.query

    if filters["q"]:
        like = "%{0}%".format(filters["q"])
        query = query.filter(
            db.or_(
                Enquiry.name.ilike(like),
                Enquiry.phone.ilike(like),
                Enquiry.email.ilike(like),
                Enquiry.message.ilike(like),
            )
        )
    if filters["status"]:
        query = query.filter(Enquiry.status == filters["status"])
    if filters["service"]:
        query = query.filter(Enquiry.service == filters["service"])
    if filters["date"]:
        try:
            day = datetime.strptime(filters["date"], "%Y-%m-%d").date()
            query = query.filter(db.func.date(Enquiry.created_at) == day.isoformat())
        except ValueError:
            pass

    sort_column = {
        "created_at": Enquiry.created_at,
        "name": Enquiry.name,
        "phone": Enquiry.phone,
        "email": Enquiry.email,
        "service": Enquiry.service,
        "status": Enquiry.status,
    }.get(filters["sort"], Enquiry.created_at)

    query = query.order_by(sort_column.asc() if filters["direction"] == "asc" else sort_column.desc())
    return query


def _read_application_filters(request_obj, from_args=False):
    source = request_obj.form if from_args else request_obj.args
    return {
        "q": (source.get("q") or "").strip(),
        "status": source.get("status") or "",
        "role": source.get("role") or "",
        "date": source.get("date") or "",
        "sort": source.get("sort") or "created_at",
        "direction": source.get("direction") or "desc",
    }


def _filtered_application_query(filters):
    query = JobApplication.query

    if filters["q"]:
        like = "%{0}%".format(filters["q"])
        query = query.filter(
            db.or_(
                JobApplication.name.ilike(like),
                JobApplication.phone.ilike(like),
                JobApplication.email.ilike(like),
                JobApplication.message.ilike(like),
            )
        )
    if filters["status"]:
        query = query.filter(JobApplication.status == filters["status"])
    if filters["role"]:
        query = query.filter(JobApplication.role == filters["role"])
    if filters["date"]:
        try:
            day = datetime.strptime(filters["date"], "%Y-%m-%d").date()
            query = query.filter(db.func.date(JobApplication.created_at) == day.isoformat())
        except ValueError:
            pass

    sort_column = {
        "created_at": JobApplication.created_at,
        "name": JobApplication.name,
        "phone": JobApplication.phone,
        "email": JobApplication.email,
        "role": JobApplication.role,
        "status": JobApplication.status,
    }.get(filters["sort"], JobApplication.created_at)

    query = query.order_by(sort_column.asc() if filters["direction"] == "asc" else sort_column.desc())
    return query


def register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
