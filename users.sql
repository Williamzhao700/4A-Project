DROP TABLE IF EXISTS users;

CREATE TABLE users(
    id INTEGER PRIMARY KEY,
    username VARCHAR(256) NOT NULL,
    password VARCHAR(256) NOT NULL
);

INSERT INTO users (id, username, password) VALUES(1, 'test', '19013bdbbf37def502d27840c7beaabc7fd85a6565bff3f01b09db4cf722e642');