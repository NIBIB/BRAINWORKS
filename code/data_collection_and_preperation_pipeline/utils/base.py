import os, sys
import traceback
import tracemalloc, linecache
import psutil
import time, datetime
import math

from collections import UserList, UserDict
import atexit, signal

from multiprocessing import Lock, parent_process, set_start_method, cpu_count
from multiprocessing.pool import Pool, ThreadPool
from threading import Thread, Condition
import pickle

from configuration.config import Config


class Base:
    """ Base utility class with useful stuff for all other utilities """
    log_lock = Lock()  # log multiprocessing lock

    def __init__(self, config=None):
        self.config = config or Config  # if no config provided, use the original
        self.log_file = f"{self.config.log_directory}/main.log"

        if self.config.debug:
            self.debug(f"{self.__class__.__name__}: RUNNING IN DEBUG MODE")

        # track time markers
        # Keys identify different timings to keep track of, specified in all the time functions.
        # value is: {'start': start_time, 'last': last_time, 'last_diff': last_diff, 'total': total_time, 'num': num_times}
        #   start is defined by first time self.mark_time(id) is called.
        #   last is the time set every time after
        #   diff is the previous difference from mark() to add()
        #   sum is the total summed differences
        #   num is the number of differences recorded (to get an average)
        self.times = {}
        self.time_na = "N/A"

        self.track_memory()  # begin tracking memory usage (in debug mode)

    # Logging
    def debug(self, *args, **kwargs):
        if self.config.debug:
            self.log("[DEBUG]", *args, **kwargs)

    def log(self, *args, **kwargs):
        print(*args, **kwargs, flush=True)
        # with self.log_lock:  # get output lock
        #     print(*args, **kwargs, flush=True)
        #     with open(self.log_file, 'a') as f:
        #         f.write(' '.join(args))

    def err(self, *args, **kwargs):
        """ Log to stderr """
        print(*args, **kwargs, file=sys.stderr, flush=True)
        #self.log(*args, **kwargs, file=sys.stderr)

    def throw(self, msg):
        """ Log an error and throw an exception """
        self.err(msg)
        raise Exception(msg)

    def ensure_path(self, path, file=True):
        """
        Ensures that all directories in the given path exist.
        If file is True, the given path is a file.
        """
        if file:
            dir_path = path[:path.rfind('/')]
        else:
            dir_path = path
        os.makedirs(dir_path, exist_ok=True)  # if any dirs don't exist, make them

    def validate_date(self, text, format="%Y/%m/%d", throw=False):
        """ Validate a string date format. Returns a datetime object if valid."""
        try:
            return datetime.datetime.strptime(text, format).date()
        except ValueError:
            err = f'Incorrect data format, should be {format}. Got: "{text}"'
            if throw: raise ValueError(err)
            self.log(err)
            return None

    def date_string(self, date):
        """ Return a string for the given datetime object """
        return date.strftime("%Y/%m/%d")

    def format_seconds(self, seconds, decimals=3):
        """ format seconds into hh:mm:ss """
        if seconds < 60:
            if decimals == 0: return f"{int(round(seconds, decimals))}s"
            else: return f"{round(seconds, decimals)}s"
        else:
            return str(datetime.timedelta(seconds=int(seconds)))

    # Profiling
    def mark_time(self, id):
        """ Start timing """
        now = time.time()
        if self.times.get(id):  # if this ID already exists
            self.times[id]['last'] = now  # update last time
        else:  # if this ID is new, initialize it
            self.times[id] = {'start': now, 'last': now, 'diff': 0, 'sum': 0, 'num': 0}

    def add_time(self, id):
        """ Add the time passed since the marked time to the list """
        if self.times.get(id):  # if this ID exists
            now = time.time()
            diff = now - self.times[id]['last']  # difference since last mark()
            self.times[id]['diff'] = diff  # set difference
            self.times[id]['sum'] += diff  # add difference tot sum
            self.times[id]['num'] += 1     # increment number of differences
            self.times[id]['last'] = now   # set last time
        else:
            self.mark_time(id)  # if ID doesn't exist, just do mark()

    def get_time_total(self, id, decimals=0):
        """ Show the total time since the first mark() was called """
        if not self.times.get(id):  # this ID doesn't exist
            return self.time_na

        t = time.time() - self.times[id]['start']  # difference from start
        return self.format_seconds(t, decimals)

    def get_time_sum(self, id, decimals=3):
        """ Show the total summed time of the recorded intervals """
        if not self.times.get(id):  # this ID doesn't exist
            return self.time_na

        t = self.times[id]['sum']  # get sum of all marked differences
        return self.format_seconds(t, decimals)

    def get_time_avg(self, id, decimals=3, divisor=1):
        """
        Show the average time between mark() and add() calls.
        Optionally provide a nuber to divide that time by (useful when the time is a batch of something).
        """
        if not self.times.get(id) or not self.times[id]['num']:
            return self.time_na  # this ID doesn't exist or no times added yet

        # ID exists and times have been added
        t = self.times[id]['sum'] / self.times[id]['num']  # show average recorded intervals
        t = t/divisor
        return self.format_seconds(t, decimals)

    def get_time_last(self, id, decimals=3):
        """ Show the last time difference recorded """
        if not self.times.get(id) or not self.times[id]['num']:
            return self.time_na  # this ID doesn't exist or no times added yet

        t = self.times[id]['diff']  # last difference
        return self.format_seconds(t, decimals)

    def clear_time(self, *ids):
        """ Clear the time stats for the given ID or IDS"""
        for id in [*ids]:
            if not self.times.get(id): continue
            del self.times[id]

    def progress(self, i, total, out=False, every=None):
        """
        Returns and optionally prints current progress roughly <every> ammount of progress made
        """
        every = every or int(total/100) or 1  # default is to make progress every 1%
        if (i + 1) % every == 0 or i + 1 == total:  # at a progress point or at the end
            decimals = int(math.log10(total/every)) - 1  # precision
            percent = 100 * (i + 1) / total  # percentage completed
            p = f"{round(percent, decimals)}%"
            if out: self.log(p)
            return p

    # Memory profiling
    def format_bytes(self, n):
        """ Format a number of bytes to be human-readable"""
        for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]:
            if abs(n) < 1024.0:
                return f"{n:3.1f} {unit}"
            n /= 1024.0
        return f"{n:.1f}YiB"

    def memory(self, num=False):
        """ Returns the percentage of current memory used """
        mem = psutil.virtual_memory()[2]
        if num: return float(mem)
        else: return f"{mem}%"

    def track_memory(self):
        """
        Begin tracking memory usage.
        Only runs in debug mode.
        """
        if not self.config.debug: return
        tracemalloc.start()

    def display_memory(self, limit=10):
        """
        Display memory trace since last track_memory() call.
        Only runs in debug mode.
        """
        if not self.config.debug: return
        self.debug("Preparing memory usage log...")
        snapshot = tracemalloc.take_snapshot().filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        ))
        top_stats = snapshot.statistics('lineno')

        self.debug("---------------------")
        self.debug(f"Top {limit} lines")
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            # replace "/path/to/module/file.py" with "module/file.py"
            filename = os.sep.join(frame.filename.split(os.sep)[-2:])
            self.debug(f"#{index}: {filename}:{frame.lineno} | {self.format_bytes(stat.size)}")
            line = linecache.getline(frame.filename, frame.lineno).strip()
            if line: self.debug(f'    {line}')

        other = top_stats[limit:]
        if other:
            size = sum(stat.size for stat in other)
            self.debug(f"{len(other)} other: {self.format_bytes(size)}")
        total = sum(stat.size for stat in top_stats)
        self.debug(f"Total allocated size: {self.format_bytes(total)}")
        self.debug("--------------------")

    # Misc
    def trace(self):
        """ Return the traceback string from an Exception """
        return f"\n{traceback.format_exc()}"

    def exc(self, exception):
        return f"{exception.__class__.__name__}: {exception}"

    def batch_list(self, lst, size=None, number=None):
        """ Given a list, turn it into a list of lists with batch size <size> or a specific <number> of batches """
        if number:
            size = math.ceil(len(lst) / number)
        return [lst[i:i + size] for i in range(0, len(lst), size)]

    def parallelize(self, func, args, n=cpu_count()*2):
        """
        Parallelize a given function across multiple processes.
        <arg_list> must be an iterable to be split amongst each parallel function call.
        <n> How many processes to run in parallel. Arguments will be evenly distributed.
        """
        # How many function calls per process
        # low-ball it so we don't accidentally overload some processes. This means that the worst
        #  to happen would be a few processes get an extra
        chunks = int(math.floor(len(args) / n))
        self.log(f"Parallel Processing: {n} processes, {len(args)} jobs, {chunks} jobs per process (minimum).")
        with Pool(n) as pool:  # get multiprocessing pool context
            return pool.map(func, args, chunks)  # chunks args for each func call


