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
    return render_template("gradebook.html")


@app.route('/students/')
def students():
    students = query_db('SELECT * FROM student')
    return render_template('students.html', students=students)

@app.route('/students/create/', methods=['GET', 'POST'])
def student_create():
	if request.method == "GET":
		return render_template('student_create.html')
	elif request.method == "POST":
		g.db.execute('INSERT INTO student (first_name, last_name, alias, grad_year, email) values (:first_name, :last_name, :alias, :grad_year, :email)', request.form)
		g.db.commit()
		if "create_and_add" in request.form:
			return render_template('student_create.html')
		elif "create" in request.form:
			return redirect(url_for('students'))

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
		return redirect(url_for('students'))

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
    return render_template('assignments.html', assignments=assignments)

@app.route('/assignments/create/', methods=['GET', 'POST'])
def assignment_create():
	if request.method == 'GET':
		return render_template('assignment_create.html')
	elif request.method == 'POST':
		g.db.execute('INSERT INTO assignment (name, description, due_date, points) values (:name, :description, :due_date, :points)', request.form)
		g.db.commit()
		if "create_and_add" in request.form:
			return render_template('assignment_create.html')
		elif "create" in request.form:
			return redirect(url_for('assignments'))

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
