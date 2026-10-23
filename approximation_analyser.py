import math
import numpy as np
import math

from database.DatabaseManager import CheckString, DatabaseManager

def STD(values):
    mean = sum(values)/len(values)
    std = [(values[i] - mean)**2 for i in range(len(values))]
    std = sum(std)/(len(std))
    return math.sqrt(std)

def VAR(values):
    mean = sum(values)/len(values)
    var = [(values[i] - mean)**2 for i in range(len(values))]
    return sum(var)/len(var)


class ApproximationAnalyser:
    def __init__(self, database=None):
        if database == None:
            self.db = DatabaseManager()
        else:
            CheckString(database)
            self.db = DatabaseManager()
    def ListApproximations(self, program, approximation=None, training_dataset=None, testing_dataset=None):
        #Lists all optimizations for a given program
        #May be filtered for approximation technique, training dataset and testing dataset
        CheckString(program, 'program')
        program = self.db.RetrieveProgramID(program)
        entries = self.db.RetrieveProgramApproxHist(program)
        if approximation != None:
            approximation = self.db.RetrieveApproxTechID(approximation)
            entries = [entry for entry in entries if entry[4]==approximation]

        if training_dataset != None:
            entries = [entry for entry in entries if entry[2]==training_dataset]
        if testing_dataset != None:
            entries = [entry for entry in entries if entry[3]==testing_dataset]
        entries = [entry[0] for entry in entries]
        return entries
    def GetApproximation(self, ID):
        data = self.db.RetrieveApproxHistData(ID)
        dataset = self.db.RetrieveDataset(data[3])
        approximation = self.db.RetrieveApproxHist(data[0])
        return {
            'data': data,
            'dataset': dataset,
            'approximation': approximation
        }
    def RMSE(self, approximation):
        approximation = self.GetApproximation(approximation)
        acc = 0
        for i in range(approximation['dataset'].shape[0]):
            acc = acc + (approximation['approximation']['value'][i] - approximation['dataset']['out'][i])**2
        acc = acc / approximation['dataset'].shape[0]
        return math.sqrt(acc)
    def GAE(self, approximation):
        approximation = self.GetApproximation(approximation)
        greatest_error = 0
        for i in range(approximation['dataset'].shape[0]):
            error = abs(approximation['approximation']['value'][i] - approximation['dataset']['out'][i])
            if error > greatest_error:
                greatest_error = error
        return greatest_error
    def Covariance(self, approximation):
        approximation = self.GetApproximation(approximation)
        real_mean = np.mean(approximation['dataset']['out'])
        estimated_mean = np.mean(approximation['approximation']['value'])
        acc = 0
        for i in range(approximation['dataset'].shape[0]):
            acc = acc + ((approximation['dataset']['out'][i] - real_mean) * (approximation['approximation']['value'][i] - estimated_mean))
        return acc / (approximation['dataset'].shape[0])
    def PearsonCorrelation(self, approximation):
        approx = approximation
        approximation = self.GetApproximation(approximation)
        real_std = STD(approximation['dataset']['out'])
        est_std = STD(approximation['approximation']['value'])
        covariance = self.Covariance(approx)
        return covariance/(real_std*est_std)
    def GetTrainingResources(self, approximation):
        approximation = self.db.RetrieveApproxHistData(approximation)
        return {
            'time':         approximation[5],
            'energy':       approximation[6],
            'temperature':  approximation[7],
            'memory':       approximation[8]
        }
    def _getApproximationResources(self, approximation):
        approximation = self.db.RetrieveApproxHistData(approximation)
        approximation = self.db.RetrieveApproxHist(approximation[0])
        approximation = approximation.drop(columns=['value'])
        return approximation
    def GetApproximationResources(self, approximation):
        approximation = self._getApproximationResources(approximation)
        metrics = {}
        for metric in ['time', 'energy', 'temperature']:
            metrics[metric] = {}
            metrics[metric]['total'] = sum(approximation[metric])
            metrics[metric]['greatest'] = max(approximation[metric])
            metrics[metric]['interval'] = metrics[metric]['greatest'] - min(approximation[metric])
            metrics[metric]['avg'] = metrics[metric]['total']/len(approximation[metric])
            metrics[metric]['var'] = VAR(approximation[metric])
            metrics[metric]['std'] = STD(approximation[metric])
        return metrics
    def GetApproximationStability(self, approximations):
        metrics = {}
        RMSEs = [self.RMSE(app) for app in approximations]
        metrics['RMSE'] = {
            'smallest': min(RMSEs),
            'greatest': max(RMSEs),
            'avg':      sum(RMSEs)/len(RMSEs),
            'var':      VAR(RMSEs),
            'std':      STD(RMSEs)
        }
        GAEs = [self.GAE(app) for app in approximations]
        metrics['GAE'] = {
            'smallest': min(GAEs),
            'greatest': max(GAEs),
            'avg':      sum(GAEs)/len(GAEs),
            'var':      VAR(GAEs),
            'std':      STD(GAEs)
        }
        COVs = [self.Covariance(app) for app in approximations]
        metrics['covariance'] = {
            'smallest': min(COVs),
            'greatest': max(COVs),
            'avg':      sum(COVs)/len(COVs),
            'var':      VAR(COVs),
            'std':      STD(COVs)
        }
        PEAs = [self.PearsonCorrelation(app) for app in approximations]
        metrics['Pearson'] = {
            'smallest': min(PEAs),
            'greatest': max(PEAs),
            'avg':      sum(PEAs)/len(PEAs),
            'var':      VAR(PEAs),
            'std':      STD(PEAs)
        }
        return metrics
    def GetResourceStability(self, approximations):
        metrics = {}

        trainings = [self.GetTrainingResources(app) for app in approximations]
        metrics['training'] = {}
        time = [i['time'] for i in trainings]
        metrics['training']['time'] = {
            'smallest': min(time),
            'greatest': max(time),
            'avg':      sum(time)/len(time),
            'var':      VAR(time),
            'std':      STD(time)
        }
        energy = [i['energy'] for i in trainings]
        metrics['training']['energy'] = {
            'smallest': min(energy),
            'greatest': max(energy),
            'avg':      sum(energy)/len(energy),
            'var':      VAR(energy),
            'std':      STD(energy)
        }
        temperature = [i['temperature'] for i in trainings]
        metrics['training']['energy'] = {
            'smallest': min(temperature),
            'greatest': max(temperature),
            'avg':      sum(temperature)/len(temperature),
            'var':      VAR(temperature),
            'std':      STD(temperature)
        }

        metrics['testing'] = {}
        testings = [self.GetApproximationResources(app) for app in approximations]
        
        for metric in ['time', 'energy', 'temperature']:
            metric_total = [i[metric]['total'] for i in testings]
            metric_average = [i[metric]['avg'] for i in testings]
            metrics['testing'][metric] = {
                'total': {
                    'smallest': min(metric_total),
                    'greatest': max(metric_total),
                    'avg':      sum(metric_total)/len(metric_total),
                    'var':      VAR(metric_total),
                    'std':      VAR(metric_total)
                },
                'average': {
                    'smallest': min(metric_average),
                    'greatest': max(metric_average),
                    'avg':      sum(metric_average)/len(metric_average),
                    'var':      VAR(metric_average),
                    'std':      VAR(metric_average)
                }
            }
        return metrics
    def GetTrainingPareto(self, approximations):
        objectives = ['time', 'energy', 'temperature', 'memory']
        aux = [{} for _ in range(len(approximations))]
        for i in range(len(approximations)):
            aux[i]['index'] = i
            resources = self.GetTrainingResources(approximations[i])
            for obj in objectives:
                aux[i][obj] = resources[obj]
        approximations = aux
        pareto_set = [approximations[0]]
        for app in approximations[1:]:
            dominated = False
            if any(all(pareto_set[i][obj] <= app[obj] for obj in objectives) and any(pareto_set[i][obj] < app[obj] for obj in objectives) for i in range(len(pareto_set))):
                dominated = True
            if not dominated:
                pareto_set.append(app)
                pareto_set = [p for p in pareto_set if not any(all(pareto_set[i][obj] <= p[obj] for obj in objectives) and any(pareto_set[i][obj] < p[obj] for obj in objectives) for i in range(len(pareto_set)))]
        p_set = [pareto_set[0]]
        for i in range(1, len(pareto_set)):
            duplicate = False
            for j in range(len(p_set)):
                if i == j:
                    continue
                if all(pareto_set[i][obj] == p_set[j][obj] for obj in objectives):
                    duplicate = True
                    break
            if not duplicate:
                p_set.append(pareto_set[i])
        return p_set
    def GetApproximationPareto(self, approximations, objective):
        if type(objective) != str:
            raise Exception(f'objectives must be of type str, received {type(objective)}')
        if objective not in ['total', 'greatest', 'interval', 'avg', 'var', 'std']:
            raise Exception(f'objective must be in {['total', 'greatest', 'interval', 'avg', 'var', 'std']}, received {objective}')
        aux = [self.GetApproximationResources(app) for app in approximations]
        objectives = ['time', 'energy', 'temperature']
        aux_2 = []
        for i in range(len(approximations)):
            approximation = {'index': approximations[i]}
            for obj in objectives:
                approximation[obj] = aux[i][obj][objective]
            aux_2.append(approximation)
        approximations = aux_2



        pareto_set = [approximations[0]]
        for app in approximations[1:]:
            dominated = False
            if any(all(pareto_set[i][obj] <= app[obj] for obj in objectives) and any(pareto_set[i][obj] < app[obj] for obj in objectives) for i in range(len(pareto_set))):
                dominated = True
            if not dominated:
                pareto_set.append(app)
                pareto_set = [p for p in pareto_set if not any(all(pareto_set[i][obj] <= p[obj] for obj in objectives) and any(pareto_set[i][obj] < p[obj] for obj in objectives) for i in range(len(pareto_set)))]
        p_set = [pareto_set[0]]
        for i in range(1, len(pareto_set)):
            duplicate = False
            for j in range(len(p_set)):
                if i == j:
                    continue
                if all(pareto_set[i][obj] == p_set[j][obj] for obj in objectives):
                    duplicate = True
                    break
            if not duplicate:
                p_set.append(pareto_set[i])
        return p_set
