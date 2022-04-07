"""From https://github.com/ClearcodeHQ/pytest-mysql 
and partially https://github.com/ClearcodeHQ/mirakuru

under GNU 3




Adapted here for maintenance and to avoid conda/pip installation 
"""

import re
import subprocess
import signal
from contextlib import contextmanager
import socket
from pkg_resources import parse_version
import os
import uuid
import py
import time
import psutil
from typing import Union, Optional, IO, Any, Dict, Tuple, List, Set, Type, Iterator, TypeVar, Callable
import platform
from types import TracebackType
import errno
from pytest import FixtureRequest, TempPathFactory
import pytest

from multiprocessing import Process


# Windows does not have SIGKILL, fall back to SIGTERM.
SIGKILL = getattr(signal, "SIGKILL", signal.SIGTERM)

MySQLProcessManagerType = TypeVar("MySQLProcessManagerType", bound="MySQLProcessManager")

# used to mark our subprocesses
ENV_UUID = "lume_services_uuid"



PS_XE_PID_MATCH = re.compile(r"^.*?(\d+).+$")
"""_sre.SRE_Pattern matching PIDs in result from `$ ps xe -o pid,cmd`."""


def processes_with_env(env_name: str, env_value: str) -> Set[int]:
    """
    Find PIDs of processes having environment variable matching given one.
    Internally it uses `psutil` library.
    :param str env_name: name of environment variable to be found
    :param str env_value: environment variable value prefix
    :return: process identifiers (PIDs) of processes that have certain
             environment variable equal certain value
    :rtype: set
    """
    pids = set()

    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=["pid", "environ"])
        except (psutil.NoSuchProcess, IOError):
            # can't do much if psutil is not able to get this process details
            pass
        else:
            penv = pinfo.get("environ")
            if penv and env_value in penv.get(env_name, ""):
                pids.add(pinfo["pid"])

    return pids


