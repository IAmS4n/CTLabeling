import json
import os
import random
import time

from flask import Blueprint
from flask import g
from flask import render_template, request, redirect, url_for

from labeler import utils, config
from labeler.auth import login_required
from labeler.ct import get_ct
from labeler.db import get_db
from labeler.utils import int_key_load

bp = Blueprint("panel", __name__, url_prefix="/panel")


def receive(form):
    sqlite_connection = get_db()
    cursor = sqlite_connection.cursor()

    # print(form)
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
            zs_result[int(tmp[1])] = (form[name] == "positive")

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


def prepare_data(pid, wl, ww):
    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    # load old values
    query = """SELECT path, zs, professor_need, dicom_need, zs_result from samples where pid = ?;"""
    cursor.execute(query, (pid,))
    path, zs, professor_need, dicom_need, zs_result = cursor.fetchone()
    zs = int_key_load(zs)

    try:
        zs_result = int_key_load(zs_result)
    except:
        zs_result = {}

    # new form values
    rnd = random.getrandbits(32)
    send_time = time.time()

    mini_slices = []
    slices = []
    full_path = os.path.join(config.data_path, path)
    final_z = list(set(zs_result.keys()) | set(zs))
    ct = get_ct(full_path, wl=wl, ww=ww, z_list=final_z)

    for z, s in zip(final_z, ct):
        img, thumbnail = utils.encode(s)
        row = {"z": z, "img": img}
        if z in zs_result:
            if zs_result[z]:
                row["positive"] = True
            else:
                row["negative"] = True
        slices.append(row)

        mini_slices.append({"z": z, "thumbnail": thumbnail, "status": zs_result.get(z, None)})

    details = json.dumps(mini_slices)

    # save log
    query = """INSERT INTO log_send (pid, uid, rnd, send_time, path, details) VALUES (?, ?, ?, ?, ?, ?);"""
    data_tuple = (pid, g.user["id"], rnd, send_time, path, details)
    cursor.execute(query, data_tuple)
    sqliteConnection.commit()

    cursor.close()
    return slices, send_time, rnd, professor_need, dicom_need


def next_pids(pid):
    role = g.user["role"]

    sqliteConnection = get_db()
    cursor = sqliteConnection.cursor()

    if role == 1:
        query_npid = """select next from (SELECT pid, professor_check, student_check, lead(pid) OVER (ORDER BY priority DESC, pid ASC) as next from samples where (professor_check = 0  AND student_check = 0) OR pid = ?) where pid=?;"""
        query_hpid = """SELECT pid from samples WHERE professor_check = 0  AND student_check = 0 ORDER BY priority DESC, pid ASC LIMIT 1;"""
    else:
        query_npid = """select next from (SELECT pid, professor_check, student_check, lead(pid) OVER (ORDER BY priority DESC, pid ASC) as next from samples where professor_need = 1 OR pid = ?) where pid=?;"""
        query_hpid = """SELECT pid from samples WHERE professor_need = 1 ORDER BY priority DESC, pid ASC LIMIT 1;"""

    cursor.execute(query_npid, (pid, pid))
    res = cursor.fetchone()
    if (res is None) or (res[0] is None):
        npid = -1
    else:
        npid = res[0]

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


@bp.route("/images<pid>", methods=["GET"])
@login_required
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

    slices, send_time, rnd, _, _ = prepare_data(pid, wl=wl, ww=ww)

    return render_template(
        "update_images.js", send_time=send_time, rnd=rnd, slices=slices
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

    slices, send_time, rnd, professor_need, dicom_need = prepare_data(
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
        view_list=config.view_list,
        professor_need=professor_need,
        dicom_need=dicom_need,
    )


@bp.route("/")
@bp.route("/list")
@login_required
def show_list():
    plist = get_list()
    return render_template("list.html", plist=plist)