class ThreadQueue:
    """
    Unordered queue of function return values from a thread pool.
    Freely submit any number of function calls with submit().
    Retrieve the next available result with next() (blocking). If None is returned, the queue is empty.
    Retrieved results will be returned in order of completion.
    """
    def __init__(self, threads=3):
        self.threads = threads
        self.thread_pool = ThreadPool(threads)
        self.results = {}  # available items returned, indexed with a unique identifier.
        self.ID = 0  # incrementing ID for self.results
        self.condition = Condition()

    def submit(self, func, args):
        """ submit a function to the queue """
        self.results[self.ID] = self.thread_pool.apply_async(func, args)  # store async result
        self.ID += 1

    def next(self, wait=0.1):
        """ Return the next available result from the queue """
        while len(self.results):  # while there are items in the queue
            for ID, result in self.results.items():
                if result.ready():  # if result completed
                    del self.results[ID]  # remove from results
                    return result.get()  # return it
            time.sleep(wait)
        return None  # queue empty


class StoredObject(Base):
    def __init__(self, name, path="./", populate=None):
        """ An object that persists on disk """
        Base.__init__(self)
        self.name = name  # display name
        self.file = f"{path}/{name}.pickle"  # dump file name
        self.populate = populate  # function to populate when no dumpfile exists
        self.modified = False  # whether this object has been modified since initialization
        self.handling_exit = False  # whether exit has already been handled (to avoid redundant handling)

        # save to disk on program exit
        atexit.register(self._save)
        signal.signal(signal.SIGTERM, self._save)

        self._load()  # load list from disk

    def _load(self):
        """ Load the list from disk """
        if os.path.exists(self.file):  # list is stored on disk
            self.log(f"{self.name} file dump found. Loading... ",)
            with open(self.file, 'rb') as f:  # load pickled list
                self.data = pickle.load(f)
        else:  # dump file not found
            self.log(f"{self.name} file dump not found. Populating...")
            self.data = {}  # initialize empty
            if self.populate:
                self.data = self.populate()  # populate it
                self.modified = True

    def _save(self, *args):
        """
        Save to disk.
        (the *args are because signal passes some arguments)
        """
        if self.handling_exit: return  # avoid redundant exit handling
        self.handling_exit = True

        if not self.modified:
            self.log(f"No change in {self.name}  - skipping file dump.")
            return  # if the object didn't change, don't save it

        def _save_thread():
            self.ensure_path(self.file, file=True)
            with open(self.file, 'wb') as f:
                pickle.dump(self.data, f, pickle.HIGHEST_PROTOCOL)
            self.log(f"Saved {self.name} to disk.")

        self.log(f"Saving {self.name} dump to disk - don't interrupt...  ({self.file})")
        thread = Thread(target=_save_thread)  # run as thread to prevent keyboard interrupt
        thread.start()
        while True:
            try:
                thread.join()  # wait for save thread to finish
                self.log("Exiting...")
                sys.exit(0)  # end program
            except KeyboardInterrupt:
                self.log("prevented interrupt...")


