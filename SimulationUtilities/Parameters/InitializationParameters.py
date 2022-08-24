from dataclasses import dataclass, field
from .parameters import Parameters

@dataclass
class InitializationParameters(Parameters):
    use_init_values: bool = False
    init_variables: dict = field(default_factory=dict)
    use_init_file: bool = False
    init_filename: str = ""

    def set_init_variables(self, init_variables:dict):
        if init_variables is not None:
            self.init_variables = init_variables

    def set_use_init_file(self, use_init_file):
        self.use_init_file = use_init_file

    def set_use_init_values(self, use_init_values):
        self.use_init_values = use_init_values

    def set_init_filename(self, init_filename: str):
        if init_filename is not None:
            self.init_filename = init_filename

    def set_initialization_parameters_full(self, init_file, init_variables):
        self.init_variables.update(init_variables)
        self.use_init_file = True
        self.init_filename = init_file
        self.use_init_values = True


