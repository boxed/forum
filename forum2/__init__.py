import cProfile
import itertools
import logging
import os
import re
import subprocess
import sys
import threading
import traceback
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from io import StringIO
from logging import addLevelName
from tempfile import NamedTemporaryFile
from time import time

from django.conf import settings
from django.db.backends import utils as django_db_utils
from termcolor import colored


MEDIA_PREFIXES = '/static/'

state = threading.local()


def get_current_request():
    return getattr(state, 'current_request', None)


def current_request_middleware(get_response):
    def middleware(request):
        state.current_request = request
        request.STACKS = defaultdict(list)
        request.DB_USING_COUNTS = defaultdict(int)

        response = get_response(request)
        return response

    return middleware


class ProfileMiddleware:
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode, is available for superuser otherwise,
    but you really shouldn't add this middleware to any production configuration.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.prof = None

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not request.profiler_disabled and (settings.DEBUG or request.user.is_staff) and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def __call__(self, request):
        # Disable profiling early on /media requests since touching request.user will add a
        # "Vary: Cookie" header to the response.
        request.profiler_disabled = False
        for prefix in MEDIA_PREFIXES:
            if request.path.startswith(prefix):
                request.profiler_disabled = True
                break
        if not request.profiler_disabled and (settings.DEBUG or request.user.is_staff) and 'prof' in request.GET:
            self.prof = cProfile.Profile()
            self.prof.enable()

        response = self.get_response(request)

        if not getattr(request, 'profiler_disabled', True) and (settings.DEBUG or (hasattr(request, 'user') and request.user.is_staff)) and 'prof' in request.GET:
            self.prof.disable()

            import pstats
            s = StringIO()
            ps = pstats.Stats(self.prof, stream=s).sort_stats('cumulative')
            ps.print_stats()

            stats_str = s.getvalue()

            if 'graph' in request.GET:
                with NamedTemporaryFile() as stats_dump:
                    ps.stream = stats_dump
                    ps.dump_stats(stats_dump.name)

                    gprof2dot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'profiling', 'gprof2dot.py')
                    gprof2dot = subprocess.Popen(('python', gprof2dot_path, '-f', 'pstats', stats_dump.name), stdout=subprocess.PIPE)

                    response['Content-Type'] = 'image/svg+xml'
                    if os.path.exists('/usr/bin/dot'):
                        response.content = subprocess.check_output(('/usr/bin/dot', '-Tsvg'), stdin=gprof2dot.stdout)
                    elif os.path.exists('/usr/local/bin/dot'):
                        response.content = subprocess.check_output(('/usr/local/bin/dot', '-Tsvg'), stdin=gprof2dot.stdout)
                    else:
                        response['Content-Type'] = 'text/plain'
                        response['Content-Disposition'] = "attachment; filename=gprof2dot-graph.txt"
                        response.content = subprocess.check_output('tee', stdin=gprof2dot.stdout)

            else:
                limit = 280
                result = []

                def strip_extra_path(s, token):
                    if token not in s:
                        return s
                    pre, _, post = s.rpartition(' ')
                    post = post[post.rindex(token) + len(token):]
                    return f'{pre} {post}'

                for line in stats_str.split("\n")[:limit]:
                    should_bold = settings.BASE_DIR in line and '/site-packages/' not in line or '/tri/' in line
                    line = line.replace(settings.BASE_DIR, '')
                    line = strip_extra_path(line, '/site-packages')
                    line = strip_extra_path(line, '/Python.framework/Versions')
                    if should_bold:
                        line = f'<b>{line}</b>'

                    line = line.replace(' ', '&nbsp;')
                    result.append(line)

                response.content = '<div style="font-family: monospace; white-space: nowrap">%s</div' % "<br />\n".join(result)

                response['Content-Type'] = 'text/html'

        return response


