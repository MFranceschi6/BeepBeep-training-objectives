# encoding: utf8
import os
from datetime import datetime
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Training_Objective(db.Model):
    __tablename__ = 'training_objective'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    kilometers_to_run = db.Column(db.Float)
    runner_id = db.Column(db.Integer)

class Last_Run(db.Model):
    __tablename__ = 'last_run'
    runner_id = db.Column(db.Integer, primary_key=True)
    lastRunId = db.Column(db.Integer)
