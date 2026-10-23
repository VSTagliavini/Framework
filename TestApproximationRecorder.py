from approximation_recorder import Approximator, ApproximatorRecorder
from dataset_manager import DatasetManager, SRS, LHS

from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

class DT(Approximator):
    def __init__(self):
        pass
    def Initialization(self):
        self.tree = DecisionTreeRegressor()
    def Train(self, input, output):
        self.tree.fit(input, output)
    def Approximate(self, x):
        return self.tree.predict(x.reshape(1, -1))[0]

class SupportVR(Approximator):
    def __init__(self):
        pass
    def Initialization(self):
        self.svr = make_pipeline(StandardScaler(), SVR())
    def Train(self, input, output):
        self.svr.fit(input, output)
    def Approximate(self, x):
        return self.svr.predict(x.reshape(1, -1))[0]



parameters = 8
def testfunction(x):
    acc = 0
    for i in range(8):
        acc = acc + i*(x[i]**i)
    return acc

generator = DatasetManager(SRS, 'laptop', testfunction, 8)
training_dataset_id, _ = generator.GenerateDataset(500)
training_dataset = generator.GetDataset(training_dataset_id)

generator = DatasetManager(LHS, 'laptop', testfunction, 8)
testing_dataset_id, _ = generator.GenerateDataset(250)
testing_dataset = generator.GetDataset(testing_dataset_id)

app = DT()
app.SetName('DT')
rec = ApproximatorRecorder('laptop', testfunction, parameters, measure_approximation_history=True, measure_flops=True, measure_time=True, measure_memory=True, measure_energy=True, measure_temperature=True)
rec.SetApproximationAlgorithm(app)

rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)

#####

def testfunction2(x):
    acc = 0
    for i in range(8):
        acc = acc + i*(x[i]**i)
    return acc

generator = DatasetManager(SRS, 'laptop', testfunction2, 8)
training_dataset_id, _ = generator.GenerateDataset(500)
training_dataset = generator.GetDataset(training_dataset_id)

generator = DatasetManager(LHS, 'laptop', testfunction2, 8)
testing_dataset_id, _ = generator.GenerateDataset(250)
testing_dataset = generator.GetDataset(testing_dataset_id)

app = SupportVR()
app.SetName('SVR')
rec = ApproximatorRecorder('laptop', testfunction2, parameters, measure_approximation_history=True, measure_flops=True, measure_time=True, measure_memory=True, measure_energy=True, measure_temperature=True)
rec.SetApproximationAlgorithm(app)

rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
rec.Train(training_dataset_id)
rec.Test(testing_dataset_id)
