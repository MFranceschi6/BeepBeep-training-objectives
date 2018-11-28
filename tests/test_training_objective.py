import pytest, os, unittest, jwt, requests, json
from beepbeep.trainingobjectiveservice.app import create_app
from flask_webtest import TestApp as _TestApp
from beepbeep.trainingobjectiveservice.database import db, Training_Objective, Last_Run
from beepbeep.trainingobjectiveservice.views.swagger import check_runner_id
from unittest import mock
from unittest.mock import patch, Mock
from flask import json
from flask.json import jsonify
from datetime import datetime, timezone
from werkzeug.wrappers import BaseRequest
from werkzeug.exceptions import HTTPException


_HERE = os.path.dirname(__file__)
_TODAY = int(datetime.utcnow().timestamp())

with open(os.path.join(_HERE, 'privkey.pem')) as f:
    _KEY = f.read()


def create_token(data):
    return jwt.encode(data, _KEY, algorithm='RS512')
    

_TOKEN = {'iss': 'beepbeep',
          'aud': 'beepbeep.io'}


class TestViews(unittest.TestCase):
    def setUp(self):
        app = create_app()
        self.app = _TestApp(app)
        self.token = create_token(_TOKEN).decode('ascii')
        self.headers = {'Authorization': 'Bearer ' + self.token}

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/beepbeep.trainingobjectiveservice_test.db'

    yield app
    os.unlink('/tmp/beepbeep.trainingobjectiveservice_test.db')


@pytest.fixture
def db_instance(app):
    db.init_app(app)
    db.create_all(app=app)

    with app.app_context():
        yield db


@pytest.fixture
def client(app):
    client = app.test_client()

    yield client

def correct_format_date(year = 2025, month = 2, day = 1):
    return int(datetime.strptime(str(year)+'-'+str(month)+'-'+str(day), '%Y-%m-%d').timestamp())



def mock_add_trainig_objective(client, db_instance, n_training_objectives=1, user_id=1, start_date=_TODAY, end_date=_TODAY, kilometers_to_run=1):
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        for j in range(n_training_objectives):
            response = client.post('/users/' + str(user_id) + '/training_objectives', json={
                                                            'start_date': start_date,
                                                            'end_date': end_date,
                                                            'kilometers_to_run': kilometers_to_run
                                                        })
        return response

def check_get_json(result_json, id_training_objective = 1, start_date = _TODAY, end_date = _TODAY, kilometers_to_run = 1, 
                            travelled_kilometers = 0, runner_id = 1):
    for result in result_json:
        assert result_json[0]['id'] == id_training_objective
        assert result_json[0]['start_date'] == start_date
        assert result_json[0]['end_date'] == end_date
        assert result_json[0]['kilometers_to_run'] == kilometers_to_run
        assert result_json[0]['travelled_kilometers'] == travelled_kilometers
        assert result_json[0]['runner_id'] == runner_id



def test_get(client, db_instance):
#Test for the t_o of a user that doesn't exist
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 404
        mocked.return_value.json.return_value.get.return_value = 'error'
        response = client.get('/users/2/training_objectives')
        assert response.status_code == 404

#Test when dataservice is not reachable
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 503
        mocked.return_value.json.return_value.get.return_value = 'error'
        response = client.get('/users/2/training_objectives')
        assert response.status_code == 503

#Test for the t_o of a user that doesn't have t_o
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 2).count() == 0
        response = client.get('/users/2/training_objectives')
        assert response.status_code == 200
        assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 2).count() == 1
        assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 2).count() == 0

#Test 2 consecutive get_training_objectives of a user with a run 
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        mock_add_trainig_objective(client, db_instance)
        response = client.get('/users/1/training_objectives')
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).first().travelled_kilometers == 0
    assert response.status_code == 200
    assert db_instance.session.query(Training_Objective).count() == 1
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count() == 1
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        mocked.return_value.json.return_value = [
                                            {
                                              "id": 1,
                                              "title": "Run1",
                                              "description": "Run1Description",
                                              "strava_id": 0,
                                              "distance": 1000,
                                              "start_date": correct_format_date(year = 2011),
                                              "elapsed_time": 10,
                                              "average_speed": 10,
                                              "total_elevation_gain": 10,
                                              "runner_id": 1
                                            }
                                        ]
        
        response = client.get('/users/1/training_objectives')
        check_get_json(response.json, travelled_kilometers = 1000/1000)
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).first().travelled_kilometers == 1
    assert response.status_code == 200
    assert db_instance.session.query(Training_Objective).count() == 1
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count() == 1
    response = client.delete('/users/1/training_objectives')
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count()==0

