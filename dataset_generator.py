import types
import numpy as np
import pandas as pd

from database.DatabaseManager import DatabaseManager, CheckString, GetMachine

def SRS(p, d):
    points = []
    for _ in range(p):
        points.append(np.random.rand(d))
    return points
def LHS(p, d):
    limits = 1/p
    dims = [[aux for aux in range(p)] for _ in range(d)]

    data = []
    for _ in range(p):
        chosen = [-1 for _ in range(d)]
        for i in range(d):
            c = np.random.choice(dims[i])
            dims[i].pop(dims[i].index(c))
            chosen[i] =  np.random.rand() * limits * c
        data.append(chosen)
    return data

class DatasetGenerator:
    def __init__(self, sampling_method, device_name, objective_function, num_parameters, database=None):
        if type(sampling_method) != types.FunctionType:
            raise Exception(f'sampling_methods must be of type function, received {type(sampling_method)} - {sampling_method}')
        CheckString(sampling_method.__name__, 'sampling_method')
        self.sampling_method = sampling_method

        CheckString(device_name, 'device_name')
        self.device_name = device_name

        if type(objective_function) != types.FunctionType:
            raise Exception(f'function must be of type function, received {type(objective_function)} - {objective_function}')
        CheckString(objective_function.__name__, 'objective_function name')
        self.function = objective_function

        if not isinstance(num_parameters, int):
            raise Exception(f'num_parameters must be integer, received {type(num_parameters)} - {num_parameters}')
        if num_parameters <= 0:
            raise Exception(f'num_parameters must be greater than 0, received {num_parameters}')
        self.num_parameters = num_parameters

        if database == None:
            self.db = DatabaseManager()
        else:
            CheckString(database, 'database')
            self.db = DatabaseManager(database)

    def GenerateDataset(self, points):
        data = self.sampling_method(points, self.num_parameters)
        data = pd.DataFrame(data, columns=[f'in_{d}' for d in range(self.num_parameters)])

        if not self.db.RetrieveMachineID(self.device_name):
            machine = self.db.InsertMachine(GetMachine(self.device_name))
        else:
            machine = self.db.RetrieveMachineID(self.device_name)
        if not self.db.RetrieveProgramID(self.function.__name__):
            program = self.db.InsertProgram(self.function.__name__)
        else:
            program = self.db.RetrieveProgramID(self.function.__name__)
        return self.db.InsertDataset(self.sampling_method.__name__, program, machine, data), data

    def GetDataset(self, id):
        return self.db.RetrieveDataset(id)
    def RemoveDataset(self, id):
        self.db.RemoveDataset(id)

