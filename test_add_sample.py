import json
import sqlite3


def add(path, zs, priority):
    db = sqlite3.connect("./instance/ct.sqlite")
    cursor = db.cursor()

    query = """INSERT INTO samples (path, zs, priority, student_check, professor_check, professor_need) VALUES (?, ?, ?, 0, 0, 0);"""
    data_tuple = (path, json.dumps(zs), priority)
    cursor.execute(query, data_tuple)
    db.commit()
    cursor.close()
    db.close()


add("patient_99/SR 4/", list(range(20, 100, 5)), 10)
add("patient_98/SR 4/", list(range(20, 100, 5)), 10)
add("patient_97/SR 4/", list(range(20, 100, 5)), 10)
add("patient_96/SR 4/", list(range(20, 100, 5)), 10)
add("patient_95/SR 4/", list(range(20, 100, 5)), 10)
