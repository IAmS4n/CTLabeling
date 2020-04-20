DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS samples;
DROP TABLE IF EXISTS log_send;
DROP TABLE IF EXISTS log_receive;


CREATE TABLE user
(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT        NOT NULL,
    role     TEXT        NOT NULL
);

CREATE TABLE samples
(
    pid             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    path            TEXT    NOT NULL,
    zs              TEXT    NOT NULL,
    priority        INTEGER NOT NULL,
    student_check   INTEGER NOT NULL DEFAULT 0,
    professor_check INTEGER NOT NULL DEFAULT 0,
    professor_need  INTEGER NOT NULL DEFAULT 0,
    dicom_need      INTEGER NOT NULL DEFAULT 0,
    positive_zs     TEXT
);

CREATE TABLE log_send
(
    pid       INTEGER,
    send_time TEXT,
    path      TEXT,
    details   TEXT,
    rnd       TEXT
);

CREATE TABLE log_receive
(
    pid          INTEGER,
    send_time    TEXT,
    receive_time TEXT,
    details      TEXT,
    rnd          TEXT,
    role         INTEGER
);