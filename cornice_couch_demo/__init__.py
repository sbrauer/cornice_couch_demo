from pyramid.config import Configurator
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import unauthenticated_userid
from couchdb import Server
from .resources import get_user, Root, view_registry

def get_couchdb(dbname, uri=None):
    if uri:
        server = Server(uri)
    else:
        server = Server()
    if dbname in server:
        db = server[dbname]
    else:
        db = server.create(dbname)
    return db

def main(global_config, **settings):
    config = Configurator(settings=settings)

    db = get_couchdb(settings['couchdb.db'], settings['couchdb.uri'])
    view_registry.sync(db)

    def get_db(request):
        return db

    config.add_request_method(get_db, 'db', reify=True)

    def get_user_object(request):
        userid = unauthenticated_userid(request)
        if userid is not None:
            return get_user(db, userid)

    config.add_request_method(get_user_object, 'user', reify=True)

    config.set_root_factory(Root)

    def check_password(username, password, request):
        user = request.user
        if user and user.check_password(password):
            # Return list of principals (other than username).
            return []
        return None
    config.set_authentication_policy(
        BasicAuthAuthenticationPolicy(check_password))
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.include("cornice")
    config.scan(".views")
    return config.make_wsgi_app()
