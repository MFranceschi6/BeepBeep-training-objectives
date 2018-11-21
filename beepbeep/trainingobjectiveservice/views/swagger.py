import os
from datetime import datetime
from flakon import SwaggerBlueprint
from flask import request, jsonify
import requests
from beepbeep.trainingobjectiveservice.database import db, Training_Objective, Last_Run
import json


HERE = os.path.dirname(__file__)
YML = os.path.join(HERE, '..', 'static', 'api.yaml')
api = SwaggerBlueprint('API', __name__, swagger_spec=YML)

DATASERVICE = os.environ['DATA_SERVICE']

def check_runner_id(runner_id, send_get=True):

    if int(runner_id) <= 0:
        return 400

    if send_get:
        status_code = requests.get(DATASERVICE + '/user/' + runner_id).status_code
        if status_code == 404:
            return 404

        if status_code != 200:
            return 502

    return 200

@api.operation('getTrainingObjectives')
def get_training_objectives(runner_id):
    status_code = check_runner_id(runner_id)
    if status_code != 200:
        return "", status_code

    training_objectives = db.session.query(Training_Objective).filter(Training_Objective.runner_id == int(runner_id))
    print(str(training_objectives) + ' ' + str(type(training_objectives)))
    print(str(training_objectives[0]) + ' ' + str(type(training_objectives[0])))
    return jsonify([t_o.to_json() for t_o in training_objectives])

@api.operation('addTrainingOebjective')
def add_training_objective(runner_id):

    training_objective = request.json

    status_code = check_runner_id(runner_id)
    if status_code != 200:
        return "", status_code

    start_date = datetime.fromtimestamp(training_objective['start_date'])
    end_date = datetime.fromtimestamp(training_objective['end_date'])

    if start_date < datetime.now() or start_date > end_date:
        return "", 400

    db_training_objective = Training_Objective.from_json(training_objective)
    db_training_objective.runner_id = runner_id
    db.session.add(db_training_objective)
    db.session.commit()
    

    return "", 201

@api.operation('deleteTrainingObjectives')
def delete_training_objectives(runner_id):
    status_code = check_runner_id(runner_id, send_get=False)
    if status_code != 200:
        return "", status_code

    db.session.query(Training_Objective).filter(Training_Objective.runner_id == runner_id).delete()
    db.session.query(Last_Run).filter(Last_Run.runner_id == runner_id).delete()
    db.session.commit()
    return "", 204
