# -*- coding: utf-8 -*-


def test_ordering_example(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(test_example="""
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
    """)

    expected_output = """<Module test_example.py>
  <Function test_one[red-a-1]>
  <Function test_two[red-a-1]>
  <Function test_one[red-c-1]>
  <Function test_two[red-c-1]>
  <Function test_one[red-b-1]>
  <Function test_two[red-b-1]>
  <Function test_one[green-b-1]>
  <Function test_two[green-b-1]>
  <Function test_one[green-c-1]>
  <Function test_two[green-c-1]>
  <Function test_one[green-a-1]>
  <Function test_two[green-a-1]>
  <Function test_one[blue-c-1]>
  <Function test_two[blue-c-1]>
  <Function test_one[blue-b-1]>
  <Function test_two[blue-b-1]>
  <Function test_one[blue-a-1]>
  <Function test_two[blue-a-1]>
  <Function test_one[red-a-2]>
  <Function test_two[red-a-2]>
  <Function test_one[red-b-2]>
  <Function test_two[red-b-2]>
  <Function test_one[red-c-2]>
  <Function test_two[red-c-2]>
  <Function test_one[green-b-2]>
  <Function test_two[green-b-2]>
  <Function test_one[green-c-2]>
  <Function test_two[green-c-2]>
  <Function test_one[green-a-2]>
  <Function test_two[green-a-2]>
  <Function test_one[blue-c-2]>
  <Function test_two[blue-c-2]>
  <Function test_one[blue-b-2]>
  <Function test_two[blue-b-2]>
  <Function test_one[blue-a-2]>
  <Function test_two[blue-a-2]>
  <Function test_one[green-b-3]>
  <Function test_two[green-b-3]>
  <Function test_one[green-a-3]>
  <Function test_two[green-a-3]>
  <Function test_one[green-c-3]>
  <Function test_two[green-c-3]>
  <Function test_one[red-c-3]>
  <Function test_two[red-c-3]>
  <Function test_one[red-b-3]>
  <Function test_two[red-b-3]>
  <Function test_one[red-a-3]>
  <Function test_two[red-a-3]>
  <Function test_one[blue-c-3]>
  <Function test_two[blue-c-3]>
  <Function test_one[blue-b-3]>
  <Function test_two[blue-b-3]>
  <Function test_one[blue-a-3]>
  <Function test_two[blue-a-3]>"""

    # run pytest with the following cmd args
    result = testdir.runpytest(
        '--collect-only',
        '-v'
    )

    # fnmatch_lines does an assertion internally
    # result.stdout.fnmatch_lines([
    #     '*::test_sth PASSED*',
    # ])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0
    assert expected_output in result.stdout.str()
