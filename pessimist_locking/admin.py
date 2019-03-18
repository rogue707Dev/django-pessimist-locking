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
from django.contrib.auth.models import User
from django.core.checks import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from pessimist_locking.exceptions import SoftPessimisticLockException
from pessimist_locking.locking_services import add_pessimistic_lock
import logging


logger = logging.getLogger(__name__)


class SoftPessimisticChangeLockModelAdmin(admin.ModelAdmin):
    """
    subclass to ModelAdmin that brings in pessimistic locking
    """

    def change_view(self, request, object_id, form_url='', extra_context=None):
        logger.debug("change_view object_id: %s", object_id)

        try:
            return super(SoftPessimisticChangeLockModelAdmin, self).change_view(request, object_id, form_url, extra_context)

        except SoftPessimisticLockException as e:
            logger.info("object_id: {} locked".format(object_id))

            opts = self.model._meta

            self.message_user(
                request,
                _('[%(model)s id:%(obj)s] wird gerade von %(user)s auf %(ip)s bearbeitet.') % {
                    'model': opts.verbose_name,
                    'obj': object_id,
                    'user': User.objects.get(id=e.lock.user_id),
                    'ip': e.lock.user_ip_address
                },
                messages.ERROR
            )

            # as an alternative: set everything readonly by overriding has_change_permission of modelAdmin
            return redirect(reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name)))

    def get_object(self, request, object_id, from_field=None, temp_nolock=False):
        logger.debug("get_object object_id: %s", object_id)

        # first get the instance
        instance = super(SoftPessimisticChangeLockModelAdmin, self).get_object(request, object_id, from_field)

        url_name = request.resolver_match.url_name
        change_permission = "%s.%s%s" % (self.model._meta.app_label, 'change_', self.model._meta.model_name)
        if request.user.has_perm(change_permission):
            logger.debug("check locks as user has change_permission: %s", change_permission)

            if url_name is not None and url_name.endswith('_change') and not temp_nolock:
                try:
                    add_pessimistic_lock(request, request.user, instance)

                except SoftPessimisticLockException as e:
                    raise e

        return instance
