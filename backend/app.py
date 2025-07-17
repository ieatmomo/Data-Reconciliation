from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from analysis import analyse_files, create_trend_graph
from config import MONGO_URI
from models import save_to_db, get_historic_data

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

@app.route('/')
def home():
    return "Welcome to the Flask App!"

@app.route('/upload', methods=['POST'])
def upload_files():
    # Check if both files are present
    if 'old' not in request.files or 'new' not in request.files:
        return jsonify({"error": "Missing one or more required files"}), 400

    fileOld = request.files['old']
    fileNew= request.files['new']

    result = analyse_files(fileOld, fileNew)  # Must return a dict
    save_to_db(result)

    return jsonify(result), 200

@app.route('/history', methods=['GET'])
def get_historic_data():
    system = request.args.get('system')
    # Query all records for the given system name
    results = get_historic_data(system)
    trend_graph = create_trend_graph(results) #returns base64 encoded string
    return jsonify({"trend_graph": trend_graph}), 200

if __name__ == '__main__':
    app.run(debug=True)