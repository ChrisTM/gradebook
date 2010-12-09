import sqlite3
from flask import Flask, g, url_for, redirect, render_template, request
from model import Student, Assignment, Grade, db

DEBUG = True
SECRET_KEY = "'K\xaf\xd2\xc7\xc2#J\x05s%\x99J\x8e\xda\x85\xbe<t\xb2\xea\xab\xa7\xa4\xef'"

app = Flask(__name__)
app.config.from_object(__name__)


def invisible_none(value):
	"""A finalizer for Jinja2 to let None values not be rendered."""
	if value is None:
		return ''
	return value

app.jinja_env.finalize = invisible_none


@app.before_request
def before_request():
	# I have to connect to the database from here, and not the main thread,
	# because if I made the connection in model.py for eg. and not the main
	# thread, then when I try to use the model subclasses to access the
	# database in the views in gradebook.py, then the db connection is going
	# to be accessed by *not* the main thread. I think there's probably a
	# more elegant solution. TODO?
    db.connect()

@app.after_request
def after_request(response):
	db.close()
	return response


@app.route('/')
def index():
    return redirect(url_for("gradebook"), code=302)

@app.route('/gradebook/')
def gradebook():
	assignments = Assignment.all()
	students = Student.all()
	assignment_pks = [a.pk for a in assignments]
	for student in students:
		# Set the grades following the order specified by assignment_pks
		grades = student.get_grades()
		by_assignment_pk = dict([(g.assignment_pk, g) for g in grades])
		student.grades = [by_assignment_pk.get(pk) for pk in assignment_pks]
	return render_template("gradebook.html", assignments=assignments,
			students=students)

@app.route('/public_gradebook/')
def public_gradebook():
	assignments = Assignment.all()
	students = Student.all()
	assignment_pks = [a.pk for a in assignments]
	for student in students:
		# Set the grades following the order specified by assignment_pks
		grades = student.get_grades()
		by_assignment_pk = dict([(g.assignment_pk, g) for g in grades])
		student.grades = [by_assignment_pk.get(pk) for pk in assignment_pks]
	return render_template("public_gradebook.html", assignments=assignments,
			students=students)


@app.route('/students/')
def students():
	students = Student.all()
	return render_template('student_list.html', students=students)

@app.route('/students/create/', methods=['GET', 'POST'])
def student_create():
	if request.method == "GET":
		return render_template('student_create.html')
	elif request.method == "POST":
		cur = g.db.execute('INSERT INTO student (first_name, last_name, alias, grad_year, email) values (:first_name, :last_name, :alias, :grad_year, :email)', request.form)
		g.db.commit()
		if "create_and_add" in request.form:
			return render_template('student_create.html')
		elif "create" in request.form:
			return redirect(url_for('student_view', student_pk=cur.lastrowid))

@app.route('/students/view/<int:student_pk>/')
def student_view(student_pk):
	student = Student.get(pk=student_pk)
	return render_template("student_view.html", student=student)

@app.route('/students/update/<int:student_pk>/', methods=['GET', 'POST'])
def student_update(student_pk):
	if request.method == 'GET':
		query = 'SELECT * FROM student WHERE pk=?'
		student = query_db(query, [student_pk])[0]
		return render_template('student_update.html', student=student)
	elif request.method == 'POST':
		query = 'UPDATE student SET first_name=:first_name, last_name=:last_name, alias=:alias, grad_year=:grad_year, email=:email WHERE pk=:pk'
		args = dict(request.form.to_dict(flat=True), pk=student_pk)
		g.db.execute(query, args)
		g.db.commit()
		return redirect(url_for('student_view', student_pk=student_pk))

@app.route('/students/delete/<int:student_pk>/', methods=['GET', 'POST'])
def student_delete(student_pk):
	student = Student.get(pk=student_pk)
	if request.method == 'GET':
		return render_template('student_delete.html', student=student)
	if request.method == 'POST':
		student.delete()
		return redirect(url_for('students'))


@app.route('/assignments/')
def assignments():
	assignments = Assignment.all()
	return render_template('assignment_list.html', assignments=assignments)

