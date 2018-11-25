# encoding: utf8
import os
from datetime import datetime
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal


db = SQLAlchemy()


class Training_Objective(db.Model):
    __tablename__ = 'training_objective'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    travelled_kilometers = db.Column(db.Float, default=0.0)
    kilometers_to_run = db.Column(db.Float)
    runner_id = db.Column(db.Integer)

    def to_json(self, secure=False):
        res = {}
        for attr in ('id', 'start_date', 'end_date', 'kilometers_to_run', 'runner_id', 'travelled_kilometers'):
            value = getattr(self, attr)
            if isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, datetime):
                value = int(value.timestamp())
            res[attr] = value
        if secure:
            res['strava_token'] = self.strava_token
        return res

    @staticmethod
    def from_json(schema):
        u = Training_Objective()

        setattr(u, 'start_date', datetime.fromtimestamp(schema['start_date']))
        setattr(u, 'end_date', datetime.fromtimestamp(schema['end_date']))
        setattr(u, 'kilometers_to_run', schema['kilometers_to_run'])

        if 'strava_token' in schema:
            setattr(u, 'strava_token', schema['strava_token'])
        if 'id' in schema:
            setattr(u, 'id', schema['id'])
        return u

class Last_Run(db.Model):
    __tablename__ = 'last_run'
    runner_id = db.Column(db.Integer, primary_key=True)
    lastRunId = db.Column(db.Integer)
