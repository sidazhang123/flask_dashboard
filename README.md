# flask_dashboard
This is an integration of a web crawler of seek.com.au and a dashboard page with login control.
The dashboard simply provides job info listing, frontend sorting and a statistical bar chart.
Data will be preserved in the DB and read by the web app.
Use contab and gunicorn to run the data collecter in /job and the web app create_app.py respectively.
