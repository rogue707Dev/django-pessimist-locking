=====
PESSIMIST LOCKING
=====


# soft pessimistic locking extenstion for django

 * use for for django >= 2.1
 * this app uses rawsql - done for postgresql
 
## installation

 * install package
 * add app to settings
 * add middleware to settings
 * run migration command

```python
INSTALLED_APPS = (
    # All your other apps here
    'pessimist_locking',
)

MIDDLEWARE = [
    # All your other apps here
    'pessimist_locking.middleware.SoftPessimisticLockReleaseMiddleware',
]
```

