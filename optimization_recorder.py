#Execute first: sudo chmod o+r -R /sys/class/powercap/intel-rapl/

import types
import time
import gc
import os
import platform

import pyRAPL
from pympler import asizeof
import psutil
import numpy as np
from progress.bar import Bar

from database.DatabaseManager import DatabaseManager, CheckString

#REMOVE LATER
import json

# - FLOPS: floppy or flopscope
#          if all else fails: FLOPS = elapsed_time * CPU maximum FLOPs * CPU utilization

#System info: platform (operational system), psutil (hardware specifications) 

class Optimizer:
    #One 'loop' of the program's optimization
    #Will be called until optimization budget is exceeded
    def Optimize(self):
        pass
    #Defines the function to be optimized
    #Must receive function and number of parameters
    def SetObjectiveFunction(self, func, params):
        raise Exception('method Optimizer.SetObjectiveFunction must change the algorithm\'s objective function')
    def Initialization(self):
        raise Exception('method Optimizar.Initialization must initialize the optimization algorithm. If not needed, overwrite it with an empty function')
    def SetName(self, name):
        CheckString(name, 'Optimizer')
        self.name = name

class Estimator:
    #One 'loop' of the program's approximation training
    #Will be called until optimization budget is exceeded
    def Train(self):
        pass
    #One approximation of the program
    def Estimate(self):
        pass

