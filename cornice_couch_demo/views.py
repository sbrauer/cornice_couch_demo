from cornice import Service
from cornice.resource import resource, view
from pyramid.httpexceptions import HTTPNotFound, HTTPForbidden
from pyramid.security import authenticated_userid, effective_principals
from pyramid.view import view_config
from . import resources

#
# Some simple generic services.
#

hello = Service(name='hello', path='/', description="Are you there?")

@hello.get()
def hello_get(request):
    """Returns Hello in JSON."""
    return {'Hello': 'World'}

whoami = Service(name='whoami', path='/whoami', description="Show credentials")

@whoami.get()
def whoami_get(request):
    """View returning the authenticated user's credentials."""
    username = authenticated_userid(request)
    principals = effective_principals(request)
    return dict(username=username, principals=principals)

#
# User-related services.
#

# Note that this could (should?) just be a Service since we're 
# only using the collection ("/users" and not "/users/{id}").
@resource(collection_path='/users', path='/users/{id}')
class User(object):
    def __init__(self, request):
        self.request = request

    def collection_get(self):
        """ Return a list of all usernames. """
        # Note: In a real app, use pagination/batching and/or search/filtering.
        return dict(users=resources.get_usernames(self.request.db))

    def valid_user(self, request):
        try:
            user_data = request.json_body
        except ValueError:
            request.errors.add('body', 'user_data', 'Not valid JSON')
            return
    
        # Make sure we have the required fields.
        for var in ('username', 'password'):
            value = user_data.get(var, '').strip()
            if value:
                user_data[var] = value
            else:
                request.errors.add('body', var, 'Missing.')
                return
    
        # Make sure username is unique.
        existing_user = resources.get_user(request.db, user_data['username'])
        if existing_user:
            request.errors.add('body', 'username', 'Already in use.')
            return

        request.validated['user_data'] = user_data

    @view(validators=('valid_user'))
    def collection_post(self):
        resources.add_user(
            self.request.db,
            username=self.request.validated['user_data']['username'],
            password=self.request.validated['user_data']['password'])
        return dict(ok=True)

mypassword = Service(name='mypassword', path='/mypassword', description="Change my password", permission='authenticated')

def valid_password(request):
    """ We expect the request body (plain text) to be the new password. """
    newpassword = request.body.strip()
    if newpassword:
        request.validated['newpassword'] = newpassword
    else:
        request.errors.add('body', 'newpassword', 'Missing.')

@mypassword.post(validators=valid_password)
def mypassword_post(request):
    """Change the authenticated user's password."""
    user = request.user
    user.set_password(request.validated['newpassword'])
    user.store(request.db)
    return dict(ok=True)

#
# Article-related services.
#

@resource(collection_path='/articles', path='/articles/{id}')
class Article(object):
    def __init__(self, request):
        self.request = request

    def collection_get(self):
        """ List of all articles in reverse created order. """
        # Note: In a real app, use pagination/batching.
        return dict(articles=[a._data for a in resources.get_all_articles(self.request.db)])

    def valid_article(self, request):
        try:
            article_data = request.json_body
        except ValueError:
            request.errors.add('body', 'article_data', 'Not valid JSON')
            return
    
        # Make sure we have the required fields.
        for var in ('title', 'body'):
            value = article_data.get(var, '').strip()
            if value:
                article_data[var] = value
            else:
                request.errors.add('body', var, 'Missing.')
                return
    
        article_data['username'] = authenticated_userid(request)
        request.validated['article_data'] = article_data

    @view(validators=('valid_article'), permission='authenticated')
    def collection_post(self):
        resources.add_article(
            self.request.db,
            title=self.request.validated['article_data']['title'],
            body=self.request.validated['article_data']['body'],
            username=self.request.validated['article_data']['username'],
        )
        return dict(ok=True)

    def get(self):
        """ Get a single article. """
        id = self.request.matchdict['id']
        article = resources.Article.load(self.request.db, id)
        if article:
            return article._data
        else:
            return HTTPNotFound()

    def valid_owner(self, request):
        id = self.request.matchdict['id']
        article = resources.Article.load(self.request.db, id)
        if article:
            if article.username != authenticated_userid(request):
                return HTTPForbidden("Must authenticate as article owner.")
        request.validated['article'] = article

    @view(validators=('valid_owner', 'valid_article'), permission='authenticated')
    def put(self):
        """ Update a single article. """
        # Note: In a real app, consider optimistic concurrency control.
        article = self.request.validated['article']
        if article:
            article.title = self.request.validated['article_data']['title']
            article.body = self.request.validated['article_data']['body']
            article.store(self.request.db)
            return dict(ok=True)
        else:
            return HTTPNotFound()

    @view(validators=('valid_owner'), permission='authenticated')
    def delete(self):
        """ Delete a single article. """
        article = self.request.validated['article']
        if article:
            resources.delete_document(self.request.db, article)
            return dict(ok=True)
        else:
            return HTTPNotFound()

articles_by_user = Service(name='articles_by_user', path='/articles/by-user/{username}', description="List articles for given user")

@articles_by_user.get()
def articles_by_user_get(request):
    """ List of all articles for a given user ID in reverse created order. """
    username = request.matchdict['username']
    return dict(articles=
        [a._data for a in resources.get_articles_for_username(
            request.db, username)
        ])
