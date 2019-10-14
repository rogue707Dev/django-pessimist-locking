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
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class SoftPessimisticChangeLock(models.Model):
    """Implements a variation of pessimistic offline locking pattern.

    this is done by adding an extra table to the database for saving acquired locks. there are no hard locks on
    database layer (such as select_for_update would produce). a lock is represented by the combination of: user_id,
    user_ip_address, content_type_id and instance_id. so a user concurrently logged in on multiple devices can be handled.

    to model automatic timeouts the fields created_at and updated_at are used. they use of 2 fields was argued by easing
    debugging and testing (compared to a single field 'timestamp').

    model makes use of generic foreignkeys to separate this feature completely from other apps.
    """

    user_id = models.PositiveIntegerField(null=False, blank=False, db_index=True)

    user_ip_address = models.CharField(max_length=50, null=False, blank=False, db_index=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(null=True, blank=True, editable=False)

    updated_at = models.DateTimeField(null=True, blank=True, editable=False)

    # NOTE: MySQL 8.0.16 is the first version that supports CHECK constraints.
    # so this will not work for mysql … we need something else there are many legacy systems (with very old mysql)
    # to be supported.
    #
    # class Meta:
    #     constraints = [
    #         models.CheckConstraint(
    #             check=(
    #                 ~models.Q(
    #                     user_ip_address__exact='',
    #                     user_ip_address__isnull=True,
    #                 )
    #             ),
    #             name='locking_ip_check'
    #         ),
    #         models.CheckConstraint(
    #             check=(
    #                 models.Q(updated_at__isnull=True) |
    #                 models.Q(updated_at__gt=F('created_at'))
    #             ),
    #             name='locking_updated_check'
    #         )
    #     ]

    def save(self, *args, **kwargs):
        # but that didn't work - MIND: blank seems only be used for validation
        if self.created_at is None:
            self.created_at = timezone.now()

        super(SoftPessimisticChangeLock, self).save(*args, **kwargs)

    def __str__(self):
        return "{}: user_id: {} user_ip_address: {} content_object: {}".format(
            self.id, self.user_id, self.user_ip_address, self.content_object
        )
