import json
import os
import random
import sqlite3
import time

import flask
from flask import Flask
from flask import render_template, request, redirect, url_for

import config
import utils
from ct import get_ct

app = Flask(__name__)


def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(config.db_path)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()


def get_role(user=None, password=None):
    if user is None and password is None:
        try:
            user = request.cookies.get('user')
            password = request.cookies.get('pass')
        except:
            return -1

    if config.student["user"] == user and config.student["pass"] == password:
        return 1
    elif config.professor["user"] == user and config.professor["pass"] == password:
        return 2

    return -1


def receive(form):
    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    # print(form)
    pid = int(form["pid"])
    role = get_role()

    send_time = form["send_time"]
    receive_time = time.time()
    rnd = form["rnd"]
    details = json.dumps(form)

    # save log
    query = """INSERT INTO log_receive (pid, send_time, receive_time, details, rnd, role) VALUES (?, ?, ?, ?, ?, ?);"""
    data_tuple = (pid, send_time, receive_time, details, rnd, role)
    cursor.execute(query, data_tuple)
    sqliteConnection.commit()

    # update samples
    positive_zs = []
    for name in form.keys():
        if name.startswith("z"):
            z = int(name[1:])
            positive_zs.append(z)
    positive_zs = json.dumps(positive_zs)

    if ("professor_need" in form) and form["professor_need"] == "1":
        professor_need = True
    else:
        professor_need = False

    if role == 1:
        query = """Update samples set student_check = 1, professor_need = ?, positive_zs = ? where pid = ?"""
    else:
        query = """Update samples set professor_check = 1, professor_need = ?, positive_zs = ? where pid = ?"""
    cursor.execute(query, (professor_need, positive_zs, pid))
    sqliteConnection.commit()

    cursor.close()


def prepare_data(pid, wl, ww):
    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    # load old values
    query = """SELECT path, zs, professor_need, positive_zs from samples where pid = ?;"""
    cursor.execute(query, (pid,))
    path, zs, professor_need, positive_zs = cursor.fetchone()
    zs = json.loads(zs)
    if positive_zs is not None:
        positive_zs = json.loads(positive_zs)
    else:
        positive_zs = []

    # new form values
    rnd = random.getrandbits(32)
    send_time = time.time()

    mini_slices = []
    slices = []
    full_path = os.path.join(config.data_path, path)

    ct = get_ct(full_path, wl=wl, ww=ww, z_list=zs)
    for z, s in zip(zs, ct):
        img, thumbnail = utils.encode(s)
        slices.append({"z": z, "img": img, "checked": z in positive_zs})
        mini_slices.append({"z": z, "thumbnail": thumbnail, "checked": z in positive_zs})

    details = json.dumps(mini_slices)

    # save log
    query = """INSERT INTO log_send (pid, send_time, path, details, rnd) VALUES (?, ?, ?, ?, ?);"""
    data_tuple = (pid, send_time, path, details, rnd)
    cursor.execute(query, data_tuple)
    sqliteConnection.commit()

    cursor.close()
    return slices, send_time, rnd, professor_need


def next_pid(pid):
    role = get_role()

    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    if role == 1:
        query = """SELECT pid from samples WHERE pid != ? AND professor_check = 0  AND student_check = 0 ORDER BY priority DESC, pid ASC LIMIT 1;"""
    else:
        query = """SELECT pid from samples WHERE pid != ? AND professor_need = 1 ORDER BY priority DESC, pid ASC LIMIT 1;"""
    cursor.execute(query, (pid,))
    res = cursor.fetchone()

    if res is None:
        npid = -1
    else:
        npid = res[0]

    cursor.close()
    return npid


def get_list():
    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    query = """SELECT pid, student_check, professor_check, professor_need from samples ORDER BY priority DESC, pid ASC;"""
    cursor.execute(query)

    plist = []
    for pid, student_check, professor_check, professor_need in cursor.fetchall():
        plist.append({"pid": pid, "professor_need": professor_need,
                      "student": student_check, "professor": professor_check})
    cursor.close()
    return plist

@app.route('/images<pid>', methods=['GET'])
def update_images(pid):
    pid = int(pid)

    wl = request.args.get("wl")
    if wl is None:
        wl = -400
    else:
        wl = int(wl)

    ww = request.args.get("ww")
    if ww is None:
        ww = 1500
    else:
        ww = int(ww)

    slices, send_time, rnd, professor_need = prepare_data(pid, wl=wl, ww=ww)

    return render_template('update_images.js', send_time=send_time, rnd=rnd, slices=slices)

@app.route('/patient<pid>', methods=['GET', 'POST'])
def show_patient(pid):
    role = get_role()
    if 0 > role:
        return redirect(url_for('show_login'))
    #######################################################
    pid = int(pid)
    npid = next_pid(pid)

    if request.method == 'POST':
        receive(request.form)
        if npid < 0:
            return redirect(url_for('show_list'))
        else:
            return redirect(url_for('show_patient', pid=npid))

    slices, send_time, rnd, professor_need = prepare_data(pid, wl=-400, ww=1500)

    return render_template('patient.html', send_time=send_time, rnd=rnd, slices=slices,
                           pid=pid, npid=npid, role=role,
                           professor_need=professor_need)


@app.route('/')
@app.route('/list')
def show_list():
    role = get_role()

    if 0 > role:
        return redirect(url_for('show_login'))
    ############################################################
    plist = get_list()
    return render_template('list.html', plist=plist)


@app.route('/login', methods=['GET', 'POST'])
def show_login():
    if request.method == 'POST':
        if 0 < get_role(request.form['user'], request.form['pass']):
            resp = redirect(url_for('show_list'))
            # resp = make_response("Ok")
            resp.set_cookie('user', request.form['user'])
            resp.set_cookie('pass', request.form['pass'])
            return resp

    return render_template('login.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0")
