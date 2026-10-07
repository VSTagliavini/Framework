import random
import numpy as np
import time
import math

from optimization_recorder import Optimizer, Recorder

def roulette(population, reproductors):
        breeders = []
        total = sum(individual['fitness'] for individual in population)
        individuals_probabilities = [individual['fitness']/total for individual in population]

        for individual in range(reproductors):
            chosen = np.random.choice(len(population), p=individuals_probabilities)
            breeders.append(population[chosen])

        return breeders
def roulette_exlusive(population, reproductors):
    breeders = []
    auxiliary_population = population

    for individual in range(reproductors):
        total = sum(individual['fitness'] for individual in auxiliary_population)
        individuals_probabilities = [individual['fitness']/total for individual in auxiliary_population]
        chosen = np.random.choice(len(auxiliary_population), p=individuals_probabilities)
        breeders.append(auxiliary_population[chosen])
        auxiliary_population.pop(chosen)
    
    return breeders
def tournament(population, reproductors):
    breeders = []
    bracket = 3
    for individual in range(reproductors):
        tournament = random.sample(population, bracket)
        winner = max(tournament, key=lambda x: x['fitness'])
        breeders.append(winner)
    return breeders
selection_algorithms = {
    'roulette': roulette,
    'roulette_exclusive': roulette_exlusive,
    'tournament': tournament,
}
def one_point(parent1, parent2, rate):
    if np.random.uniform(0, 1) > rate:
        return parent1, parent2
    
    crossover_point = random.choice(range(len(parent1['genes'])))
    child1 = {
        'genes': parent1['genes'][0:crossover_point] + parent2['genes'][crossover_point:],
        'fitness': -999999
    }
    child2 = {
        'genes': parent2['genes'][0:crossover_point] + parent1['genes'][crossover_point:],
        'fitness': -999999
    }
    return child1, child2
def two_points(parent1, parent2, rate):
    if np.random.uniform(0, 1) > rate:
        return parent1, parent2
    
    crossover_point1 = random.choice(range(len(parent1['genes'])-2)) + 1
    crossover_point2 = random.choice(range(crossover_point1+1, len(parent1['genes'])))
    child1 = {
        'genes': parent1['genes'][0:crossover_point1] + parent2['genes'][crossover_point1:crossover_point2] + parent1['genes'][crossover_point2:],
        'fitness': -999999
    }
    child2 = {
        'genes': parent2['genes'][0:crossover_point1] + parent1['genes'][crossover_point1:crossover_point2] + parent2['genes'][crossover_point2:],
        'fitness': -999999
    }
    return child1, child2
crossover_algorithms = {
    'one_point': one_point,
    'two_points': two_points
}

class GA(Optimizer):
    def __init__(self, population_size, reproductors, crossover_rate, mutation_rate, selection_criteria, crossover_algorithm):
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.reproductors = reproductors
        self.selection_criteria = selection_criteria
        self.crossover_algorithm = crossover_algorithm
    
        self.best_individual = {
            'genes': None,
            'fitness': -999999
        }
                    
    def _generation_creation(self):
        return selection_algorithms[self.selection_criteria](self.population, self.reproductors)
        
    def _crossover(self, parent1, parent2, crossover_rate):
        return crossover_algorithms[self.crossover_algorithm](parent1, parent2, crossover_rate)
    
    def _mutation(self, individual, mutation_rate):
        if np.random.uniform(0, 1) > mutation_rate:
            return individual
        mutation_point = random.choice(range(len(individual['genes'])))
        individual['genes'][mutation_point] = np.random.uniform(0, 1)
        return individual

    def Optimize(self):
        for individual in self.population:
            individual['fitness'] = -1 * self.fitness_function(individual['genes'])
    
        fitness = [individual['fitness'] for individual in self.population]
        generation_best = fitness.index(max(fitness))
        if generation_best > self.best_individual['fitness']:
            self.best_individual = self.population[generation_best]
                    
        parents = self._generation_creation()
        random.shuffle(parents)
        i = 0
    
        new_population = []
        while len(new_population) < self.population_size:
            child1, child2 = self._crossover(parents[i], parents[i+1], self.crossover_rate)
            new_population.append(child1)
            new_population.append(child2)
    
        while len(new_population) > self.population_size:
            new_population.pop(-1)
    
        new_population = [self._mutation(individual, self.mutation_rate) for individual in new_population]
        self.population = new_population

    def SetObjectiveFunction(self, func, params):
        self.fitness_function = func
        self.gene_size = params

    def Initialization(self):
        self.population = []
        for _ in range(self.population_size):
            individual = {'genes': [], 'fitness': -999999}
            for _ in range(self.gene_size):
                individual['genes'].append(random.uniform(0, 1))
            self.population.append(individual)

