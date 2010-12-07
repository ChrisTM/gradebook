BEGIN;

CREATE TABLE student (
	pk integer primary key,
	first_name text NOT NULL, 
	last_name text, 
	alias text,
	grad_year integer, 
	email text
);

CREATE TABLE assignment (
	pk integer primary key,
	name text NOT NULL,
	description text,
	due_date date,
	points integer
);

CREATE TABLE grade (
	pk integer primary key,
	student_pk integer NOT NULL,
	assignment_pk integer NOT NULL,
	points integer NOT NULL,
	comment text,
	FOREIGN KEY(student_pk) REFERENCES student(pk),
	FOREIGN KEY(assignment_pk) REFERENCES assignment(pk)
	UNIQUE (student_pk, assignment_pk) --It doesn't make sense to have more than one grade for the same assignment per person.
);

COMMIT;
