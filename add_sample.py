import json
import os
import sqlite3
from glob import glob


def add(zs_path, zs_init, priority):
    db = sqlite3.connect("./instance/ct.sqlite")
    cursor = db.cursor()

    query = """INSERT INTO samples (zs_path, zs_init, priority, student_check, professor_check, professor_need) VALUES (?, ?, ?, 0, 0, 0);"""
    data_tuple = (json.dumps(zs_path), json.dumps(zs_init), priority)
    cursor.execute(query, data_tuple)
    db.commit()
    cursor.close()
    db.close()


def make_zs_path(patient_dir):
    dicoms = [os.path.abspath(image) for image in glob(patient_dir + "/*") if "tmb" not in image.split("/")[-1]]

    #############################################################
    # NOTE : The sort needs be adapted with slices name format  #
    #############################################################
    dicoms = sorted(dicoms, key=lambda x: x.split("/")[-1])

    zs_path = {z: path for z, path in enumerate(dicoms)}

    return zs_path


add(make_zs_path("./sample_dicom/"), list(range(0, 24, 3)), 10)