def standard_selection(population, individual):
    available = population.copy()
    available.remove(individual)
    a, b, c = random.sample(available, 3)
    return a, b, c
selection_functions = {
    'standard': standard_selection
}
def standard_mutation(individual, individuals, mutation_chance, mutation_rate):
    mutated = {'genes': [-1]*len(individual['genes']), 'fitness': -999999}

    for gene in range(len(mutated['genes'])):
        if np.random.uniform(0, 1) > mutation_rate:
            mutated_gene = individuals[0]['genes'][gene] + mutation_rate*(individuals[1]['genes'][gene] - individuals[2]['genes'][gene])
            mutated_gene = max(mutated_gene, 0)
            mutated_gene = min(mutated_gene, 1)
            mutated['genes'][gene] = mutated_gene
        else:
            mutated['genes'][gene] = individual['genes'][gene]
    return mutated
mutation_functions = {
    'standard': standard_mutation
}

class DE(Optimizer):
    def __init__(self, population_size, crossover_rate, mutation_chance, mutation_rate, selection_criteria, mutation_function):
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_chance = mutation_chance
        self.mutation_rate = mutation_rate
        self.selection_criteria = selection_criteria
        self.mutation_function = mutation_function

        self.best_individual = {
            'genes': None,
            'fitness': -math.inf
        }

    def _selectvectors(self, population, individual):
        a, b, c = selection_functions[self.selection_criteria](population, individual)
        return a, b, c
    
    def _mutation(self, individual, individuals, mutation_chance, mutation_rate):
        mutated = mutation_functions[self.mutation_function](individual, individuals, mutation_chance, mutation_rate)
        return mutated

    def Optimize(self):
        new_population = []
        for individual in self.population:
            a, b, c = self._selectvectors(self.population, individual)
            mutated_individual = self._mutation(individual, [a, b, c], self.mutation_chance, self.mutation_rate)
            mutated_individual['fitness'] = -1 * self.fitness_function(mutated_individual['genes'])
            if mutated_individual['fitness'] > self.best_individual['fitness']:
                self.best_individual = mutated_individual
            if mutated_individual['fitness'] > individual['fitness']:
                new_population.append(mutated_individual)
            else:
                new_population.append(individual)
        self.population = new_population


    def SetObjectiveFunction(self, func, params):
        self.fitness_function = func
        self.gene_size = params

    def Initialization(self):
        self.population = []
        for _ in range(self.population_size):
            individual = {'genes': [], 'fitness': -999999}
            for _ in range(self.gene_size):
                individual['genes'].append(random.uniform(0, 1))
            self.population.append(individual)
        for individual in self.population:
            individual['fitness'] = -1 * self.fitness_function(individual['genes'])
            if individual['fitness'] > self.best_individual['fitness']:
                self.best_individual = individual

class PS(Optimizer):
    def __init__(self, population_size, c1, c2, w):
        self.population_size = population_size
        self.c1 = c1
        self.c2 = c2
        self.inertia = w
    
    def Optimize(self):
        for particle in self.population:
            particle['fitness'] = - self.function(particle['position'])
            if particle['fitness'] > particle['personal_best_fitness']:
                particle['personal_best_fitness'] = particle['fitness']
                particle['personal_best_position'] = particle['position']
            new_velocity = self.inertia * particle['velocity']
            new_velocity = new_velocity + self.c1 * np.random.uniform(0, 1) * (particle['personal_best_position'] - particle['position'])
            new_velocity = new_velocity + self.c2 * np.random.uniform(0, 1) * (self.best_individual['position'] - particle['position'])
            particle['velocity'] = new_velocity
            particle['position'] = particle['position'] + new_velocity
            for i in range(self.num_parameters):
                    particle['position'][i] = max(particle['position'][i], 0)
                    particle['position'][i] = min(particle['position'][i], 1)
        for particle in self.population:
            if particle['fitness'] > self.best_individual['fitness']:
                self.best_individual = particle
    
    def SetObjectiveFunction(self, func, params):
        self.function = func
        self.num_parameters = params

    def Initialization(self):
        self.population = []
        self.best_individual = {
            'fitness': - math.inf
        }

        for _ in range(self.population_size):
            parameters = [np.random.uniform(0, 1) for _ in range(self.num_parameters)]
            parameters = np.array(parameters)
            velocity = [np.random.uniform(0, 1) for _ in range(self.num_parameters)]
            velocity = np.array(velocity)
            particle = {
                'position': parameters,
                'fitness': - math.inf,
                'personal_best_fitness': - math.inf,
                'personal_best_position': parameters,
                'velocity': velocity
            }
            self.population.append(particle)

        self.best_individual = self.population[random.randint(0, self.population_size-1)]
        
