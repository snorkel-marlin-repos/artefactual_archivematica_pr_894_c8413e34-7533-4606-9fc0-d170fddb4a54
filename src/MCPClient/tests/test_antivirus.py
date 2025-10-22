# -*- coding: utf8 -*-
"""Tests for the archivematicaClamscan.py client script."""

import os
import sys

from collections import OrderedDict, namedtuple

import pytest
import test_antivirus_clamdscan

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

import archivematicaClamscan


def test_get_scanner(settings):
    """ Test that get_scanner returns the correct instance of antivirus
    per the user's configuration. Test return of clamdscanner by default. """

    # Ensure that environment settings are available to the mock classes.
    test_antivirus_clamdscan.setup_clamdscanner(settings)

    # Testing to ensure clamscanner is returned when explicitly set.
    settings.CLAMAV_CLIENT_BACKEND = "clamscanner"
    scanner = archivematicaClamscan.get_scanner()
    assert isinstance(scanner, archivematicaClamscan.ClamScanner)

    # Testing to ensure that clamdscanner is returned when explicitly set.
    settings.CLAMAV_CLIENT_BACKEND = "clamdscanner"
    scanner = archivematicaClamscan.get_scanner()
    assert isinstance(scanner, archivematicaClamscan.ClamdScanner)

    # Testing to ensure that clamdscanner is the default returned scanner.
    settings.CLAMAV_CLIENT_BACKEND = "fprot"
    scanner = archivematicaClamscan.get_scanner()
    assert isinstance(scanner, archivematicaClamscan.ClamdScanner)

    # Testing to ensure that clamdscanner is the default returned scanner when
    # the user configures an empty string.
    settings.CLAMAV_CLIENT_BACKEND = ""
    scanner = archivematicaClamscan.get_scanner()
    assert isinstance(scanner, archivematicaClamscan.ClamdScanner)

    # Testing to ensure that clamdscanner is returned when the environment
    # hasn't been configured appropriately and None is returned.
    settings.CLAMAV_CLIENT_BACKEND = None
    scanner = archivematicaClamscan.get_scanner()
    assert isinstance(scanner, archivematicaClamscan.ClamdScanner)

    # Testing to ensure that clamdscanner is returned when another variable
    # type is specified, e.g. in this instance, an integer.
    settings.CLAMAV_CLIENT_BACKEND = 10
    scanner = archivematicaClamscan.get_scanner()
    assert isinstance(scanner, archivematicaClamscan.ClamdScanner)


args = OrderedDict()
args['file_uuid'] = 'ec26199f-72a4-4fd8-a94a-29144b02ddd8'
args['path'] = '/path'
args['date'] = '2019-12-01'
args['task_uuid'] = 'c380e94e-7a7b-4ab8-aa72-ec0644cc3f5d'


class FileMock():

    def __init__(self, size):
        self.size = size


class ScannerMock(archivematicaClamscan.ScannerBase):
    PROGRAM = "Mock"

    def __init__(self, should_except=False, passed=False):
        self.should_except = should_except
        self.passed = passed

    def scan(self, path):
        if self.should_except:
            raise Exception("Something really bad happened!")
        return self.passed, None, None

    def version_attrs(self):
        return ("version", "virus_definitions")


def test_main_with_expected_arguments(mocker):
    mocker.patch('archivematicaClamscan.scan_file')
    archivematicaClamscan.main(args.values())
    archivematicaClamscan.scan_file.assert_called_once_with(**dict(args))


def test_main_with_missing_arguments():
    with pytest.raises(SystemExit):
        archivematicaClamscan.main([])


def setup_test_scan_file_mocks(mocker,
                               file_already_scanned=False,
                               file_size=1024,
                               scanner_should_except=False,
                               scanner_passed=False):
    deps = namedtuple('deps', [
        'file_already_scanned',
        'file_get',
        'record_event',
        'scanner',
    ])(
        file_already_scanned=mocker.patch(
            'archivematicaClamscan.file_already_scanned',
            return_value=file_already_scanned),
        file_get=mocker.patch(
            'main.models.File.objects.get',
            return_value=FileMock(size=file_size)),
        record_event=mocker.patch(
            'archivematicaClamscan.record_event',
            return_value=None),
        scanner=ScannerMock(
            should_except=scanner_should_except,
            passed=scanner_passed)
    )

    mocker.patch(
        'archivematicaClamscan.get_scanner',
        return_value=deps.scanner)

    return deps


def test_scan_file_already_scanned(mocker):
    deps = setup_test_scan_file_mocks(mocker, file_already_scanned=True)

    exit_code = archivematicaClamscan.scan_file(**dict(args))

    assert exit_code == 0
    deps.file_already_scanned.assert_called_once_with(args['file_uuid'])


RecordEventParams = namedtuple('RecordEventParams', [
    'scanner_is_None',
    'passed'
])


@pytest.mark.parametrize("setup_kwargs, exit_code, record_event_params", [
    # File size too big for given file_size param
    (
        {'file_size': 43, 'scanner_passed': None},
        0,
        RecordEventParams(scanner_is_None=None, passed=None),
    ),
    # File size too big for given file_scan param
    (
        {'file_size': 85, 'scanner_passed': None},
        0,
        RecordEventParams(scanner_is_None=None, passed=None),
    ),
    # File size within given file_size param, and file_scan param
    (
        {'file_size': 42, 'scanner_passed': True},
        0,
        RecordEventParams(scanner_is_None=False, passed=True),
    ),
    # Scan returns None with no-error, e.g. Broken Pipe
    (
        {'scanner_passed': None},
        0,
        RecordEventParams(scanner_is_None=None, passed=None),
    ),
    # Zero byte file passes
    (
        {'file_size': 0, 'scanner_passed': True},
        0,
        RecordEventParams(scanner_is_None=False, passed=True),
    ),
    # Virus found
    (
        {'scanner_passed': False},
        1,
        RecordEventParams(scanner_is_None=False, passed=False),
    ),
    # Passed
    (
        {'scanner_passed': True},
        0,
        RecordEventParams(scanner_is_None=False, passed=True),
    ),
])
def test_scan_file(mocker, setup_kwargs, exit_code, record_event_params, settings):
    deps = setup_test_scan_file_mocks(mocker, **setup_kwargs)

    # Here the user configurable thresholds for maimum file size, and maximum
    # scan size are being tested. The scan size is offset so as to enable the
    # test to fall through correctly and eventually return None for
    # not-scanned.
    settings.CLAMAV_CLIENT_MAX_FILE_SIZE = "42"
    settings.CLAMAV_CLIENT_MAX_SCAN_SIZE = "84"

    ret = archivematicaClamscan.scan_file(**dict(args))

    # The integer returned by scan_file() is going to be used as the exit code
    # of the archivematicaClamscan.py script which is important for the AM
    # workflow in order to control what to do next.
    assert exit_code == ret

    # A side effect of scan_file() is to record the corresponding event in the
    # database. Here we are making sure that record_event() is called with the
    # expected parameters.
    deps.record_event.assert_called_once_with(
        args['file_uuid'],
        args['date'],
        None if record_event_params.scanner_is_None is True else deps.scanner,
        record_event_params.passed)
