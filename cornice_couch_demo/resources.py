import datetime
from couchdb.mapping import Document, DateTimeField, TextField, ViewField
import cryptacular.bcrypt
from pyramid.security import Everyone, Authenticated, Allow

class ViewRegistry(object):
    """ All views must be synced to the database.
    This class provides a way to register views and then sync them
    later with an injected database.
    """
    def __init__(self):
        self.registry = set()

    def register(self, view):
        self.registry.add(view)

    def sync(self, db):
        for view in self.registry:
            view.sync(db)

view_registry = ViewRegistry()

class Root(object):
    __acl__ = [
        (Allow, Everyone, "view"),
        (Allow, Authenticated, "authenticated"),
    ]

    def __init__(self, request):
        self.request = request

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()

class User(Document):
    doc_type = TextField(default='User')
    username = TextField()
    # The password value is encrypted.
    password = TextField()
    by_username = ViewField('users', '''\
        function(doc) {
            if(doc.doc_type == 'User') {
                emit(doc.username, doc);
            }
        }''')

    def set_password(self, password):
        """ ``password`` is plain text"""
        self.password = unicode(crypt.encode(password))

    def check_password(self, password):
        """ ``password`` is plain text"""
        return crypt.check(self.password, password)

view_registry.register(User.by_username)

class Article(Document):
    doc_type = TextField(default='Article')
    username = TextField()
    title = TextField()
    body = TextField()
    created = DateTimeField()
    modified = DateTimeField()
    by_created = ViewField('articles', '''\
        function(doc) {
            if(doc.doc_type == 'Article') {
                emit(doc.created, doc.title);
            }
        }''')
    by_username_and_created = ViewField('articles', '''\
        function(doc) {
            if(doc.doc_type == 'Article') {
                emit([doc.username, doc.created], doc.title);
            }
        }''')

    def store(self, db):
        self.modified = datetime.datetime.utcnow()
        if not self.created:
            self.created = self.modified
        Document.store(self, db)

view_registry.register(Article.by_created)
view_registry.register(Article.by_username_and_created)

#
# Some convenience functions (to simplify view code).
#

def delete_document(db, document):
    """ Delete data for an instance of Document from db. """
    return db.delete(document._data)

def get_user(db, username):
    result = User.by_username(db, key=username)
    if result:
        return result.rows[0]
    return None

def get_usernames(db):
    return [u.username for u in User.by_username(db)]

def add_user(db, username, password):
    user = User(username=username)
    user.set_password(password)
    user.store(db)
    return user

def add_article(db, title, body, username):
    article = Article(
        title=title,
        body=body,
        username=username,
    )
    article.store(db)
    return article

def get_all_articles(db):
    return Article.by_created(db, include_docs=True, descending=True)

def get_articles_for_username(db, username):
    # If you're new to CouchDB views, the startkey and endkey values
    # may need some explanation.  Refer to:
    # http://wiki.apache.org/couchdb/View_collation#Complex_keys
    # for querying by first item in a key's array value.
    # http://wiki.apache.org/couchdb/HTTP_view_API
    # for swapping startkey and endkey values when descending.
    return Article.by_username_and_created(
           db, include_docs=True, descending=True,
           startkey=[username, {}], endkey=[username])
