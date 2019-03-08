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

__version__ = '0.1'

# synonym
VERSION = __version__


# TODO: possible improvement
# def cleanup_logs(sender, user, request, **kwargs):
#     try:
#         release_pessimistic_locks_of_user(get_client_ip(request), user)
#
#     except:
#         logging.getLogger(__name__).error("failed to cleanup lock for logged-out user: %s", user, exc_info=True)
#
#
# user_logged_out.connect(cleanup_logs)
