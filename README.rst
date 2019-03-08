=====
PESSIMIST LOCKING
=====

pessimistic locking is a simple django app to that extends django-admins modelAdmin to implement soft pessimistic locking.
soft pessimistic locking means: there are no hard locks on db-level but locks a stored on a dedicated table when a user
opens the change-page of django-admins modelAdmin and releases that "locks" when user leaves the change page or the locks reaches it's ttl.


Quick start
-----------
1. install the package

2. add app to settings like:

INSTALLED_APPS = (
    …,
    'pessimist_locking',
)

MIDDLEWARE = [
    …,
    'pessimist_locking.middleware.SoftPessimisticLockReleaseMiddleware',
]

3. run `python manage.py migrate` to create the SoftPessimisticChangeLock models.

4. enable admin for your project, add a model add a modeladmin by extending SoftPessimisticChangeLockModelAdmin


NOTE
-----------
1. used for for django >= 2.1

2. this app uses raw sql which is only done for postgresql
