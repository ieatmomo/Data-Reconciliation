from flask import current_app

def save_to_db(result):
    # result should be a dict
    mongo = current_app.extensions['pymongo']
    mongo.db.analysis_results.insert_one(result)

def get_historic_data(system_name):
    mongo = current_app.extensions['pymongo']
    results = mongo.db.analysis_results.find({'system_name': system_name}).sort('date', 1)
    return list(results)