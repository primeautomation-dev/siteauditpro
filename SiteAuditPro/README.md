# SiteAuditPro

A comprehensive, production-ready SaaS website auditing tool. Analyze websites and get detailed SEO, performance, security, and optimization reports.

## Features

### Stage 1 (MVP)
- **Website Analysis**: Enter any URL and get instant audit results
- **Basic SEO Checks**: Title tag and meta description validation
- **Structure Analysis**: H1 tags, images, and link counts
- **Clean Dashboard**: Modern, responsive UI built with TailwindCSS

### Stage 2 (Pro-Level)
- **Advanced SEO Analysis**:
  - Title length validation (ideal: 30-60 chars)
  - Meta description length and quality checks
  - H1, H2, H3 heading counts
  - Missing alt attributes detection
  - Canonical tag detection
  - Robots meta tag detection
  - Sitemap.xml availability check
  - Robots.txt availability check

- **Performance Analysis**:
  - Total page size (KB/MB)
  - JavaScript files count and total size
  - CSS files count and total size
  - Largest image file size detection
  - External scripts (CDN) count
  - Basic LCP (Largest Contentful Paint) indicator

- **Security Headers Check**:
  - Content-Security-Policy
  - X-Frame-Options
  - X-Content-Type-Options
  - Referrer-Policy
  - Strict-Transport-Security

- **Broken Links Detection**:
  - Scans up to 40 links
  - HEAD request validation
  - Working vs broken link counts

- **Image Optimization Analysis**:
  - Oversized images detection (>300KB)
  - Missing width/height attributes
  - Unoptimized format detection (JPEG/PNG vs WebP/AVIF)

- **Scoring System**:
  - SEO Score (0-100)
  - Performance Score (0-100)
  - Security Score (0-100)

- **Audit History**:
  - SQLite database storage
  - View all past audits
  - Quick access to previous reports

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Jinja2 Templates + TailwindCSS
- **Database**: SQLite with SQLModel
- **Parsing**: BeautifulSoup4
- **HTTP**: Requests
- **Server**: Uvicorn

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python run.py
   ```

3. **Open your browser**:
   Navigate to `http://localhost:8000`

## Project Structure

```
SiteAuditPro/
 ├── app/
 │    ├── main.py              # FastAPI application with routes
 │    ├── db.py                # Database setup and session management
 │    ├── models.py            # SQLModel audit model
 │    ├── utils/
 │    │     └── auditor.py     # Comprehensive website analysis logic
 │    ├── templates/
 │    │     ├── base.html      # Base template with sidebar support
 │    │     ├── index.html     # Home page with URL input
 │    │     ├── report.html    # Detailed audit report dashboard
 │    │     ├── history.html   # Audit history page
 │    │     └── partials/
 │    │           └── sidebar.html  # Navigation sidebar
 │    └── static/
 │          └── styles.css     # Tailwind compiled CSS
 ├── requirements.txt
 └── README.md
```

## Usage

1. **Run an Audit**:
   - Enter a website URL in the input field on the home page
   - Click "Analyze Website"
   - View the comprehensive audit report

2. **View Report Sections**:
   - **SEO**: Title, meta description, headings, alt attributes, canonical, robots
   - **Performance**: Page size, JS/CSS files, image sizes, LCP
   - **Security**: Security headers status
   - **Links**: Working vs broken links analysis
   - **Images**: Optimization and format checks

3. **View History**:
   - Click "History" in the sidebar
   - View all past audits with scores
   - Click "View Report" to see detailed results

## Scoring System

- **SEO Score**: Based on title quality, meta description, H1 count, alt attributes, canonical tag, robots meta, sitemap, and robots.txt
- **Performance Score**: Based on page size, JS/CSS sizes, image sizes, and optimization
- **Security Score**: Based on presence of security headers (each header = 20 points)

## Development

The application runs in development mode with auto-reload enabled. Any changes to the code will automatically restart the server.

The database (SQLite) is automatically created on first run at `./siteaudit.db`.

## License

MIT
