/* 
     the structure for the shotglass database
*/

BEGIN;

CREATE TABLE user(
	"id" INTEGER NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	username VARCHAR(20), 
	password VARCHAR(20), 
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    last_login_at TIME,
    current_login_at TIME,
    last_login_ip VARCHAR(100),
    current_login_ip VARCHAR(100),
    login_count INTEGER,
    active BOOLEAN DEFAULT 1,
    confirmed_at TIME,
	PRIMARY KEY ("id"), 
	UNIQUE (email), 
	UNIQUE (username)
);

CREATE TABLE role(
    "id" INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL UNIQUE, 
    description VARCHAR(255),
	PRIMARY KEY ("id")
);

CREATE TABLE roles_users(
	"id" INTEGER NOT NULL, 
    user_id INTEGER,
    role_id INTEGER,
	PRIMARY KEY ("id"), 
	FOREIGN KEY(user_id) REFERENCES user ("id") ON DELETE CASCADE,
	FOREIGN KEY(role_id) REFERENCES role ("id") ON DELETE CASCADE
);

COMMIT;

-- Create a default user
/* This is no longer needed
BEGIN;

INSERT INTO role (name, description) values ('superuser', 'Top level user');
INSERT INTO user (username, email ) values ('bleddy', 'bill@williesworkshop.net');
INSERT INTO roles_users (user_id, role_id ) values ((select id from user where username = 'bleddy' limit 1), (select id from role where name = 'superuser' limit 1));


COMMIT;
*/