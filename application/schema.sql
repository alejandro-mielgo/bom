DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS bom;
DROP TABLE IF EXISTS part;
DROP TABLE IF EXISTS project;


CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  email TEXT UNIQUE
);

CREATE TABLE bom (
  part_number TEXT NOT NULL,
  parent_part_number TEXT  NOT NULL,
  quantity FLOAT NOT NULL,
  PRIMARY KEY(part_number,parent_part_number),
  FOREIGN KEY (part_number) REFERENCES part(part_number),
  FOREIGN KEY (parent_part_number) REFERENCES part(part_number)
);

CREATE TABLE part (
  part_number TEXT UNIQUE PRIMARY KEY,
  name TEXT NOT NULL,
  measure_unit TEXT NOT NULL,
  owner_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  security_stock INTEGER,
  FOREIGN KEY(owner_id) REFERENCES user(id)
);

CREATE TABLE project(
  number TEXT UNIQUE PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  prefix TEXT UNIQUE NOT NULL,
  last_pn INTEGER NOT NULL DEFAULT 0
);



INSERT INTO project (number, name, prefix, last_pn)
VALUES
("AAAA-0000","proyecto coche","AAAA",6),
("BBBB-0000","proyecto moto","BBBB",-1);


INSERT INTO part (part_number,name,owner_id,status,measure_unit)
VALUES
("AAAA-0001","coche",1,'active',"units"),
("AAAA-0002","puerta",1,'active',"units"),
("AAAA-0003","luna lateral",1,'active',"units"),
("AAAA-0004","luna frontal",1,'active',"units"),
("AAAA-0005","salpicadero",1,'active',"units"),
("AAAA-0006","volante",1,'active',"units");

INSERT INTO bom (part_number,parent_part_number,quantity)
VALUES
("AAAA-0001","AAAA-0000",1),
("AAAA-0002","AAAA-0001",4),
("AAAA-0003","AAAA-0002",1),
("AAAA-0004","AAAA-0001",1),
("AAAA-0005","AAAA-0001",1),
("AAAA-0006","AAAA-0005",1);
