import flask
from flask import Flask, jsonify, redirect
from datasets import DatasetManager
from flasgger import Swagger
import requests

app = Flask(__name__)
swagger = Swagger(app)

models_host = 'http://host.docker.internal:5001'

# mm = ModelsManager()
dm = DatasetManager()
# mf = ModelsFactory()


@app.route('/')
def hello_world():
    return redirect('/apidocs')


@app.route('/models/types_list')
def get_models_types():
    """Returns list of available types of models
    ---
    responses:
      200:
        description: A list of model types
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: string
              example: ['DecisionTreeClassifier', 'GradientBoostingClassifier']
    """
    return jsonify(data=['DecisionTreeClassifier', 'GradientBoostingClassifier'])


@app.route('/datasets/list')
def get_datasets():
    """Returns list of available datasets
    ---
    responses:
      200:
        description: A list of datasets
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: string
              example: ['sample1', 'sample2']
    """
    return jsonify(data=dm.get_datasets())


@app.route('/models/models_list')
def get_users_models():
    """Returns list of available models
    ---
    parameters:
      - name: user_id
        in: query
        type: string
        required: false
    responses:
      200:
        description: A list of models
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: string
              example: ['model1', 'model2']
    """
    user = get_user(flask.request)
    try:
        response = requests.get(f'{models_host}/get_models', params={
            'user': user
        })
    except Exception:
        return jsonify(message='Model API didn\'t respond'), 400
    return response.json(), response.status_code


def get_user(req_data):
    """
    Get user from json data or from query parameter
    :param req_data: request
    :return: user_id
    """
    if req_data.json and 'user_id' in req_data.json:
        return str(req_data.json['user_id'])
    else:
        return req_data.args.get('user_id', default='')


def process_json(req_data, model_id, action='train'):
    """
    Preprocess input data
    :param req_data: request
    :param model_id: id of model
    :param action: desirable action
    :return: df, personal model_id and model
    """
    values = []
    data = req_data.json
    if action != 'create':
        df_name_from_args = req_data.args.get('df_name', None)
        if (not data or ('data' not in data and 'df_name' not in data)) and not df_name_from_args:
            raise ValueError('There is no data or df_name in request!')
            # values = dm.get_train('sample1') if action == 'train' else dm.get_test('sample1')
        elif data and 'data' in data:
            values = data['data']
        elif (data and 'df_name' in data) or df_name_from_args:
            df_name = data['df_name'] if (data and 'df_name' in data) else df_name_from_args
            values = dm.get_train(df_name) if action == 'train' else dm.get_test(df_name)

    user_id = get_user(req_data)
    pers_model_id = '_'.join([user_id, model_id])
    if pers_model_id not in requests.get(f'{models_host}/get_models').json()['data'] and action in ('train', 'test'):
        raise ModuleNotFoundError('There is no such model!')

    model_type = None
    params = None

    if action == 'create':
        model_type = data['model_type'] if data and 'model_type' in data else 'DecisionTreeClassifier'
        params = data['params'] if data and 'params' in data else {}

    return values, pers_model_id, [model_type, params]


@app.route('/models/create/<model_id>', methods=['POST'])
def create_model(model_id):
    """Creates new model
    ---
    parameters:
      - name: model_id
        in: path
        type: string
        required: true
      - name: data
        in: body
        type: object
        required: false
        schema:
          type: object
          properties:
            model_type:
              type: string
              example: DecisionTreeClassifier
            params:
              type: object
              properties:
                model_parameter:
                  type: string
              example: {max_depth: 3}
            user_id:
              type: string
              example: 123456
    responses:
      200:
        description: Status of successful operation
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'OK'
      400:
        description: Some input data was bad
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'There is no support of model SomeModel yet!'
    """
    data = flask.request
    try:
        values, pers_model_id, model = process_json(data, model_id, action='create')
        response = requests.post(f'{models_host}/create', json={
            'model_name': pers_model_id,
            'model_type': model[0],
            'params': model[1]
        })
    except ValueError as e:
        return jsonify(message=str(e)), 400
    except Exception:
        return jsonify(message='Model API didn\'t respond'), 400
    return response.json(), response.status_code


