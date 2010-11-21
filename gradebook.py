import sqlite3
from flask import Flask, g, url_for, redirect, render_template, request
from contextlib import closing

DATABASE = "./gradebook.db"
DEBUG = True
SECRET_KEY = "'K\xaf\xd2\xc7\xc2#J\x05s%\x99J\x8e\xda\x85\xbe<t\xb2\xea\xab\xa7\xa4\xef'"

app = Flask(__name__)
app.config.from_object(__name__)



def connect_db():
    """Return a connection to the gradebook database"""
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(sqlite3.connect(app.config['DATABASE'])) as db:
        with app.open_resource("schema.sql") as f:
            db.cursor().executescript(f.read())
        with app.open_resource("testdata.sql") as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=()):
    """Return a list of dictionaries representing the results of
    cursor.execute(query, args)"""
    cursor = g.db.execute(query, args)
    attributes = [row_info[0] for row_info in cursor.description]
    rows = [dict(zip(attributes, row)) for row in cursor.fetchall()]
    return rows

@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/')
def index():
    return redirect(url_for("gradebook"), code=302)

@app.route('/gradebook/')
def gradebook():
	#TODO: This method scares me. Seek help. Improve this.
	assignments = query_db("SELECT pk, name \
			FROM assignment \
			ORDER BY assignment.due_date, assignment.pk")
	students = query_db("SELECT pk, first_name, last_name \
			FROM student \
			ORDER BY last_name, student.pk, first_name")
	grades_query = "SELECT assignment.pk, grade.points \
			FROM assignment \
			LEFT JOIN grade ON grade.assignment_pk = assignment.pk \
				AND grade.student_pk = ? \
			ORDER BY assignment.due_date, assignment.pk;"
	for student in students:
		#TODO: This gets the grades (nulls for ungraded too!)
		grades = query_db(grades_query, (str(student['pk'])))
		student['grades'] = [row['points'] for row in grades]
	print assignments
	print students
	return render_template("gradebook.html", assignments=assignments,
			students=students)


@app.route('/students/')
def students():
    students = query_db('SELECT * FROM student ORDER BY first_name')
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
			return redirect(url_for('student_view', student_id=cur.lastrowid))

@app.route('/students/view/<int:student_id>/')
def student_view(student_id):
	student_query = "SELECT * FROM student WHERE pk=?"
	student = query_db(student_query, [student_id])[0]
	return render_template("student_view.html", student=student)

@app.route('/students/update/<int:student_id>/', methods=['GET', 'POST'])
def student_update(student_id):
	if request.method == 'GET':
		query = 'SELECT * FROM student WHERE pk=?'
		student = query_db(query, [student_id])[0]
		return render_template('student_update.html', student=student)
	elif request.method == 'POST':
		query = 'UPDATE student SET first_name=:first_name, last_name=:last_name, alias=:alias, grad_year=:grad_year, email=:email WHERE pk=:pk'
		args = dict(request.form.to_dict(flat=True), pk=student_id)
		g.db.execute(query, args)
		g.db.commit()
		return redirect(url_for('student_view', student_id=student_id))

@app.route('/students/delete/<int:student_id>/', methods=['GET', 'POST'])
def student_delete(student_id):
	if request.method == 'GET':
		student = query_db('SELECT * FROM student WHERE pk=?', [student_id])[0]
		return render_template('student_delete.html', student=student)
	if request.method == 'POST':
		g.db.execute('DELETE FROM student WHERE pk=?', [student_id])
		g.db.commit()
		return redirect(url_for('students'))


@app.route('/assignments/')
def assignments():
    assignments = query_db('SELECT * FROM assignment')
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
			return redirect(url_for('assignment_view', assignment_id=cur.lastrowid))

@app.route('/assignments/view/<int:assignment_id>/')
def assignment_view(assignment_id):
	assignment_query = 'SELECT * FROM assignment WHERE pk=?'
	assignment = query_db(assignment_query, [assignment_id])[0]
	students_grade_query = """
		SELECT student.first_name, student.last_name, grade.points 
		FROM student LEFT JOIN grade 
		ON grade.student_pk = student.pk AND grade.assignment_pk=? 
		ORDER BY student.first_name, student.last_name, student.pk"""
	students_grade = query_db(students_grade_query, [assignment_id])
	return render_template('assignment_view.html', assignment=assignment,
			students_grade=students_grade)

@app.route('/assignments/update/<int:assignment_id>/', methods=['GET', 'POST'])
def assignment_update(assignment_id):
	if request.method == 'GET':
		query = 'SELECT * FROM assignment WHERE pk=?'
		assignment = query_db(query, [assignment_id])[0]
		return render_template('assignment_update.html', assignment=assignment)
	elif request.method == 'POST':
		query = 'UPDATE assignment SET name=:name, description=:description, due_date=date(:due_date), points=:points WHERE pk=:pk'
		args = dict(request.form.to_dict(flat=True), pk=assignment_id)
		g.db.execute(query, args)
		g.db.commit()
		return redirect(url_for('assignments'))

@app.route('/assignment/update_grades/<int:assignment_id>/', methods=['GET', 'POST'])
def assignment_grades_update(assignment_id):
	if request.method == 'GET':
		assignment_query = 'SELECT * from assignment WHERE pk=?'
		assignment = query_db(assignment_query, [assignment_id])[0]
		students_grade_query = """
			SELECT student.first_name, student.last_name, student.pk,
				grade.points
			FROM student LEFT JOIN grade 
			ON grade.student_pk = student.pk AND grade.assignment_pk=? 
			ORDER BY student.first_name, student.last_name, student.pk"""
		students_grade = query_db(students_grade_query, [assignment_id])
		return render_template("assignment_grades_update.html",
				assignment=assignment, students_grade=students_grade)
	if request.method == 'POST':
		students_grades = {} # keys are student pks, values are grades
		graded_students_query = """
			SELECT student_pk 
			FROM grade 
			WHERE assignment_pk=?"""
		graded_students = g.db.execute(graded_students_query, [assignment_id])
		graded_students = graded_students.fetchall()
		graded_students = [row[0] for row in graded_students]
		for key, value in request.form.iteritems():
			if value == "":
				continue
			points = int(value)
			student_pk = int(key[len("student_"):]) #Strips off "student_"
			if student_pk in graded_students:
				g.db.execute("""
					UPDATE grade
					SET points=? 
					WHERE student_pk=? AND assignment_pk=?""",
					[points, student_pk, assignment_id])
			else: #grade does not already exist, so create it
				g.db.execute("""
					INSERT INTO grade
					(student_pk, assignment_pk, points)
					VALUES (?, ?, ?)""",
					[student_pk, assignment_id, points])
		g.db.commit()
		return redirect(url_for('assignment_view',
			assignment_id=assignment_id))

@app.route('/assignments/delete/<int:assignment_id>/', methods=['GET', 'POST'])
def assignment_delete(assignment_id):
	if request.method == 'GET':
		assignment = query_db('SELECT * FROM assignment WHERE pk=?', [assignment_id])[0]
		return render_template('assignment_delete.html', assignment=assignment)
	if request.method == 'POST':
		g.db.execute('DELETE FROM assignment WHERE pk=?', [assignment_id])
		g.db.commit()
		return redirect(url_for('assignments'))


if __name__ == '__main__':
    app.run(debug=True)
