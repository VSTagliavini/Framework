from dataset_manager import DatasetManager, SRS


parameters = 8
def testfunction(x):
    acc = 0
    for i in range(8):
        acc = acc + i*(x[i]**i)
    return acc



generator = DatasetManager(SRS, 'laptop', testfunction, 8)

dataset_id, _ = generator.GenerateDataset(500)
print(f'id {dataset_id}')
dataset = generator.GetDataset(dataset_id)
print(dataset)