@app.route('/assignments/create/', methods=['GET', 'POST'])
def assignment_create():
	if request.method == 'GET':
		return render_template('assignment_create.html')
	elif request.method == 'POST':
		cur = g.db.execute("""
				INSERT INTO assignment (name, description, due_date, points) 
				VALUES (:name, :description, :due_date, :points)
				""", request.form)
		g.db.commit()
		if "create_and_add" in request.form:
			return render_template('assignment_create.html')
		elif "create" in request.form:
			return redirect(url_for('assignment_view', assignment_pk=cur.lastrowid))

@app.route('/assignments/view/<int:assignment_pk>/')
def assignment_view(assignment_pk):
	assignment = Assignment.get(pk=assignment_pk)
	students = Student.all()
	grades = assignment.get_grades()
	student_pks = [s.pk for s in students]
	g_by_student_pk = dict([(g.student_pk, g) for g in grades])
	for s in students:
		s.grade = g_by_student_pk.get(s.pk)
	return render_template('assignment_view.html', assignment=assignment,
			students=students)

@app.route('/assignments/update/<int:assignment_pk>/', methods=['GET', 'POST'])
def assignment_update(assignment_pk):
	if request.method == 'GET':
		query = 'SELECT * FROM assignment WHERE pk=?'
		assignment = query_db(query, [assignment_pk])[0]
		return render_template('assignment_update.html', assignment=assignment)
	elif request.method == 'POST':
		query = 'UPDATE assignment SET name=:name, description=:description, due_date=date(:due_date), points=:points WHERE pk=:pk'
		args = dict(request.form.to_dict(flat=True), pk=assignment_pk)
		g.db.execute(query, args)
		g.db.commit()
		return redirect(url_for('assignments'))

@app.route('/assignment/update_grades/<int:assignment_pk>/', methods=['GET', 'POST'])
def assignment_grades_update(assignment_pk):
	if request.method == 'GET':
		assignment_query = 'SELECT * from assignment WHERE pk=?'
		assignment = query_db(assignment_query, [assignment_pk])[0]
		students_grade_query = """
			SELECT student.first_name, student.last_name, student.pk,
				grade.points
			FROM student LEFT JOIN grade 
			ON grade.student_pk = student.pk AND grade.assignment_pk=? 
			ORDER BY student.first_name, student.last_name, student.pk"""
		students_grade = query_db(students_grade_query, [assignment_pk])
		return render_template("assignment_grades_update.html",
				assignment=assignment, students_grade=students_grade)
	if request.method == 'POST':
		students_grades = {} # keys are student pks, values are grades
		graded_students_query = """
			SELECT student_pk 
			FROM grade 
			WHERE assignment_pk=?"""
		graded_students = g.db.execute(graded_students_query, [assignment_pk])
		graded_students = graded_students.fetchall()
		graded_students = [row[0] for row in graded_students]
		for key, value in request.form.iteritems():
			student_pk = int(key[len("student_"):]) #Strips off "student_"
			if student_pk in graded_students:
				if value == "":
					g.db.execute("""
						DELETE FROM grade
						WHERE student_pk=? AND assignment_pk=?""",
						[student_pk, assignment_pk])
					g.db.commit()
				else:
					# TODO: Sanitize here. Message flash on error.
					# TODO: This would be a good place to use executemany.
					# Assuming that's more efficient.
					points = int(value)
					g.db.execute("""
						UPDATE grade
						SET points=? 
						WHERE student_pk=? AND assignment_pk=?""",
						[points, student_pk, assignment_pk])
			else: #grade does not already exist, so create it
				points = int(value)
				g.db.execute("""
					INSERT INTO grade
					(student_pk, assignment_pk, points)
					VALUES (?, ?, ?)""",
					[student_pk, assignment_pk, points])
		g.db.commit()
		return redirect(url_for('assignment_view',
			assignment_pk=assignment_pk))

@app.route('/assignments/delete/<int:assignment_pk>/', methods=['GET', 'POST'])
def assignment_delete(assignment_pk):
	assignment = Assignment.get(pk=assignment_pk)
	if request.method == 'GET':
		return render_template('assignment_delete.html',
				assignment=assignment)
	if request.method == 'POST':
		assignment.delete()
		return redirect(url_for('assignments'))


if __name__ == '__main__':
    app.run(debug=True)
