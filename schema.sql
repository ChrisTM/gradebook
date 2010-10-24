CREATE TABLE person (
	pk integer primary key,
	first_name text, 
	last_name text, 
	alias text,
	grad_year integer, 
	email text
);

CREATE TABLE assignment (
	pk integer primary key,
	name text,
	description text,
	due_date date,
	points integer
);

CREATE TABLE grade (
	pk integer primary key,
	points integer,
	comment text,
	person_pk integer,
	assignment_pk integer,
	FOREIGN KEY(person_pk) REFERENCES person(pk),
	FOREIGN KEY(assignment_pk) REFERENCES assignment(pk)
);
