"""
Data models for the RSFM website.

Enquiry: every Contact-page submission. This is the model required by the
mandatory database-storage feature — no enquiry should ever be lost.

JobApplication: every Careers-page submission, stored for the same reason
even though it wasn't explicitly required, so applications aren't lost
either.
"""
from datetime import datetime

from extensions import db

STATUS_CHOICES = ["New", "Contacted", "In Progress", "Completed", "Closed"]


class Enquiry(db.Model):
    __tablename__ = "enquiries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    service = db.Column(db.String(120), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="New")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "service": self.service,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at,
        }


class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(120), nullable=True)
    experience = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="New")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
