import flask
from flask import Flask, jsonify
import models
from datasets import DatasetManager
from models.factory import ModelsFactory

app = Flask(__name__)


user_models = {}
dm = DatasetManager()
mf = ModelsFactory()


@app.route('/')
def hello_world():
    return 'Hello, world!'


@app.route('/models/types_list')
def get_models_types():
    """Returns all available model types"""
    return jsonify(data=models.__all__)


@app.route('/datasets/list')
def get_datasets():
    """Returns all available datasets"""
    return jsonify(data=dm.get_datasets())


@app.route('/models/user_models_list')
def get_users_models():
    """Returns all created models"""
    return jsonify(data=list(user_models.keys()))


def get_user(data):
    """

    :param data: request json
    :return: User_id casted to string or empty string
    """
    if data and 'user_id' in data:
        return str(data['user_id'])
    else:
        return ''


def process_json(data, model_id, action='train'):
    """
    Creates
    :param data:
    :param model_id:
    :param action:
    :return:
    """
    values = []

    if not data or ('data' not in data and 'df_name') not in data:
        # raise ValueError('There is no data in request!')
        values = dm.get_train('sample1') if action == 'train' else dm.get_test('sample1')
    elif 'data' in data:
        values = data['data']
    elif 'df_name' in data:
        values = dm.get_train(data['df_name']) if action == 'train' else dm.get_test(data['df_name'])

    user_id = get_user(data)
    print(user_id)
    pers_model_id = '_'.join([model_id, user_id])
    if pers_model_id not in user_models and action in ('train', 'test'):
        raise ModuleNotFoundError('There is no such model!')

    model = None

    if action == 'create':
        model_type = data['model_type'] if data and 'model_type' in data else 'DecisionTreeClassifier'
        params = data['params'] if data and 'params' in data else {}

        model = mf.get_model(model_type, params)

    return values, pers_model_id, model


@app.route('/models/create/<model_id>')
def create_model(model_id):
    """
    Create new model
    :param model_id: id of new model
    :return: Status of operation
    """
    data = flask.request.json
    try:
        values, pers_model_id, model = process_json(data, model_id, action='create')
    except ValueError as e:
        return jsonify(message=str(e)), 401
    except ModuleNotFoundError as e:
        return jsonify(message=str(e)), 404

    user_models[pers_model_id] = model
    return jsonify(message='OK'), 200


@app.route('/models/delete/<model_id>')
def delete_model(model_id):
    """
    Delete model
    :param model_id: id of model
    :return: Status of operation
    """
    data = flask.request.json
    user_id = get_user(data)

    pers_model_id = '_'.join([model_id, user_id])
    if pers_model_id in user_models:
        del user_models[pers_model_id]

    return jsonify(message='OK'), 200


@app.route('/datasets/load/<df_name>')
def load_dataset(df_name):
    """
    Create new dataset
    :param df_name: name of dataset
    :return: Status of operation
    """
    try:
        data = flask.request.json
        if not data or 'data' not in data or len(data['data']) != 3:
            raise ValueError('data field should contain X_train, y_train and X_test arrays')
        dm.add_dataset(df_name, *data['data'])
    except ValueError as e:
        return jsonify(message=str(e)), 401
    except ModuleNotFoundError as e:
        return jsonify(message=str(e)), 404

    return jsonify(message='OK'), 200


@app.route('/models/train/<model_id>')
def train_model(model_id):
    """
    Fit model with parameters
    :param model_id: model_name
    :return: Status of operation
    """
    data = flask.request.json
    try:
        values, pers_model_id, _ = process_json(data, model_id, action='train')
        user_models[pers_model_id].fit(*values)
    except ValueError as e:
        return jsonify(message=str(e)), 401
    except ModuleNotFoundError as e:
        return jsonify(message=str(e)), 404

    return jsonify(message='OK'), 200


@app.route('/models/predict/<model_id>')
def get_predict(model_id):
    """
    Predict
    :param model_id:
    :return: Status and predicts
    """
    data = flask.request.json
    try:
        values, pers_model_id, _ = process_json(data, model_id, action='test')
        model = user_models[pers_model_id]
        predicts = list(map(int, model.predict(values)))
    except ValueError as e:
        return jsonify(message=str(e)), 401
    except ModuleNotFoundError as e:
        return jsonify(message=str(e)), 404

    return jsonify(message='OK',
                   values=predicts), 200


if __name__ == '__main__':
    app.run()
