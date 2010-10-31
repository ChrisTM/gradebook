CREATE TABLE student (
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
	student_pk integer,
	assignment_pk integer,
	FOREIGN KEY(student_pk) REFERENCES student(pk),
	FOREIGN KEY(assignment_pk) REFERENCES assignment(pk)
	-- Should write a unique constraint on (person_pk, assignment_pk)
);
