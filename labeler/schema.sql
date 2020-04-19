DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user
(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT        NOT NULL,
    role     TEXT        NOT NULL
);
