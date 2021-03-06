# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from abc import ABCMeta, abstractmethod
from os import walk
from os.path import abspath, dirname, isdir, isfile, join as pathjoin


__all__ = ("Adapter", "AdapterError")
__author__ = "Tyson Smith"
__credits__ = ["Tyson Smith"]


class AdapterError(Exception):
    """The base class for exceptions raised by an Adapter"""


class Adapter(metaclass=ABCMeta):
    """An Adapter is an interface between Grizzly and a fuzzer. A subclass must
    be created in order to add support for additional fuzzers. The Adapter is
    responsible for handling input/output data and executing the fuzzer.
    It is expected that any processes launched or file created on file system
    in the adapter will also be cleaned up in the adapter.
    NOTE: Some methods must not be overloaded doing so will prevent Grizzly from
    operating correctly.

    Attributes:
        _harness (str): Path to harness file that will be used. If None, no
                        harness will be used.
        fuzz (dict): Available as a safe scratch pad for the end-user.
        monitor (TargetMonitor): Used to provide Target status information to
                                 the adapter.
        remaining (int): Can be used to indicate the number of TestCases
                         remaining to process.
    """

    HARNESS_FILE = pathjoin(dirname(__file__), "harness.html")
    IGNORE_UNSERVED = True  # Only report test cases with served content
    NAME = None  # must be a unique string
    RELAUNCH = 0  # maximum iterations between Target relaunches (<1 use default)
    TEST_DURATION = 30  # maximum execution time per test (used as minimum timeout)

    __slots__ = ("_harness", "fuzz", "monitor", "remaining")

    def __init__(self):
        if not isinstance(self.NAME, str):
            raise AdapterError("%s.NAME must be a string" % (type(self).__name__,))
        self._harness = None
        self.fuzz = dict()
        self.monitor = None
        self.remaining = None

    def cleanup(self):
        """Automatically called once at shutdown. Used internally by Grizzly.
        *** DO NOT OVERLOAD! ***

        Args:
            None

        Returns:
            None
        """
        self.shutdown()

    def enable_harness(self, file_path=None):
        """Enable use of a harness during fuzzing. By default no harness is used.
        *** DO NOT OVERLOAD! ***

        Args:
            file_path (str): Path to file to use as a harness. If None the default
                             harness is used.

        Returns:
            None
        """
        if file_path is None:
            file_path = self.HARNESS_FILE
        with open(file_path, "rb") as in_fp:
            self._harness = in_fp.read()

    def get_harness(self):
        """Get the harness. Used internally by Grizzly.
        *** DO NOT OVERLOAD! ***

        Args:
            None

        Returns:
            TestFile: The active harness.
        """
        return self._harness

    @staticmethod
    def scan_path(path, ignore=("desktop.ini", "thumbs.db"), recursive=False):
        """Scan a path and yield the files within it. This is available as
        a helper method.

        Args:
            path (str): Path to file or directory.
            ignore (iterable(str)): Files to ignore.
            recursive (bool): Scan recursively into directories.

        Yields:
            str: Absolute path to files.
        """
        full_path = abspath(path)
        if isdir(full_path):
            for root, _, files in walk(full_path):
                for fname in files:
                    if fname in ignore or fname.startswith("."):
                        # skip ignored and hidden system files
                        continue
                    yield pathjoin(root, fname)
                if not recursive:
                    break
        elif isfile(full_path):
            yield full_path

    @abstractmethod
    def generate(self, testcase, server_map):
        """Automatically called. Populate testcase here.

        Args:
            testcase (TestCase): TestCase intended to be populated.
            server_map (ServerMap): A ServerMap.

        Returns:
            None
        """

    def on_served(self, testcase, served):
        """Optional. Automatically called after a test case is successfully served.

        Args:
            testcase (TestCase): TestCase that was served.
            served (list(str)): Files served from testcase.

        Returns:
            None
        """

    def on_timeout(self, testcase, served):
        """Optional. Automatically called if timeout occurs while attempting to
        serve a test case. By default it calls `self.on_served()`.

        Args:
            testcase (TestCase): TestCase that was served.
            served (list(str)): Files served from testcase.

        Returns:
            None
        """
        self.on_served(testcase, served)

    def pre_launch(self):
        """Optional. Automatically called before launching the Target.

        Args:
            None

        Returns:
            None
        """

    def setup(self, input_path, server_map):
        """Optional. Automatically called once at startup.

        Args:
            input_path (str): Points to a file or directory passed by the user.
                              None is passed by default.
            server_map (ServerMap): A ServerMap

        Returns:
            None
        """

    def shutdown(self):
        """Optional. Automatically called once at shutdown.

        Args:
            None

        Returns:
            None
        """
