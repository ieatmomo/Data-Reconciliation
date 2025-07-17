from flask import current_app

def save_to_db(result):
    '''
    Saves analysis results to DB for auditing and trend data visualisation
    '''
    # result should be a dict
    mongo = current_app.extensions['pymongo']

    mongo.db.analysis_results.insert_one(result)

def get_historic_data(system_name):
    '''
    SELECT * from system_name 
    ORDER BY DATE ASC
    Returns the daily trend data for match rate for a given system
    '''
    mongo = current_app.extensions['pymongo']

    results = mongo.db.analysis_results.find({'system_name': system_name}).sort('date', 1)

    return list(results)
