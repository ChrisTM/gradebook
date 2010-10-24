import sqlite3
from gradebook import app
from contextlib import closing

def init_db():
    with closing(sqlite3.connect(app.config['DATABASE'])) as db:
        with app.open_resource("schema.sql") as f:
            db.cursor().executescript(f.read())
        with app.open_resource("testdata.sql") as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

class Model(object):
    """A superclass for all active records."""
    db = connect_db()
    _table = None #Name of the table
    def __init__(self):
        self._in_db = False #True, if the object was pulled from the db

    @classmethod
    def _query_db(cls, query, args=()):
        """Return a list of dictionaries representing the results of
        cursor.execute(query, args)"""
        cursor = cls.db.execute(query, args)
        attributes = [x[0] for x in cursor.description]
        rows = [dict(zip(attributes, row)) for row in cursor.fetchall()]
        return rows

    @classmethod
    def get(cls, pk=None):
        if pk:
            return cls._query_db("SELECT * FROM ? WHERE pk=?;", 
                    (cls._table, pk, ))
        else:
            return cls._query_db("SELECT * FROM ?;", (cls._table, ))

    def update(self):
        pass

    def delete(self, pk=None):

    def save(self):
        """INSERT or UPDATE the object into the db as necessary."""
        pass


class Person(Model):
    def __init__(self, pk=None, first_name=None, last_name=None, alias=None,
            grad_year=None, email=None, in_db=False):
        self.first_name = first_name
        self.last_name = last_name
        self.alias = alias
        self.grad_year = grad_year
        self.email = email
        self._in_db = in_db

    def save(self):
        Model._query_db(

    def __str__(self):
        if self.first_name and self.last_name:
            return "{0} {1}".format(self.first_name, self.last_name)
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name

    @classmethod
    def get(cls, pk=None):
        if pk:
            return cls._query_db("SELECT * FROM person WHERE pk=?;", (pk, ))
        else:
            return cls._query_db("SELECT * FROM person;")


class Assignment(Model):
    pass

class Grade(Model):
    pass

if __name__ == "__main__":
    #init_db()
    print Person.get()

    p = Person(first_name="Chris")
