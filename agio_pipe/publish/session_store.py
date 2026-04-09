import json
from pathlib import Path

from agio.tools import local_dirs


class SessionStore:
    store_path = Path(local_dirs.cache_dir('publish_sessions'))

    def __init__(self, session_id: str):
        self.session_id = session_id

    def dump(self, data):
        session_path = self.session_file()
        session_path.parent.mkdir(parents=True, exist_ok=True)
        with session_path.open('w') as session_file:
            json.dump(data, session_file, indent=2, ensure_ascii=False)
        return session_path

    def load(self):
        session_path = self.session_file()
        if not session_path.exists():
            raise FileNotFoundError(f"Session file not found: {session_path}")
        with open(session_path) as session_file:
            session_dict = json.load(session_file)
        return session_dict

    def session_file(self) -> Path:
        return self.store_path.joinpath(self.session_id).with_suffix('.json')