class MySQLProcessManager:

    def __init__(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Union[int, float] = 3600,
        sleep: float = 0.1,
        expected_returncode: Optional[int] = None,
        envvars: Optional[Dict[str, str]] = None,
        stdin: Union[None, int, IO[Any]] = subprocess.PIPE,
        stdout: Union[None, int, IO[Any]] = subprocess.PIPE,
        stderr: Union[None, int, IO[Any]] = None,
    ) -> None:

        self.command = command
     #   self.command_parts = command_parts =
        self._cwd = cwd

        self._timeout = timeout
        self._sleep = sleep
        self._expected_returncode = expected_returncode
        self._envvars = envvars or {}

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        self._endtime: Optional[float] = None
        self.process: Optional[subprocess.Popen] = None
        """A :class:`subprocess.Popen` instance once process is started."""

        self._uuid = f"{os.getpid()}:{uuid.uuid4()}"


    def start(self, command):

        if self.process is None:
            self.process = subprocess.Popen(command, **self._popen_kwargs)

        self._set_timeout()


    def pre_start_check(self) -> bool:
        try:
            sock = socket.socket()
            sock.connect((self.host, self.port))
            return True
        except (socket.error, socket.timeout):
            return False
        finally:
            # close socket manually for sake of PyPy
            sock.close()

    def post_start_check(self) -> False:
        return self.pre_start_check()


    def check_subprocess(self) -> bool:
        """ Make sure the process didn't exit with an error and run the checks.
        """
        if self.process is None:  # pragma: no cover
            # No process was started.
            return False

        exit_code = self.process.poll()
        if exit_code is not None and exit_code != 0:
            # The main process exited with an error. Clean up the children
            # if any.
            self._kill_all_kids(SIGKILL)
            self._clear_process()
            raise Exception(f"Process exited with exit_code {exit_code}")

        return self.post_start_check()

    def kill_all_subprocesses(self, sig):
        pids = processes_with_env(ENV_UUID, self._uuid)
        for pid in pids:
            try:
                os.kill(pid, sig)
            except OSError as err:
                # killed before we could exit
                if err.errno in [errno.ESRCH, errno.EPERM]:
                    pass
                else:
                    raise
        return pids

    def __enter__(self: MySQLProcessManagerType):
        return self.start()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit context manager stopping the subprocess."""
        self.stop()

    def running(self) -> bool:
        """
        Check if executor is running.
        :returns: True if process is running, False otherwise
        :rtype: bool
        """
        if self.process is None:
            return False
        return self.process.poll() is None

    @property
    def _popen_kwargs(self) -> Dict[str, Any]:
        """
        Get kwargs for the process instance.
        .. note::
            We want to open ``stdin``, ``stdout`` and ``stderr`` as text
            streams in universal newlines mode, so we have to set
            ``universal_newlines`` to ``True``.
        :return:
        """
        kwargs: Dict[str, Any] = {}

        if self._stdin:
            kwargs["stdin"] = self._stdin
        if self._stdout:
            kwargs["stdout"] = self._stdout
        if self._stderr:
            kwargs["stderr"] = self._stderr
        kwargs["universal_newlines"] = True

        kwargs["shell"] = self._shell

        env = os.environ.copy()
        env.update(self._envvars)
        # Trick with marking subprocesses with an environment variable.
        #
        # There is no easy way to recognize all subprocesses that were
        # spawned during lifetime of a certain subprocess so mirakuru does
        # this hack in order to mark who was the original parent. Even if
        # some subprocess got daemonized or changed original process group
        # mirakuru will be able to find it by this environment variable.
        #
        # There may be a situation when some subprocess will abandon
        # original envs from parents and then it won't be later found.
        env[ENV_UUID] = self._uuid
        kwargs["env"] = env

        kwargs["cwd"] = self._cwd
        if platform.system() != "Windows":
            kwargs["preexec_fn"] = os.setsid

        return kwargs

    def start(self: MySQLProcessManagerType) -> MySQLProcessManagerType:
        """
        Start defined process.
        After process gets started, timeout countdown begins as well.
        :returns: itself
        :rtype: SimpleExecutor
        """
        if self.process is None:
            command: Union[str, List[str], Tuple[str, ...]] = self.command
            self.process = subprocess.Popen(command, **self._popen_kwargs)

        self._set_timeout()
        return self

    def _set_timeout(self) -> None:
        """Set timeout for possible wait."""
        self._endtime = time.time() + self._timeout

    def _clear_process(self) -> None:
        """
        Close stdin/stdout of subprocess.
        It is required because of ResourceWarning in Python 3.
        """
        if self.process:
            self.process.__exit__(None, None, None)
            self.process = None

        self._endtime = None


    def stop(
        self: MySQLProcessManagerType,
        stop_signal: Optional[int] = None,
        expected_returncode: Optional[int] = None,
    ) -> MySQLProcessManagerType:
        if self.process is None:
            return self


        try:
            os.killpg(self.process.pid, signal.SIGINT)
        except OSError as err:
            if err.errno in [errno.ESRCH, errno.EPERM]:
                pass
            else:
                raise

        def process_stopped() -> bool:
            """Return True only only when self.process is not running."""
            return self.running() is False

        self._set_timeout()
        try:
            self.wait_for(process_stopped)
        except:
            # at this moment, process got killed,
            pass

        if self.process is None:
            # the process has already been force killed and cleaned up by the
            # `wait_for` above.
            return self  # type: ignore[unreachable]
        self._kill_all_kids(SIGKILL)
        exit_code = self.process.wait()
        self._clear_process()

        if expected_returncode is None:
            expected_returncode = self._expected_returncode
        if expected_returncode is None:
            # Assume a POSIX approach where sending a SIGNAL means
            # that the process should exist with -SIGNAL exit code.
            # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.returncode
            expected_returncode = -SIGKILL

        if exit_code and exit_code != expected_returncode:
            raise Exception(f"process finished with exit code {exit_code}")

        return self

    @contextmanager
    def stopped(self: MySQLProcessManagerType) -> Iterator[MySQLProcessManagerType]:
        """
        Stop process for given context and starts it afterwards.
        Allows for easier writing resistance integration tests whenever one of
        the service fails.
        :yields: itself
        :rtype: SimpleExecutor
        """
        if self.running():
            self.stop()
            yield self
            self.start()

    def kill(
        self: MySQLProcessManagerType, wait: bool = True, sig: Optional[int] = None
    ) -> MySQLProcessManagerType:
        """
        Kill the process if running.
        :param bool wait: set to `True` to wait for the process to end,
            or False, to simply proceed after sending signal.
        :param int sig: signal used to kill process run by the executor.
            None by default.
        :returns: itself
        :rtype: SimpleExecutor
        """
        if sig is None:
            sig = SIGKILL
        if self.process and self.running():
            os.killpg(self.process.pid, sig)
            if wait:
                self.process.wait()

        self._kill_all_kids(sig)
        self._clear_process()
        return self

    def output(self) -> Optional[IO[Any]]:
        """Return subprocess output."""
        if self.process is not None:
            return self.process.stdout
        return None  # pragma: no cover

    def err_output(self) -> Optional[IO[Any]]:
        """Return subprocess stderr."""
        if self.process is not None:
            return self.process.stderr
        return None  # pragma: no cover

    def wait_for(
        self: MySQLProcessManagerType, wait_for: Callable[[], bool]
    ) -> MySQLProcessManagerType:
        """
        Wait for callback to return True.
        Simply returns if wait_for condition has been met,
        raises TimeoutExpired otherwise and kills the process.
        :param callback wait_for: callback to call
        :raises: mirakuru.exceptions.TimeoutExpired
        :returns: itself
        :rtype: SimpleExecutor
        """
        while self.check_timeout():
            if wait_for():
                return self
            time.sleep(self._sleep)

        self.kill()
        raise Exception(f"Timeout expired timeout={self._timeout}")

    def check_timeout(self) -> bool:
        """
        Check if timeout has expired.
        Returns True if there is no timeout set or the timeout has not expired.
        Kills the process and raises TimeoutExpired exception otherwise.
        This method should be used in while loops waiting for some data.
        :return: True if timeout expired, False if not
        :rtype: bool
        """
        return self._endtime is None or time.time() <= self._endtime


class PytestMySQLException(Exception):
    """Base plguin's exceptions"""


