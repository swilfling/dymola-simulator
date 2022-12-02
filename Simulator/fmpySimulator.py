import numpy as np
import fmpy
import fmpy.fmi2
import numpy.lib.recfunctions as rfs
from pandas import DataFrame
from .ModelicaSimulator import ModelicaSimulator


class FMPYSimulator(ModelicaSimulator):
    """
    Simulator based on FMPY library - Simulate a single FMU
    """
    fmu_dir = ""
    fmu_filename = ""
    input_data = None
    input_feature_names = []
    output_feature_names = []
    simulation_results = None
    fmu = None

    def __init__(self, fmu_filename="", input_feature_names=None, output_feature_names=None, input_data=None, **kwargs):
        super().__init__(**kwargs)
        self.input_data = input_data
        self.fmu_filename = fmu_filename
        self.input_feature_names = input_feature_names
        self.output_feature_names = output_feature_names

    def _get_simulation_results(self, trajectory_names, **kwargs):
        simulation_results = {}
        for name in trajectory_names:
            simulation_results.update({name: np.array(self.simulation_results[name])})
            simulation_results.update({f"data_{name}": np.array(self.input_data[name])})
            if self.simulation_results.size > self.input_data.shape[0]:
                raise Exception("Sizes of simulation results and input data do not match.")
        return DataFrame(simulation_results, index=np.array(self.simulation_results["Time"]))

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






