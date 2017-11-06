from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for, send_file, \
    send_from_directory
from flask_paginate import Pagination, get_page_args
from conn import connect_db
from functools import wraps
from passlib.hash import sha256_crypt
import gc, os
from job import Job_obj

app = Flask(__name__, instance_path='C:/Users/pkwcc/PycharmProjects/flask/protected')


@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow: /"


@app.route('/upload')
def upload():
    return render_template('file_upload.html')


def special_requirement(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            if session['username'] == 'job':
                return f(*args, **kwargs)
            else:
                raise Exception
        except:
            flash('Denied')
            return redirect(url_for('index'))

    return wrap


@app.route('/return_file/<path:filename>')
@special_requirement
def return_file(filename):
    try:
        return send_from_directory(os.path.join(app.instance_path, ''), filename)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('download'))


@app.route('/download')
@special_requirement
def download():
    return render_template('file_download.html')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    password = request.form['password']
    try:
        conn, cursor = connect_db()
        cursor.execute("SELECT * FROM user WHERE username = '{:}'".format(user))
        row = cursor.fetchone()
        if row:
            if sha256_crypt.verify(password, row[2]):
                cursor.close()
                conn.close()
                gc.collect()
                session['login'] = True
                session['username'] = request.form['username']
                flash('LoggedIn')
                return jsonify({'url': url_for(row[3])})
            else:
                raise Exception('Wrong Password')
        else:
            raise Exception('User Not Found')

    except Exception as e:
        return jsonify({'msg': str(e)})


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            if session['login']:
                return f(*args, **kwargs)
            else:
                raise Exception
        except:
            flash('Login first')
            return redirect(url_for('index'))

    return wrap


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('LoggedOut')
    gc.collect()
    return redirect(url_for('index'))


@app.route('/job_dashboard')
@app.route('/job_dashboard/<indicator>')
# @login_required
def job_dashboard(indicator=None):
    session["cur_location"] = indicator
    if not indicator:
        return render_template("job_dashboard.html")
    if indicator == "job_listing":
        return redirect(url_for("job_listing"))


@app.route('/job_listing/', defaults={'page': 1})
@app.route('/job_listing', defaults={'page': 1})
@app.route('/job_listing/page/<int:page>/')
@app.route('/job_listing/page/<int:page>')
# @login_required
def job_listing(page):
    job = Job_obj.Job_search()
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    if page == 1:
        res, fk1, fk2 = job.find(offset, per_page, True)
        session["workType"] = fk1
        session["subClass"] = fk2
    else:
        res = job.find(offset, per_page, False)
    pagination = Pagination(page=page, per_page=per_page, total=job.total, record_name='search_res', format_total=True,
                            format_number=True)

    return render_template('job_dashboard.html',
                           res=res,
                           per_page=per_page,
                           pagination=pagination,
                           )


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


if __name__ == '__main__':
    app.secret_key = "super secret key"
    app.debug = True
    app.run()
