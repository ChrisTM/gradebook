import sqlite3
from contextlib import closing

DATABASE = "./gradebook.db"

class Database(object):
	def __init__(self, database_name):
		"""Create an Database object associated with sqlite3 file
		`database_name`"""
		self.database_name = database_name

	def init_db(self):
		with closing(self.connect()) as db:
			with open("schema.sql") as f:
				db.cursor().executescript(f.read())
			with open("testdata.sql") as f:
				db.cursor().executescript(f.read())
			db.commit()

	def connect(self):
		"""Return a connection to the gradebook database"""
		self.con = sqlite3.connect(self.database_name)
		self.con.row_factory = sqlite3.Row
		# By default, foreign_key constraints are not enforced. This is enabled especially for the cascading deletes for students and assignments.
		self.con.execute("PRAGMA foreign_keys=ON")
		return self.con

	# Commit can be false by default because of the implicit commits
	# sqlite3 has, and because we commit on connection close
	def execute(self, query, args=None, commit=False):
		cur = self.con.cursor()
		cur.execute(query, args or ())
		if commit:
			self.con.commit()
		return cur

	def close(self):
		self.con.commit()
		self.con.close()

db = Database(DATABASE)

class Model(object):
	_table_name = None
	_default_order = None
	_column_names = None

	def __init__(self, **kwargs):
		print kwargs
		# TODO: validation for setting proper keys as per column defs
		for column in self._column_names + ['pk']:
			setattr(self, column, kwargs.get(column))
		self._in_db = False

	def __repr__(self):
		return "<{0}: {1}>".format(self.__class__.__name__, self.pk)

	@classmethod
	def _from_row(cls, row_dict):
		obj = cls(**row_dict)
		obj._in_db = True
		return obj

	@classmethod
	def get(cls, pk=None):
		query = "SELECT * FROM {0} WHERE pk=?".format(cls._table_name)
		cur = db.execute(query, (pk, ))
		row = cur.fetchone()
		obj = cls._from_row(row)
		return obj

	@classmethod
	def all(cls, order=None):
		order = order or cls._default_order
		if order:
			query = "SELECT * FROM {0} ORDER BY {1} COLLATE NOCASE"
			query = query.format(cls._table_name, order)
		else:
			query = "SELECT * FROM {0}".format(cls._table_name)
		cur = db.execute(query)
		rows = cur.fetchall()
		objs = [cls._from_row(row) for row in rows]
		return objs

	def delete(self):
		if self._in_db:
			query = "DELETE FROM {0} WHERE pk=?".format(
					self.__class__._table_name)
			args = (self.pk, )
			db.execute(query, args)

class Student(Model):
	_table_name = 'student'
	_default_order = 'first_name, last_name, pk'
	_column_names = ['first_name', 'last_name', 'alias', 'grad_year', 'email']

	@property
	def full_name(self):
		full_name = ' '.join([self.first_name, self.last_name])
		# We strip to remove trailing/leading space if last or first name is
		# missing.
		return full_name.strip()

	def save(self):
		# TODO: This could benefit from getting put into the model as much as
		# possible.
		if self._in_db:
			query = """UPDATE student SET first_name=?, last_name=?, alias=?,
			grad_year=?, email=?  WHERE pk=?"""
			args = [self.first_name, self.last_name, self.alias,
					self.grad_year, self.email, self.pk]
			db.execute(query, args)
		else:
			query = """INSERT INTO student (first_name, last_name, alias,
			grad_year, email) VALUES (?, ?, ?, ?, ?)"""
			args = [self.first_name, self.last_name, self.alias,
					self.grad_year, self.email]
			cur = db.execute(query, args)
			self.pk = cur.lastrowid

	def get_grades(self):
		# TODO: Genericize get to accept kwargs and use that here:
		# return Grade.get(assignment_pk=self.pk)
		query = """SELECT * FROM grade WHERE student_pk=?"""
		args = [self.pk]
		cur = db.execute(query, args)
		rows = cur.fetchall()
		objs = [Grade._from_row(row) for row in rows]
		return objs

class Assignment(Model):
	_table_name = 'assignment'
	_default_order = '-due_date, name, pk'
	_column_names = ['name', 'description', 'comment', 'due_date', 'points', 'is_public']

	def save(self):
		# TODO: This could benefit from getting put into the model as much as
		# possible.
		print self.__dict__
		if self._in_db:
			query = """UPDATE assignment SET name=?, description=?,
			due_date=?, points=?, comment=?, is_public=? WHERE pk=?"""
			args = [self.name, self.description, self.due_date, self.points,
					self.comment, self.is_public, self.pk]
			db.execute(query, args)
		else:
			query = """INSERT INTO assignment (name, description, due_date,
			points, comment, is_public) VALUES (?, ?, ?, ?, ?, ?)"""
			args = [self.name, self.description, self.due_date, self.points,
					self.comment, self.is_public]
			cur = db.execute(query, args)
			self.pk = cur.lastrowid

	def get_grades(self):
		# TODO: Genericize get to accept kwargs and use that here:
		# return Grade.get(assignment_pk=self.pk)
		query = """SELECT * FROM grade WHERE assignment_pk=?"""
		args = [self.pk]
		cur = db.execute(query, args)
		rows = cur.fetchall()
		objs = [Grade._from_row(row) for row in rows]
		return objs

class Grade(Model):
	_table_name = 'grade'
	_default_order = 'pk'
	_column_names = ['student_pk', 'assignment_pk', 'points', 'comment']

	def save(self):
		# TODO: This could benefit from getting put into the model as much as
		# possible.
		if self._in_db:
			query = """UPDATE grade SET student_pk=?, assignment_pk=?,
			points=?, comment=? WHERE pk=?"""
			args = [self.student_pk, self.assignment_pk, self.points,
					self.comment, self.pk]
			db.execute(query, args)
		else:
			query = """INSERT INTO grade (student_pk, assignment_pk, points,
			comment) VALUES (?, ?, ?, ?)"""
			args = [self.student_pk, self.assignment_pk, self.points,
					self.comment]
			cur = db.execute(query, args)
			self.pk = cur.lastrowid