class Recorder:
    def __init__(self, device_name, objective_function, num_parameters, estimator=None, measure_optimizing_history=False, measure_flops=False, measure_time=False, measure_memory=False, measure_energy=False, measure_temperature=False, database=None):
        CheckString(device_name, 'device_name')
        self.device_name = device_name

        if type(objective_function) != types.FunctionType:
            raise Exception(f'function must be of type function, received {type(objective_function)} - {objective_function}')
        self.function = objective_function
        
        if not isinstance(num_parameters, int):
            raise Exception(f'num_parameters must be integer, received {type(num_parameters)} - {num_parameters}')
        if num_parameters <= 0:
            raise Exception(f'num_parameters must be greater than 0, received {num_parameters}')
        self.num_parameters = num_parameters

        if estimator == None:
            self.use_estimator = False
        else:
            if not issubclass(type(estimator), Estimator):
                raise Exception(f'estimator must be subclass of Estimator')
            self.use_estimator = True
            self.estimator = estimator

        if not isinstance(measure_optimizing_history, bool):
            raise Exception(f'measure_optimizing_history must be bool, received {type(measure_optimizing_history)}')
        self.solutions = {}
        self.measure_history = measure_optimizing_history
        if self.measure_history:
            self.histories = {}
        if not isinstance(measure_flops, bool):
            raise Exception(f'measure_flops must be bool, received {type(measure_flops)}')
        self.measure_flops = measure_flops
        if self.measure_flops:
            self.flops = {}
        if not isinstance(measure_time, bool):
            raise Exception(f'measure_time must be bool, received {type(measure_time)}')
        self.measure_time = measure_time
        if self.measure_time:
            self.times = {}
        if not isinstance(measure_memory, bool):
            raise Exception(f'measure_memory must be bool, received {type(measure_memory)}')
        self.measure_memory = measure_memory
        if self.measure_memory:
            self.memories = {}
            self.max_memory_depth = 0
        if not isinstance(measure_energy, bool):
            raise Exception(f'measure_energy must be bool, received {type(measure_energy)}')
        self.measure_energy = measure_energy
        if self.measure_energy:
            self.energies = {}
            pyRAPL.setup()
            self.energy_measurement = pyRAPL.Measurement('energy_measurement')

        if not isinstance(measure_temperature, bool):
            raise Exception(f'measure_temperature must be bool, received {type(measure_temperature)}')
        self.measure_temperature = measure_temperature
        if self.measure_temperature:
            self.temperatures = {}
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

    def _evaluate_function(self, x):
        if self.use_estimator:
            return self.estimator(x)
        else:
            return self.function(x)

    def _optimization_function(self, x):

        if self.measure_time:
            elapsed_time = time.perf_counter() - self.previous_time
            self.times[self.current_operation].append(elapsed_time)
        if self.measure_temperature:
            temp = psutil.sensors_temperatures()['coretemp']
            self.temperatures[self.current_operation].append([i for i in temp if i.label == f'Core {psutil.Process().cpu_num()}'][0].current)
        if self.measure_energy:
            self.energy_measurement.end()
            self.energies[self.current_operation].append(self.energy_measurement.result.pkg[0])
        if self.measure_memory:
            gc.collect()
            memory = asizeof.asizeof(self.optimizer, limit=self.max_memory_depth)
            while memory < 0:
                self.max_memory_depth = self.max_memory_depth+1
                gc.collect()
                memory = asizeof.asizeof(self.optimizer, limit=self.max_memory_depth)
            self.memories[self.current_operation].append(memory)

        if self.time_budget:
            aux = time.perf_counter()
        value = self._evaluate_function(x)

        self.solutions[self.current_operation].append(x)
        if self.time_budget:
            print(f'elapsed_time {time.perf_counter() - aux}', end='')
            self.execution_time = self.execution_time + (time.perf_counter() - aux)
            print(f'total {self.execution_time}')

        if self.measure_energy:
            self.energy_measurement.begin()
        if self.measure_time:
            self.previous_time = time.perf_counter()
        if self.measure_history:
            self.histories[self.current_operation].append(value)

        self.function_calls = self.function_calls + 1
        return value
    #PSEUDOCODE
    #if measures flops:     end flops measurement, record flops
    #value = self._evaluate_function(x)
    #if measures flops:     start flops measurement

    #Uses self.estimator to approximate self.function
    #Trains the model for a given amount of function evaluations, time elapsed (flops?) or until a given speedup is achieved
    #Measures specificed performance metrics
    #Additionally, may approximate function several times to check consistency
    def TrainEstimator(self):
        pass

    #Uses self.optimizer to optimize the self.function
    #Optimizes for a given amount of function evaluations, time elapsed (flops?) or until a given speedup is achieved
    #Measures specificed performance metrics
    #Also measures self.estimator.Estimate if it is used
    #Additionally, may optimize function several times to check consistency
    def Optimize(self, budget, unit, repetitions):
        self._save_machine()
        if unit in ('seconds', 'flops'):
            print('time budget')
            self.time_budget = True
        else:
            self.time_budget = False

        for iteration in range(repetitions):
            bar = Bar(f'{self.function.__name__} - {self.optimizer.name} - {iteration}', max=budget)
            bar.width = 50
            bar.next(0)
            self.current_operation = iteration
            self._initialize_history()
            cost = 0
            last_cost = 0
            self.function_calls = 0

            self.optimizer.Initialization()

            while cost < budget:
                if self.time_budget:
                    self.execution_time = 0
                ###IMPLEMENT LATER
                #if unit = time or flops:
                #   Record current_executions
                #   Measure initial time
            
                self.optimizer.Optimize()

                last_cost = cost
                if unit == 'executions':
                    cost = self.function_calls
                if unit == 'seconds':
                    cost = cost + self.execution_time

                ###IMPLEMENT LATER
                #if unit = 'time' or 'flops'
                #   Measure current time
                #   Elapsed time = (current time - initial time) - sum(self.times of executions since the last loop (self.function_calls-current_executions))            
                if unit in ('seconds', 'flops'):
                    pass
                ###IMPLEMENT LATER
                #if unit = 'time'
                #cost = cost + elapsed_time
                if unit == 'seconds':
                    pass
                ###IMPLEMENT LATER
                #if unit = 'flops'
                #cost = cost + (calculated flops)
                if unit == 'flops':
                    pass
                bar.next(cost-last_cost)
            bar.finish()
            self._save_optimization_history()

    def SetAutotuningAlgorithm(self, optimizer):
        #READD LATER
        #if not issubclass(type(optimizer), Optimizer):
        #    raise Exception(f'optimizer must be subclass of Optimizer')
        self.optimizer = optimizer
        self.optimizer.SetObjectiveFunction(self._optimization_function, self.num_parameters)
        self.optimization = self.db.InsertAutotuningTech(self.optimizer.name)

    def _initialize_history(self):
        self.solutions[self.current_operation] = []
        if self.measure_history:
            self.histories[self.current_operation] = []
        if self.measure_time:
            self.times[self.current_operation] = []
            self.previous_time = time.perf_counter()
        if self.measure_energy:
            self.energies[self.current_operation] = []
            self.energy_measurement.begin()
        if self.measure_memory:
            self.memories[self.current_operation] = []
        if self.measure_temperature:
            self.temperatures[self.current_operation] = []

    def _save_machine(self):
        net_stats = psutil.net_if_stats()
        net_speeds = [net_stats[a].mtu for a in net_stats]
        while len(net_speeds) < 5:
            net_speeds.append(0)
        
        m = {
            'NAME':                     self.device_name,
            'OS':                       platform.system()[0:32],
            'RELEASE':                  platform.release()[0:32],
            'VERSION':                  platform.version()[0:32],
            'PROCESSOR_ARCHITECTURE1':  platform.architecture()[0][0:32],
            'PROCESSOR_ARCHITECTURE2':  platform.architecture()[1][0:32],
            'INSTRUCTION_SET':          platform.machine()[0:32],
            'CPU_CORES':                psutil.cpu_count(),
            'MEMORY':                   psutil.virtual_memory().total,
            'NIC0':                     net_speeds[0],
            'NIC1':                     net_speeds[1],
            'NIC2':                     net_speeds[2],
            'NIC3':                     net_speeds[3],
            'NIC4':                     net_speeds[4],
        }
        self.machine = self.db.InsertMachine(m)

    def _save_optimization_history(self):
        history = {}
        history['solutions'] = self.solutions[self.current_operation]
        if self.measure_history:
            if type(self.histories[self.current_operation][0]) == np.float64:
                self.histories[self.current_operation] = [i.item() for i in self.histories[self.current_operation]]
            history['value'] = self.histories[self.current_operation]
        if self.measure_time:
            history['time'] = self.times[self.current_operation]
        if self.measure_memory:
            history['memory'] = self.memories[self.current_operation]
        if self.measure_energy:
            history['energy'] = self.energies[self.current_operation]
        if self.measure_temperature:
            history['temperature'] = self.temperatures[self.current_operation]

        self.db.InsertAutotuningHist(self.program, self.optimization, self.machine, None, None, history)


        #Export performance metrics, optimization and estimation algorithms used, and system information
        #Also export additional data provided by the user (such as if it used a container or virtual machine)
        #Exports to a small SQL database
#    def Export_Measurements(self):
#        #Maybe update to retrieve additional information through OS specific APIs
#
#        #TEMPORARY
#        
#
#        output = {}
#        if self.measure_history:
#            output['histories'] = self.histories
#        if self.measure_time:
#            output['times'] = self.times
#        if self.measure_memory:
#            output['memories'] = self.memories
#        if self.measure_energy:
#            output['energies'] = self.energies
#        if self.measure_temperature:
#            output['temperatures'] = self.temperatures
#        with open('temporary_output.json', 'w') as save_file:
#            json.dump(output, save_file, indent=4)