class SA(Optimizer):
    def __init__(self, starting_temperature=100, cooling_rate=1, reset_temperature=True):
        self.default_temp = starting_temperature
        self.default_cool = cooling_rate
        self.default_reset = reset_temperature
        
    def Optimize(self):
        candidate = self.solution + np.random.uniform(-0.1, 0.1, self.num_parameters)
            
        for i in range(self.num_parameters):
            candidate[i] = max(candidate[i], 0)
            candidate[i] = min(candidate[i], 1)
            
        candidate_performance = self.function(candidate)

        if candidate_performance <= self.solution_performance:
            self.solution = candidate
            self.solution_performance = candidate_performance

            self.temperature = max(self.temperature - self.cooling_rate, 0)
            if self.reset_temperature and self.temperature == 0:
                self.temperature = self.starting_temperature
        else:
            probability = np.exp((self.solution_performance - candidate_performance)/(self.temperature+1e-6))
            if np.random.uniform(0, 1) < probability:
                self.solution = candidate
                self.solution_performance = candidate_performance
        self.temperature = max(self.temperature - self.cooling_rate, 0)
        if self.reset_temperature and self.temperature == 0:
            self.temperature = self.starting_temperature

    def SetObjectiveFunction(self, func, params):
        self.function = func
        self.num_parameters = params

    def Initialization(self):
        self.starting_temperature = self.default_temp
        self.cooling_rate = self.default_cool
        self.reset_temperature = self.default_reset

        self.solution = np.random.uniform(0, 1, self.num_parameters)
        self.solution_performance = self.function(self.solution)
        self.temperature = self.starting_temperature

class BH(Optimizer):
    def __init__(self, local_optimization_steps=50, temperature=0.9, learning_rate=0.01):
        self.local_optimization_steps = local_optimization_steps
        self.default_temp = temperature
        self.learning_rate = learning_rate        

    def _sgd(self, num_iterations):
        local_position = self.solution
        local_position_performance = self.solution_performance

        for iteration in range(num_iterations):
            local_position = local_position - self.learning_rate * local_position_performance
            for i in range(self.num_parameters):
                local_position[i] = max(local_position[i], 0)
                local_position[i] = min(local_position[i], 1)

            local_position_performance = self.function(local_position)

        return local_position_performance, local_position

    def _acceptance(self, new, old):
        alpha = new/old
        return self.starting_temperature > alpha

    def Optimize(self):
        local_position = self.solution + 0.5*np.random.uniform(-1, 1, self.num_parameters)
        for i in range(self.num_parameters):
            local_position[i] = max(local_position[i], 0)
            local_position[i] = min(local_position[i], 1)
        local_position_performance, local_position = self._sgd(self.local_optimization_steps)
        if self._acceptance(local_position_performance, self.solution_performance):
            self.solution = local_position
            self.solution_performance = local_position_performance   

    def SetObjectiveFunction(self, func, params):
        self.function = func
        self.num_parameters = params

    def Initialization(self):
        self.starting_temperature = self.default_temp

        self.solution = np.random.uniform(0, 1, self.num_parameters)
        self.solution_performance = self.function(self.solution)

