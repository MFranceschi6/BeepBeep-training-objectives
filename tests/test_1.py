from beepbeep.trainingobjectiveservice.app import create_app
from beepbeep.trainingobjectiveservice.database import db, Training_Objective
from unittest import mock
from flask.json import jsonify
import pytest
import os
from datetime import datetime


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


def test_delete(client, db_instance):
    response = client.delete('/users/2/training_objectives')

    print(response)
    assert response.status_code == 204


def test_add(client, db_instance):

    assert db_instance.session.query(Training_Objective).count() == 0

    with mock.patch('beepbeep.trainingobjectiveservice.views.swagger.get_request_retry') as mocked:
        mocked.return_value.status_code = 200

        time = int(datetime.utcnow().timestamp())
        response = client.post('/users/3000/training_objectives', json={
            'start_date': time,
            'end_date': time,
            'kilometers_to_run': 1
        })

    print(response)
    assert response.status_code == 201

    assert db_instance.session.query(Training_Objective).count() == 1

    t_o = db_instance.session.query(Training_Objective).first()
    assert t_o.start_date == datetime.fromtimestamp(time)
    assert t_o.end_date == datetime.fromtimestamp(time)
    assert t_o.kilometers_to_run == 1
