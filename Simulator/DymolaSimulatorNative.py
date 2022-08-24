import os

from ..SimulationUtilities import simulation_utils as simutils
from .ModelicaSimulator import ModelicaSimulator


class DymolaSimulatorNative(ModelicaSimulator):
    """
    Dymola Simulator. This simulator uses the native Dymola-Python interface.
    The simulator offers the following methods:
    Base class: see ModelicaSimulator
    Additional:
    - terminate
    """
    dymolapath = ""
    dymola = None
    show_dymola_window = False

    def __init__(self, dymolapath="", show_dymola_window=False, **kwargs):
        super().__init__(**kwargs)
        self.dymolapath = dymolapath
        self.show_dymola_window = show_dymola_window

    def __del__(self):
        self.terminate()

    def terminate(self):
        """
        Terminate Simulation. This closes Dymola.
        """
        self._close_dymola()

    ################################# Private methods #################################################################

    def _open_dymola(self):
        """
        Open Dymola. This instantiates self.dymola as a new instance of the DymolaPythonInterface
        """
        try:
            from dymola.dymola_interface import DymolaInterface
            self.dymola = DymolaInterface(self.dymolapath, showwindow=self.show_dymola_window) if self.dymola is None else self.dymola
        except ModuleNotFoundError:
            raise Exception("Import Dymola Interface: Dymola Module not found - probably no Dymola installation on this machine.")
        except NameError:
            raise Exception("Open Dymola: Dymola module not found - probably no Dymola installation on this machine.")

    def _close_dymola(self):
        """
        Close Dymola.
        """
        if self.dymola is not None:
            self.dymola.close()
        self.dymola = None

    def _handle_dymola_exception(self, ex):
        """
        Dymola Exception: Print Dymola Error log
        """
        print(("Error: " + str(ex)))
        if self.dymola is not None:
            print(self.dymola.getLastErrorLog())

    def _export_equations(self, model_name):
        """
            Get simulation results from Dymola output file.
            @param trajectory_names: names of trajectories to return

            Optional parameter: out_file_name: Alternative output filename
        """
        try:
            self._open_dymola()
            self.dymola.exportEquations(os.path.join(self.get_data_dir(), f'{model_name}_equations.mml'))
        except Exception as ex:
            self._handle_dymola_exception(ex)
            self._close_dymola()

    def _get_simulation_results(self, trajectory_names, **kwargs):
        """
        Get simulation results from Dymola output file.
        @param trajectory_names: names of trajectories to return

        Optional parameter: out_file_name: Alternative output filename
        """
        result_path = os.path.join(self.get_data_dir(abspath=True), f"{kwargs.get('out_file_name', self.result_filename)}.mat")
        try:
            self._open_dymola()
            # trajectory_names = dymola.readTrajectoryNames(result_file_name_extended) # This would return all trajectories
            traj_names_full = ["Time"] + trajectory_names
            traj_exist = self.dymola.existTrajectoryNames(result_path, traj_names_full)
            traj_to_read = [name for name, exists in zip(traj_names_full, traj_exist) if exists]
            traj_size = self.dymola.readTrajectorySize(result_path)
            trajectories = self.dymola.readTrajectory(result_path, traj_to_read, traj_size)
            return simutils.create_df(trajectories, traj_to_read)
        except FileExistsError:
            print(f"Error: Result file {result_path} does not exist. Possible reason: Simulation not successful.")
        except Exception as ex:
            self._handle_dymola_exception(ex)
            self._close_dymola()

    def _simulate_model(self,
                        additional_params=None,
                        export_equations_enabled=False,
                        **kwargs):
        """
        Simulate model
        @param additional_params: additional params to set before simulation
        @param export_equations_enabled: enable equation export - still in progress
        """
        out_file_name = kwargs.get('out_file_name', self.result_filename)
        if export_equations_enabled:
            self._export_equations(out_file_name)
        try:
            # Instantiate the Dymola interface and start Dymola
            self._open_dymola()
            # Add package to Modelica path and open model
            self.dymola.AddModelicaPath(self.workdir_path)
            self.dymola.openModel(os.path.join(self.workdir_path, "package.mo"))
            # Set additional parameters - used in sweeps
            if additional_params:
                for param_key, param_val in additional_params.items():
                    if param_key != "":
                        additional_command = f"{param_key}={param_val}"
                        self.dymola.ExecuteCommand(additional_command)

            result_file = os.path.join(self.get_data_dir(), out_file_name)
            # Simulate Model
            simulation_success = self.dymola.simulateModel(self.model_name_full,
                                                           startTime=self.sim_params.start_time,
                                                           stopTime=self.sim_params.stop_time,
                                                           numberOfIntervals=self.sim_params.num_intervals,
                                                           outputInterval=self.sim_params.output_interval,
                                                           tolerance=self.sim_params.tolerance,
                                                           fixedstepsize=self.sim_params.fixed_stepsize,
                                                           method=self.sim_params.algorithm,
                                                           resultFile=result_file)
            if not simulation_success:
                raise Exception("Dymola Simulation failed.")
        except Exception as ex:
            self._handle_dymola_exception(ex)
            self._close_dymola()
