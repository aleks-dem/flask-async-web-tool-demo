# Third-Party Notices

This project depends on third-party open-source libraries.  
At the time of publication, primary Python dependencies are under permissive licenses (MIT/BSD-style).

## Key Dependencies (non-exhaustive)

- Flask (BSD)
- Flask-Login (MIT)
- Flask-Session (BSD)
- Flask-Babel (BSD-3-Clause)
- Celery (BSD-3-Clause)
- redis-py (MIT)
- APScheduler (MIT)
- pandas (BSD-3-Clause)
- numpy (BSD-3-Clause, with bundled runtime components in binary distributions)
- openpyxl (MIT)
- XlsxWriter (BSD-2-Clause)
- python-docx (MIT)
- PyYAML (MIT)
- gunicorn (MIT)

## Notes

- Container runtime also installs LibreOffice from the base OS repository; its license terms are separate from Python package licenses.
- You are responsible for validating transitive dependency licenses in your target distribution model.
