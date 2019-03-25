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
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.urls import resolve
from pessimist_locking.locking_services import release_pessimistic_locks_of_user
from pessimist_locking.utils import get_client_ip
import logging


logger = logging.getLogger(__name__)


def get_lock_excluded_urls():
    return ['/jsi18n/', '/admin/jsi18n/', '/media/', '/static/', '/stats/', '/favicon.ico', '/login/', ] + getattr(settings, 'LOCK_EXCLUDE_URLS', [])


class SoftPessimisticLockReleaseMiddleware:
    """
    middleware to listen for users current position
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        self.process_request(request)

        return response

    def process_request(self, request):
        excluded_urls = get_lock_excluded_urls()

        client_ip = get_client_ip(request)
        path_info = request.path_info
        logger.debug("lock_handling_request_listener / client_ip: %s / path_info: %s", client_ip, path_info)

        # TODO: improve here: startswith is not always the best … think about havin '/' in excluded_urls?!
        if request.is_ajax() or any(path_info.startswith(x) for x in excluded_urls) or path_info.endswith('-upload/') or path_info.endswith('.pdf') or 'nolock' in request.GET.urlencode():
            logger.debug("url: %s is excluded from lock handling", path_info)
            return None

        try:
            logger.debug("%s is lock handling since not in exclude.list: %s", path_info, excluded_urls)

            cookie = request.COOKIES.get('sessionid')
            if cookie is None:
                logger.debug("no cookie")
                return None

            session = Session.objects.get(pk=cookie)
            if session is None:
                logger.debug("no session for cookie: %s", cookie)
                return None

            uid = session.get_decoded().get('_auth_user_id')
            url_conf = resolve(path_info)

            if url_conf.url_name is not None:
                url_name = url_conf.url_name
                url_splitted = url_name.split('_')
                permission_str = "{}_change_{}".format(url_splitted[0], url_splitted[1])

                if not url_name.endswith('_change') or not request.user.has_perm(permission_str):
                    logger.debug("path: %s", path_info)
                    release_pessimistic_locks_of_user(client_ip, User.objects.get(pk=uid))

        except:
            logger.warning("failed to resolve url: %s", path_info, exc_info=True)

        return None
