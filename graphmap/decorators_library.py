"""
 Decorators from https://wiki.python.org/moin/PythonDecoratorLibrary
"""
from Queue import Queue
from threading import Thread
import threading, sys, traceback
import functools, logging
import time


def dump_args(func):
    "This decorator dumps out the arguments passed to a function before calling it"
    argnames = func.func_code.co_varnames[:func.func_code.co_argcount]
    fname = func.func_name

    @functools.wraps(func)
    def echo_func(*args, **kwargs):
        print fname, ":", ', '.join(
            '%s=%r' % entry
            for entry in zip(argnames, args) + kwargs.items())
        return func(*args, **kwargs)

    return echo_func


class asynchronous(object):
    def __init__(self, func):
        self.func = func

        def threaded(*args, **kwargs):
            self.queue.put(self.func(*args, **kwargs))

        self.threaded = threaded

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def start(self, *args, **kwargs):
        self.queue = Queue()
        thread = Thread(target=self.threaded, args=args, kwargs=kwargs)
        thread.start()
        return asynchronous.Result(self.queue, thread)

    class NotYetDoneException(Exception):
        def __init__(self, message):
            self.message = message

    class Result(object):
        def __init__(self, queue, thread):
            self.queue = queue
            self.thread = thread

        def is_done(self):
            return not self.thread.is_alive()

        def get_deco_result(self):
            if not self.is_done():
                raise asynchronous.NotYetDoneException('the call has not yet completed its task')

            if not hasattr(self, 'deco_result'):
                self.deco_result = self.queue.get()

            return self.deco_result


if __name__ == '__main__':
    # sample usage
    import time


    @asynchronous
    def long_process(num):
        time.sleep(10)
        return num * num


    deco_result = long_process.start(12)

    for i in range(20):
        print i
        time.sleep(1)

        if deco_result.is_done():
            print "deco_result {0}".format(deco_result.get_deco_result())

    deco_result2 = long_process.start(13)

    try:
        print "deco_result2 {0}".format(deco_result2.get_deco_result())

    except asynchronous.NotYetDoneException as ex:
        print ex.message

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class log_with(object):
    '''Logging decorator that allows you to log with a
specific logger.
'''
    # Customize these messages
    ENTRY_MESSAGE = 'Entering {}'
    EXIT_MESSAGE = 'Exiting {}'

    def __init__(self, logger=None):
        self.logger = logger

    def __call__(self, func):
        '''Returns a wrapper that wraps func.
The wrapper will log the entry and exit points of the function
with logging.INFO level.
'''
        # set logger if it was not set earlier
        if not self.logger:
            logging.basicConfig()
            self.logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwds):
            self.logger.info(
                self.ENTRY_MESSAGE.format(func.__name__))  # logging level .info(). Set to .debug() if you want to
            f_deco_result = func(*args, **kwds)
            self.logger.info(
                self.EXIT_MESSAGE.format(func.__name__))  # logging level .info(). Set to .debug() if you want to
            return f_deco_result

        return wrapper


def lazy_thunkify(f):
    """Make a function immediately return a function of no args which, when called,
    waits for the deco_result, which will start being processed in another thread."""

    @functools.wraps(f)
    def lazy_thunked(*args, **kwargs):
        wait_event = threading.Event()

        deco_result = [None]
        exc = [False, None]

        def worker_func():
            try:
                func_deco_result = f(*args, **kwargs)
                deco_result[0] = func_deco_result
            except Exception, e:
                exc[0] = True
                exc[1] = sys.exc_info()
                print "Lazy thunk has thrown an exception (will be raised on thunk()):\n%s" % (
                    traceback.format_exc())
            finally:
                wait_event.set()

        def thunk():
            wait_event.wait()
            if exc[0]:
                raise exc[1][0], exc[1][1], exc[1][2]

            return deco_result[0]

        threading.Thread(target=worker_func).start()

        return thunk

    return lazy_thunked


def time_dec(func):
    @functools.wraps(func)
    def wrapper(*arg):
        t = time.time()
        res = func(*arg)
        time_taken_msec = int((time.time() - t) * 10 ** 3)
        print('Time taken by function ', func.func_name, ' is :', time_taken_msec, 'ms')
        return res

    return wrapper
