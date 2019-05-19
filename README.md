# pytest-param-priority

A test execution ordering plugin based on defined priority for
parameters.

-----

This [pytest](https://github.com/pytest-dev/pytest) plugin was generated
with [Cookiecutter](https://github.com/audreyr/cookiecutter) along with
[@hackebrot](https://github.com/hackebrot)'s
[cookiecutter-pytest-plugin](https://github.com/pytest-dev/cookiecutter-pytest-plugin)
template.

## Features

Defines a `@param_priority ` decorator that
can be used to decorate pytest fixtures with a priority number.

This plugin implements the same sorting algorithm as pytest's default,
but takes the priority into account. This means that, for a given scope,
a parameter with a higher priority will take priority when defining the
least number of fixture instantiations.

This plugin is still in a very early Alpha state and is intended to be
used for testing and development purposes. Its public interface has a
high chance of changing and should not be considered stable.

## Requirements

  - pytest

## Installation

You can install "pytest-param-priority" via
[pip](https://pypi.org/project/pip/) from
[PyPI](https://pypi.org/project):

    $ pip install pytest-param-priority

## Usage

Consider the following test:

```python
import pytest
import time


@pytest.fixture(scope="module", params=[1, 2, 3])
def number(request):
    return request.param

@pytest.fixture(scope="module", params=["a", "b", "c"])
def letter(request):
    return request.param

@pytest.fixture(scope="module")
def my_expensive_setup_fixture(letter, number):
    time.sleep(1)

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
```
 
You can see that pytest minimizes the number of fixture
parameter changes globally among all parameters at the
same scope. For instance, look how `red` appears discontinuously in
the beginning, then in two groups at the end:

```
<Module test_one.py>
  <Function test_one[red-a-1]>
  <Function test_two[red-a-1]>
  <Function test_one[red-a-2]>
  <Function test_two[red-a-2]>
  <Function test_one[red-b-2]>
  <Function test_two[red-b-2]>
  <Function test_one[green-b-2]>
  <Function test_two[green-b-2]>
  <Function test_one[green-b-1]>
  <Function test_two[green-b-1]>
  <Function test_one[green-b-3]>
  <Function test_two[green-b-3]>
  <Function test_one[green-a-3]>
  <Function test_two[green-a-3]>
  <Function test_one[green-c-3]>
  <Function test_two[green-c-3]>
  <Function test_one[red-c-3]>
  <Function test_two[red-c-3]>
  <Function test_one[blue-c-3]>
  <Function test_two[blue-c-3]>
  <Function test_one[blue-c-2]>
  <Function test_two[blue-c-2]>
  <Function test_one[blue-c-1]>
  <Function test_two[blue-c-1]>
  <Function test_one[blue-b-3]>
  <Function test_two[blue-b-3]>
  <Function test_one[blue-a-3]>
  <Function test_two[blue-a-3]>
  <Function test_one[blue-b-2]>
  <Function test_two[blue-b-2]>
  <Function test_one[blue-b-1]>
  <Function test_two[blue-b-1]>
  <Function test_one[blue-a-2]>
  <Function test_two[blue-a-2]>
  <Function test_one[blue-a-1]>
  <Function test_two[blue-a-1]>
  <Function test_one[green-c-2]>
  <Function test_two[green-c-2]>
  <Function test_one[green-c-1]>
  <Function test_two[green-c-1]>
  <Function test_one[red-c-2]>
  <Function test_two[red-c-2]>
  <Function test_one[red-c-1]>
  <Function test_two[red-c-1]>
  <Function test_one[red-b-3]>
  <Function test_two[red-b-3]>
  <Function test_one[red-a-3]>
  <Function test_two[red-a-3]>
  <Function test_one[green-a-2]>
  <Function test_two[green-a-2]>
  <Function test_one[green-a-1]>
  <Function test_two[green-a-1]>
  <Function test_one[red-b-1]>
  <Function test_two[red-b-1]>

======================== no tests ran in 0.04 seconds =========================

Process finished with exit code 0
```

Now we can use our priorities to set a strict parameter
order for our tests. Let's say we want to first run
the *number* parameter, then *color*, then *letter*.
 We can use our priority decorators to to that (*zero* being the *highest priority*):
 
 ```python
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
```

Now we can see that the test order is based on all *number*
parameters, then all *color* parameters and finally all
*letter* parameters:

```
<Module test_one.py>
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
  <Function test_two[blue-a-3]>

======================== no tests ran in 0.04 seconds =========================

Process finished with exit code 0
```

## Contributing

Contributions are very welcome. Tests can be run with
[tox](https://tox.readthedocs.io/en/latest/), please ensure the coverage
at least stays the same before you submit a pull request.

## License

Distributed under the terms of the
[MIT](http://opensource.org/licenses/MIT) license,
"pytest-param-priority" is free and open source software

## Issues

If you encounter any problems, please [file an
issue](https://github.com/Sup3rGeo/pytest-param-priority/issues) along
with a detailed description.
