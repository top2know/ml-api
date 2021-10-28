from sklearn.datasets import make_classification


class DatasetManager:

    def __init__(self):
        self.datasets = {}
        self.add_dataset('sample1', *self._get_random_dataset(), self._get_random_dataset()[0])
        self.add_dataset('sample2', *self._get_random_dataset(), self._get_random_dataset()[0])

    @staticmethod
    def _get_random_dataset():
        return make_classification(n_classes=2, n_features=10, n_samples=10000)

    def add_dataset(self, name, X_train, y_train, X_test):
        self.datasets[name] = {
            'X_train': X_train,
            'y_train': y_train,
            'X_test': X_test
        }

    def _validate_name(self, name):
        if name not in self.datasets:
            raise ValueError(f'There is no dataset "{name}"!')

    def get_datasets(self):
        return list(self.datasets.keys())

    def get_train(self, name):
        self._validate_name(name)

        df = self.datasets[name]
        return df['X_train'], df['y_train']

    def get_test(self, name):
        self._validate_name(name)

        df = self.datasets[name]
        return df['X_test']
