import pickle
import os
import psycopg2
import time
from flask import jsonify

PATH = 'storage/models'


class ModelsManager:

    def __init__(self):
        time.sleep(5)
        self.conn = psycopg2.connect(
            dbname='my_server',
            user='toptun',
            password='password',
            host='host.docker.internal',
            port=5432)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""DROP TABLE IF EXISTS user_models;
CREATE TABLE user_models(
        user_id TEXT,
        model_id TEXT,
        path TEXT NOT NULL,
        model_type TEXT NOT NULL,
        params TEXT NOT NULL,
        PRIMARY KEY (user_id, model_id)
);""")

    @staticmethod
    def split_name(name):
        split_index = name.index('_')
        return name[:split_index], name[split_index + 1:]

    def add_model(self, name, model, model_type=None, params=None):
        user, model_name = self.split_name(name)
        path = f'{PATH}/{name}.pickle'
        with open(path, 'wb') as f:
            pickle.dump(model, f)

        if model_type is not None:
            params_str = str(params).replace("'", '"')
            if name not in self.get_models():
                self.cursor.execute(
                    f"INSERT INTO user_models (user_id, model_id, path, model_type, params) "
                    f"VALUES ('{user}', '{model_name}', '{path}', '{model_type}', '{params_str}');")
            else:
                self.cursor.execute(
                    f"UPDATE user_models "
                    f"SET model_type = '{model_type}', params = '{params_str}' "
                    f"WHERE user_id = '{user}' AND model_id = '{model_name}';")

    def get_path(self, name):
        user, model = self.split_name(name)
        self.cursor.execute(
            f"SELECT path FROM user_models "
            f"WHERE user_id = '{user}' AND model_id = '{model}';")
        path = self.cursor.fetchone()[0]
        return path

    def get_model(self, name):
        self._validate_name(name)
        path = self.get_path(name)
        with open(path, 'rb') as f:
            return pickle.load(f)

    def delete_model(self, name):
        if name in self.get_models():
            user, model = self.split_name(name)
            path = self.get_path(name)
            self.cursor.execute(
                f"DELETE FROM user_models "
                f"WHERE user_id = '{user}' AND model_id = '{model}';")
            os.remove(path)

    def _validate_name(self, name):
        if name not in self.get_models():
            raise ValueError(f'There is no dataset "{name}"!')

    def get_models(self):
        self.cursor.execute(
            'SELECT user_id, model_id FROM user_models;')
        results = self.cursor.fetchall()
        return list(map(lambda x: '_'.join(x), results))
        # models = filter(lambda x: x.endswith('.pickle'), listdir(PATH))
        # return list(map(lambda x: x.replace('.pickle', ''), models))

    def get_models_for_user(self, name):
        self.cursor.execute(
            'SELECT model_id, path FROM user_models WHERE user_id = \'%s\';' % name)
        results = self.cursor.fetchall()
        return list(map(lambda x: x[0], results))
        # by_user = filter(lambda x: x.startswith(name + '_'), listdir(PATH))
        # return list(map(lambda x: x.replace('.pickle', '').replace(name + '_', ''), by_user))
