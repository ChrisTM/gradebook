import sqlite3
from gradebook import app
from contextlib import closing

class Database(object):
	def __init__(self, database_name):
		"""Create an Database object associated with sqlite3 file
		`database_name`"""
		self.database_name = database_name

	def init_db(self):
		with closing(self.connect()) as db:
			with app.open_resource("schema.sql") as f:
				db.cursor().executescript(f.read())
			with app.open_resource("testdata.sql") as f:
				db.cursor().executescript(f.read())
			db.commit()

	def connect(self):
		"""Return a connection to the gradebook database"""
		self.con = sqlite3.connect(self.database_name)
		self.con.row_factory = sqlite3.Row
		return self.con

	def execute(self, query, args=None, commit=True):
		cur = self.con.cursor()
		res = cur.execute(query, args or ())
		if commit:
			self.con.commit()
		return res

	def close():
		self.con.close()

db = Database(app.config['DATABASE'])
db.connect()


class Student(object):
	def __init__(self, pk=None, first_name=None, last_name=None, alias=None,
			grad_year=None, email=None):
		self.pk = pk
		self.first_name = first_name
		self.last_name = last_name
		self.alias = alias
		self.grad_year = grad_year
		self.email = email
		self._in_db = False

	def full_name(self):
		return ' '.join([self.first_name, self.last_name])

	@classmethod
	def _from_row(cls, row_object):
		obj = cls()
		for key in row_object.keys():
			setattr(obj, key, row_object[key])
		obj._in_db = True
		return obj

	@classmethod
	def get(cls, pk=None):
		cur = db.execute("SELECT * FROM student WHERE pk=?", (pk, ))
		row = cur.fetchone()
		obj = cls._from_row(row)
		return obj

	@classmethod
	def all(cls):
		cur = db.execute("SELECT * FROM student")
		rows = cur.fetchall()
		objs = [cls._from_row(row) for row in rows]
		return objs

	def save(self):
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

	def delete(self):
		if self._in_db:
			query = "DELETE FROM student WHERE pk=?"
			args = [self.pk]
			db.execute(query, args)
