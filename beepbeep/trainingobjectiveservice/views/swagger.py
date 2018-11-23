import os
from datetime import datetime,timedelta
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

#update_distance updates the travelled_kilometers for each training objectives: in particular fetchs the 
# new runs, i.e. those which have an id greater than last considered id(which is stored in field "lastRunId" of Last_Run table of db)
def update_distance(training_objectives, runner_id): 
    lastRunId = db.session.query(Last_Run.lastRunId).filter(Last_Run.runner_id == runner_id).first().lastRunId #we take the id of the last fetched run
    dict_to = {}
    user = db.session.query(Last_Run).filter(Last_Run.runner_id == runner_id).first()
    maxRunId = user.lastRunId
    for to in training_objectives:
        id = to.id
        start_date = to.start_date

        end_date = to.end_date
        travelled_kilometers = to.travelled_kilometers

        str_start_date = str(start_date).replace(" ","T") + "Z"
        str_end_date = str(end_date).replace(" ","T") + "Z"

        print(DATASERVICE + '/user/' + runner_id + '/runs?start-date=' + str_start_date + "&finish-date=" + str_end_date + "&from-id=" + str(lastRunId))#request to data service

        runs_response = requests.get(DATASERVICE + '/user/' + runner_id + '/runs?start-date=' + str_start_date + "&finish-date=" + str_end_date + "&from-id=" + str(lastRunId))#request to data service
        list_of_runs = runs_response.json()
        status_code = runs_response.status_code
        if status_code == 404:
            return 404

        if status_code != 200:
            return 502

        partial_sum = 0
        for run in list_of_runs:
            partial_sum += run['distance']
            if(run['id'] > maxRunId): #here we pick the max id of the runs
                maxRunId = run['id']
        partial_sum /= 1000
        travelled_kilometers += partial_sum
        dict_to[id] = travelled_kilometers

    for to in training_objectives:
        to.travelled_kilometers = dict_to[to.id]
    user.lastRunId = maxRunId #here we update the lastRunId of the user (lastRunId is the id of the last fetched run by the user)
    db.session.commit()
    return 200
        

@api.operation('getTrainingObjectives')
def get_training_objectives(runner_id):
    status_code = check_runner_id(runner_id)
    if status_code != 200:
        return "", status_code


    user1 = db.session.query(Last_Run).filter(Last_Run.runner_id == runner_id)
    if user1.count() == 0: #if runner_id is not yet present in Last_run table, we add it
        db_last_run = Last_Run()
        db_last_run.runner_id = runner_id
        db_last_run.lastRunId = -1 #dummy value
        db.session.add(db_last_run)
        db.session.commit()

    training_objectives = db.session.query(Training_Objective).filter(Training_Objective.runner_id == runner_id)
    status_code = update_distance(training_objectives, runner_id)
    if status_code != 200:
        return "", status_code

    training_objectives = db.session.query(Training_Objective).filter(Training_Objective.runner_id == int(runner_id))
    return jsonify([t_o.to_json() for t_o in training_objectives])


@api.operation('addTrainingObjective')
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

