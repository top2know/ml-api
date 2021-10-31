import pickle
from os import listdir
import os

PATH = 'storage/models'


class ModelsManager:

    @staticmethod
    def add_model(name, model):
        with open(f'{PATH}/{name}.pickle', 'wb') as f:
            pickle.dump(model, f)

    def get_model(self, name):
        self._validate_name(name)
        with open(f'{PATH}/{name}.pickle', 'rb') as f:
            return pickle.load(f)

    def delete_model(self, name):
        if name in self.get_models():
            os.remove(f'{PATH}/{name}.pickle')

    def _validate_name(self, name):
        if name not in self.get_models():
            raise ValueError(f'There is no dataset "{name}"!')

    @staticmethod
    def get_models():
        models = filter(lambda x: x.endswith('.pickle'), listdir(PATH))
        return list(map(lambda x: x.replace('.pickle', ''), models))

    @staticmethod
    def get_models_for_user(name):
        by_user = filter(lambda x: x.startswith(name + '_'), listdir(PATH))
        return list(map(lambda x: x.replace('.pickle', '').replace(name + '_', ''), by_user))