class MySQLUnsupported(PytestMySQLException):
    """Exception raised when an unsupported MySQL has been encountered."""


class VersionNotDetected(PytestMySQLException):
    """Exception raised when exector could not detect mysqls' version."""

    def __init__(self, output):
        """Create error message."""
        super().__init__("Could not detect version in {}".format(output))


class DatabaseExists(PytestMySQLException):
    """Raise this exception, when the database already exists"""



class MySQLExecutor(MySQLProcessManager):
    """MySQL Executor for running MySQL server."""

    VERSION_RE = re.compile(r"(?:[a-z_ ]+)(Ver)? (?P<version>[\d.]+).*", re.I)
    IMPLEMENTATION_RE = re.compile(r".*MariaDB.*")

    def __init__(
        self,
        mysqld_safe,
        mysqld,
        admin_exec,
        logfile_path,
        params,
        base_directory,
        user,
        host,
        port,
        timeout=60,
        install_db=None,
    ):
        """
        Specialised Executor to run and manage MySQL server process.
        :param str mysqld_safe: path to mysqld_safe executable
        :param str mysqld: path to mysqld executable
        :param str admin_exec: path to mysqladmin executable
        :param str logfile_path: where the server shoyld wrute it's logs
        :param str params: string containing additional starting parameters
        :param path base_directory: base directory where the temporary files,
            database files, socket and pid will be placed in.
        :param str user: mysql user name
        :param str host: server's host
        :param int port: server's port
        :param int timeout: executor's timeout for start and stop actions
        :param int install_db:
        """
        self.mysqld_safe = mysqld_safe
        self.mysqld = mysqld
        self.install_db = install_db
        self.admin_exec = admin_exec
        self.base_directory = base_directory
        self.datadir = self.base_directory.mkdir(f"mysqldata_{port}")
        self.pidfile = self.base_directory.join(f"mysql-server.{port}.pid")
        self.unixsocket = str(self.base_directory.join(f"mysql.{port}.sock"))
        self.logfile_path = logfile_path
        self.user = user
        self._initialised = False
        command = (
            f"{self.mysqld_safe} "
            f"--datadir={self.datadir} "
            f"--pid-file={self.pidfile} "
            f"--port={port} "
            f"--socket={self.unixsocket} "
            f"--log-error={self.logfile_path} "
            f"--tmpdir={self.base_directory} "
            f"--skip-syslog {params}"
        )
        super().__init__(command, host, port, timeout=timeout)

    def version(self):
        """Read MySQL's version."""
        version_output = subprocess.check_output(
            [self.mysqld, "--version"]
        ).decode("utf-8")
        try:
            return self.VERSION_RE.search(version_output).groupdict()["version"]
        except AttributeError as exc:
            raise VersionNotDetected(version_output) from exc

    def implementation(self):
        """Detect MySQL Implementation."""
        version_output = subprocess.check_output(
            [self.mysqld, "--version"]
        ).decode("utf-8")
        if self.IMPLEMENTATION_RE.search(version_output):
            return "mariadb"
        return "mysql"

    def initialize_mysqld(self):
        """
        Initialise mysql directory.
        #. Remove mysql directory if exist.
        #. `Initialize MySQL data directory
            <https://dev.mysql.com/doc/refman/5.7/en/data-directory-initialization-mysqld.html>`_
        :param str mysql_init: mysql_init executable
        :param str datadir: path to datadir
        :param str base_directory: path to base_directory
        """
        if self._initialised:
            return
        init_command = (
            f"{self.mysqld} --initialize-insecure "
            f"--datadir={self.datadir} --tmpdir={self.base_directory} "
            f"--log-error={self.logfile_path}"
        )
        subprocess.check_output(init_command, shell=True)
        self._initialised = True

    def initialise_mysql_db_install(self):
        """
        Initialise mysql directory for older MySQL installations or MariaDB.
        #. Remove mysql directory if exist.
        #. `Initialize MySQL data directory
            <https://dev.mysql.com/doc/refman/5.7/en/data-directory-initialization-mysqld.html>`_
        :param str mysql_init: mysql_init executable
        :param str datadir: path to datadir
        :param str base_directory: path to base_directory
        """
        if self._initialised:
            return
        init_command = (
            f"{self.install_db} --user={self.user} "
            f"--datadir={self.datadir} --tmpdir={self.base_directory}"
        )
        subprocess.check_output(init_command, shell=True)
        self._initialised = True

    def start(self):
        """Trigger initialisation during start."""
        implementation = self.implementation()
        if implementation == "mysql" and parse_version(
            self.version()
        ) > parse_version("5.7.6"):
            self.initialize_mysqld()
        elif implementation in ["mysql", "mariadb"]:
            if self.install_db:
                self.initialise_mysql_db_install()
            else:
                raise MySQLUnsupported("mysqld_init path is missing.")
        else:
            raise MySQLUnsupported(
                "Only MySQL and MariaDB servers are supported with MariaDB."
            )
        super().start()

    def shutdown(self):
        """Send shutdown command to the server."""
        shutdown_command = (
            f"{self.admin_exec} --socket={self.unixsocket} "
            f"--user={self.user} shutdown"
        )
        try:
            subprocess.check_output(shutdown_command, shell=True)
        except subprocess.CalledProcessError:
            # Fallback to using root user for shutdown
            shutdown_command = (
                f"{self.admin_exec} --socket={self.unixsocket} "
                f"--user=root shutdown"
            )
            subprocess.check_output(shutdown_command, shell=True)

    def stop(self, sig=None, exp_sig=None):
        """Stop the server."""
        self.shutdown()
        super().stop(sig, exp_sig)