#Test two runs that complete the training_objectives of a user
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        mock_add_trainig_objective(client, db_instance)
        response = client.get('/users/1/training_objectives')
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).first().travelled_kilometers == 0
    assert response.status_code == 200
    assert db_instance.session.query(Training_Objective).count() == 1
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count() == 1
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        mocked.return_value.json.return_value = [
                                            {
                                              "id": 1,
                                              "title": "Run1",
                                              "description": "Run1Description",
                                              "strava_id": 0,
                                              "distance": 500,
                                              "start_date": correct_format_date(year = 2011),
                                              "elapsed_time": 10,
                                              "average_speed": 10,
                                              "total_elevation_gain": 10,
                                              "runner_id": 1
                                            },
                                            {
                                              "id": 2,
                                              "title": "Run1",
                                              "description": "Run1Description",
                                              "strava_id": 0,
                                              "distance": 500,
                                              "start_date": correct_format_date(year = 2012),
                                              "elapsed_time": 10,
                                              "average_speed": 10,
                                              "total_elevation_gain": 10,
                                              "runner_id": 1
                                            },
                                        ]
        
        response = client.get('/users/1/training_objectives')
        plan_travelled_kilometers = db_instance.session.query(Training_Objective).\
                                                        filter(Training_Objective.runner_id == 1).\
                                                        first().kilometers_to_run
        check_get_json(response.json, travelled_kilometers = plan_travelled_kilometers)
    assert response.status_code == 200
    assert db_instance.session.query(Training_Objective).count() == 1
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count() == 1
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).first().travelled_kilometers == 1
    assert plan_travelled_kilometers == 1


def test_delete(client, db_instance):
#Test for the a user that doesn't exit
    response = client.delete('/users/2/training_objectives')
    assert response.status_code == 204
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 2).count()==0
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 2).count()==0



#Test for the a registered user without t_o
    response = client.delete('/users/1/training_objectives')
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count()==0
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count()==0
    assert response.status_code == 204

#Test for the a registered user with 1 t_o
    mock_add_trainig_objective(client, db_instance)
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count() == 1
    response = client.delete('/users/1/training_objectives')
    assert response.status_code == 204
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count() == 0
    assert db_instance.session.query(Training_Objective).count() == 0
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count()==0

#Test for the a registered user with more t_o
    mock_add_trainig_objective(client, db_instance, 2)
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count() == 2
    response = client.delete('/users/1/training_objectives')
    assert response.status_code == 204
    assert response.status_code == 204
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.id == 1).count() == 0
    assert db_instance.session.query(Training_Objective).count() == 0
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count()==0


#Test for removing the training_objectives of one user when in db there are more user
    mock_add_trainig_objective(client, db_instance, 1, 2)
    mock_add_trainig_objective(client, db_instance, 2)
    assert db_instance.session.query(Training_Objective).count() == 3
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count() == 2
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 2).count() == 1
    response = client.delete('/users/1/training_objectives')
    assert response.status_code == 204
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 2).count() == 1
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.runner_id == 1).count() == 0
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 1).count()==0
    assert db_instance.session.query(Last_Run).filter(Last_Run.runner_id == 2).count()==1


#Test for removing the training_objectives providing wrong format in url
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200
        response = client.post('/users/a/training_objectives', json={
                        'start_date': _TODAY,
                        'end_date': _TODAY,
                        'kilometers_to_run': 1
                        })
    assert response.status_code == 400

def test_add(client, db_instance):

#Test add a t_o from unregistered user
    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 404
        mocked.return_value.json.return_value.get.return_value = 'error'
        response = client.post('/users/1/training_objectives', json={
                        'start_date': _TODAY,
                        'end_date': _TODAY,
                        'kilometers_to_run': 1
                    })
        assert response.status_code == 404
    assert db_instance.session.query(Training_Objective).count() == 0

#Test add a t_o
    response = mock_add_trainig_objective(client, db_instance)
    assert response.status_code == 201
    assert db_instance.session.query(Training_Objective).count() == 1
    t_o = db_instance.session.query(Training_Objective).first()
    assert t_o.start_date == datetime.fromtimestamp(_TODAY)
    assert t_o.end_date == datetime.fromtimestamp(_TODAY)
    assert t_o.kilometers_to_run == 1
    response = client.delete('/users/1/training_objectives')
    assert response.status_code == 204

#Test add 2 t_0
    mock_add_trainig_objective(client, db_instance,2)
    assert db_instance.session.query(Training_Objective).count() == 2
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.id == 1).count() == 1
    assert db_instance.session.query(Training_Objective).filter(Training_Objective.id == 2).count() == 1
    response = client.delete('/users/1/training_objectives')
    assert response.status_code == 204


#Test add a t_o with a negative number of km
    response = mock_add_trainig_objective(client, db_instance, kilometers_to_run=-1)
    assert response.status_code == 400
    assert db_instance.session.query(Training_Objective).count() == 0

#Test add a t_0 with 0 km
    response = mock_add_trainig_objective(client, db_instance, kilometers_to_run=0)
    assert response.status_code == 400
    assert db_instance.session.query(Training_Objective).count() == 0

#Test add a t_o that starts in the past
    t = correct_format_date(year = 2015)
    response = mock_add_trainig_objective(client, db_instance,1, 1, t, t)
    assert response. status_code == 400
    assert db_instance.session.query(Training_Objective).count() == 0

#Test add a t_o that ends before the start date
    start_date = correct_format_date(year = 2018, month = 2)
    end_date = correct_format_date(year = 2018, month = 1)
    response = mock_add_trainig_objective(client, db_instance,1, 1, start_date, end_date)
    assert response. status_code == 400
    assert db_instance.session.query(Training_Objective).count() == 0

def test_check_runner(client, db_instance):
    try:
        check_runner_id(-1)
    except HTTPException as e:
        assert e.code == 400

    try:
        check_runner_id(0)
    except HTTPException as e:
        assert e.code == 400

    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 503
        try:
            response = check_runner_id(1)
        except HTTPException as e:
            assert e.code == 503