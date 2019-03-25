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
from django.conf import settings
from django.contrib.admin.options import get_content_type_for_model
from django.db import connection
from django.utils.translation import ugettext as _
from django.utils import timezone
from pessimist_locking.exceptions import SoftPessimisticLockException
from pessimist_locking.models import SoftPessimisticChangeLock
from pessimist_locking.utils import get_client_ip
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)


DEFAULT_LOCK_DURATION_MINUTES = 5


def get_lock_duration():
    return getattr(settings, 'LOCK_DURATION_MINUTES', DEFAULT_LOCK_DURATION_MINUTES)


def cleanup_outdated_pessimistic_locks():
    """
    deletes all outdated locks form database - outdated either by created_at or by updated_at field.
    created_at outdated = created_at < settings.LOCK_DURATION_MINUTES & updated_at = NULL
    updated_at outdated = created_at < settings.LOCK_DURATION_MINUTES & updated_at < settings.LOCK_DURATION_MINUTES
    """
    logger.debug("cleanup_outdated_pessimistic_locks")

    time_threshold = timezone.now() - timedelta(minutes=get_lock_duration())

    query = """delete from {}
      where (
        created_at < %s
        and updated_at is NULL
      ) or (
        updated_at is not NULL
        and updated_at < %s
      )
    """.format(SoftPessimisticChangeLock._meta.db_table)

    return connection.cursor().execute(query, [time_threshold, time_threshold])


def get_pessimistic_lock(content_type_id, object_id, timestamp=None):
    """
    looks up database for existing lock on model - that is instance_id and content_type_id in combination with
    created_at and updated_at timestamp fields. method is used internally and has no real value to be used from
    clients directly

    also calls cleanup_outdated_pessimistic_locks to handle outdated locks.
    only one lock item is return - even if there would be more in the database.

    :param content_type_id: content-type of the model to lock
    :param object_id: pk of the model instance to lock
    :param timestamp: datetime to avoid monkey-patching for tests
    :return: found lock or None
    """

    if timestamp == None:
        timestamp = timezone.now()

    logger.debug("get_pessimistic_lock  current_content_type_id: %s, current_object_id: %s", content_type_id, object_id)

    # first to a cleanup - this is the simplest implementation
    cleanup_outdated_pessimistic_locks()

    time_threshold = timestamp - timedelta(minutes=get_lock_duration())

    query = """select *
      from {}
      where content_type_id = %s
      and object_id = %s
      and((
          created_at > %s
          and updated_at is NULL
        ) or (
          updated_at is not NULL
          and updated_at > %s
        )
      )""".format(SoftPessimisticChangeLock._meta.db_table)

    query_result = SoftPessimisticChangeLock.objects.raw(query, [
        content_type_id,
        object_id,
        time_threshold,
        time_threshold
    ])

    lock_objects = list(query_result)
    if len(lock_objects) == 0:
        return None

    return lock_objects[0]


def get_pessimistic_lock_for_model(model, timestamp=None):
    """
    just a shortshand for get_pessimistic_lock
    """
    logger.debug("get_pessimistic_lock_for_model model: %s timestamp: %s", model, timestamp)

    current_content_type_id = get_content_type_for_model(model).pk

    current_object_id = model.pk

    return get_pessimistic_lock(current_content_type_id, current_object_id, timestamp)


def add_pessimistic_lock(request, user, model, timestamp=None):
    """
    this is the main entry to clients of locking_services. try to get a lock on model for a user - the method looks
    up lock-database entries and than compares given params for user/user-ip/model and timestamp to decide about giving
    a pessimistic lock or raise a SoftPessimisticWriteLockException in case of lock exists for another user.

    this implementation also updates an existing lock. so this method should also be called when user is still
    interacting with the locked model.

    :param  request: current django request
    :param  user: model object of current user
    :param  model: model object of current model
    :param  timestamp: datetime to avoid monkey-patching for tests
    :return created lock object
    :raises SoftPessimisticLockException in case other user holds a pessimistic lock on that models-instance
    """

    if timestamp == None:
        timestamp = timezone.now()

    logger.debug("add_pessimistic_lock / request: %s, user: %s, model: %s", request, user, model)

    current_content_type_id = get_content_type_for_model(model).pk
    current_object_id = model.pk

    # get valid lock
    existing_lock = get_pessimistic_lock(current_content_type_id, current_object_id, timestamp)

    current_remote_ip = get_client_ip(request)
    current_user_id = user.pk

    if existing_lock is not None:

        if existing_lock.user_id != current_user_id or existing_lock.user_ip_address != current_remote_ip:
            raise SoftPessimisticLockException(_('Locked by another User!'), existing_lock)

        else:
            existing_lock.updated_at = timestamp
            existing_lock.save(force_update=True)
            return existing_lock

    logger.debug("no lock for: %s so let's created on for user_id: %s / ip: %s", model, current_user_id, current_remote_ip)

    new_lock = SoftPessimisticChangeLock(
        user_id=current_user_id,
        content_type_id=current_content_type_id,
        object_id=current_object_id,
        user_ip_address=current_remote_ip,
        created_at=timestamp
    )

    new_lock.save(force_insert=True)
    return new_lock


def release_pessimistic_locks_of_user(ip_address, user):
    """
    releases all locks of a given user / uio-address combination.
    this can be useful if a logout signal was caught or the user went to some other page on the app.

    :param ip_address: current django request
    :param user: model object of current user
    :return: count of deleted objects
    """
    logger.debug("release_pessimistic_locks_of_user / ip_address: %s, user: %s", ip_address, user)

    current_user_id = user.pk

    query = """delete from {}
      where user_id = %s
      and user_ip_address = %s
    """.format(SoftPessimisticChangeLock._meta.db_table)

    return connection.cursor().execute(query, [current_user_id, ip_address])
