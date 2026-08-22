from pathlib import Path
import uuid

def create_workspace():
    job_id = uuid.uuid4().hex
    path = Path("data/jobs") / job_id
    path.mkdir(parents=True, exist_ok=True)
    return job_id, path