def get_config(request):
    """Return a dictionary with config options."""
    config = {}
    options = [
        "mysqld",
        "mysqld_safe",
        "admin",
        "host",
        "port",
        "user",
        "passwd",
        "dbname",
        "params",
        "logsdir",
        "install_db",
    ]
    for option in options:
        option_name = "mysql_" + option
        conf = request.config.getoption(option_name) or request.config.getini(
            option_name
        )
        config[option] = conf
    return config


def mysql_proc(
    mysqld_exec=None,
    admin_executable=None,
    mysqld_safe=None,
    host=None,
    user=None,
    port=-1,
    params=None,
    logs_prefix="",
    install_db=None,
):
    """
    Process fixture factory for MySQL server.
    :param str mysqld_exec: path to mysql executable
    :param str admin_executable: path to mysql_admin executable
    :param str mysqld_safe: path to mysqld_safe executable
    :param str host: hostname
    :param str user: user name
    :param str|int|tuple|set|list port:
        exact port (e.g. '8000', 8000)
        randomly selected port (None) - any random available port
        [(2000,3000)] or (2000,3000) - random available port from a given range
        [{4002,4003}] or {4002,4003} - random of 4002 or 4003 ports
        [(2000,3000), {4002,4003}] -random of given range and set
    :param str params: additional command-line mysqld parameters
    :param str logs_prefix: prefix for log filename
    :param str install_db: path to legacy mysql_install_db script
    :rtype: func
    :returns: function which makes a redis process
    """

    @pytest.fixture(scope="session")
    def mysql_proc_fixture(
        request: FixtureRequest, tmp_path_factory: TempPathFactory
    ):
        """
        Process fixture for MySQL server.
        #. Get config.
        #. Initialize MySQL data directory
        #. `Start a mysqld server
            <https://dev.mysql.com/doc/refman/5.0/en/mysqld-safe.html>`_
        #. Stop server and remove directory after tests.
            `See <https://dev.mysql.com/doc/refman/5.6/en/mysqladmin.html>`_
        :param FixtureRequest request: fixture request object
        :param tmp_path_factory: pytest fixture for temporary directories
        :rtype: pytest_dbfixtures.executors.TCPExecutor
        :returns: tcp executor
        """
        config = get_config(request)
        mysql_mysqld = mysqld_exec or config["mysqld"]
        mysql_admin_exec = admin_executable or config["admin"]
        mysql_mysqld_safe = mysqld_safe or config["mysqld_safe"]
        mysql_port = port or config["port"]
        mysql_host = host or config["host"]
        mysql_params = params or config["params"]
        mysql_install_db = install_db or config["install_db"]

        tmpdir = py.path.local(
            tmp_path_factory.mktemp(f"pytest-mysql-{request.fixturename}")
        )

        logsdir = config["logsdir"]
        if logsdir:
            if logs_prefix:
                logfile_path = os.path.join(
                    logsdir,
                    f"{logs_prefix}mysql-server.{mysql_port}.log",
                )
        else:
            logfile_path = tmpdir.join(f"mysql-server.{port}.log")

        mysql_executor = MySQLExecutor(
            mysqld_safe=mysql_mysqld_safe,
            mysqld=mysql_mysqld,
            admin_exec=mysql_admin_exec,
            logfile_path=logfile_path,
            base_directory=tmpdir,
            params=mysql_params,
            user=user or config["user"] or "root",
            host=mysql_host,
            port=mysql_port,
            install_db=mysql_install_db,
        )
        with mysql_executor:
            yield mysql_executor

    return mysql_proc_fixture