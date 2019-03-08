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
import logging


logger = logging.getLogger(__name__)


class SoftPessimisticLockException(Exception):
    def __init__(self, message, lock):
        super(SoftPessimisticLockException, self).__init__(message)
        self.lock = lock
