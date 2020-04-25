import json
import os
import random
import sqlite3
import time

from flask import Blueprint
from flask import g
from flask import render_template, request, redirect, url_for, current_app
from werkzeug.exceptions import BadRequest

from labeler import utils
from labeler.auth import login_required
from labeler.ct import get_ct
from labeler.db import get_db
from labeler.utils import int_key_json_load

bp = Blueprint("panel", __name__, url_prefix="/panel")


def check_limit():
    check_pass = True

    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    query = """SELECT COUNT(pid) from log_send WHERE uid = ? AND type = 'AdditionalSlice' AND CAST(send_time AS INTEGER)>?;"""
    cursor.execute(query, (g.user["id"], int(time.time()) - 24 * 60 * 60))
    res = cursor.fetchone()
    if (res is not None) and (res[0] is not None):
        check_pass &= res[0] < current_app.config["MAX_ADDITIONAL_SLICE_PER_DAY"]
    else:
        check_pass = False

    query = """SELECT COUNT(pid) from log_send WHERE uid = ? AND type = 'NormalSlices' AND CAST(send_time AS INTEGER)>?;"""
    cursor.execute(query, (g.user["id"], int(time.time()) - 24 * 60 * 60))
    res = cursor.fetchone()
    if (res is not None) and (res[0] is not None):
        check_pass &= res[0] < current_app.config["MAX_PATIENT_PER_DAY"]
    else:
        check_pass = False

    cursor.close()

    if not check_pass:
        raise BadRequest()

    return check_pass


def receive(form):
    sqlite_connection = get_db()
    cursor = sqlite_connection.cursor()

    pid = int(form["pid"])
    role = g.user["role"]

    send_time = form["send_time"]
    receive_time = time.time()
    rnd = form["rnd"]
    details = json.dumps(form)

    # save log
    query = """INSERT INTO log_receive (pid, uid, rnd, send_time, receive_time, details) VALUES (?, ?, ?, ?, ?, ?);"""
    data_tuple = (pid, g.user["id"], rnd, send_time, receive_time, details)
    cursor.execute(query, data_tuple)
    sqlite_connection.commit()

    # update samples
    zs_result = {}
    for name in form.keys():
        if name.startswith("z") and "_" in name:
            tmp = name.split("_")
            assert (len(tmp) == 3) and (form[name] in ["positive", "negative"])
            z = int(tmp[1])
            hmac = tmp[2]
            assert utils.zhmac(pid, z) == hmac
            zs_result[z] = (form[name] == "positive")

    zs_result = json.dumps(zs_result)  # keys will cast to str

    if ("professor_need" in form) and form["professor_need"] == "1":
        professor_need = 1
    else:
        professor_need = 0

    if ("dicom_need" in form) and form["dicom_need"] == "1":
        dicom_need = 1
    else:
        dicom_need = 0

    if role == 1:
        query = """Update samples set student_check = 1, professor_need = ?, dicom_need = ?, zs_result = ? where pid = ?"""
    else:
        query = """Update samples set professor_check = 1, professor_need = ?, dicom_need = ?, zs_result = ? where pid = ?"""
    cursor.execute(query, (professor_need, dicom_need, zs_result, pid))
    sqlite_connection.commit()

    cursor.close()


def prepare_normal_slices(pid, wl, ww):
    assert check_limit()

    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    # load old values
    query = """SELECT zs_path, zs_init, professor_need, dicom_need, zs_result from samples where pid = ?;"""
    cursor.execute(query, (pid,))
    zs_path, zs_init, professor_need, dicom_need, zs_result = cursor.fetchone()
    zs_path = int_key_json_load(zs_path)
    zs_init = int_key_json_load(zs_init)

    try:
        zs_result = int_key_json_load(zs_result)
    except:
        zs_result = {}

    # new form values
    rnd = random.getrandbits(32)
    send_time = time.time()

    mini_slices = []
    slices = []

    final_z = sorted(list(set(zs_result.keys()) | set(zs_init)))
    ct = get_ct(zs_path, wl=wl, ww=ww, z_list=final_z)

    for z, s in zip(final_z, ct):
        img, thumbnail = utils.encode(s)
        row = {"z": z, "hmac": utils.zhmac(pid, z), "img": img}
        if z in zs_result:
            if zs_result[z]:
                row["positive"] = True
            else:
                row["negative"] = True
        slices.append(row)

        mini_slices.append({"z": z, "thumbnail": thumbnail, "status": zs_result.get(z, None)})

    details = json.dumps(mini_slices)

    # save log
    query = """INSERT INTO log_send (pid, uid, rnd, send_time, type, details) VALUES (?, ?, ?, ?, ?, ?);"""
    data_tuple = (pid, g.user["id"], rnd, send_time, "NormalSlices", details)
    cursor.execute(query, data_tuple)
    sqliteConnection.commit()
    cursor.close()

    for z in range(min(final_z) - 1, max(final_z) + 2):
        if z not in final_z:
            slices.append({"z": z, "hmac": "", "img": ""})
    slices = sorted(slices, key=lambda i: i['z'])

    return slices, send_time, rnd, professor_need, dicom_need


