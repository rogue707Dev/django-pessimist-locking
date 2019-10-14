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
from django.db import transaction, IntegrityError
from django.utils import timezone
from pessimist_locking.locking_services import get_lock_duration, cleanup_outdated_pessimistic_locks, \
    get_pessimistic_lock
from pessimist_locking.models import SoftPessimisticChangeLock
from datetime import timedelta
import pytest


@pytest.mark.skip(reason='dropped db constraints since unsupported in mysql')
@pytest.mark.django_db
def test_model_updatedat_constraints():
    current_time = timezone.now()

    try:
        with transaction.atomic():
            lock = SoftPessimisticChangeLock(
                user_id=1,
                user_ip_address="127.0.0.1",
                content_type_id=1,
                object_id=1,
                created_at=current_time - timedelta(minutes=10),
                updated_at=current_time - timedelta(minutes=20),
            )
            lock.save()

        pytest.fail("expected IntegrityError for user_id")

    except IntegrityError as e:
        # name of custom constraint
        assert "locking_updated_check" in e.__str__()


@pytest.mark.django_db
def test_cleanup_created_at():
    # first ensure correct setting here
    assert get_lock_duration() == 5

    current_time = timezone.now()
    ts = current_time - timedelta(minutes=1)

    # create a lock and see if given created_at is used
    createdat_tobe_not_deleted = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=ts
    )

    createdat_tobe_not_deleted.save()
    assert SoftPessimisticChangeLock.objects.count() == 1

    retrieve_lock1 = SoftPessimisticChangeLock.objects.get(user_id=1)
    assert retrieve_lock1 is not None
    assert ts == retrieve_lock1.created_at

    # lock that at the threshold
    createdat_tobe_deleted_1 = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=5)
    )
    createdat_tobe_deleted_1.save()
    assert createdat_tobe_deleted_1.id is not None

    # lock that is over the threshold
    createdat_tobe_deleted_2 = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=15)
    )
    createdat_tobe_deleted_2.save()
    assert createdat_tobe_deleted_2.id is not None

    # lock that is under the threshold
    createdat_tobe_not_deleted_1 = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=4)
    )
    createdat_tobe_not_deleted_1.save()
    assert createdat_tobe_not_deleted_1.id is not None
    assert SoftPessimisticChangeLock.objects.get(id=createdat_tobe_not_deleted_1.id).updated_at is None

    # check amount
    assert SoftPessimisticChangeLock.objects.count() == 4

    # run cleanup
    cleanup_outdated_pessimistic_locks()

    # verfy existing locks
    assert SoftPessimisticChangeLock.objects.count() == 2
    assert createdat_tobe_not_deleted in SoftPessimisticChangeLock.objects.all()
    assert createdat_tobe_not_deleted_1 in SoftPessimisticChangeLock.objects.all()


@pytest.mark.django_db
def test_cleanup_updated_at():
    # first ensure correct setting here
    assert get_lock_duration() == 5

    current_time = timezone.now()

    # now verify updated at fields
    updatedat_tobe_not_deleted = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=40),  # outdated
        updated_at=current_time - timedelta(minutes=1)
    )
    updatedat_tobe_not_deleted.save()
    assert updatedat_tobe_not_deleted.id is not None

    # updated_at at the treshold
    updatedat_tobe_deleted1 = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=40),  # outdated
        updated_at=current_time - timedelta(minutes=5)  # at the threshold
    )
    updatedat_tobe_deleted1.save()
    assert updatedat_tobe_deleted1.id is not None

    # updated_at over the treshold
    updatedat_tobe_deleted2 = SoftPessimisticChangeLock(
        user_id=1,
        content_type_id=1,
        object_id=1,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=40),  # outdated
        updated_at=current_time - timedelta(minutes=30)
    )
    updatedat_tobe_deleted2.save()
    assert updatedat_tobe_deleted2.id is not None

    # check amount
    assert SoftPessimisticChangeLock.objects.count() == 3

    # run cleanup
    cleanup_outdated_pessimistic_locks()

    assert SoftPessimisticChangeLock.objects.count() == 1
    assert updatedat_tobe_not_deleted in SoftPessimisticChangeLock.objects.all()


