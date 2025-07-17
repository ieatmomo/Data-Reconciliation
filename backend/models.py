from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class AnalysisResult(db.Model):
    #implement later
    id = db.Column(db.Integer, primary_key=True)

    def save_to_db(self):
        ### implement later
        return 0
    
    def query_analysis(self):
        ### implement later, use .all or .first to ensure object format
        return 1
    
    def get_historic_data(self, system_name):
        ### implement later
        return 2