class LoggingMiddleware:
    """Configure root logger using settings from settings.py

    Lumber logging is controlled using the following settings:

    LOG_TO_CONSOLE = False
    CONSOLE_LEVEL = 'NOTSET'
    LOG_TO_LUMBER = True
    LUMBER_SERVICE = 'unknown'
    LUMBER_LEVEL = 'NOTSET'
    LUMBER_ADD_TAGS = []
    LOG_TO_FILE = False
    """

    def __init__(self, get_response):
        """Reconfigure root logger to log to console and/or lumber
        """
        self.get_response = get_response
        # logging.setup_logging()

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        if settings.DEBUG:
            view_func = getattr(view_func, 'wrapped_view_function', view_func)
            filename = view_func.__code__.co_filename
            lineno = view_func.__code__.co_firstlineno
            if view_func.__name__ != 'serve_static':
                log.info('Invoking view, File "{}", line {}, in {}.{}'. format(filename, lineno, view_func.__module__, view_func.__name__))

    def __call__(self, request):
        request._start_time = datetime.now()

        # Bail out early if it's a media request to avoid accessing the session
        # if request.path.startswith('/media/') or request.path == '/favicon.ico':
        #     request._audit_context_processing_done = True
        # else:
        #     set_current_request(request)
        #     if settings.DEBUG:
        #         from triengine.base.cursor import set_sql_debug
        #         sql_debug_cookie = request.COOKIES.get('sqlDebug')
        #         if sql_debug_cookie is not None:
        #             set_sql_debug(int(sql_debug_cookie))
        #         request.STACKS = {}
        #         request.DB_USING_COUNTS = defaultdict(int)
        #         if should_trace():
        #             log.debug('%s %s' % (request.META['REQUEST_METHOD'], request.get_full_path()), fg='magenta')
        #     if request.session:
        #         logging.AuditContext.set(request.session.get('audit_context', None))

        response = self.get_response(request)

        """Refresh session audit context if modified
        """
        # from triengine.base.cursor import get_sql_debug, sql_debug
        # if getattr(request, '_audit_context_processing_done', False):
        #     return response
        # if hasattr(request, 'session') and hasattr(request, 'user'):
        #     if request.user and request.user.is_authenticated:
        #         context = logging.AuditContext.get_current()
        #         session_context = request.session.get('audit_context', None)
        #         if context and context != session_context:
        #             request.session['audit_context'] = context
        if get_sql_debug() == 4 and hasattr(request, 'STACKS'):  # hasattr check because process_request might not be called in case of an early redirect
            highscore = sorted([
                (len(sql_queries), stack_trace, sql_queries)
                for stack_trace, sql_queries in request.STACKS.items()
            ])
            # Print the worst offenders
            number_of_offenders = 3
            for count, stack, sql_queries in highscore[-number_of_offenders:]:
                if count > 3:  # 2 times is ok-ish, more is suspicious
                    sql_debug('------ %s times: -------' % count, bold=True)
                    sql_debug(stack, sql_trace=True)
                    sql_queries = set(sql_queries)
                    query_cutoff = 3
                    for x in list(sql_queries)[:query_cutoff]:
                        sql_debug(x, sql=True)
                    if len(sql_queries) > 3:
                        sql_debug('... and %d more unique statements' % (len(sql_queries) - query_cutoff))
            sql_debug('Total number of SQL statements: %s' % sum(request.DB_USING_COUNTS.values()))
        if settings.DEBUG:
            if hasattr(request, 'total_sql_time'):
                total_time = "total sql time: %.3f" % request.total_sql_time
                sql_debug(msg='%s %s %s' % (request.META['REQUEST_METHOD'], request.get_full_path(), total_time))
            set_sql_debug(None)
            duration = '-'
            if hasattr(request, '_start_time'):
               duration = '%.3fs' % (datetime.now() - request._start_time).total_seconds()
            log.debug('{} -> {}'.format(request.get_full_path(), response.status_code), fg='magenta', duration=duration)
        return response

#
# replace default debug wrapper
#

log = logging.getLogger('db')
SQL = 11
addLevelName(SQL, 'SQL')


def safe_unicode_literal(cursor, params):
    if params is None:
        return 'NULL'

    if isinstance(params, (list, tuple)):
        return tuple([safe_unicode_literal(cursor, x) for x in params])
    elif isinstance(params, (float, int)):
        return repr(params)
    elif isinstance(params, (date, datetime)):
        return repr(params.isoformat())
    elif isinstance(params, dict):
        return dict((k, safe_unicode_literal(cursor, v)) for k, v in params.items())
    elif isinstance(params, bytes):
        return repr(params.decode(errors="replace"))
    else:
        return repr(params)


def set_sql_debug(new_state):
    setattr(state, 'sql_debug', new_state)


def get_sql_debug():
    """ :rtype: bool """
    result = getattr(state, 'sql_debug', None)
    if result is not None:
        return result
    return getattr(settings, 'SQL_DEBUG', False)


@contextmanager
def no_sql_debug():
    """
    Context manager to temporarily suspend sql logging.

    This is useful inside the sql debug implementation to avoid infinite recursion.
    """
    old_state = get_sql_debug()
    set_sql_debug(False)
    yield
    set_sql_debug(old_state)


def sql_debug(msg, **kwargs):
    if get_sql_debug():
        #log.log(level=logging.INFO, msg=msg, **kwargs)
        print(msg)


