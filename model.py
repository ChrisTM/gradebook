import sqlite3
from gradebook import app
from contextlib import closing

def init_db(filename):
    with closing(sqlite3.connect(app.config['DATABASE'])) as db:
        with app.open_resource("schema.sql") as f:
            db.cursor().executescript(f.read())
        db.commit()

class Model(object):
    """A superclass for all active records."""
    db = sqlite3.connect(app.config['DATABASE'])

    def __init__(self):
        self._in_db = False #True, if the object was pulled from the db

    def save(self):
        """INSERT or UPDATE the object into the db as necessary."""
        pass
    def create(self):
        pass
    def get(self):
        pass

class Person(Model):
    _table_name = 'person'
    def __init__(self, first_name=None, last_name=None, alias=None,
            grad_year=None, email=None):
        self.first_name = first_name
        self.last_name = last_name
        self.alias = alias
        self.grad_year = grad_year
        self.email = email

    def save(self):
        db.execute

    def __str__(self):
        if self.first_name and self.last_name:
            return "{0} {1}".format(self.first_name, self.last_name)
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
    @classmethod
    def get(pk=None):
        pass


class Assignment(Model):
    pass

class Grade(Model):
    pass

if __name__ == "__main__":
    p = Person(first_name="Chris")
