insert into student values (
	null, "Christopher", "Mitchell", "goose", 2012, "chrism@lclark.edu"
);
insert into student values (
	null, "Jamie", "Curtis", "rooster", 2012, null
);
insert into student values (
	null, "Devin", "Owen", "bookclub", 2014, "devin@example.com"
);


insert into assignment (name, description, due_date, points) values (
	"HW 1", "Do this", date('2010-09-13'), 10);
insert into assignment (name, description, due_date, points) values (
	"HW 2", "Do that", date('2010-10-15'), 10);
insert into assignment (name, description, due_date, points) values (
	"HW 3", "Do something else", date('2010-10-25'), 20);

-- Chris has grades 8, 9, 20. Devin is doing well with nearly full marks. Jamie is in the middle of the class.
insert into grade (points, student_pk, assignment_pk) values (8, 1, 1);
insert into grade (points, student_pk, assignment_pk) values (9, 1, 2);
insert into grade (points, student_pk, assignment_pk) values (20, 1, 3);
insert into grade (points, student_pk, assignment_pk) values (8, 2, 1);
insert into grade (points, student_pk, assignment_pk) values (7, 2, 2);
insert into grade (points, student_pk, assignment_pk) values (19, 2, 3);
insert into grade (points, student_pk, assignment_pk) values (10, 3, 1);
insert into grade (points, student_pk, assignment_pk) values (10, 3, 2);
insert into grade (points, student_pk, assignment_pk) values (19, 3, 3);
