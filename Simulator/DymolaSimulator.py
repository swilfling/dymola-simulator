import os
from .DymolaSimulatorNative import DymolaSimulatorNative
from .. SimulationUtilities import DymolaCommands


class DymolaSimulator(DymolaSimulatorNative):
    """
    MOS script based Dymola simulator
    Implements simulation commands in MOS scripts. These scripts are stored in the script_dir.
    Methods - inherited:
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
    - get_stop_time
    Setters:
    - set_start_time
    - set_stop_time
    Additional Methods:
    - create_mos_script
    - execute_commands
    - get_script_dir
    - run_dymola_script
    - run_dymola_scripts
    """
    script_dir = "Scripts"

    def __init__(self, script_dir="Scripts", **kwargs):
        super().__init__(**kwargs)
        self.script_dir = script_dir
        os.makedirs(self.get_script_dir(abspath=True), exist_ok=True)

    def setup_experiment(self, exp_name="", package_paths=[], fmu_paths_full=[], **kwargs):
        """
        Setup experiment.
        """
        setup_commands = DymolaCommands.create_setup_cmds(self.workdir_path, self.package_paths_full + package_paths,
                                                          self.package_name, fmu_paths_full)
        self.execute_commands(setup_commands, f"setup_script_{exp_name}.mos")

    def run_experiment(self, exp_name="", trajectory_names=[], start_time=None, stop_time=None,
                       plot_enabled=False, store_csv=True, **kwargs):
        """
        Run experiment - main function. Uses MOS scripts.
        @param exp_name: Experiment name - optional
        @param trajectory_names: Names of trajectories to return
        @param start_time Simulation start time
        @param stop_time Simulation stop time
        """
        return super().run_experiment(exp_name, trajectory_names, start_time, stop_time,
                                      plot_enabled=plot_enabled, store_csv=store_csv,
                                      script_name=f"simulation_script_{exp_name}.mos", **kwargs)

    def execute_commands(self, commands, script_name=""):
        """
        Execute Dymola commands in MOS script.
        @param commands: List of commands
        @param script_name: Name of script
        """
        script_path = self.create_mos_script(commands, script_name)
        self.run_dymola_script(script_path)


    ####################################### Dymola Script Creation ####################################################

    def create_mos_script(self, commands=[], filename=""):
        """
        Create a mos script to evaluate certain commands. The script is stored in the directory self.script_dir.
        @param commands: Commands to write
        @param filename: Script filename
        @return Path to script
        """
        script_path = os.path.join(self.get_script_dir(abspath=True), filename)
        with open(script_path, "w") as f:
            f.writelines(commands)
        return script_path

    def get_script_dir(self, abspath=False):
        """
        Get script directory.
        @param abspath: Select if you want to use the absolute path.
        @return Path to script directory.
        """
        return os.path.join(self.get_root_dir(abspath), self.script_dir)

    def run_dymola_script(self, script_path: str):
        """
        Execute Dymola Script.
        @param script_path: Path to MOS script
        """
        try:
            self._open_dymola()
            print("Running script: " + script_path)
            script_success = self.dymola.RunScript(script_path)
            if not script_success:
                raise Exception("Script execution failed.")
        except Exception as ex:
            self._handle_dymola_exception(ex)
            self._close_dymola()

    def run_dymola_scripts(self, script_paths: list):
        """
        Run multiple Dymola scripts.
        @param script_paths: List of paths
        """
        [self.run_dymola_script(path) for path in script_paths if path]

    ####################################### Simulate model using MOS scripts ###########################################

    def _simulate_model(self, script_name="simulation_script.mos", additional_params=None, export_equations_enabled=False, **kwargs):
        """
        Simulate model
        @param additional_params: additional params to set before simulation
        @param export_equations_enabled: enable equation export - still in progress
        @param script_name: name for simulation script
        """
        out_file_name = kwargs.get('out_file_name', self.result_filename)
        if export_equations_enabled:
            self._export_equations(out_file_name)
        cmds = DymolaCommands.create_sim_cmds_extended(simulation_parameters=self.sim_params,
                                                       workdir_path=self.workdir_path,
                                                       model_name_full=self.model_name_full(),
                                                       resultfile_path_full=os.path.join(self.get_data_dir(), out_file_name),
                                                       use_init=self.init_params.use_init_values,
                                                       init_variables=self.init_params.init_variables,
                                                       additional_parameters=additional_params)
        self.execute_commands(cmds, script_name)

    ############################### Commands ##########################################################################

    def _init_experiment(self, exp_name="", **kwargs):
        """
        Initialize Experiment based on init file.
        """
        if self.init_params.use_init_file:
            init_file_path = os.path.join(self.get_data_dir(), self.init_params.init_filename)
            init_command = DymolaCommands.create_load_init_cond_cmd(self.sim_params.start_time, init_file_path)
            self.execute_commands(init_command, f"init_script_{exp_name}.mos")

