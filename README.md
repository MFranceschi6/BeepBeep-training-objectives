# BeepBeep-training-objectives :runner:

## API Documentation :trollface:

This microservice provide a standard API, the documentation can be found at this [page](https://mfranceschi6.github.io/BeepBeep-training-objectives)

Do you want to know how I made it? Well nothing more simpler: use make :smile:

first of all change the variables PKG, SERVICE and API inside the makefile

```
...

API=api.yaml #name of the api specification file
PKG=beepbeep #name of the package
SERVICE=dataservice #name of the service
...

```

then runs doc_dependecies to install the programs needed
and doc

```
$ sudo make doc_dependencies
$ make docs
```

This will create a directory docs in the project and put data inside the path `$(PKG)/$(SERVICE)/static/doc/`

It's a good idea to show the documentation with the service: run it and go to `/api/doc` you can see from `home.py` how the website is served

```python
import os
from flask import send_from_directory, Blueprint
...

static_file_dir = os.path.dirname(os.path.realpath(__file__))
home = Blueprint('home', __name__)

...

@home.route('/api/<name>')
@home.route('/api/<path>/<name>')
def render_static(name, path=None):
    if name == 'doc':
        return send_from_directory(static_file_dir+"/../static/doc", 'index.html')

...
```



## How to run It :smile:

BE SURE THAT `python3` and `pip3` are referring to `python 3.7.x`.
To find your `python` and `pip` version, run this commands:

```bash
$ python3 --version
> Python 3.7.0
$ pip3 --version
> pip 18.0 from /usr/local/lib/python3.7/site-packages/pip (python 3.7)
```


Once you found commands refering to the correct version, use them in the following scripts.

- Open a new terminal and run `redis-server`

  `$ redis-server`

- Open a new terminal and run `data-service`

  ```bash
  cd <YOUR_DIRECTORY>/BeepBeep-dataservice/
  pip3 install -r requirements.txt
  python3 setup.py develop
  beepbeep-dataservice
  ```
