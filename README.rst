Cornice Couch Demo
==================

A demo web service based on Cornice/Pyramid.
Goes a little beyond other examples I could find by providing:

* persistence (using CouchDB, but those details are kept out of the views)
* Basic Authentication
* full CRUD example
* TODO: a front-end using Angular

The intent is only to serve as an example. The app is intentionally
very simplistic. It allows for CRUD of a very trivial article type.

Anyone can:

* get a list articles (either all articles or just articles by a specific user)
* get a single article
* get a list of all usernames
* create a new user account

Authenticated requests can:

* create new articles
* update or delete articles that the user created
* change password

Here's a quick overview of the endpoints the service will provide:

"/"
    GET - test that service is up (hello world)

"/whoami"
    GET - returns the current user's credentials

"/users"
    GET - list of all usernames
    POST - create a new user account (error if name not unique)

"/mypassword"
    PUT - update authenticated user's password; requires authenticated permission

"/articles"
    GET -list of all articles (in reverse created order)

    POST - add a new article (must be authenticated; article owned by user)

"/articles/{id}"
    GET - one article

    PUT - update article (must be authenticated as the article's owner)

    DELETE - delete article (must be authenticated as the article's owner)

"/articles/by-user/{username}"
    GET - list of articles for the user (in reverse created order)

