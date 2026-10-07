import math
import numpy as np
import scipy
import math

from database.DatabaseManager import CheckString, DatabaseManager

def MAD(values):
    mean = np.average(values)
    distances = [abs(v - mean) for v in values]
    return np.average(distances)

class Analyser:
    def __init__(self, database=None):
        if database == None:
            self.db = DatabaseManager()
        else:
            CheckString(database)
            self.db = DatabaseManager()
    def GetIterationsToImprovement(self, data):
        #Returns a list of the best solutions found by the algorihtm and how long they stayed the best solution
        iterations = 1
        d = [[data['data']['value'][0], 0]]
        for i in range(1, data['data'].shape[0]):
            if data['data']['value'][i] < d[-1][0]:
                d[-1][1] = iterations
                iterations = 1
                d.append([data['data']['value'][i], 0])
            else:
                iterations = iterations + 1
        d[-1][1] = iterations
        return d
    def _get_value_change(self, data):
        aux = [0]
        aux = [abs(data['data']['value'][0])]
        for i in range(1, data['data'].shape[0]):
            aux.append(abs(data['data']['value'][i] - data['data']['value'][i-1]))
        return aux
    def _generate_pareto_entries(self, algs, objectives):
        set = []
        for alg in algs:
            entry = []
            for obj in objectives.keys():
                if obj == 'value':
                    if objectives[obj] == 'smaller':
                        entry.append(alg[0])
                    else:
                        entry.append(-alg[0])
                else:
                    if objectives[obj] == 'smaller':
                        entry.append(alg[1][0][obj])
                    else:
                        entry.append(-alg[1][0][obj])
            set.append(entry)
        return set
    def ListOptimizations(self, program, machine=None, autotuning=None, approximation=None, dataset=None):
        #Lists all optimizations for a given program
        #May be filtered for machine, autotuning technique, approximation technique and dataset
        CheckString(program, 'program')
        program = self.db.RetrieveProgramID(program)
        entries = self.db.RetrieveProgramAutotuning(program)
        if machine != None:
            machine = self.db.RetrieveMachineID(machine)
            entries = [entry for entry in entries if entry[3]==machine]
        if autotuning != None:
            autotuning = self.db.RetrieveAutotuningTechID(autotuning)
            entries = [entry for entry in entries if entry[2]==autotuning]
        if approximation != None:
            approximation = self.db.RetrieveApproxTechID(approximation)
            entries = [entry for entry in entries if entry[4]==approximation]
        if dataset != None:
            dataset = self.db.RetrieveTrainingDataData(dataset)
            entries = [entry for entry in entries if entry[5]==dataset]
        entries = [entry[0] for entry in entries]
        return entries
    def GetOptimization(self, ID):
        #Recovers the dataframe stored on a parquet file
        data = self.db.RetrieveAutotuningHist(ID)
        columns = ['time', 'memory', 'energy', 'temperature']
        for column in columns:
            if column not in data['data'].columns:
                data['data'].insert(data['data'].shape[1], column, [-1] * data['data'].shape[0])
        return data
    def CheckConvergence(self, data, i=100, goal='iterations', iterations=50):
        #Checks if the algorithm converged by:
        #- Not improvig it's solution for a number of iterations
        #- Achieving a solution equal to or smalller than a given value
        if goal in ['iterations', 'value']:
            data = self.GetIterationsToImprovement(data)
        if goal == 'step':
            data = self._get_value_change(data)

        if goal == 'iterations':
            it = 0
            for d in data:
                if d[1] >= i:
                    return d[0], it
                it = it + d[1]
            return None
        if goal == 'value':
            it = 0
            for d in data:
                if d[0] <= i:
                    return d[0], it
                it = it + d[1]
            return None
        if goal == 'step':
            iter = iterations
            for aux in range(len(data)):
                if data[aux] <= i:
                    iter = iter - 1
                if iter == 0:
                    return aux
                if data[aux] > i:
                    iter = iterations
            return None
    def BestValue(self, data):
        aux = math.inf
        for d in data['data']['value']:
            if d < aux:
                aux = d
        return aux
    def GetOptimizationStability(self, opts, objective_value=None, confidence_interval=0.95, conv_i=100, conv_g='iterations', conv_it=50):
        #Returns basic metrics on the algorithm stability across multiple iterations
        basic_metrics = []

        datas = []
        best_solutions = []
        for opt in opts:
            data = self.GetOptimization(opt)
            datas.append(data)
            steps = self._get_value_change(data)
            best_values = self.GetIterationsToImprovement(data)
            convergence = self.CheckConvergence(data, conv_i, conv_g, conv_it)

            basic_metrics.append({
                'sol': best_values[-1][0],
                'found': data['data'].shape[0] - best_values[-1][1],
                'step_avg': np.average(steps),
                'step_var': np.var(steps),
                'step_std': np.std(steps),
                'converged': convergence[0],
                'converged_in': convergence[1]
            })
            best_solutions.append(best_values[-1][0])
        best_solutions = (best_solutions, )

        ci = scipy.stats.bootstrap(best_solutions, np.average, confidence_level=confidence_interval, axis=0)

        ans = {}
        if objective_value != None:
            ans['target_achieved'] =    sum([1 if a['sol'] <= objective_value else 0 for a in basic_metrics])/len(basic_metrics)
        ans['ci_low'] = ci.confidence_interval.low
        ans['ci_high'] = ci.confidence_interval.high

        ans['sol_best'] =               min([a['sol'] for a in basic_metrics])
        ans['sol_worst'] =              max([a['sol'] for a in basic_metrics])
        ans['sol_avg'] =                np.average([a['sol'] for a in basic_metrics])
        ans['sol_var'] =                np.var([a['sol'] for a in basic_metrics])
        ans['sol_std'] =                np.std([a['sol'] for a in basic_metrics])
        ans['sol_mad'] =                MAD([a['sol'] for a in basic_metrics])
        ans['found_best'] =             min([a['found'] for a in basic_metrics])
        ans['found_avg'] =              np.average([a['found'] for a in basic_metrics])
        ans['found_var'] =              np.var([a['found'] for a in basic_metrics])
        ans['found_std'] =              np.std([a['found'] for a in basic_metrics])
        ans['found_mad'] =              MAD([a['found'] for a in basic_metrics])
        ans['conv_earliest'] =          min(a['converged_in'] for a in basic_metrics)
        ans['conv_avg'] =               np.average([a['converged_in'] for a in basic_metrics])
        ans['conv_var'] =               np.var([a['converged_in'] for a in basic_metrics])
        ans['conv_std'] =               np.std([a['converged_in'] for a in basic_metrics])
        ans['conv_mad'] =               MAD([a['converged_in'] for a in basic_metrics])
        ans['step_avg'] =               np.average([a['step_avg'] for a in basic_metrics])
        ans['step_var'] =               np.average([a['step_var'] for a in basic_metrics])
        ans['ster_std'] =               np.average([a['step_std'] for a in basic_metrics])
        ans['step_mad'] =               MAD([a['step_avg'] for a in basic_metrics])
        ans['time_total'] =             np.average([sum([data['data']['time']]) for data in datas]) if datas[0]['data']['time'][0] != -1 else None        
        ans['time_avg'] =               np.average([np.average(data['data']['time']) for data in datas]) if datas[0]['data']['time'][0] != -1 else None
        ans['time_var'] =               np.average([np.var(data['data']['time']) for data in datas]) if datas[0]['data']['time'][0] != -1 else None
        ans['time_std'] =               np.average([np.std(data['data']['time']) for data in datas]) if datas[0]['data']['time'][0] != -1 else None
        ans['time_mad'] =               MAD([data['data']['time'] for data in datas]) if datas[0]['data']['time'][0] != -1 else None
        ans['memory_avg'] =             np.average([np.average(data['data']['memory']) for data in datas]) if datas[0]['data']['memory'][0] != -1 else None
        ans['memory_var'] =             np.average([np.var(data['data']['memory']) for data in datas]) if datas[0]['data']['memory'][0] != -1 else None
        ans['memory_std'] =             np.average([np.std(data['data']['memory']) for data in datas]) if datas[0]['data']['memory'][0] != -1 else None
        ans['memory_mad'] =             MAD([data['data']['memory'] for data in datas]) if datas[0]['data']['memory'][0] != -1 else None
        ans['energy_total'] =           np.average([sum(data['data']['energy']) for data in datas]) if datas[0]['data']['energy'][0] != -1 else None
        ans['energy_avg'] =             np.average([np.average(data['data']['energy']) for data in datas]) if datas[0]['data']['energy'][0] != -1 else None
        ans['energy_var'] =             np.average([np.var(data['data']['energy']) for data in datas]) if datas[0]['data']['energy'][0] != -1 else None
        ans['energy_std'] =             np.average([np.std(data['data']['energy']) for data in datas]) if datas[0]['data']['energy'][0] != -1 else None
        ans['energy_mad'] =             MAD([data['data']['energy'] for data in datas]) if datas[0]['data']['energy'][0] != -1 else None
        ans['temperature_avg'] =        np.average([np.average(data['data']['temperature']) for data in datas]) if datas[0]['data']['temperature'][0] != -1 else None
        ans['temperature_var'] =        np.average([np.var(data['data']['temperature']) for data in datas]) if datas[0]['data']['temperature'][0] != -1 else None
        ans['temperature_std'] =        np.average([np.std(data['data']['temperature']) for data in datas]) if datas[0]['data']['temperature'][0] != -1 else None
        ans['temperature_mad'] =        MAD([data['data']['temperature'] for data in datas]) if datas[0]['data']['temperature'][0] != -1 else None

        return ans
    def CompareOptimizations(self, optimizations:list, intervals=None):
        #Returns a list of the best algorithm across the optimization
        #and the proportion of time each algorithm was the best at each interval
        size = optimizations[0]['data'].shape[0]
        for opt in range(1, len(optimizations)):
            if optimizations[0]['data'].shape[0] != size:
                raise Exception('all data on optimizations must be of same length')

        if intervals == None:
            intervals = [round(size/4)-1, round(size/2)-1, round(3*size/4)-1, size-1]
        else:
            if len(intervals) != len(set(intervals)):
                raise Exception(f'intervals may not have repeated entries: {intervals}')
            if not all(intervals[i] > intervals[i-1] for i in range(1, len(intervals))):
                raise Exception(f'intervals must be sorted in ascending order: {intervals}')

        exit = {}
        best_values = [self.GetIterationsToImprovement(opt) for opt in optimizations]
        bests = []
        for values in best_values:
            aux = []
            for v in values:
                aux.extend([v[0]] * v[1])
            bests.append(aux)

        best = []
        for i in range(len(bests[0])):
            aux1 = math.inf
            aux2 = None
            for ii in range(len(bests)):
                if bests[ii][i] < aux1:
                    aux1 = bests[ii][i]
                    aux2 = ii
            best.append([aux2, aux1])

        bests = [[best[0][0], best[0][1], 0]]
        pos = 0
        for i in range(1, len(best)):
            if best[i][0] == bests[pos][0] and best[i][1] == bests[pos][1]:
                bests[pos][2] = bests[pos][2] + 1
            else:
                bests.append([best[i][0], best[i][1], i])
                pos = pos + 1
        exit['history'] = bests

        aux_bests = []
        interval_pos = 0
        segment_start = 0
        for optimization, value, segment_end in bests:
            while interval_pos < len(intervals) and intervals[interval_pos] <= segment_end:
                interval = intervals[interval_pos]
                if segment_start <= interval < segment_end:
                    aux_bests.append([optimization, value, interval])
                    segment_start = interval + 1
                interval_pos += 1
            aux_bests.append([optimization, value, segment_end])
            segment_start = segment_end + 1

        exit['intervals'] = [-1] * len(intervals)
        pos = 0
        for i in range(len(intervals)):
            acc_freq = [0] * len(optimizations)
            while pos < len(aux_bests) and aux_bests[pos][2] <= intervals[i]:
                acc_freq[aux_bests[pos][0]] = acc_freq[aux_bests[pos][0]] + aux_bests[pos][2]
                if pos > 0:
                    acc_freq[aux_bests[pos][0]] = acc_freq[aux_bests[pos][0]] - aux_bests[pos-1][2]
                pos = pos + 1
            length = intervals[i]
            if i > 0:
                length = length - intervals[i-1]
            acc_freq = [acc/length for acc in acc_freq]
            exit['intervals'][i] = acc_freq
        return exit
    def GetExecutionMetrics(self, optimization, intervals):
        #Returns basic execution metrics
        size = optimization['data'].shape[0]
        for opt in range(1, len(optimization)):
            if optimization['data'].shape[0] != size:
                raise Exception('all data on optimizations must be of same length')

        if intervals == None:
            intervals = [round(size/4)-1, round(size/2)-1, round(3*size/4)-1, size-1]
        else:
            if len(intervals) != len(set(intervals)):
                raise Exception(f'intervals may not have repeated entries: {intervals}')
            if not all(intervals[i] > intervals[i-1] for i in range(1, len(intervals))):
                raise Exception(f'intervals must be sorted in ascending order: {intervals}')

        metrics = [{}] * len(intervals)
        for i in range(len(intervals)):
            end = intervals[i]
            start = intervals[i-1] if i > 0 else 0

            metrics[i] = {
                'time_total':           sum(optimization['data']['time'][start:end]) if optimization['data']['time'][0] != -1 else None,
                'time_avg':             np.average(optimization['data']['time'][start:end]) if optimization['data']['time'][0] != -1 else None,
                'time_var':             np.var(optimization['data']['time'][start:end]) if optimization['data']['time'][0] != -1 else None,
                'time_std':             np.std(optimization['data']['time'][start:end]) if optimization['data']['time'][0] != -1 else None,
                
                'memory_avg':           np.average(optimization['data']['memory']) if optimization['data']['memory'][0] != -1 else None,
                'memory_var':           np.var(optimization['data']['memory']) if optimization['data']['memory'][0] != -1 else None,
                'memory_std':           np.std(optimization['data']['memory']) if optimization['data']['memory'][0] != -1 else None,
                
                'energy_total':         sum(optimization['data']['energy']) if optimization['data']['energy'][0] != -1 else None,
                'energy_avg':           np.average(optimization['data']['energy']) if optimization['data']['energy'][0] != -1 else None,
                'energy_var':           np.var(optimization['data']['energy']) if optimization['data']['energy'][0] != -1 else None,
                'energy_std':           np.std(optimization['data']['energy']) if optimization['data']['energy'][0] != -1 else None,
                
                'temperature_avg':      np.average(optimization['data']['temperature']) if optimization['data']['temperature'][0] != -1 else None,
                'temperature_var':      np.var(optimization['data']['temperature']) if optimization['data']['temperature'][0] != -1 else None,
                'temperature_std':      np.std(optimization['data']['temperature']) if optimization['data']['temperature'][0] != -1 else None,
            }
        return metrics
    def GetWhenSolutionWasFound(self, data, value):
        for i in range(len(data['data']['value'])):
            if data['data']['value'][i] <= value:
                return i
        return None
    def GetAreaUnderCurve(self, data, ideal_value):
        values = self.GetIterationsToImprovement(data)
        area = []
        for value in values:
            area.extend([value[0]] * value[1])
        acc = 0
        for i in range(1, len(area)):
            acc = acc + (((area[i-1] + area[i])/2) - ideal_value)
        return acc
    def GetConvergenceRate(self, data, window=None):
        #Calculate the rate of convergence across a moving window
        rate = []
        values = self.GetIterationsToImprovement(data)
        best_values = []
        for value in values:
            best_values.extend([value[0]] * value[1])

        if window != None:
            i = 1
            while i*window < len(best_values):
                rate.append(abs(best_values[i * window] - best_values[(i-1) * window]))
                i = i+1
            rate.append(abs(best_values[-1] - best_values[(i-1)*window]))
            return rate
        else:
            best_value = best_values[-1]
            for i in range(len(best_values)):
                if best_values[i] != best_value:
                    rate.append(math.log(best_values[i] - best_value))
                else:
                    rate.append(None)
            return rate
    def GetMedianAbsoluteDeviation(self, opts):
        best_values = [self.BestValue(self.GetOptimization(opt)) for opt in opts]
        median = np.median(best_values)
        best_values = [abs(value-median) for value in best_values]
        return np.average(best_values)
    def GetSolutionDiversity(self, data, window):
        #Measures the differences between solutions tested by the algorithm across multiple optimizations
        #Measures differences on inputs or outputs across a moving window

        diversities = []
        pos = 0
        while pos+window <= data['data'].shape[0]:
            diversity = {}
            if pos + window > data['data'].shape[0]:
                break
            distances = []
            distances_dim = [ [] for _ in range(len(data['data']['solutions'][0]))]
            distances_out = []
            for i in range(window):
                for j in range(i+1, window):
                    distances.append(np.sqrt(sum([(data['data']['solutions'][pos+i][k] - data['data']['solutions'][pos+j][k])**2 for k in range(len(data['data']['solutions'][0]))])))
                    for k in range(len(data['data']['solutions'][0])):
                        distances_dim[k].append(abs(data['data']['solutions'][pos+i][k] - data['data']['solutions'][pos+j][k]))
                    distances_out.append(abs(data['data']['value'][pos+i] - data['data']['value'][pos+j]))
            
            diversity['in_avg'] = np.average(distances)
            diversity['in_gst'] = max(distances)
            diversity['in_std'] = np.std(distances)
            diversity['in_var'] = np.var(distances)
            diversity['in_dim_avg'] = np.average([np.average(d) for d in distances_dim])
            diversity['in_dim_avg_i'] = [np.average(d) for d in distances_dim]
            diversity['in_dim_gst'] = max([max(d) for d in distances_dim])
            diversity['in_din_gst_in'] = [max(d) for d in distances_dim]
            diversity['in_dim_std'] = np.average([np.std(d) for d in distances_dim])
            diversity['in_dim_std_in'] = [np.std(d) for d in distances_dim]
            diversity['in_dim_var'] = np.average([np.var(d) for d in distances_dim])
            diversity['in_dim_var_in'] = [np.var(d) for d in distances_dim]
            diversity['out_avg'] = np.average(distances_out)
            diversity['out_gst'] = max(distances_out)
            diversity['out_std'] = np.std(distances_out)
            diversity['out_var'] = np.var(distances_out)
            diversity['out_ran'] = max(distances_out) - min(distances_out)
            diversity['out_mad'] = MAD(distances_out)

            pos = pos + window
            diversities.append(diversity)
        return diversities
        pass
    def GetParetoSet(self, data, objectives, points):
        values = [self.GetIterationsToImprovement(d) for d in data]
        for value in values:
            value[0][1] = value[0][1] - 1
            for i in range(1, len(value)):
                value[i][1] = value[i][1] + value[i-1][1]
        
        pareto_sets = {}
        for point in points:
            algs = [[-1, -1] for d in data]
            for i in range(len(data)):
                for value in values[i]:
                    if value[1] >= point:
                        algs[i][0] = value[0]
                        break
                algs[i][1] = self.GetExecutionMetrics(data[i], [point])

            algs = self._generate_pareto_entries(algs, objectives)
            pareto_set = [[data[0]['ID'], algs[0]]]
            for alg in range(1, len(algs)):
                dominated = False
                for _, p in pareto_set:
                    if all(p[i] <= algs[alg][i] for i in range(len(objectives))) and any(p[i] < algs[alg][i] for i in range(len(objectives))):
                        dominated = True
                        break
                if not dominated:
                    pareto_set.append([data[alg]['ID'], algs[alg]])
                    pareto_set = [p for p in pareto_set if not ((all(algs[alg][i] <= p[1][i] for i in range(len(objectives)))) and any(algs[alg][i] < p[1][i] for i in range(len(objectives))))]
            pareto_sets[point] = pareto_set
        return pareto_sets  
