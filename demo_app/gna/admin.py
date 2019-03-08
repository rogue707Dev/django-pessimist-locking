from django.contrib import admin
from pessimist_locking.admin import SoftPessimisticChangeLockModelAdmin
from .models import Cheese


@admin.register(Cheese)
class CheeseAdmin(SoftPessimisticChangeLockModelAdmin):
    pass
