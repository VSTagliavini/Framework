from approximation_analyser import ApproximationAnalyser

analyser = ApproximationAnalyser()
approxs = analyser.ListApproximations('testfunction', approximation='DT')

for approx in approxs:
    print(approx)
    print(f'RMSE                    {analyser.RMSE(approx)}')
    print(f'GAE                     {analyser.GAE(approx)}')
    print(f'COVARIANCE              {analyser.Covariance(approx)}')
    print(f'PEARSON CORRELATION     {analyser.PearsonCorrelation(approx)}')
    print(f'Training Resources {analyser.GetTrainingResources(approx)}')
    
    print(f'Approximation Resources {analyser.GetApproximationResources(approx)}')

print(f'Approximation Stability {analyser.GetApproximationStability(approxs)}')
print(f'Resource Stability {analyser.GetResourceStability(approxs)}')
print(f'Training Pareto {analyser.GetTrainingPareto(approxs)}')
print(f'Approximation Pareto {analyser.GetApproximationPareto(approxs, 'total')}')
