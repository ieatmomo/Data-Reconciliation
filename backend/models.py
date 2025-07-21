from db import db
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MatchingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    match_rate = db.Column(db.Float)
    system_name = db.Column(db.String(128))
    num_exceptions = db.Column(db.Integer)
    primary_key_used = db.Column(db.String(256)) 
    exceptions = db.relationship('ExceptionRecord', backref='matching_data', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'match_rate': self.match_rate,
            'system_name': self.system_name,
            'num_exceptions': self.num_exceptions,
            'primary_key_used': self.primary_key_used
        }

class ExceptionRecord (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matching_data_id = db.Column(db.Integer, db.ForeignKey('matching_data.id'), nullable=False)
    name = db.Column(db.String(128))
    old_value = db.Column(db.String(256))
    new_value = db.Column(db.String(256))

def check_existing_data(system_name, primary_key_used, match_rate, num_exceptions):
    """
    Check if similar data already exists in the database.
    Returns the existing record if found, None otherwise.
    """
    # Look for records with same system, primary key, match rate, and exception count
    # within the last 24 hours to avoid exact duplicates
    yesterday = datetime.now() - timedelta(hours=24)
    
    existing = MatchingData.query.filter(
        MatchingData.system_name == system_name,
        MatchingData.primary_key_used == primary_key_used,
        MatchingData.match_rate == match_rate,
        MatchingData.num_exceptions == num_exceptions,
        MatchingData.date >= yesterday
    ).first()
    
    return existing

def save_to_db(result):
    date = result.get("date")
    if isinstance(date, pd.Timestamp):
        date = date.to_pydatetime()

    match_rate = float(result.get("match_pct"))
    system_name = result.get("system_name")
    exceptions_list = result.get("exceptions", [])
    num_exceptions = len(exceptions_list)
    primary_key_used = ','.join(result.get("primary_key", []))

    # Check if this exact data already exists
    existing_record = check_existing_data(system_name, primary_key_used, match_rate, num_exceptions)
    
    if existing_record:
        print(f"Duplicate data detected for {system_name}. Skipping database save.")
        return existing_record.to_dict()

    # Only save if it's new data
    matching_data = MatchingData(
        date=date,
        match_rate=match_rate,
        system_name=system_name,
        num_exceptions=num_exceptions,
        primary_key_used=primary_key_used
    )
    db.session.add(matching_data)
    db.session.flush()

    for exc in exceptions_list:
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
    print(f"New data saved for {system_name}")
    return matching_data.to_dict()

def get_historic_data(system_name, primary_key_used=None):
    query = MatchingData.query.filter_by(system_name=system_name)
    
    if primary_key_used:
        query = query.filter_by(primary_key_used=primary_key_used)
    
    results = query.order_by(MatchingData.date.asc()).all()
    return [r.to_dict() for r in results]


