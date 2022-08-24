import numpy as np
import numpy.lib.recfunctions as rfs
import fmpy
import fmpy.fmi2
from pandas import DataFrame
from .ModelicaSimulator import ModelicaSimulator


class FMPYSimulator(ModelicaSimulator):
    """
    Simulator based on FMPY library - Simulate a single FMU
    """
    fmu_dir = ""
    fmu_filename = ""
    data_filename = ""
    input_data = None
    input_feature_names = []
    output_feature_names = []
    simulation_results = None
    fmu = None

    def __init__(self, fmu_filename="", input_feature_names=None, output_feature_names=None, data_filename="", **kwargs):
        super().__init__(**kwargs)
        self.data_filename = data_filename
        self.fmu_filename = fmu_filename
        self.input_feature_names = input_feature_names
        self.output_feature_names = output_feature_names

    def _get_simulation_results(self, trajectory_names, **kwargs):
        simulation_results = {"Time":np.array(self.simulation_results["Time"])}
        for name in trajectory_names:
            simulation_results.update({name: np.array(self.simulation_results[name])})
            if len(self.simulation_results.size) > self.input_data.shape[0]:
                raise Exception("Sizes of simulation results and input data do not match.")
        return DataFrame(simulation_results[trajectory_names],index=simulation_results["Time"], columns=trajectory_names)

    def _create_simulation_input_from_file(self, data_filename, skip_rows=4):
        input_data = np.genfromtxt(data_filename, delimiter=';', names=True)
        input_data = rfs.rename_fields(input_data,{"Zeitraum":"Time"})
        pick_columns = ["Time"] + self.input_feature_names + self.output_feature_names
        rows = input_data[pick_columns]
        return rows[skip_rows-1:]

    def _create_start_values(self, input_data):
        return{name: input_data[name] for name in self.input_feature_names + self.output_feature_names}

    def _extract_and_instantiate_FMU(self, instance_name):
        model_description = fmpy.read_model_description(self.fmu_filename)
        self.fmu_dir = fmpy.extract(self.fmu_filename)
        fmu = fmpy.fmi2.FMU2Slave(guid=model_description.guid,
                        unzipDirectory=self.fmu_dir,
                        modelIdentifier=model_description.coSimulation.modelIdentifier,
                        instanceName=instance_name)
        fmu.instantiate()
        return fmu

    def _init_experiment(self, exp_name="", **kwargs):
        self.fmu = self._extract_and_instantiate_FMU("FMU1")
        self.input_data = self._create_simulation_input_from_file(self.data_filename)
        init_values = self.input_data[0] if not self.init_params.use_init_values else list(self.init_params.init_variables.values())
        self.start_values = self._create_start_values(init_values)

    def _simulate_model(self, **kwargs):
        result = fmpy.simulate_fmu(filename=self.fmu_dir,
                                   start_time=self.sim_params.start_time,
                                   stop_time=self.sim_params.stop_time,
                                   step_size=self.sim_params.output_interval,
                                   output_interval=self.sim_params.output_interval,
                                   start_values=self.start_values,
                                   input=self.input_data,
                                   output=self.output_feature_names,
                                   fmi_type='CoSimulation',
                                   fmu_instance=self.fmu)
        self.simulation_results = rfs.rename_fields(result, {"time":"Time"})






