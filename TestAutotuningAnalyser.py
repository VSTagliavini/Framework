import AutotuningAnalyser

aux = AutotuningAnalyser.Analyser()

for alg in ['GeneticAlgorithm', 'DifferentialEvolution', 'ParticleSwarm', 'SimulatedAnnealing', 'BasinHopping', 'NelderMead']:
    opts = aux.ListOptimizations('testfunction', autotuning=alg)
    print(opts)

    if alg == 'GeneticAlgorithm':
        datas = []
        for opt in opts:
            datas.append(aux.GetOptimization(opt))
        print(aux.GetSolutionDiversity(datas[0], 50))