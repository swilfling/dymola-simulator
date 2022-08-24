import os
from dataclasses import dataclass
from .parameters import Parameters

@dataclass
class Directories(Parameters):
    root_dir: str = ""

    @staticmethod
    def _abspath(path, abspath):
        return os.path.abspath(path) if abspath else path

    def get_paths(self,abspath=False):
        return []

    # Create directory structure in rootdir
    def create_directories(self, rootdir=""):
        [os.makedirs(path, exist_ok=True) for path in self.get_paths_from_rootdir(rootdir)]

    # Get paths from rootdir
    def get_paths_from_rootdir(self, rootdir="", abspath=True):
        return [self._abspath(os.path.join(rootdir, item), abspath) for item in self.get_paths()]

    @staticmethod
    def create_directory_structure(directories=None):
        for path in directories:
            os.makedirs(path, exist_ok=True)