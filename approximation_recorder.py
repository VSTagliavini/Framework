import gc
import os
import psutil
from pympler import asizeof
import pyRAPL
import time
import types
import pandas as pd

from database.DatabaseManager import DatabaseManager, CheckString, GetMachine

class Approximator:
    #One loop of the algorithms training
    def Train(self, input, output):
        raise Exception('method Approximator.Train must be overwritten')
    #Approximates one the objective function in a given point
    def Approximate(self):
        raise Exception('method Approximator.Approximate must be overwritten')    
    #Function that initializes the Approximator
    def Initialization(self):
        raise Exception('method Approximator.Initialization must initialize the optimization algorithm. If not needed, overwrite it with an empty function')

    def SetName(self, name):
        CheckString(name, 'Optimizer')
        self.name = name

class ApproximatorRecorder:
    def __init__(self, device_name, objective_function, num_parameters, measure_approximation_history=False, measure_flops=False, measure_time=False, measure_memory=False, measure_energy=False, measure_temperature=False, database=None):
        CheckString(device_name, 'device_name')
        self.device_name = device_name
        
        if type(objective_function) != types.FunctionType:
            raise Exception(f'objective_function must be of type function, received {type(objective_function)} - {objective_function}')
        self.function = objective_function

        if not isinstance(num_parameters, int):
            raise Exception(f'num_parameters must be integer, received {type(num_parameters)} - {num_parameters}')
        if num_parameters <= 0:
            raise Exception(f'num_parameters must be greater than 0, received {num_parameters}')
        self.num_parameters = num_parameters

        if not isinstance(measure_approximation_history, bool):
            raise Exception(f'measure_approximation_history must be bool, received {type(measure_approximation_history)}')
        self.measure_history = measure_approximation_history
        if not isinstance(measure_flops, bool):
            raise Exception(f'measure_flops must be bool, received {type(measure_flops)}')
        self.measure_flops = measure_flops
        if not isinstance(measure_time, bool):
            raise Exception(f'measure_time must be bool, received {type(measure_time)}')
        self.measure_time = measure_time
        if not isinstance(measure_memory, bool):
            raise Exception(f'measure_memory must be bool, received {type(measure_memory)}')
        self.measure_memory = measure_memory
        if self.measure_memory:
            self.max_memory_depth = 0
        if not isinstance(measure_energy, bool):
            raise Exception(f'measure_energy must be bool, received {type(measure_energy)}')
        self.measure_energy = measure_energy
        if self.measure_energy:
            pyRAPL.setup()
            self.energy_measurement = pyRAPL.Measurement('energy_measurement')
        if not isinstance(measure_temperature, bool):
            raise Exception(f'measure_temperature must be bool, received {type(measure_temperature)}')
        self.measure_temperature = measure_temperature
        if self.measure_temperature:
            self.core = os.sched_getaffinity(0)
            self.core = list(os.sched_getaffinity(0))[0]
            os.sched_setaffinity(0, {self.core})
            self.core = psutil.Process().cpu_num

        if database == None:
            self.db = DatabaseManager()
        else:
            CheckString(database, 'database')
            self.db = DatabaseManager(database)
        self.program = self.db.InsertProgram(objective_function.__name__)

    #Internal function to measure approximation technique performance
    def _approximation_function(self, x):
        if self.measure_time:
            elapsed_time = time.perf_counter() - self.previous_time
            if self.training:
                self.time_training.append(elapsed_time)
            if self.testing:
                self.time_testing.append(elapsed_time)
        if self.measure_temperature:
            temp = psutil.sensors_temperatures()['coretemp']
            if self.training:
                self.temperature_training.append([i for i in temp if i.label == f'Core {psutil.Process().cpu_num()}'][0].current)
            if self.testing:
                self.temperature_testing.append([i for i in temp if i.label == f'Core {psutil.Process().cpu_num()}'][0].current)
        if self.measure_energy:
            self.energy_measurement.end()
            if self.training:
                self.energy_training.append(self.energy_measurement.result.pkg[0])
            if self.testing:
                self.energy_testing.append(self.energy_measurement.result.pkg[0])