class CursorDebugWrapper(django_db_utils.CursorWrapper):

    def trace_sql(self, msg):
        if len(msg) > 10000:
            msg = '%s... [%d bytes sql]' % (re.sub(r'[\x00-\x08\x0b-\x1f\x80-\xff].*', '.', msg[:10000]), len(msg))
        else:
            msg = re.sub(r'[\x00-\x08\x0b-\x1f\x80-\xff]', '.', msg)

        if get_sql_debug() != 4:
            sql_debug(msg, sql=True, read_only=self.db.alias == 'read-only')
        return msg

    @staticmethod
    def trace_time(t):
        sql_debug('Time: %.3f' % t, sql=True, slow=t > 0.1)

    @staticmethod
    def trace_total_sql_time(t):
        req = get_current_request()
        if req:
            if not hasattr(req, 'total_sql_time'):
                req.total_sql_time = 0.0
            req.total_sql_time += t

    @staticmethod
    def format_stack_trace(frame):
        lines = traceback.format_stack(frame)

        base_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..')) + "/"
        msg = []
        skip_template_code = False
        for line in itertools.dropwhile(lambda l: ('/lib/python' in l
                                                   or "django/core" in l
                                                   or 'pydev/pydevd' in l
                                                   or 'gunicorn' in l), lines):
            match = re.match(r' *File "(.*)", line (\d+), in (.*)\n +(.*)\n', line)
            if not match:
                continue
            file_name, line, fn, context = match.groups()

            file_name = file_name.replace(base_path, '')
            extra = ''
            if fn == '_resolve_lookup':
                f = frame
                while f.f_back and 'bit' not in f.f_locals:
                    f = f.f_back
                if 'bit' in f.f_locals:
                    extra = colored('(looking up: %s) ' % f.f_locals['bit'], color='red')
            elif "django/template" in file_name:
                if skip_template_code:
                    continue
                skip_template_code = True
            elif skip_template_code:
                skip_template_code = False

            msg.append('  File "%s", line %s, in %s => %s%s' % (file_name, line, fn, extra, context.strip()))

        stack = "\n".join(msg[-20:]).rstrip()
        return stack

    def execute(self, sql, params=None):
        if get_sql_debug() >= 3:
            frame = sys._getframe().f_back
            while "django/db" in frame.f_code.co_filename:
                frame = frame.f_back
            stack = self.format_stack_trace(frame)

            if get_sql_debug() != 4:
                sql_debug("STACK: ===>\n" + stack, sql_trace=True)

        if get_sql_debug() >= 1:
            # convert to utf-8, by some means
            trace_sql = sql
            if params:
                trace_sql = sql % safe_unicode_literal(self.cursor, params)
            msg = self.trace_sql(trace_sql)
            using_db = self.db.alias

            if get_sql_debug() == 4 and get_current_request():
                get_current_request().STACKS[stack].append(msg)
                get_current_request().DB_USING_COUNTS[using_db] += 1

        start = time()
        try:
            return super().execute(sql, params)
        finally:
            stop = time()
            if 3 <= get_sql_debug() < 4:
                sql_debug('Found Rows: %d' % self.cursor.rowcount, sql=True)
            if 1 <= get_sql_debug() < 4:
                sql_time = stop - start
                self.trace_time(sql_time)
                self.trace_total_sql_time(sql_time)
            elif get_sql_debug() >= 2:
                if params:
                    sql %= safe_unicode_literal(self.cursor, params)
                self.db.queries.append({
                    'sql': sql,
                    'time': "%.3f" % (stop - start),
                })
            if getattr(settings, "SQL_TIMING", False):
                self.db.queries.append({
                    'sql': sql,
                    'time': (stop - start),
                })

    def executemany(self, sql, param_list):
        start = time()
        if get_sql_debug():
            for i, params in enumerate(param_list):
                output = sql % safe_unicode_literal(self.cursor, params)
                if i:
                    output += '\t* '
                self.trace_sql(output)
        try:
            return super().executemany(sql, param_list)
        finally:
            stop = time()
            if get_sql_debug() == 1:
                self.trace_time(stop - start)
            elif get_sql_debug() == 2:
                self.db.queries.append({
                    'sql': '%s times: %s' % (len(param_list), sql),
                    'time': "%.3f" % (stop - start),
                })
            if getattr(settings, "SQL_TIMING", False):
                self.db.queries.append({
                    'sql': sql,
                    'time': (stop - start),
                })

    def __iter__(self):
        return iter(self.cursor)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)


if getattr(settings, "REPLACE_CURSOR_DEBUG_WRAPPER", True):
    import django.db.backends.utils
    django.db.backends.utils.CursorDebugWrapper = CursorDebugWrapper
