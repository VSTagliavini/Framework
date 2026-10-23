import autotuning_analyser

aux = autotuning_analyser.AutotuningAnalyser()

datas = []
for alg in ['GeneticAlgorithm', 'DifferentialEvolution', 'ParticleSwarm', 'SimulatedAnnealing', 'BasinHopping', 'NelderMead']:
    opts = aux.ListOptimizations('testfunction', autotuning=alg)
    print(opts)

    if alg == 'GeneticAlgorithm':
        for opt in opts:
            data = aux.GetOptimization(opt)
            datas.append(data)
            print(f'Converged in 40 iterations? {aux.CheckConvergence(opt, i=40)}')
            print(f'Best solutions {aux.GetIterationsToImprovement(opt)}')
#        diversities = aux.GetSolutionDiversity(opts[0], 50)
#        for diversity in diversities:
#            print('diversity')
#            for a in diversity:
#                print(f'   {a}: {diversity[a]}')
        print(opts)
#        print(f'Optimization stability\n{aux.GetOptimizationStability(opts, conv_i=10)}')
        par_set = aux.GetParetoSet(opts, {'value': 'smaller', 'time_total': 'smaller'}, [99, 199, 299, 399, 499])
        for p in par_set:
            print(f'{p}: {par_set[p]}')