#        if self.measure_memory:
#            gc.collect()
#            memory = asizeof.asizeof(self.approximator, limit=self.max_memory_depth)
#            while memory <= 0:
#                self.max_memory_depth = self.max_memory_depth + 1
#                gc.collect()
#                memory = asizeof.asizeof(self.approximator, limit=self.max_memory_depth)
#            if self.training:
#                self.memory_training.append(memory)
#            if self.testing:
#                self.memory_testing.append(memory)

        value = self.approximator.Approximate(x)

        if self.training:
            self.approximations_training.append(value)
        if self.testing:
            self.approximations_testing.append(value)

        if self.measure_energy:
            self.energy_measurement.begin()
        if self.measure_time:
            self.previous_time = time.perf_counter()

        return value

    #Trains the model until the buget is exceeded
    #Saves the training performance to self.db and returns its entry's ID
    def Train(self, dataset, iterative=False):
        if type(iterative) != bool:
            raise Exception(f'iterative must be of type bool, received {type(iterative)}')
        self.training = iterative

        self._initialize_training_history()

        self.training_dataset = dataset
        dataset = self.db.RetrieveDataset(dataset)

        input = dataset[[f'in_{d}' for d in range(self.num_parameters)]].to_numpy()
        output = dataset['out'].to_numpy()

        if self.measure_temperature:
            temp = psutil.sensors_temperatures()['coretemp']
            self.training_temperature_start = [i for i in temp if i.label == f'Core {psutil.Process().cpu_num()}'][0].current
        if self.measure_energy:
            start_energy = self.energy_measurement.begin()
        if self.measure_time:
            start_time = time.perf_counter()

        self.approximator.Initialization()
        self.approximator.Train(input, output)

        if self.measure_time:
            self.training_time = time.perf_counter() - start_time
        if self.measure_temperature:
            temp = psutil.sensors_temperatures()['coretemp']
            self.training_temperature = [i for i in temp if i.label == f'Core {psutil.Process().cpu_num()}'][0].current
            self.training_temperature = self.training_temperature - self.training_temperature_start
        if self.measure_energy:
            self.energy_measurement.end()
            self.training_energy = self.energy_measurement.result.pkg[0]
        if self.measure_memory:
            gc.collect()
            self.training_memory = asizeof.asizeof(self.approximator, limit=self.max_memory_depth)
            while self.training_memory <= 0:
                self.max_memory_depth = self.max_memory_depth + 1
                gc.collect()
                self.training_memory = asizeof.asizeof(self.approximator, limit=self.max_memory_depth)

    #Tests the model for a given dataset
    #Saves the testing performance to self.db and returns its entry's ID
    def Test(self, dataset):
        self._initialize_testing_history()
        self.testing = True
        self.estimates = []

        self.testing_dataset = dataset
        dataset = self.db.RetrieveDataset(dataset)

        dataset = dataset[[f'in_{d}' for d in range(self.num_parameters)]]
        dataset = dataset.to_numpy()

        self.previous_time = time.perf_counter()

        for data in dataset:
            self.estimates.append(self._approximation_function(data))
        self._save_approximation_history()

    #Receives a class that extends Approximator and sets it as self.approximator
    #Additionally saves it to self.db
    def SetApproximationAlgorithm(self, approximator):
        self.approximator = approximator
        self.approximation = self.db.InsertApproxTech(self.approximator.name)

    #Saves current machine's data to self.db
    def _set_machine(self):
        self.machine = self.db.InsertMachine(GetMachine(self.device_name))

    #Initializes training performances lists
    def _initialize_training_history(self):
        self.approximations_training = []
        self.flops_training = []
        self.time_training = []
        self.memory_training = []
        self.energy_training = []
        self.temperature_training = []

    #Initializes testing performances lists
    def _initialize_testing_history(self):
        self.approximations_testing = []
        self.flops_testing = []
        self.time_testing = []
        self.memory_testing = []
        self.energy_testing = []
        self.temperature_testing = []

    #Saves history to self.db
    #case defines if it is training or testing
    def _save_approximation_history(self):
        data = [[-1, -1, -1, -1] for _ in range(len(self.estimates))]

        entries = len(self.estimates)
        for i in range(entries):
            data[i][0] = self.estimates[i]
        if self.measure_time:
            for i in range(entries):
                data[i][1] = self.time_testing[i]
        else:
            for i in range(entries):
                data[i][1] = -1
        if self.measure_energy:
            for i in range(entries):
                data[i][2] = self.energy_testing[i]
        else:
            for i in range(entries):
                data[i][2] = -1
        if self.measure_temperature:
            for i in range(entries):
                data[i][3] = self.temperature_testing[i]
        else:
            for i in range(entries):
                data[i][3] = -1
#        if self.measure_memory:
#            for i in range(entries):
#                data[i][4] = self.memory_testing[i]
#        else:
#            for i in range(entries):
#                data[i][4] = -1

        data = pd.DataFrame(data, columns=['value', 'time', 'energy', 'temperature'])#, 'memory'])
            
        self.db.InsertApproxHist(self.program, self.training_dataset, self.testing_dataset, self.approximation, [self.training_time, self.training_energy, self.training_temperature, self.training_memory], data)





