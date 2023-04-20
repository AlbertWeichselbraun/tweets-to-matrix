import gzip
from json import dump
from pathlib import Path


class FileSystemStorage:
    """
    Store compressed JSON data in the file system.
    """
    def __init__(self, base_directory: str):
        self.base_directory = Path(base_directory)

    def store(self, obj_id: int, obj: object):
        obj_id = str(obj_id)
        fpath = self.base_directory / obj_id[-3:] / obj_id[-6:-3]
        if not fpath.exists():
            fpath.mkdir(parents=True)
        with gzip.open(f'{fpath}/{obj_id}.json.gz', 'wt') as f:
            dump(obj, f)

    def exists(self, obj_id: int):
        obj_id = str(obj_id)
        fpath = self.base_directory / obj_id[-3:] / obj_id[-6:-3] / (obj_id + '.json.gz')
        return fpath.exists()
