import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, ConversationHandler
import configparser
import requests
import pandas as pd

CREATE_ASK_NAME, CREATE_ASK_MODEL_TYPE, CREATE_ASK_PARAMS = range(3)
LOAD_DATASET_ASK_NAME, LOAD_DATASET_ASK_TARGET, LOAD_DATASET_LOAD_TRAIN, LOAD_DATASET_LOAD_TEST = range(4)

HELP_STRING = """Supported commands:
/create_model - creates new model (interactive)
/delete_model model_name - deletes model `model_name`
/load_dataset - loads files (interactive)
/train model_name df_name - trains model `model_name` over the dataset `df_name`
/predict model_name df_name - returns predicts of model `model_name` over the dataset `df_name`
"""


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, my fellow user!\n" + HELP_STRING)


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=HELP_STRING)


def csv_to_pandas_df(file_link):
    with open('my_file.csv', "wb") as file:
        response = requests.get(file_link)
        file.write(response.content)
    res = pd.read_csv('my_file.csv')
    os.remove('my_file.csv')
    return res


# FILE DOWNLOAD


def load_dataset(update, context):
    update.message.reply_text(f'To create new dataset please enter its name\n'
                              f'To exit use /cancel anytime during the process')
    return LOAD_DATASET_ASK_NAME


def get_dataset_name(update, context):
    context.user_data['df_name'] = update.message.text
    update.message.reply_text(f'Please enter name of target column')
    return LOAD_DATASET_ASK_TARGET


def get_target_name(update, context):
    context.user_data['target'] = update.message.text
    update.message.reply_text(f'Download train dataset (only .csv) '
                              f'and write the name of target value - all in one message')
    return LOAD_DATASET_LOAD_TRAIN


def get_train_df(update, context):
    target = context.user_data['target']
    if not update.message.document.file_name.endswith('.csv'):
        update.message.reply_text(f'Only .csv is supported, please try again!')
        return LOAD_DATASET_LOAD_TRAIN
    df = csv_to_pandas_df(context.bot.get_file(update.message.document.file_id).file_path)\
        .select_dtypes(['number']).dropna()
    if target not in df.columns:
        update.message.reply_text(f'Target column {target} not found in dataset or is incorrect! '
                                  f'Please, enter the target column again!')
        return LOAD_DATASET_ASK_TARGET

    train_data = df.drop([target], axis=1).values
    test_data = df[target].values
    context.user_data['X_train'] = train_data.tolist()
    context.user_data['y_train'] = test_data.tolist()

    update.message.reply_text(f'Download test dataset (only .csv and it shouldn\'t contain target value)')
    return LOAD_DATASET_LOAD_TEST


def get_test_df(update, context):
    if not update.message.document.file_name.endswith('.csv'):
        update.message.reply_text(f'Only .csv is supported, please try again!')
        return LOAD_DATASET_LOAD_TRAIN
    df = csv_to_pandas_df(context.bot.get_file(update.message.document.file_id).file_path)\
        .select_dtypes(['number']).dropna()

    test_data = df.values.tolist()

    response = requests.get(f'http://localhost:5000/datasets/load/{context.user_data["df_name"]}',
                            json={
                                'data': [
                                    context.user_data['X_train'],
                                    context.user_data['y_train'],
                                    test_data
                                ]
                            })

    if response.status_code == 401:
        update.message.reply_text(f'Your files are bad!\n'
                                  f'Error message: {response.json()["message"]}')
    elif response.status_code == 200:
        update.message.reply_text(f'Your dataset is successfully loaded')
    else:
        update.message.reply_text('Oops something went wrong!')

    return ConversationHandler.END


# CREATING NEW MODEL


def create_new(update, context):
    update.message.reply_text(f'To create new model please enter its name\n'
                              f'To exit use /cancel anytime during the process')
    return CREATE_ASK_NAME


def get_name(update, context):
    model_name = update.message.text
    context.user_data['model_name'] = model_name
    reply_keyboard = requests.get('http://localhost:5000/models/types_list').json()['data']
    context.user_data['supported_models'] = reply_keyboard
    update.message.reply_text('Please select type of model',
                              reply_markup=ReplyKeyboardMarkup(
                                  [reply_keyboard],
                                  one_time_keyboard=True,
                                  input_field_placeholder='Which model?'
                              ))
    return CREATE_ASK_MODEL_TYPE


def get_model_type(update, context):
    model_type = update.message.text
    if model_type not in context.user_data['supported_models']:
        update.message.reply_text('You selected unsupported model type, please choose again!',
                                  reply_markup=ReplyKeyboardMarkup(
                                      [context.user_data['supported_models']],
                                      one_time_keyboard=True,
                                      input_field_placeholder='Which model?'
                                  ))
        return CREATE_ASK_MODEL_TYPE
    context.user_data['model_type'] = model_type
    update.message.reply_text(f'Now please enter desired parameters for your {model_type} one per line\n'
                              f'Example:\n'
                              f'n_estimators=5\n'
                              f'learning_rate=0.1\n\n'
                              f'You can use /skip to use default params',
                              reply_markup=ReplyKeyboardRemove())
    return CREATE_ASK_PARAMS


