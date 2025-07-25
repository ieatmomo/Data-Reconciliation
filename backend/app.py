from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from analysis import etl, mapping, compare, graph
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import save_to_db, get_historic_data
from helpers import file_checker, convert_json_safe, parse_uploaded_file
from models import MatchingData
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
            return jsonify({"error": "Invalid file type. Only CSV, XLSX, XLS, and XML files are allowed."}), 401
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    fileOld = request.files['old']
    fileNew = request.files['new']

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{fileOld.filename}") as tmp_old, \
             tempfile.NamedTemporaryFile(delete=False, suffix=f"_{fileNew.filename}") as tmp_new:
            
            # Save uploaded files to temporary locations
            fileOld.save(tmp_old.name)
            fileNew.save(tmp_new.name)

            # Load mapping config
            mapping_cfg = mapping.load_mapping('analysis/mapping.yaml')
            
            # Use helper functions for file parsing
            df_old = parse_uploaded_file(tmp_old.name, fileOld.filename)
            df_new = parse_uploaded_file(tmp_new.name, fileNew.filename)
            
            # Normalize data using existing ETL
            df_old = etl.normalize(df_old, mapping_cfg)
            df_new = etl.normalize(df_new, mapping_cfg)

            # Get primary key from frontend, fallback to auto-detect
            pk_str = request.form.get('primary_key')
            if pk_str:
                pk_cols = [col.strip() for col in pk_str.split(',') if col.strip()]
            else:
                pk_cols = mapping.detect_primary_key(df_old, df_new)

            # Run comparison
            result = compare.run_compare(df_old, df_new, pk_cols, mapping_cfg)

            # Generate system name from filename (remove extension and normalize)
            system_name = fileOld.filename.rsplit('.', 1)[0].lower().strip()
            
            # Override with mapping config if it exists and is not default
            if mapping_cfg.get("pair_name") and mapping_cfg.get("pair_name") != "unknown":
                system_name = mapping_cfg.get("pair_name")

            # Get available columns for frontend
            common_cols = list(set(df_old.columns) & set(df_new.columns))

            # Prepare result for database
            result_for_db = {
                "system_name": system_name,
                "date": pd.Timestamp.now(),
                "match_pct": result["match_pct"],
                "exceptions": result["exceptions"],
                "primary_key": pk_cols
            }

            # Save to database
            try:
                save_to_db(result_for_db)
            except Exception as e:
                return jsonify({"error": f"Database save failed: {str(e)}"}), 500

            # Prepare response for frontend
            response_data = {
                "match_pct": result["match_pct"],
                "exceptions": result["exceptions"],
                "primary_key": pk_cols,
                "system_name": system_name,
                "date": result_for_db["date"].isoformat(),
                "available_columns": common_cols  # Send available columns to frontend
            }

            return jsonify(convert_json_safe(response_data)), 200

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500
    finally:
        # Clean up temporary files
        try:
            import os
            if 'tmp_old' in locals():
                os.unlink(tmp_old.name)
            if 'tmp_new' in locals():
                os.unlink(tmp_new.name)
        except:
            pass  # Ignore cleanup errors

@app.route('/db_check')
def db_check():
    try:
        count = MatchingData.query.count()
        return jsonify({"status": "success", "row_count": count}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/systems', methods=['GET'])
def get_available_systems():
    '''
    Get all unique system names from the database.
    '''
    try:
        
        # Get all unique system names
        systems = db.session.query(MatchingData.system_name).distinct().all()
        system_names = [system[0] for system in systems if system[0]]
        
        return jsonify({
            "systems": sorted(system_names),
            "count": len(system_names)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve systems: {str(e)}"}), 500

@app.route('/system_details/<system_name>', methods=['GET'])
def get_system_details(system_name):
    '''
    Get available primary keys for a specific system.
    '''
    try:
        
        # Get unique primary keys used for this system
        records = MatchingData.query.filter_by(system_name=system_name).all()
        
        if not records:
            return jsonify({"error": f"No data found for system: {system_name}"}), 404
        
        primary_keys = list(set([r.primary_key_used for r in records if r.primary_key_used]))
        
        return jsonify({
            "system_name": system_name,
            "primary_keys": primary_keys,
            "record_count": len(records)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve system details: {str(e)}"}), 500

@app.route('/history', methods=['GET'])
def get_historic_data_route():
    '''
    Endpoint to retrieve historic data for a given system name and primary key
    '''
    system = request.args.get('system')
    primary_key_used = request.args.get('primary_key_used')

    if system is None:
        return jsonify({"error": "System name is required"}), 400
    
    try:
        results = get_historic_data(system, primary_key_used)
        
        if not results:
            return jsonify({
                "dates": [],
                "exception_counts": [],
                "match_rates": [],
                "primary_keys_used": [],
                "system_name": system
            }), 200
        
        # Extract data for frontend: format dates without time
        dates = []
        for r in results:
            if hasattr(r['date'], 'strftime'):
                dates.append(r['date'].strftime('%Y-%m-%d')) 
            else:
                dates.append(str(r['date']).split(' ')[0]) 
        
        exception_counts = [r['num_exceptions'] for r in results]
        match_rates = [r['match_rate'] for r in results]
        primary_keys_used = [r.get('primary_key_used', 'Unknown') for r in results]
        
        # Get the actual system name from the first result (all should be the same)
        actual_system_name = results[0]['system_name'] if results else system
        
        return jsonify({
            "dates": dates,
            "exception_counts": exception_counts,
            "match_rates": match_rates,
            "primary_keys_used": primary_keys_used, 
            "system_name": actual_system_name  
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve historic data: {str(e)}"}), 500

@app.route('/analysis', methods=['GET'])
def get_specific_analysis():
    '''
    Endpoint to retrieve specific analysis data including detailed exceptions.
    '''
    system = request.args.get('system')
    primary_key_used = request.args.get('primary_key_used')
    date = request.args.get('date')

    if not system:
        return jsonify({"error": "System name is required"}), 400
    
    if not date:
        return jsonify({"error": "Date is required"}), 400
    
    try:
        from models import MatchingData, ExceptionRecord
        from datetime import datetime
        
        # Parse the date string to datetime
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Build query
        query = MatchingData.query.filter_by(system_name=system)
        if primary_key_used:
            query = query.filter_by(primary_key_used=primary_key_used)
        
        # Filter by date (comparing only the date part)
        query = query.filter(db.func.date(MatchingData.date) == target_date)
        
        # Get the specific record
        record = query.first()
        
        if not record:
            return jsonify({"error": "No analysis found for the specified criteria"}), 404
        
        # Get exception records
        exception_records = ExceptionRecord.query.filter_by(matching_data_id=record.id).all()
        
        # Format exceptions
        exceptions = []
        for exc in exception_records:
            exception_data = {
                "field": exc.name,
                "old": exc.old_value,
                "new": exc.new_value
            }
            
            # Add primary key values if available
            pk_columns = record.primary_key_used.split(',') if record.primary_key_used else []
            # Note: Individual PK values for each exception would need to be stored separately
            # For now, we'll just indicate that this record belongs to this analysis
            
            exceptions.append(exception_data)
        
        # Prepare response
        response_data = {
            "system_name": record.system_name,
            "date": record.date.strftime('%Y-%m-%d'),
            "match_rate": record.match_rate,
            "primary_key_used": record.primary_key_used,
            "exceptions": exceptions,
            "analysis_id": record.id
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve analysis data: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)