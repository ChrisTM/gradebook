import sqlite3
import re
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
	students = Student.all()
	assignments = Assignment.all()
	assignments_by_pk = dict([(a.pk, a) for a in assignments])
	for student in students:
		# Set the grades following the order specified by assignment_pks
		grades = student.get_grades()
		grades_by_pk = dict([(g.assignment_pk, g) for g in grades])
		grades = [grades_by_pk.get(pk) for pk in assignments_by_pk]
		student.has_comments = False
		for grade in grades:
			if grade.comment:
				student.has_comments = True
			grade.assignment = assignments_by_pk[grade.assignment_pk]
		student.grades = grades
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
		student = Student(
				first_name = request.form['first_name'],
				last_name = request.form['last_name'],
				alias = request.form['alias'],
				grad_year = request.form['grad_year'],
				email = request.form['email'],
				)
		student.save()
		if "create_and_add" in request.form:
			return render_template('student_create.html')
		elif "create" in request.form:
			return redirect(url_for('student_view', student_pk=student.pk))

@app.route('/students/view/<int:student_pk>/')
def student_view(student_pk):
	student = Student.get(pk=student_pk)
	return render_template("student_view.html", student=student)

@app.route('/students/update/<int:student_pk>/', methods=['GET', 'POST'])
def student_update(student_pk):
	student = Student.get(pk=student_pk)
	if request.method == 'GET':
		return render_template('student_update.html', student=student)
	elif request.method == 'POST':
		student.first_name = request.form['first_name']
		student.last_name = request.form['last_name']
		student.alias = request.form['alias']
		student.grad_year = request.form['grad_year']
		student.email = request.form['email']
		student.save()
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
		assignment = Assignment(
				name = request.form['name'],
				description = request.form['description'],
				#comment = request.form['comment'], #This causes an HTTP 400 when a value wasn't submitted in the form (because of a KeyError on the MultiDict). How stupid!
				due_date = request.form['due_date'],
				points = request.form['points'],
				)
		assignment.save()
		if "create_and_add" in request.form:
			return render_template('assignment_create.html')
		elif "create" in request.form:
			return redirect(url_for('assignment_view',
				assignment_pk=assignment.pk))

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
	assignment = Assignment.get(pk=assignment_pk)
	if request.method == 'GET':
		return render_template('assignment_update.html',
				assignment=assignment)
	elif request.method == 'POST':
		query = 'UPDATE assignment SET name=:name, description=:description, due_date=date(:due_date), points=:points WHERE pk=:pk'
		assignment.name = request.form['name']
		assignment.description = request.form['description']
		#assignment.comment = request.form['comment'] #Need to update the form to include this first, or else a 400 status code will occur
		assignment.due_date = request.form['due_date']
		assignment.points = request.form['points']
		assignment.save()
		return redirect(url_for('assignment_view',
			assignment_pk=assignment.pk))

#TODO: The POST part of this view is totally lame. It's slow, messy. Urgh.
@app.route('/assignment/update_grades/<int:assignment_pk>/', methods=['GET', 'POST'])
def assignment_grades_update(assignment_pk):

	assignment = Assignment.get(pk=assignment_pk)
	students = Student.all()
	grades = assignment.get_grades()
	# We decorate the student's with their grades
	student_pks = [s.pk for s in students]
	g_by_student_pk = dict([(grade.student_pk, grade) for grade in grades])
	for s in students:
		s.grade = g_by_student_pk.get(s.pk)

	if request.method == 'GET':
		return render_template("assignment_grades_update.html",
				assignment=assignment, students=students)
	if request.method == 'POST':
		# Corral the form data
		form_data = {}
		ex = re.compile(r"^student_(?P<student_pk>\d+)_(?P<data_type>comment|points)$")
		for key, value in request.form.iteritems():
			res = ex.match(key)
			if res is None:
				continue
			info = res.groupdict()
			pk = int(info['student_pk'])
			if not form_data.has_key(pk):
				form_data[pk] = {}
			if info['data_type'] == 'points':
				try:
					points = int(value)
				except ValueError:
					points = ""
				form_data[pk]['points'] = points
			if info['data_type'] == 'comment':
				form_data[pk]['comment'] = value

		for student_pk, info in form_data.iteritems():
			if g_by_student_pk.has_key(student_pk):
				grade = g_by_student_pk[student_pk]
				grade.points = info['points']
				grade.comment = info['comment']
				grade.save()
			else:
				grade = Grade(student_pk=student_pk,
						assignment_pk=assignment.pk, 
						points=info['points'],
						comment=info['comment'])
				grade.save()
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
