from flask import Flask,request, jsonify
from models import AnalysisResult
from analysis import analyse_files, create_trend_graph

app = Flask(__name__)

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

    result = analyse_files(fileOld, fileNew)  # Custom function to process files
    AnalysisResult.save_to_db(result)

    return jsonify({"message": "Files received successfully!"}), 200

@app.route('/result', methods=['GET'])
def get_result():
    result = (AnalysisResult.query_analysis()).to_dict()
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)