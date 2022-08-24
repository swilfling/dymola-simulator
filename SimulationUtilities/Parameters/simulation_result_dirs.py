from dataclasses import dataclass
import os
from .directories import Directories

@dataclass
class SimulatorDirs(Directories):
    result_root_dir: str = ""
    result_data_dir: str = ""
    result_plot_dir: str = ""

    # Get relative path to result data dir
    def get_res_data_dir(self, rootdir="", abspath=False):
        return self._abspath(os.path.join(rootdir, self.root_dir, self.result_root_dir, self.result_data_dir), abspath)

    # Get relative path to plot dir
    def get_res_plot_dir(self, rootdir="", abspath=False):
        return self._abspath(os.path.join(rootdir, self.root_dir, self.result_root_dir, self.result_plot_dir), abspath)

    def get_res_root_dir(self, rootdir="", abspath=False):
        return self._abspath(os.path.join(rootdir, self.root_dir), abspath)

    # Get all relative_paths
    def get_paths(self, abspath=False):
        return [self._abspath(path, abspath) for path in [self.root_dir, self.get_res_data_dir(), self.get_res_plot_dir()]]
