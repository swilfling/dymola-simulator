import os

from ..SimulationUtilities import simulation_utils as simutils
from . import ModelicaSimulator
from buildingspy.simulate.Simulator import Simulator
from buildingspy.io.outputfile import Reader


class BuildingsPySimulator(ModelicaSimulator):
    """
    Modelica Simulator based on the BuildingsPy Library.
    The simulator supports the following methods:
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    ######################### Implementation ###########################################################################

    def _get_simulation_results(self, trajectory_names, **kwargs):
        """
        Get simulation results from result file
        @param trajectory_names: names of trajectories
        Virtual method - override this
        """
        result_file_name = kwargs.get('out_file_name', self.result_filename)
        r = Reader(result_file_name, "dymola")
        # Get time
        t,y = r.values(trajectory_names[0])
        trajectories = [t]
        trajectories += [r.values(name)[1] for name in trajectory_names]
        simulation_results = simutils.create_df(trajectories, trajectory_names)
        return simulation_results

    def _simulate_model(self, additional_params=None, **kwargs):
        """
         Simulate model
         @param additional_params: additional params to set before simulation
         """
        result_directory_path = self.get_data_dir()
        # Instantiate simulator
        sim = Simulator(self.model_name_full, "dymola", result_directory_path, self.workdir_path)

        sim.setStartTime(self.sim_params.start_time)
        sim.setStopTime(self.sim_params.stop_time)
        sim.setNumberOfIntervals(self.sim_params.num_intervals)
        sim.setSolver(self.sim_params.algorithm)

        # Set additional parameters - used in sweeps
        sim.addParameters(additional_params)
        # sim.showGUI(show=True)

        result_file_name = os.path.join(result_directory_path, kwargs.get('out_file_name', self.result_filename))
        sim.setResultFile(result_file_name)

        # Add command execution
        for command in kwargs.get('commands', []):
            sim.addPreProcessingStatement(command)
        # Simulate model
        sim.simulate()