@app.route('/models/delete/<model_id>', methods=['DELETE'])
def delete_model(model_id):
    """Deletes model if it exists
    ---
    parameters:
      - name: model_id
        in: path
        type: string
        required: true
      - name: data
        in: body
        type: object
        required: false
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: 123456
    responses:
      200:
        description: Status of successful operation
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'OK'
    """
    data = flask.request
    user_id = get_user(data)

    pers_model_id = '_'.join([user_id, model_id])
    try:
        response = requests.get(f'{models_host}/delete', params={
            'name': pers_model_id
        })
    except Exception:
        return jsonify(message='Model API didn\'t respond'), 400
    return response.json(), response.status_code


@app.route('/datasets/load/<df_name>', methods=['POST'])
def load_dataset(df_name):
    """Load new dataset
    ---
    parameters:
      - name: df_name
        in: path
        type: string
        required: true
        description: Name of dataset
      - name: data
        in: body
        type: object
        required: false
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: 123456
            data:
              type: object
              properties:
                X_train:
                  type: array
                  items:
                    type: array
                    items:
                      type: number
                  example: [[0, 0], [0, 1], [1, 0]]
                y_train:
                  type: array
                  items:
                    type: number
                  example: [1, 0, 1]
                X_test:
                  type: array
                  items:
                    type: array
                    items:
                      type: number
                  example: [[1, 1]]
    responses:
      200:
        description: Status of successful operation
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'OK'
      400:
        description: Some input data was bad
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'There is no support of model SomeModel yet!'
    """
    try:
        data = flask.request.json
        if not data or 'data' not in data or len(data['data']) != 3 \
                or 'X_train' not in data['data']\
                or 'y_train' not in data['data']\
                or 'X_test' not in data['data']:
            raise ValueError('data field should contain X_train, y_train and X_test arrays')
        dm.add_dataset(df_name, **data['data'])
    except ValueError as e:
        return jsonify(message=str(e)), 400

    return jsonify(message='OK'), 200


@app.route('/models/train/<model_id>', methods=['PUT'])
def train_model(model_id):
    """Train model
    ---
    parameters:
      - name: model_id
        in: path
        type: string
        required: true
      - name: data
        in: body
        type: object
        required: false
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: 123456
            df_name:
              type: string
              example: sample1
    responses:
      200:
        description: Status of successful operation
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'OK'
      400:
        description: Train process failed
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'There is no data or df_name in request!'
      404:
        description: Model not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'There is no such model!'
    """
    data = flask.request
    try:
        values, pers_model_id, _ = process_json(data, model_id, action='train')
        response = requests.put(f'{models_host}/train', json={
            'name': pers_model_id,
            'values': values
        })
        return response.json(), response.status_code
    except ValueError as e:
        return jsonify(message=str(e)), 400
    except ModuleNotFoundError as e:
        return jsonify(message=str(e)), 404
    except Exception:
        return jsonify(message='Model API didn\'t respond'), 400


@app.route('/models/predict/<model_id>')
def get_predict(model_id):
    """Get predicts
    ---
    parameters:
      - name: model_id
        in: path
        type: string
        required: true
      - name: user_id
        in: query
        type: string
        required: false
      - name: df_name
        in: query
        type: string
        required: false
    responses:
      200:
        description: Status of successful operation
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'OK'
            features:
              type: array
              items:
                type: array
                items:
                  type: number
              example: [[0, 0], [0, 1], [1, 0]]
              description: objects to predict
            targets:
              type: array
              items:
                type: number
              example: [1, 0, 1]
              description: Model's predicts
      400:
        description: Predict process failed
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'There is no data or df_name in request!'
      404:
        description: Model not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: 'There is no such model!'
    """
    data = flask.request
    try:
        values, pers_model_id, _ = process_json(data, model_id, action='test')
        response = requests.put(f'{models_host}/predict', json={
            'name': pers_model_id,
            'values': values
        })
        return response.json(), response.status_code
    except ValueError as e:
        return jsonify(message=str(e)), 400
    except ModuleNotFoundError as e:
        return jsonify(message=str(e)), 404
    except Exception:
        return jsonify(message='Model API didn\'t respond'), 400


if __name__ == '__main__':
    app.run()
