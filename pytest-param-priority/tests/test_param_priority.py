# -*- coding: utf-8 -*-
import pytest
import time
from pytest_param_priority import parameter_priority


@parameter_priority(0)
@pytest.fixture(scope="module", params=[1, 2, 3])
def number(request):
    return request.param

@parameter_priority(2)
@pytest.fixture(scope="module", params=["a", "b", "c"])
def letter(request):
    return request.param

@pytest.fixture(scope="module")
def my_expensive_setup_fixture(letter, number):
    time.sleep(1)

@parameter_priority(1)
@pytest.fixture(scope="module", params=["red", "green", "blue"])
def color(request):
    return request.param

@pytest.fixture(scope="module")
def intermediate_step(color, my_expensive_setup_fixture):
    pass

def test_one(intermediate_step):
    pass

def test_two(intermediate_step):
    pass


def bar_fixture(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile("""
        def test_sth(bar):
            assert bar == "europython2015"
    """)

    # run pytest with the following cmd args
    result = testdir.runpytest(
        '--foo=europython2015',
        '-v'
    )

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines([
        '*::test_sth PASSED*',
    ])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def help_message(testdir):
    result = testdir.runpytest(
        '--help',
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines([
        'param-priority:',
        '*--foo=DEST_FOO*Set the value for the fixture "bar".',
    ])


def hello_ini_setting(testdir):
    testdir.makeini("""
        [pytest]
        HELLO = world
    """)

    testdir.makepyfile("""
        import pytest

        @pytest.fixture
        def hello(request):
            return request.config.getini('HELLO')

        def test_hello_world(hello):
            assert hello == 'world'
    """)

    result = testdir.runpytest('-v')

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines([
        '*::test_hello_world PASSED*',
    ])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0