@pytest.mark.django_db
def test_getter_cleanup_call():

    result = SoftPessimisticChangeLock.objects.all()
    assert len(result) == 0

    # create timestamp
    current_time = timezone.now()

    # create an outdated lock
    outdated_lock = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=2,
        object_id=2,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=40),  # outdated
        updated_at=current_time - timedelta(minutes=10)
    )

    # to see objects.create is doing the expected
    assert outdated_lock.id is not None
    assert SoftPessimisticChangeLock.objects.count() == 1

    # check cleanup_outdated_pessimistic_locks was called internally
    lock = get_pessimistic_lock(None, None, current_time)

    assert lock is None
    assert SoftPessimisticChangeLock.objects.count() == 0


@pytest.mark.django_db
def test_getter_cleanup_call_ts_default():
    result = SoftPessimisticChangeLock.objects.all()
    assert len(result) == 0

    # create timestamp
    current_time = timezone.now()

    # create an outdated lock
    outdated_lock = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=1,
        object_id=2,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=40),  # outdated
        updated_at=current_time - timedelta(minutes=10)
    )

    # to see objects.create is doing the expected
    assert outdated_lock.id is not None
    assert SoftPessimisticChangeLock.objects.count() == 1

    # check cleanup_outdated_pessimistic_locks was called internally
    lock = get_pessimistic_lock(content_type_id=1, object_id=2)
    assert lock is None
    assert SoftPessimisticChangeLock.objects.count() == 0


@pytest.mark.django_db
def test_getter_singleresult():
    result = SoftPessimisticChangeLock.objects.all()
    assert len(result) == 0

    # create timestamp
    current_time = timezone.now()

    # now lets create 2 valid locks - that could only be possible as manual db-insert or programming error
    lock1 = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=2,
        object_id=2,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=1)
    )

    assert lock1.id is not None
    assert lock1.created_at is not None
    assert lock1.updated_at is None

    lock2 = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=2,
        object_id=2,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=2)
    )

    assert lock2.id is not None
    assert lock2.created_at is not None
    assert lock2.updated_at is None

    assert SoftPessimisticChangeLock.objects.count() == 2

    lock = get_pessimistic_lock(content_type_id=2, object_id=2, timestamp=current_time)

    assert lock is not None
    assert isinstance(lock, SoftPessimisticChangeLock)
    assert SoftPessimisticChangeLock.objects.count() == 2


@pytest.mark.django_db
def test_getter_createdat():
    assert SoftPessimisticChangeLock.objects.count() == 0

    # create timestamp
    current_time = timezone.now()

    lock1 = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=4,
        object_id=4,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=6)
    )
    assert lock1.id is not None

    lock2 = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=4,
        object_id=4,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=4)
    )
    assert lock2.id is not None

    # to ensure where cause is correct
    other_obj_lock = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=4,
        object_id=5,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=4)
    )
    assert other_obj_lock.id is not None

    assert SoftPessimisticChangeLock.objects.count() == 3

    lock = get_pessimistic_lock(content_type_id=4, object_id=4, timestamp=current_time)
    assert lock is not None
    assert SoftPessimisticChangeLock.objects.count() == 2
    assert lock == lock2


@pytest.mark.django_db
def test_getter_updatedat():
    assert SoftPessimisticChangeLock.objects.count() == 0

    # create timestamp
    current_time = timezone.now()

    lock1 = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=5,
        object_id=5,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=60),
        updated_at=current_time - timedelta(minutes=10)
    )
    assert lock1.id is not None

    lock2 = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=5,
        object_id=5,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=60),
        updated_at=current_time - timedelta(minutes=1)
    )
    assert lock2.id is not None

    # to ensure where cause is correct
    other_obj_lock = SoftPessimisticChangeLock.objects.create(
        user_id=1,
        content_type_id=6,
        object_id=5,
        user_ip_address="127.0.0.1",
        created_at=current_time - timedelta(minutes=60),
        updated_at=current_time - timedelta(minutes=1)
    )
    assert other_obj_lock.id is not None

    assert SoftPessimisticChangeLock.objects.count() == 3

    lock = get_pessimistic_lock(content_type_id=5, object_id=5, timestamp=current_time)

    assert lock is not None
    assert SoftPessimisticChangeLock.objects.count() == 2
    assert lock == lock2
