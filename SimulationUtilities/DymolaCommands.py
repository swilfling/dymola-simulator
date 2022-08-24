# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 11:54:39 2021

@author: Basak
"""
import os
from .Parameters import DymolaModelParameters


# Create initial condition loading script
def create_load_init_cond_cmd(start_time, init_file):
    return [f"importInitialResult(\"{init_file}.mat\", {start_time});{os.linesep}"]


def create_set_workdir_cmd(workdir_path):
    return [f"Modelica.Utilities.System.setWorkDirectory(\"{workdir_path}\");{os.linesep}"]


def create_FMU_import_cmds(package_name, fmu_paths_full):
    return [f"importFMU(\"{path}\", true, false, false, \"{package_name}\");{os.linesep}" for path in fmu_paths_full if path]


def create_open_model_cmds(package_paths_full):
    return [(f"openModel(\"{path}\");{os.linesep}" if path else "") for path in package_paths_full]


def create_additional_param_cmds(additional_parameters):
    return [f"{key}={value};{os.linesep}" for key, value in additional_parameters.items()] if additional_parameters else []


def create_FMI_sim_time_cmds(sim_params):
    return [f"fmi_StartTime={sim_params.start_time};{os.linesep}",
            f"fmi_StopTime={sim_params.stop_time};{os.linesep}",
            f"fmi_NumberOfSteps={sim_params.num_intervals};{os.linesep}"]


def create_sim_cmds_extended(simulation_parameters, workdir_path, model_name_full, resultfile_path_full,
                             use_init=False, init_variables=None, additional_parameters=None):
    additional_parameter_commands = create_additional_param_cmds(additional_parameters)

    # Create simulation command - Parse simulation parameters
    simulation_cmd_params = {"startTime": simulation_parameters.start_time,
                             "stopTime": simulation_parameters.stop_time,
                             "outputInterval": simulation_parameters.output_interval,
                             "resultFile": f"\"{resultfile_path_full}\""}
    if use_init:
        simulation_cmd_params.update({"initialNames":  "{\"" + "\",\"".join(init_variables.keys()) + "\"}",
                                      "initialValues": "{" + ",".join("{}".format(value) for value in init_variables.values()) + "}"})

    adjusted_params = ",".join("{}={}".format(key, value) for key, value in simulation_cmd_params.items())
    simulate_model_cmd = f"simulateExtendedModel(\"{model_name_full}\", {adjusted_params});{os.linesep}"
    # Write simulation command to file
    return create_set_workdir_cmd(workdir_path) + additional_parameter_commands + [simulate_model_cmd]

# Create setup commands
def create_setup_cmds(workdir_path, package_paths_full, package_name, fmu_paths_full=[]):
    lines = create_open_model_cmds(package_paths_full) + create_set_workdir_cmd(workdir_path)
    if len(fmu_paths_full) > 0:
        lines += create_FMU_import_cmds(package_name,fmu_paths_full)
    return lines

# Create model switching commands
def create_model_switch_cmds(package_name, model_name, component_1: DymolaModelParameters, component_2: DymolaModelParameters, fmu_instance_name):
    parameters = ",".join(("{}={} ".format(key, value) for key, value in component_2.parameters.items())) if component_2.parameters else ""

    return [f"text = getClassText(\"{package_name}.{model_name}\");{os.linesep}",
            f"start_index = Modelica.Utilities.Strings.find(text, \"{component_1.model_name}\");{os.linesep}",
            f"end_index = Modelica.Utilities.Strings.find(text, \";\", startIndex=start_index);{os.linesep}",
            f"text_to_replace = Modelica.Utilities.Strings.substring(text, start_index,end_index);{os.linesep}",
            f"replacement_text = \"{component_2.model_name} {fmu_instance_name} ({parameters});\";{os.linesep}",
            f"text_new = Modelica.Utilities.Strings.replace(text, text_to_replace, replacement_text);{os.linesep}",
            f"setClassText(\"{package_name}\", text_new);{os.linesep}",
            f"checkModel(\"{package_name}.{model_name}\");{os.linesep}"]

