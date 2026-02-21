from datetime import datetime

class Project:
    def __init__(self, name, status="open"):
        self.name = name
        self.status = status
        self.created_at = datetime.now()

class Task:
    def __init__(self, title, project_name, priority="Medium", due_date=None):
        self.title = title
        self.project_name = project_name
        self.priority = priority
        self.due_date = due_date
        self.created_at = datetime.now()