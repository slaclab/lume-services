"""From https://github.com/ClearcodeHQ/pytest-mysql under GNU 3

Adapted here for maintenance and to avoid conda/pip installation 
"""


import re
import subprocess
from pkg_resources import parse_version

from mirakuru import TCPExecutor


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



class MySQLExecutor(TCPExecutor):
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


def mysql(
    process_fixture_name,
    passwd=None,
    dbname=None,
    charset="utf8",
    collation="utf8_general_ci",
):
    """
    Client fixture factory for MySQL server.
    Factory. Create connection to mysql. If you want you can give a scope,
    default is 'session'.
    For charset and collation meaning,
    see `Database Character Set and Collation
    <https://dev.mysql.com/doc/refman/5.5/en/charset-database.html>`_
    :param str process_fixture_name: process fixture name
    :param str passwd: mysql server's password
    :param str dbname: database's name
    :param str charset: MySQL characterset to use by default
        for *tests* database
    :param str collation: MySQL collation to use by default
        for *tests* database
    :returns: function ``mysql_fixture`` with suit scope
    :rtype: func
    """

    def _connect(
        connect_kwargs: dict, query_str: str, mysql_db: str
    ) -> MySQLdb.Connection:
        """Apply given query to a  given MySQLdb connection."""
        mysql_conn: MySQLdb.Connection = MySQLdb.connect(**connect_kwargs)
        try:
            mysql_conn.query(query_str)
        except ProgrammingError as e:
            if "database exists" in str(e):
                raise DatabaseExists(
                    f"Database {mysql_db} already exists. There's some test "
                    f"configuration error. Either you start your own server "
                    f"with the database name used in tests, or you use two "
                    f"fixtures with the same database name on the same "
                    f"process fixture."
                ) from e
            raise
        return mysql_conn

    @pytest.fixture
    def mysql_fixture(request: FixtureRequest) -> MySQLdb.Connection:
        """
        Client fixture for MySQL server.
        #. Get config.
        #. Try to import MySQLdb package.
        #. Connect to mysql server.
        #. Create database.
        #. Use proper database.
        #. Drop database after tests.
        :param request: fixture request object
        :returns: connection to database
        """
        config = get_config(request)
        process: Union[
            NoopMySQLExecutor, MySQLExecutor
        ] = request.getfixturevalue(process_fixture_name)
        if not process.running():
            process.start()

        mysql_user = process.user
        mysql_passwd = passwd or config["passwd"]
        mysql_db = dbname or config["dbname"]

        connection_kwargs = {
            "host": process.host,
            "user": mysql_user,
            "passwd": mysql_passwd,
        }
        if process.unixsocket:
            connection_kwargs["unix_socket"] = process.unixsocket
        else:
            connection_kwargs["port"] = process.port

        query_str = (
            f"CREATE DATABASE `{mysql_db}` "
            f"DEFAULT CHARACTER SET {charset} "
            f"DEFAULT COLLATE {collation}"
        )
        try:
            mysql_conn: MySQLdb.Connection = _connect(
                connection_kwargs, query_str, mysql_db
            )
        except OperationalError:
            # Fallback to mysql connection with root user
            connection_kwargs["user"] = "root"
            mysql_conn: MySQLdb.Connection = _connect(
                connection_kwargs, query_str, mysql_db
            )
        mysql_conn.query(f"USE `{mysql_db}`")
        yield mysql_conn

        # clean up after test that forgot to fetch selected data
        if not mysql_conn.open:
            mysql_conn: MySQLdb.Connection = MySQLdb.connect(
                **connection_kwargs
            )
        try:
            mysql_conn.store_result()
        except Exception as e:
            print(str(e))
        query_drop_database = f"DROP DATABASE IF EXISTS `{mysql_db}`"
        mysql_conn.query(query_drop_database)
        mysql_conn.close()

    return mysql_fixture