class NM(Optimizer):
    def __init__(self, function, num_parameters, reflection=1, expansion=2, contraction=0.5, shrinkage=0.5):
        self.reflection = reflection
        self.expansion = expansion
        self.contraction = contraction
        self.shrinkage = shrinkage

    def SetObjectiveFunction(self, func, params):
        self.function = func
        self.num_parameters = params

    def Initialization(self):
        self.vertices = []
        for i in range(self.num_parameters+1):
            parameters = np.random.rand(self.num_parameters)
            self.vertices.append({
                'parameters': parameters,
                'value': self.function(parameters)
            })

    def OrderingKey(self, x):
        return x['value']

    def _clip(self, parameters):
        for i in range(len(parameters)):
            parameters[i] = max(parameters[i], 0)
            parameters[i] = min(parameters[i], 0)
        return parameters

    def _calculatecentroid(self):
        vertices = [vertice['parameters'] for vertice in self.vertices[0:self.num_parameters]]
        sums = [0] * self.num_parameters
        for i in range(self.num_parameters):
            for j in range(self.num_parameters):
                sums[i] = sums[i] + vertices[j][i]
        centroid = [sum/self.num_parameters for sum in sums]
        return centroid

    def Optimize(self):
        for _ in range(1):
            self.vertices.sort(key=self.OrderingKey)
            centroid = np.array(self._calculatecentroid())

            reflected = self._clip(centroid + self.reflection * (centroid - self.vertices[-1]['parameters']))
            reflected_performance = self.function(reflected)

            if (reflected_performance >= self.vertices[0]['value']) and (reflected_performance < self.vertices[self.num_parameters-1]['value']):
                self.vertices[-1]['parameters'] = reflected
                self.vertices[-1]['value'] = reflected_performance
                continue
            if reflected_performance < self.vertices[0]['value']:
                expanded = self._clip(centroid  + self.expansion * (reflected - centroid))
                expanded_performance = self.function(expanded)
                if expanded_performance < reflected_performance:
                    self.vertices[-1]['parameters'] = expanded
                    self.vertices[-1]['value'] = expanded_performance
                    continue
                else:
                    self.vertices[-1]['parameters'] = reflected
                    self.vertices[-1]['value'] = reflected_performance
                    continue
            if reflected_performance >= self.vertices[self.num_parameters-1]['value'] and reflected_performance < self.vertices[-1]['value']:
                contracted = self._clip(centroid + self.contraction * (reflected - centroid))
                contracted_performance = self.function(contracted)
                if contracted_performance < reflected_performance:
                    self.vertices[-1]['parameters'] = contracted
                    self.vertices[-1]['value'] = contracted_performance
                    continue
                else:
                    for i in range(1, self.num_parameters+1):
                        self.vertices[i]['parameters'] = self._clip(self.vertices[0]['parameters'] + self.shrinkage * (self.vertices[i]['parameters'] - self.vertices[0]['parameters']))
                        self.vertices[i]['value'] = self.function(self.vertices[i]['parameters'])
                        continue
                    
            if reflected_performance >= self.vertices[-1]['value']:
                contracted = self._clip(centroid + self.contraction * (self.vertices[-1]['parameters'] - centroid))
                contracted_performance = self.function(contracted)
                if contracted_performance < self.vertices[-1]['value']:
                    self.vertices[-1]['parameters'] = contracted
                    self.vertices[-1]['value'] = contracted_performance
                    continue
                else:
                    for i in range(1, self.num_parameters+1):
                        self.vertices[i]['parameters'] = self._clip(self.vertices[0]['parameters'] + self.shrinkage * (self.vertices[i]['parameters'] - self.vertices[0]['parameters']))
                        self.vertices[i]['value'] = self.function(self.vertices[i]['parameters'])
                        continue
    




def testfunction(x):
    acc = 0
    for i in range(len(x)):
        acc = acc + i * (x[i]**i)
    #time.sleep(x[7]*1e-1)
    return acc

ga = GA(50, 30, 0.75, 0.25, 'tournament', 'two_points',)
ga.SetName('GeneticAlgorithm')
de = DE(50, 0.5, 0.5, 0.5, 'standard', 'standard')
de.SetName('DifferentialEvolution')
ps = PS(50, 0.5, 0.5, 0.5)
ps.SetName('ParticleSwarm')
sa = SA(500, 5, False)
sa.SetName('SimulatedAnnealing')
bh = BH(50, 0.9, 0.01)
bh.SetName('BasinHopping')
nm = NM(1, 2, 0.5, 0.5)
nm.SetName('NelderMead')

autotuning_algorithms = [de, ps, sa, bh, nm]#[ga, de, ps, sa, bh, nm]

recorder = Recorder('Laptop', testfunction, 8, measure_optimizing_history=True, measure_time=True, measure_memory=True, measure_energy=True, measure_temperature=True, database=None)
for algorithm in autotuning_algorithms:
    recorder.SetAutotuningAlgorithm(algorithm)
    recorder.Optimize(500, 'executions', 22)

