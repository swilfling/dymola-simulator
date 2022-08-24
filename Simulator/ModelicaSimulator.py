import os

from ..SimulationUtilities import simulation_utils as simutils
from ..SimulationUtilities.Parameters import SimulationParameters, SimulatorDirs, InitializationParameters


class ModelicaSimulator:
    """
    Base class for Modelica simulator (abstract).
    The simulator offers the following methods:
    Simulation:
    - run_simulation
    - run_simulation_sweep
    - setup_experiment
    - run_experiment
    Plotting:
    - plot_simulation_results
    - plot_multiple_results
    - plot_sweep_results
    Initialization:
    - set_init_variables
    - set_init_file
    - set_init_params_full
    Getters:
    - get_root_dir
    - get_data_dir
    - get_plot_dir
    - model_name_full
    - get_start_time
    - get_stop_tim
    Setters:
    - set_start_time
    - set_stop_time
    """
    workdir_path = ""
    package_paths_full = ["package.mo"]
    package_name = ""
    model_name = ""
    result_filename = "results"
    init_filename = "results"
    result_dirs: SimulatorDirs = SimulatorDirs()
    sim_params: SimulationParameters = SimulationParameters()
    init_params: InitializationParameters = InitializationParameters()

    def __init__(self, result_root_dir="./", **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.result_dirs = SimulatorDirs(result_root_dir, "SimulationResults", "ResultData", "Plots")
        self.result_dirs.create_directories()

    ############################ Main methods #################################################

    def setup_experiment(self, **kwargs):
        """
        Setup experiment.
        Virtual method - override this method if necessary
        """
        pass

    def plot_simulation_results(self, simulation_results, **kwargs):
        """
        Plot simulation results

        @param simulation_results: Simulation results

        Optional parameter: out_file_name: output filename
        Additionally, plotting params can be passed here, e.g fig_size=(10,10)

        """
        if simulation_results is not None:
            result_file_name = kwargs.pop('out_file_name', self.result_filename)
            simutils.plot_result(simulation_results, self.get_plot_dir(), result_file_name, **kwargs)

    def run_simulation(self, trajectory_names: list, store_csv=False, **kwargs):
        """
        Run simulation
        @param trajectory_names: names of trajectories to return
        @param store_csv: enable storing to csv file
        Optional parameter out_file_name: select output filename
        @return: Simulation results
        """
        out_file_name = kwargs.get('out_file_name', self.result_filename)
        self._simulate_model(**kwargs)
        simulation_results = self._get_simulation_results(trajectory_names, out_file_name=out_file_name)
        if store_csv:
            try:
                results_path = os.path.join(self.get_data_dir(abspath=True), f"{out_file_name}.csv")
                simulation_results.to_csv(results_path, sep=";", index_label="Zeitraum", date_format='%d.%m.%Y %H:%M')
            except AttributeError:
                print("Simulation results do not exist.")
        return simulation_results

    def run_simulation_sweep(self, trajectory_names: list, sweep_var: str, sweep_values: list, store_csv=False, **kwargs):
        """
        Run sweep simulation
        @param trajectory_names: Trajectories to return
        @param sweep_var: Variable to sweep over
        @param sweep_values: Sweep values
        @param store_csv: enable storing to csv file
        """
        return [self.run_simulation(trajectory_names, store_csv=store_csv, additional_params={sweep_var: val},
                                    out_file_name=f'{self.model_name_full()}_{sweep_var}_{val}'.replace(".", "_"), **kwargs)
                for val in sweep_values]

    def plot_multiple_results(self, results, set_colors=False, **kwargs):
        """
        Plot multiple results in one graph
        @param results: Pandas dataframe
        @param set_colors: Use colormap
        Optional parameter: out_file_name
        """
        out_file_name = kwargs.pop('out_file_name', self.result_filename)
        simutils.plot_multiple_results(results, self.get_plot_dir(), out_file_name, set_colors=set_colors, **kwargs)

    def plot_sweep_results(self, sweep_results, sweep_var, sweep_vals=None, **kwargs):
        """
        Plot sweep results - Create plots for each result
        @param sweep_results: Pandas dataframe
        @param sweep_var: sweep variable
        @param sweep_vals: sweep values

        Optional parameter: out_file_name
        """
        out_file_name = kwargs.pop('out_file_name', self.result_filename)
        for val, result in zip(sweep_vals, sweep_results):
            self.plot_simulation_results(result, out_file_name=f'{out_file_name}_{sweep_var}_{val}'.replace(".", "_"))

    def run_experiment(self, exp_name="",trajectory_names=[], start_time=None, stop_time=None, plot_enabled=False,
                       **kwargs):
        """
        Run experiment - main function
        @param exp_name: Experiment name - optional
        @param trajectory_names: Names of trajectories to return
        @param start_time Simulation start time
        @param stop_time Simulation stop time
        """
        self.set_start_time(start_time)
        self.set_stop_time(stop_time)
        out_file_name = f'{self.result_filename}_{exp_name}'
        self._init_experiment(exp_name, **kwargs)
        simulation_results = self.run_simulation(trajectory_names=trajectory_names, out_file_name=out_file_name, **kwargs)
        if plot_enabled:
            self.plot_simulation_results(simulation_results, out_file_name=out_file_name, show_legend=True, show_ylabel=True)

        return simulation_results

    ############################################ Helper methods ########################################################

    def model_name_full(self):
        return f"{self.package_name}.{self.model_name}"

    def get_plot_dir(self, abspath=False):
        return self.result_dirs.get_res_plot_dir(abspath=abspath)

    def get_data_dir(self, abspath=False):
        return self.result_dirs.get_res_data_dir(abspath=abspath)

    def get_root_dir(self, abspath=False):
        return self.result_dirs.get_res_root_dir(abspath=abspath)

    ######################################### Simulation Parameters ####################################################

    def set_start_time(self, start_time=None):
        self.sim_params.set_start_time(start_time)

    def set_stop_time(self, stop_time=None):
        self.sim_params.set_stop_time(stop_time)

    def get_start_time(self):
        return self.sim_params.get_start_time()

    def get_stop_time(self):
        return self.sim_params.get_stop_time()

    def set_sim_params(self, sim_params: SimulationParameters):
        self.sim_params = sim_params

    def get_output_interval(self):
        return self.sim_params.get_output_interval()

    ######################### Private methods ##################################################

    def _get_simulation_results(self, trajectory_names, **kwargs):
        """
        Get simulation results from result file
        @param trajectory_names: names of trajectories
        Virtual method - override this
        """
        return None

    def _init_experiment(self, exp_name="", **kwargs):
        """
        Initialize Experiment
        @param exp_name: name of experiment
        Virtual method - override this
        """
        pass

    def _simulate_model(self, **kwargs):
        """
        Simulate model
        Simulator-specific simulation methods
        Virtual method - override this
        """
        return None

    ##################### Initialization parameters ####################################################################

    def set_init_params_full(self, init_file: str, init_variables: dict):
        """
        Set initialization parameters. Also activates initialization.
        @param init_file: Path to initialization file (.mat)
        @param init_variables: Dictionary of initialization values
        """
        self.init_params.set_initialization_parameters_full(init_file, init_variables)

    def set_init_variables(self, init_variables: dict):
        self.init_params.set_init_variables(init_variables)

    def use_init_file(self, use_init_file=True):
        self.init_params.set_use_init_file(use_init_file)

    def use_init_vals(self, use_init_vals=True):
        self.init_params.set_use_init_values(use_init_vals)

    def set_init_file(self, init_file: str):
        self.init_params.set_init_filename(init_file)

