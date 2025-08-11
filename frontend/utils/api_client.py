import streamlit as st
import requests

def upload_files_for_comparison(old_upload, new_upload, map_path, primary_key=None):
    """Upload files to backend for comparison."""
    try:
        old_upload.seek(0)
        new_upload.seek(0)
        files = {
            'old': old_upload,
            'new': new_upload,
            'mapping_path': (None, map_path)
        }
        data = {}
        if primary_key:
            data['primary_key'] = ','.join(primary_key)
            
        response = requests.post("http://localhost:5000/upload", files=files, data=data)
        if response.ok:
            return response.json()
        else:
            st.error(response.text)
            return None
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

def get_available_systems():
    """Load available systems from the database."""
    try:
        response = requests.get("http://localhost:5000/systems")
        if response.ok:
            return response.json().get("systems", [])
        else:
            st.error("Failed to load available systems")
            return []
    except Exception as e:
        st.error(f"Error loading systems: {e}")
        return []

def get_system_details(system_name):
    """Get system details including primary keys."""
    try:
        response = requests.get(f"http://localhost:5000/system_details/{system_name}")
        if response.ok:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error loading system details: {e}")
        return None

def get_historical_data(system_name, primary_key_used=None):
    """Get historical data for a system."""
    try:
        params = {"system": system_name}
        if primary_key_used:
            params["primary_key_used"] = primary_key_used
        
        response = requests.get("http://localhost:5000/history", params=params)
        
        if response.ok:
            return response.json()
        else:
            st.error(f"Failed to load historical data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        return None

def get_specific_analysis(system_name, primary_key_used=None, date=None):
    """Get specific analysis data including detailed exceptions."""
    try:
        params = {"system": system_name}
        if primary_key_used:
            params["primary_key_used"] = primary_key_used
        if date:
            params["date"] = date
        
        response = requests.get("http://localhost:5000/analysis", params=params)
        
        if response.ok:
            return response.json()
        else:
            st.error(f"Failed to load analysis data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error loading analysis data: {e}")
        return None


def reject_exceptions(system_name, matching_data_id, rejected_ids):
    """Send rejected exception IDs to backend."""
    try:
        response = requests.post(f"http://localhost:5000/api/reject_exceptions", json={
            "system_name": system_name,
            "matching_data_id": matching_data_id,
            "rejected_ids": rejected_ids
        })
        
        if response.ok:
            return response.json()
        else:
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        print(f"Error rejecting exceptions: {e}")
        return {"error": str(e)}


def get_rejected_exceptions(system_name, matching_data_id):
    """Get list of rejected exception IDs."""
    try:
        response = requests.get(f"http://localhost:5000/api/get_rejected_exceptions/{system_name}/{matching_data_id}")
        
        if response.ok:
            return response.json()
        else:
            return {"rejected_ids": [], "error": f"Server error: {response.status_code}"}
    except Exception as e:
        print(f"Error getting rejected exceptions: {e}")
        return {"rejected_ids": [], "error": str(e)}


def recalculate_match_rate(matching_data_id):
    """Recalculate match rate excluding rejected exceptions."""
    try:
        response = requests.post(f"http://localhost:5000/api/recalculate_match_rate/{matching_data_id}")
        
        if response.ok:
            return response.json()
        else:
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        print(f"Error recalculating match rate: {e}")
        return {"error": str(e)}


def get_filtered_exceptions(matching_data_id):
    """Get exceptions with rejected ones filtered out and proper indexing."""
    try:
        response = requests.get(f"http://localhost:5000/api/get_filtered_exceptions/{matching_data_id}")
        
        if response.ok:
            return response.json()
        else:
            return {"error": f"Server error: {response.status_code}"}
    except Exception as e:
        print(f"Error getting filtered exceptions: {e}")
        return {"error": str(e)}