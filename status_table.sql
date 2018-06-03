DROP TABLE IF EXISTS status_table;

CREATE TABLE status_table(
    id INT PRIMARY KEY NOT NULL,
    stranger_flag INT DEFAULT 0,
    owner_in_house INT DEFAULT 0,
    direction VARCHAR(32) DEFAULT '',
    action_time VARCHAR(32) DEFAULT ''
);

INSERT INTO status_table (id, stranger_flag, owner_in_house) VALUES(1, 0, 0);
