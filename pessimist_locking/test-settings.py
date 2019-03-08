################################################################
#      _____  _____  __ __  _____  _____  _____  _____
#     |__   ||  _  ||  |  ||  _  ||__   ||__   ||  _  | .DE
#     |   __||     ||_   _||     ||   __||   __||     |
#     |_____||__|__|  |_|  |__|__||_____||_____||__|__| GMBH
#
#     ZAYAZZA PROPRIETARY/CONFIDENTIAL.
#     Copyright (c) 2019. All rights reserved.
#
################################################################


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'pessimist_locking',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pessimist',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

SECRET_KEY = 'secret-key'
