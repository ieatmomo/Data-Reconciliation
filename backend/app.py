from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from analysis import analyse_files, create_trend_graph
from config import MONGO_URI
from models import save_to_db, get_historic_data
from helpers import file_checker

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

@app.route('/')
def home():
    return "Welcome to the Flask App!"

@app.route('/upload', methods=['POST'])
def upload_files():
    '''
    Endpoint to upload two files for analysis, analyse them, and save the results to the database.
    '''
    # Check if both files are present
    if 'old' not in request.files or 'new' not in request.files:
        return jsonify({"error": "Missing one or more required files"}), 400
    
    if not file_checker(request.files['old']) or not file_checker(request.files['new']):
        return jsonify({"error": "Invalid file type. Only CSV and XLSX files are allowed."}), 401

    fileOld = request.files['old']
    
    fileNew= request.files['new']

    try:
          # Must return a dict, will be reimplemented corretly, later 
        result = analyse_files(fileOld, fileNew)
    
    except TypeError as e:
        
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
    
    try:
        save_to_db(result)
    
    except Exception as e:
       
        return jsonify({"error": f"Database save failed: {str(e)}"}), 500

    return jsonify(result), 200

@app.route('/history', methods=['GET'])
def get_historic_data():
    '''
    Endpoint to retrieve historic data for a given system name, and create a trend graph
    based on that data, returning it as a base64 encoded string.
    '''
    
    #Getting system name from frontend
    system = request.args.get('system')

    if system is None:
        
        return jsonify({"error": "System name is required"}), 400
    
    try:
        
        results = get_historic_data(system)
    
    except Exception as e:
        
        return jsonify({"error": f"Failed to retrieve historic data: {str(e)}"}), 500
    try:
        
        trend_graph = create_trend_graph(results) #returns base64 encoded string
    
    except Exception as e:
        
        return jsonify({"error": f"Failed to create trend graph: {str(e)}"}), 500
    
    return jsonify({"trend_graph": trend_graph}), 200

if __name__ == '__main__':
    app.run(debug=True)