def prepare_additional_slice(pid, wl, ww, z_list):
    assert check_limit()

    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    # load path
    query = """SELECT zs_path from samples where pid = ?;"""
    cursor.execute(query, (pid,))
    zs_path = cursor.fetchone()[0]
    zs_path = int_key_json_load(zs_path)

    # new form values
    rnd = random.getrandbits(32)
    send_time = time.time()

    mini_slices = []
    slices = []

    ct = get_ct(zs_path, wl=wl, ww=ww, z_list=z_list)
    for z, s in zip(z_list, ct):
        img, thumbnail = utils.encode(s)
        slices.append({"z": z, "hmac": utils.zhmac(pid, z), "img": img})
        mini_slices.append({"z": z, "thumbnail": thumbnail})

    details = json.dumps(mini_slices)

    # save log
    query = """INSERT INTO log_send (pid, uid, rnd, send_time, type, details) VALUES (?, ?, ?, ?, ?, ?);"""
    data_tuple = (pid, g.user["id"], rnd, send_time, "AdditionalSlice", details)
    cursor.execute(query, data_tuple)
    sqliteConnection.commit()
    cursor.close()

    return slices, send_time, rnd


def next_pids(pid):
    role = g.user["role"]

    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    if sqlite3.sqlite_version >= '3.25':
        if role == 1:
            query_npid = """select next from (SELECT pid, professor_check, student_check, lead(pid) OVER (ORDER BY priority DESC, pid ASC) as next from samples where (professor_check = 0  AND student_check = 0) OR pid = ?) where pid=?;"""
        else:
            query_npid = """select next from (SELECT pid, professor_check, student_check, lead(pid) OVER (ORDER BY priority DESC, pid ASC) as next from samples where professor_need = 1 OR pid = ?) where pid=?;"""

        cursor.execute(query_npid, (pid, pid))
        res = cursor.fetchone()
        if (res is None) or (res[0] is None):
            npid = -1
        else:
            npid = res[0]
    else:
        query_npid = """SELECT MAX(pid) from samples"""
        cursor.execute(query_npid)
        res = cursor.fetchone()
        npid = min(res[0], pid + 1)

    if role == 1:
        query_hpid = """SELECT pid from samples WHERE professor_check = 0  AND student_check = 0 ORDER BY priority DESC, pid ASC LIMIT 1;"""
    else:
        query_hpid = """SELECT pid from samples WHERE professor_need = 1 ORDER BY priority DESC, pid ASC LIMIT 1;"""

    cursor.execute(query_hpid)
    res = cursor.fetchone()
    if (res is None) or (res[0] is None):
        hpid = -1
    else:
        hpid = res[0]

    cursor.close()
    return npid, hpid


def get_list():
    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    query = """SELECT pid, student_check, professor_check, professor_need, dicom_need from samples ORDER BY priority DESC, pid ASC;"""
    cursor.execute(query)

    plist = []
    for (
            pid,
            student_check,
            professor_check,
            professor_need,
            dicom_need,
    ) in cursor.fetchall():
        plist.append(
            {
                "pid": pid,
                "professor_need": professor_need,
                "dicom_need": dicom_need,
                "student": student_check,
                "professor": professor_check,
            }
        )
    cursor.close()
    return plist


@bp.route("/slices<pid>", methods=["GET"])
@login_required
def update_slices(pid):
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

    slices, send_time, rnd, _, _ = prepare_normal_slices(pid, wl=wl, ww=ww)

    return render_template(
        "update_slices.js", send_time=send_time, rnd=rnd, slices=slices
    )


@bp.route("/more_slices<pid>", methods=["GET"])
@login_required
def additonal_slice(pid):
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

    z_min = int(request.args.get("z_min"))
    z_max = int(request.args.get("z_max"))
    z_list = list(range(z_min, z_max))
    assert len(z_list) <= 3

    slices, send_time, rnd = prepare_additional_slice(pid, wl=wl, ww=ww, z_list=z_list)

    return render_template(
        "update_slices.js", send_time=send_time, rnd=rnd, slices=slices
    )


@bp.route("/patient<pid>", methods=["GET", "POST"])
@login_required
def show_patient(pid):
    pid = int(pid)
    npid, hpid = next_pids(pid)

    if request.method == "POST":
        receive(request.form)
        if npid < 0:
            return redirect(url_for("panel.show_list"))
        else:
            return redirect(url_for("panel.show_patient", pid=npid))

    slices, send_time, rnd, professor_need, dicom_need = prepare_normal_slices(
        pid, wl=-400, ww=1500
    )

    return render_template(
        "patient.html",
        send_time=send_time,
        rnd=rnd,
        slices=slices,
        pid=pid,
        npid=npid,
        hpid=hpid,
        professor_need=professor_need,
        dicom_need=dicom_need,
    )


@bp.route("/")
@bp.route("/list")
@login_required
def show_list():
    plist = get_list()
    return render_template("list.html", plist=plist)