class StoredList(StoredObject, UserList):
    def __init__(self, *args, **kwargs):
        """ A list that persists on disk """
        UserList.__init__(self)
        StoredObject.__init__(self, *args, **kwargs)

    def append(self, *args):
        self.modified = True
        UserList.append(self, *args)

    def extend(self, lst):
        if not len(lst): return
        self.modified = True
        UserList.extend(self, lst)

    def __getitem__(self, i):
        return self.data[i]  # avoids weird stuff with slicing

    def __setitem__(self, *args):
        self.modified = True
        UserList.__setitem__(self, *args)

    def __delitem__(self, *args):
        self.modified = True
        UserList.__delitem__(self, *args)

    def __iadd__(self, *args):
        self.modified = True
        UserList.__iadd__(self, *args)

    def insert(self, *args):
        self.modified = True
        UserList.insert(self, *args)

    def pop(self, i=-1):
        self.modified = True
        return self.data.pop(i)

    def remove(self, *args):
        self.modified = True
        UserList.remove(*args)

    def clear(self):
        self.modified = True
        UserList.clear(self)


class StoredDict(UserDict, StoredObject):
    def __init__(self, *args, **kwargs):
        """ An ordered dictionary that persists on disk, sorted by value """
        UserDict.__init__(self)
        StoredObject.__init__(self, *args, **kwargs)

    def __setitem__(self, *args):
        self.modified = True
        UserDict.__setitem__(self, *args)

    def __delitem__(self, *args):
        self.modified = True
        UserDict.__delitem__(self, *args)

    def update(self, *args):
        self.modified = True
        UserDict.update(self, *args)