def get_params(update, context):
    params = {}
    ignored_params = []
    for line in update.message.text.split('\n'):
        if line == '/skip':
            continue
        line_split = line.split('=')
        key = line_split[0]
        if len(line_split) == 2:
            try:
                value = float(line_split[1])
                if int(value) == value:
                    value = int(value)
            except ValueError:
                value = line_split[1]
            params[key] = value
        else:
            ignored_params.append(line)

    response = requests.get(f'http://localhost:5000/models/create/{context.user_data["model_name"]}', json={
        'user_id': update.effective_chat.id,
        'model_type': context.user_data['model_type'],
        'params': params
    })

    if response.status_code == 404:
        update.message.reply_text('You selected unsupported model type! Create operation failed!')
    elif response.status_code == 401:
        update.message.reply_text(f'Parameters are invalid, please enter again!\n'
                                  f'Error message: {response.json()["message"]}')
        return CREATE_ASK_PARAMS
    elif response.status_code == 200:
        update.message.reply_text(f'Your model {context.user_data["model_name"]} is created!' +
                                  (f'\nHowever, the next parameters are ignored as invalid:\n'
                                   f' {", ".join(ignored_params)}' if len(ignored_params) > 0 else ''))
    else:
        update.message.reply_text('Oops something went wrong!')

    return ConversationHandler.END


# TRAIN


def train(update, context):
    args = context.args
    if len(args) != 2:
        update.message.reply_text(f'You should send model_name and dataset_name,'
                                  f' but you sent {len(args)} parameters')
    else:
        model_name, df_name = args[0], args[1]
        response = requests.get(f'http://localhost:5000/models/train/{model_name}', json={
            'user_id': update.effective_chat.id,
            'df_name': df_name
        })
        if response.status_code in (200, 401, 404):
            update.message.reply_text(str(response.json()['message']))
        # elif response.status_code == 401:
        #     update.message.reply_text(str(response.json()['message']))
        # elif response.status_code == 200:
        #     update.message.reply_text(response.json()['message'])
        else:
            update.message.reply_text('Oops something failed!')


# PREDICT


def predict(update, context):
    args = context.args
    if len(args) != 2:
        update.message.reply_text(f'You should send model_name and dataset_name,'
                                  f' but you sent {len(args)} parameters')
    else:
        model_name, df_name = args[0], args[1]
        response = requests.get(f'http://localhost:5000/models/predict/{model_name}', json={
            'user_id': update.effective_chat.id,
            'df_name': df_name
        })
        if response.status_code in (401, 404):
            update.message.reply_text(str(response.json()['message']))
        # elif response.status_code == 401:
        #     update.message.reply_text(str(response.json()['message']))
        elif response.status_code == 200:
            update.message.reply_text('Predicting went good!')
        else:
            update.message.reply_text('Oops something failed!')


def delete_model(update, context):
    args = context.args
    if len(args) != 1:
        update.message.reply_text(f'You should send model_name,'
                                  f' but you sent {len(args)} parameters')

    response = requests.get(f'http://localhost:5000/models/delete/{args[0]}', json={
        'user_id': update.effective_chat.id
    })

    if response.status_code == 200:
        update.message.reply_text('Deleting went good!')
    else:
        update.message.reply_text('Oops something failed!')


def cancel(update, context):
    update.message.reply_text('Operation cancelled')

    return ConversationHandler.END


def run():
    config = configparser.ConfigParser()
    config.read("config")

    updater = Updater(token=config['BOT']['token'], use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('train', train))
    dispatcher.add_handler(CommandHandler('predict', predict))
    dispatcher.add_handler(CommandHandler('delete_model', delete_model))

    create_new_handler = ConversationHandler(
        entry_points=[CommandHandler('create_model', create_new)],
        states={
            CREATE_ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            CREATE_ASK_MODEL_TYPE: [MessageHandler(Filters.text & ~Filters.command, get_model_type)],
            CREATE_ASK_PARAMS: [MessageHandler(~Filters.command, get_params), CommandHandler('skip', get_params)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(create_new_handler)

    load_handler = ConversationHandler(
        entry_points=[CommandHandler('load_dataset', load_dataset)],
        states={
            LOAD_DATASET_ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, get_dataset_name)],
            LOAD_DATASET_ASK_TARGET: [MessageHandler(Filters.text & ~Filters.command, get_target_name)],
            LOAD_DATASET_LOAD_TRAIN: [
                MessageHandler(Filters.document, get_train_df)
            ],
            LOAD_DATASET_LOAD_TEST: [MessageHandler(Filters.document, get_test_df)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(load_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    echo_handler2 = MessageHandler(Filters.document & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(echo_handler2)

    updater.start_polling()
