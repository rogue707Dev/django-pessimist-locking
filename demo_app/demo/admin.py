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
from django.contrib import admin
from .models import Cheese
from pessimist_locking.admin import SoftPessimisticChangeLockModelAdmin


@admin.register(Cheese)
class CheeseAdmin(SoftPessimisticChangeLockModelAdmin):
    pass
