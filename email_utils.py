"""
Sends email notifications whenever a new enquiry or job application is
submitted — one copy to the company, and (when an email address was
provided) a confirmation copy back to the person who submitted it.

Configuration is entirely environment-driven (see .env.example). If
MAIL_ENABLED is False (the default until SMTP credentials are supplied),
sending is skipped and a message is logged instead — a missing mail
configuration should never break a form or lose a submission, since the
database write already happened before this runs.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("rsfm.email")


def _mail_is_configured(cfg):
    if not cfg.get("MAIL_ENABLED"):
        logger.info("MAIL_ENABLED is False — skipping email. Set MAIL_ENABLED=True and SMTP credentials in .env to enable sending.")
        return False
    if not cfg.get("MAIL_USERNAME") or not cfg.get("MAIL_PASSWORD"):
        logger.warning("Email skipped: MAIL_USERNAME/MAIL_PASSWORD not configured in .env.")
        return False
    return True


def _send_raw_email(cfg, to_addr, subject, body):
    """Low-level send. Never raises — logs and returns False on failure."""
    msg = MIMEMultipart()
    msg["From"] = cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("MAIL_USERNAME")
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(cfg.get("MAIL_SERVER"), cfg.get("MAIL_PORT"), timeout=10) as server:
            if cfg.get("MAIL_USE_TLS"):
                server.starttls()
            server.login(cfg.get("MAIL_USERNAME"), cfg.get("MAIL_PASSWORD"))
            server.sendmail(msg["From"], [to_addr], msg.as_string())
        logger.info("Email sent to %s: %s", to_addr, subject)
        return True
    except Exception as exc:  # noqa: BLE001 — log and continue, never break the request
        logger.error("Failed to send email to %s: %s", to_addr, exc)
        return False


# ---------------------------------------------------------------------------
# Enquiry (Contact page) emails
# ---------------------------------------------------------------------------

def send_enquiry_emails(app, enquiry):
    """Send the company notification and, if an email was given, a
    confirmation to the person who submitted the enquiry."""
    cfg = app.config
    if not _mail_is_configured(cfg):
        return {"company": False, "sender": False}

    company_addr = cfg.get("ENQUIRY_NOTIFY_EMAIL") or cfg.get("COMPANY_EMAIL")

    company_subject = "New Website Enquiry — {0}".format(enquiry.name)
    company_body = (
        "A new enquiry has been submitted on the RSFM website.\n\n"
        "Name:             {name}\n"
        "Phone:            {phone}\n"
        "Email:            {email}\n"
        "Service Required: {service}\n"
        "Submitted:        {created_at}\n"
        "Status:           {status}\n\n"
        "Message:\n{message}\n\n"
        "----\n"
        "This is an automated notification from the RSFM website contact form."
    ).format(
        name=enquiry.name,
        phone=enquiry.phone or "Not provided",
        email=enquiry.email or "Not provided",
        service=enquiry.service or "Not specified",
        created_at=enquiry.created_at.strftime("%d %b %Y, %I:%M %p"),
        status=enquiry.status,
        message=enquiry.message,
    )
    company_sent = _send_raw_email(cfg, company_addr, company_subject, company_body)

    sender_sent = False
    if enquiry.email:
        sender_subject = "We've received your enquiry — {0}".format(cfg.get("COMPANY_SHORT", "RSFM"))
        sender_body = (
            "Hi {name},\n\n"
            "Thank you for reaching out to {company_name}. We've received your enquiry "
            "and a member of our team will contact you within one business day.\n\n"
            "Here's a copy of what you submitted:\n\n"
            "Service Required: {service}\n"
            "Message:          {message}\n\n"
            "If anything above needs correcting, just reply to this email or call us at "
            "{phone} / {phone2}.\n\n"
            "Regards,\n"
            "{company_name}\n"
            "{address1}, {address2}\n"
            "{email}"
        ).format(
            name=enquiry.name,
            company_name=cfg.get("COMPANY_NAME"),
            service=enquiry.service or "Not specified",
            message=enquiry.message,
            phone=cfg.get("COMPANY_PHONE"),
            phone2=cfg.get("COMPANY_PHONE_2"),
            address1=cfg.get("COMPANY_ADDRESS_LINE1"),
            address2=cfg.get("COMPANY_ADDRESS_LINE2"),
            email=cfg.get("COMPANY_EMAIL"),
        )
        sender_sent = _send_raw_email(cfg, enquiry.email, sender_subject, sender_body)

    return {"company": company_sent, "sender": sender_sent}


# ---------------------------------------------------------------------------
# Job application (Careers page) emails
# ---------------------------------------------------------------------------

def send_application_emails(app, application):
    """Send the company notification and, if an email was given, a
    confirmation to the applicant."""
    cfg = app.config
    if not _mail_is_configured(cfg):
        return {"company": False, "sender": False}

    company_addr = cfg.get("ENQUIRY_NOTIFY_EMAIL") or cfg.get("COMPANY_EMAIL")

    company_subject = "New Job Application — {0}".format(application.name)
    company_body = (
        "A new job application has been submitted on the RSFM website.\n\n"
        "Name:             {name}\n"
        "Phone:            {phone}\n"
        "Email:            {email}\n"
        "Position:         {role}\n"
        "Experience:       {experience}\n"
        "Submitted:        {created_at}\n"
        "Status:           {status}\n\n"
        "Message:\n{message}\n\n"
        "----\n"
        "This is an automated notification from the RSFM website careers form."
    ).format(
        name=application.name,
        phone=application.phone or "Not provided",
        email=application.email or "Not provided",
        role=application.role or "Not specified",
        experience=application.experience or "Not specified",
        created_at=application.created_at.strftime("%d %b %Y, %I:%M %p"),
        status=application.status,
        message=application.message or "—",
    )
    company_sent = _send_raw_email(cfg, company_addr, company_subject, company_body)

    sender_sent = False
    if application.email:
        sender_subject = "We've received your application — {0}".format(cfg.get("COMPANY_SHORT", "RSFM"))
        sender_body = (
            "Hi {name},\n\n"
            "Thank you for applying to {company_name} for the position of {role}. "
            "Our recruitment team has received your application and will be in touch if "
            "your profile matches our current requirements.\n\n"
            "Here's a copy of what you submitted:\n\n"
            "Position:   {role}\n"
            "Experience: {experience}\n"
            "Message:    {message}\n\n"
            "If anything above needs correcting, just reply to this email or call us at "
            "{phone} / {phone2}.\n\n"
            "Regards,\n"
            "{company_name}\n"
            "{address1}, {address2}\n"
            "{email}"
        ).format(
            name=application.name,
            company_name=cfg.get("COMPANY_NAME"),
            role=application.role or "Not specified",
            experience=application.experience or "Not specified",
            message=application.message or "—",
            phone=cfg.get("COMPANY_PHONE"),
            phone2=cfg.get("COMPANY_PHONE_2"),
            address1=cfg.get("COMPANY_ADDRESS_LINE1"),
            address2=cfg.get("COMPANY_ADDRESS_LINE2"),
            email=cfg.get("COMPANY_EMAIL"),
        )
        sender_sent = _send_raw_email(cfg, application.email, sender_subject, sender_body)

    return {"company": company_sent, "sender": sender_sent}
