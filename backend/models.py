from db import db
import pandas as pd
import numpy as np

class MatchingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    match_rate = db.Column(db.Float)
    system_name = db.Column(db.String(128))
    num_exceptions = db.Column(db.Integer)
    exceptions = db.relationship('ExceptionRecord', backref='matching_data', lazy=True)

class ExceptionRecord (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matching_data_id = db.Column(db.Integer, db.ForeignKey('matching_data.id'), nullable=False)
    name = db.Column(db.String(128))
    old_value = db.Column(db.String(256))
    new_value = db.Column(db.String(256))

def save_to_db(result):
    # Convert pandas.Timestamp to Python datetime
    date = result.get("date")
    if isinstance(date, pd.Timestamp):
        date = date.to_pydatetime()

    match_rate = float(result.get("match_pct"))
    system_name = result.get("system_name")
    exceptions_list = result.get("exceptions", [])
    num_exceptions = len(exceptions_list)

    matching_data = MatchingData(
        date=date,
        match_rate=match_rate,
        system_name=system_name,
        num_exceptions=num_exceptions
    )
    db.session.add(matching_data)
    db.session.flush()  # Get matching_data.id before commit

    # Save exceptions
    for exc in exceptions_list:
        # Convert numpy types to str/int
        name = str(exc.get("field", ""))
        old_value = str(exc.get("old", ""))
        new_value = str(exc.get("new", ""))
        exception = ExceptionRecord(
            matching_data_id=matching_data.id,
            name=name,
            old_value=old_value,
            new_value=new_value
        )
        db.session.add(exception)

    db.session.commit()

def get_historic_data(system_name):
    results = MatchingData.query.filter_by(system_name=system_name).order_by(MatchingData.date.asc()).all()
    return [r.to_dict() for r in results]
