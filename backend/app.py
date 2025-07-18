from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from analysis import etl, mapping, compare
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import save_to_db, get_historic_data
from helpers import file_checker, convert_json_safe
import tempfile
import pandas as pd
from db import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)

with app.app_context():
    db.create_all()

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

    try:
        if not file_checker(request.files['old']) or not file_checker(request.files['new']):
            return jsonify({"error": "Invalid file type. Only CSV and XLSX files are allowed."}), 401
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    fileOld = request.files['old']
    fileNew = request.files['new']

    with tempfile.NamedTemporaryFile(delete=False, suffix=fileOld.filename) as tmp_old, \
         tempfile.NamedTemporaryFile(delete=False, suffix=fileNew.filename) as tmp_new:
        fileOld.save(tmp_old.name)
        fileNew.save(tmp_new.name)

        mapping_cfg = mapping.load_mapping('analysis/mapping.yaml')
        df_old = etl.load_file(tmp_old.name)
        df_new = etl.load_file(tmp_new.name)
        df_old = etl.normalize(df_old, mapping_cfg)
        df_new = etl.normalize(df_new, mapping_cfg)

        # Get primary key from frontend, fallback to auto-detect
        pk_str = request.form.get('primary_key')
        if pk_str:
            pk_cols = [col.strip() for col in pk_str.split(',') if col.strip()]
        else:
            pk_cols = mapping.detect_primary_key(df_old, df_new)

        result = compare.run_compare(df_old, df_new, pk_cols, mapping_cfg)

        result_for_db = {
            "system_name": mapping_cfg.get("pair_name", "unknown"),
            "date": pd.Timestamp.now(),
            "match_pct": result["match_pct"],
            "exceptions": result["exceptions"],
            "primary_key": pk_cols
        }

        try:
            save_to_db(result_for_db)
        except Exception as e:
            return jsonify({"error": f"Database save failed: {str(e)}"}), 500

        return jsonify(convert_json_safe(result_for_db)), 200
    
@app.route('/db_check')
def db_check():
    try:
        # Try a simple query
        from models import AnalysisResult
        count = AnalysisResult.query.count()
        return jsonify({"status": "success", "row_count": count}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/history', methods=['GET'])
# def get_historic_data_route():
#     '''
#     Endpoint to retrieve historic data for a given system name, and create a trend graph
#     based on that data, returning it as a base64 encoded string.
#     '''
    
#     #Getting system name from frontend
#     system = request.args.get('system')

#     if system is None:
        
#         return jsonify({"error": "System name is required"}), 400
    
#     try:
        
#         results = get_historic_data(system)
    
#     except Exception as e:
        
#         return jsonify({"error": f"Failed to retrieve historic data: {str(e)}"}), 500
#     try:
        
#         trend_graph = create_trend_graph(results) #returns base64 encoded string
    
#     except Exception as e:
        
#         return jsonify({"error": f"Failed to create trend graph: {str(e)}"}), 500
    
#     return jsonify({"trend_graph": trend_graph}), 200

if __name__ == '__main__':
    app.run(debug=True)