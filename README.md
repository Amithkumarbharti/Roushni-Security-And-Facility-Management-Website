#Live website link
https://rsfmindia.com/

# RSFM Enterprise Website

A production-ready Flask website for **Roushni Security & Facility Management (RSFM)** —
every Contact enquiry and Careers application is saved to a database, appended live to a
Microsoft Excel workbook, and emailed to both the company and the person who submitted it.

## Tech Stack

- **Backend:** Python 3, Flask, Flask-SQLAlchemy (SQLite by default)
- **Frontend:** HTML5, CSS3 (custom design system), vanilla JavaScript
- **Email:** smtplib, configured entirely through environment variables
- **Excel:** openpyxl — both live auto-updating workbooks and on-demand filtered exports
- **Fonts / Icons:** Google Fonts (Poppins + Inter), Font Awesome (via CDN)

## Project Structure

```
rsfm/
├── app.py                    # Application factory, public routes, admin routes
├── config.py                  # Environment-driven configuration (.env support)
├── extensions.py               # Shared SQLAlchemy instance
├── models.py                    # Enquiry & JobApplication database models
├── email_utils.py                # Two-way email: company + submitter confirmation
├── excel_utils.py                 # Live workbooks + on-demand filtered export
├── requirements.txt
├── .env.example                   # Copy to .env and fill in real values
├── data/exports/                   # Auto-created on first run — live .xlsx files live here
│   ├── rsfm-enquiries-live.xlsx
│   └── rsfm-applications-live.xlsx
├── templates/
│   ├── base.html, index.html, about.html, services.html,
│   │   industries.html, gallery.html, careers.html, contact.html, 404.html, 500.html
│   └── admin/
│       ├── admin_base.html       # Admin layout
│       ├── login.html            # Admin login
│       ├── dashboard.html        # Enquiry management (Tab 1)
│       └── applications.html     # Job application management (Tab 2)
└── static/
    ├── css/style.css, admin.css
    ├── js/main.js, admin.js
    └── images/logo.png, images/staff/*.jpg
```

## Running Locally

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then edit .env with real values
python app.py
```

Visit **http://localhost:5000**. On first run, Flask automatically creates:
- The SQLite database (`rsfm.db`) with its tables
- Two live Excel workbooks in `data/exports/` (headers only, ready to receive rows)

No manual setup step is needed for either.

## Where Does Submitted Data Go? (Three Places, Every Time)

Every **Contact** enquiry and every **Careers** application is, in this order:

1. **Saved to the database** — permanently, in the `enquiries` / `job_applications`
   tables. This happens first and always succeeds, independent of email or Excel.
2. **Appended to a live Excel workbook** — `data/exports/rsfm-enquiries-live.xlsx` or
   `data/exports/rsfm-applications-live.xlsx`. Open this file directly in Microsoft Excel;
   every new submission adds a new row the moment it comes in. No export button needed —
   just reopen (or refresh, if you keep it open) the same file.
3. **Emailed to two people:**
   - The **company** (`ENQUIRY_NOTIFY_EMAIL` in `.env`, defaults to `roushnifacilty@gmail.com`)
     gets a full notification with all submitted details.
   - The **person who submitted the form** gets an automatic confirmation copy of what
     they sent — *if* they provided an email address. (The Careers form now has an
     optional email field for this reason.)

Both the live-workbook write and the emails are best-effort: if either fails (e.g. no SMTP
configured yet), the enquiry/application is still safely in the database — nothing is lost.

## Admin Panel — `/admin`

Login-protected (`ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env`), with two tabs:

**Enquiries tab** (`/admin/enquiries`)
- Search by name/phone/email/message, filter by Status/Service/Date, sort any column
- Update status inline: New → Contacted → In Progress → Completed → Closed
- **Download Live Workbook** — grabs the actual live file described above, as-is
- **Export to Excel** — generates a fresh `.xlsx` from your current search/filter

**Job Applications tab** (`/admin/applications`)
- Same search / filter / sort / status-update / export capabilities, for applications

Default admin login (**change this in `.env` before deploying**):
```
Username: admin
Password: rsfm@admin123
```

## Enabling Real Email Sending

Sending is **off by default** (`MAIL_ENABLED=False`) — until you configure real SMTP
credentials, the app logs that it skipped sending rather than failing a form. To turn it on:

```
MAIL_ENABLED=True
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail-address@gmail.com
MAIL_PASSWORD=your-16-character-app-password   # not your normal Gmail password
MAIL_DEFAULT_SENDER=your-gmail-address@gmail.com
ENQUIRY_NOTIFY_EMAIL=roushnifacilty@gmail.com
```

Gmail requires an **App Password** (Google Account → Security → 2-Step Verification →
App Passwords) — a normal Gmail login password will not work for SMTP.

## Content Sources

Company facts (mission statement, values, differentiators, training process, service
list, personnel levels, and client names) come directly from the RSFM Company Profile
document. **Testimonials on the homepage are illustrative placeholders** — replace them
with verified client quotes before this site goes live.

## Deployment Checklist

- [ ] Copy `.env.example` to `.env`; set a real `SECRET_KEY` and `ADMIN_PASSWORD`
- [ ] Add real SMTP credentials and set `MAIL_ENABLED=True`
- [ ] Replace illustrative homepage testimonials with real client quotes
- [ ] Point a real domain + HTTPS certificate at the production host
- [ ] Back up `data/exports/*.xlsx` and `rsfm.db` regularly (or migrate to PostgreSQL via
      `DATABASE_URL` for production scale)
- [ ] Run through the responsive / cross-browser / accessibility checklist from the
      original project documentation
