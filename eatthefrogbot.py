import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TASKS_MENU = 'TASKS_MENU'
PROCRASTINATION = 'PROCRASTINATION'
START_OVER = 'START_OVER'
SELECTING_ACTION = 'SELECTING_ACTION'
ALL_TASKS = 'ALL_TASKS'
SHOW_TASKS = 'SHOW_TASKS'
TYPING_TASK_NAME = 'TYPING_TASK_NAME'
TYPING_TASK_DURATION = 'TYPING_TASK_DURATION'
TYPING_TASK_DEADLINE = 'TYPING_TASK_DEADLINE'
GET_TASK = 'GET_TASK'
STARTED_TASK = 'STARTED_TASK'
BACK_TO_TASK_CHOICE = 'BACK_TO_TASK_CHOICE'
BACK_TO_TASK_MENU = 'BACK_TO_TASK_MENU'
DELETE_TASK = 'DELETE_TASK'
NEW = 'NEW'
IN_PROGRESS = 'IN_PROGRESS'
DONE = 'DONE'
FINISH_TASK = 'FINISH_TASK'
EXTEND_TASK = 'EXTEND_TASK'
END = 'END'
ADD_NEW_TASK = 'ADD_NEW_TASK'

task_num = 0


class Task:
    def __init__(self, id, name, duration, time_left, deadline, state):
        self.id = id
        self.name = name
        self.duration = duration
        self.time_left = time_left
        self.deadline = deadline
        self.state = state


def start(update: Update, context: CallbackContext) -> None:
    text = (
        'Choose, what do you want me to do? To abort, simply type /stop.'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Tasks', callback_data=str(TASKS_MENU)),
        ],
        [
            InlineKeyboardButton(text='What is procrastination?', callback_data=str(PROCRASTINATION)),
        ],
        [
            InlineKeyboardButton(text='Done', callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need do send a new message
    if context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        update.message.reply_text(
            'Hi, I\'m TakeTheFrogBot! I can help you to overcome the procrastination.'
        )
        update.message.reply_text(text=text, reply_markup=keyboard)

    # set_timer(update, context)
    context.user_data[START_OVER] = False
    return SELECTING_ACTION


def end(update: Update, context: CallbackContext) -> None:
    """End conversation from InlineKeyboardButton."""
    update.callback_query.answer()

    text = 'See you around!'
    update.callback_query.edit_message_text(text=text)

    return END


def show_procrastination(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data

    text = 'Procrastination is one of the main barriers blocking you from getting up, making the right decisions and ' \
           'living the dream life you\'ve thought of. ' \
           '' \
           '\n\nRecent studies have shown that people regret more the things ' \
           'they haven\'t done than the things they have done. In addition, feelings of regret and guilt resulting ' \
           'from missed opportunities tend to stay with people much longer. ' \
           '' \
           '\n\nSometimes all our opportunities seem to be on our fingertips, but we can\'t seem to reach them. *When ' \
           'you ' \
           'procrastinate, you waste time that you could be investing in something meaningful*. If you can overcome ' \
           'this fierce enemy, you will be able to accomplish more and in doing so better utilize the potential that ' \
           'life has to offer. '

    buttons = [[InlineKeyboardButton(text='Back', callback_data=str(END))]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    user_data[START_OVER] = True

    return PROCRASTINATION


def tasks_menu(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    buttons = [
        [InlineKeyboardButton(text='Add new task', callback_data=str(ADD_NEW_TASK))],
        [InlineKeyboardButton(text='My tasks', callback_data=str(GET_TASK))],
        [InlineKeyboardButton(text='Show all tasks', callback_data=str(ALL_TASKS))],
        [InlineKeyboardButton(text='Back', callback_data=str(END))]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if not context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text='Choose an option about tasks', reply_markup=keyboard)
    else:
        number_of_tasks = len(user_data['TASKS'])
        text = 'Got it! You have {} tasks'.format(number_of_tasks)
        update.message.reply_text(text=text, reply_markup=keyboard)

    user_data[START_OVER] = True

    return SHOW_TASKS


def show_all_tasks(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    buttons = [
        [InlineKeyboardButton(text='Back', callback_data=str(BACK_TO_TASK_MENU))]
    ]

    text = 'Here is the list of *ALL* tasks (even finished)'
    if 'TASKS' not in user_data:
        user_data['TASKS'] = []

    if 'TASKS' not in user_data or len(user_data['TASKS']) == 0:
        text = '\nYou have no any tasks'
    else:
        tasks = user_data['TASKS']
        for task in tasks:
            text += '\nTask №{}: {}, duration: {}, deadline: {}'.format(task.id, task.name, task.duration,
                                                                        task.deadline)
    update.callback_query.answer()

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    user_data[START_OVER] = False

    return ALL_TASKS


def stop(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Okay, bye.')
    return END


def add_new_task_name(update: Update, context: CallbackContext) -> None:
    text = 'Okay, please, write your task.'
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    return TYPING_TASK_NAME


def save_task_name(update: Update, context: CallbackContext) -> None:
    global task_num
    user_data = context.user_data
    user_task_name = update.message.text
    if 'TASKS' not in user_data:
        user_data['TASKS'] = []
    task_num += 1
    task = Task(task_num, user_task_name, None, None, None, NEW)
    user_data['TASKS'].append(task)

    text = 'Write duration of the task in hours (e.g. 10 means 10 hours).'
    update.message.reply_text(text)
    return TYPING_TASK_DURATION


def add_new_task_duration(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    global task_num
    task_number = task_num
    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    user_data['TASKS'][element_number].duration = int(update.message.text)
    text = 'Write deadline of the task in the format YYYY-MM-DD HH:MM:SS, e.g. 2021-01-09 23:59'
    update.message.reply_text(text)
    return TYPING_TASK_DEADLINE


def add_new_task_deadline(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    user_deadline = datetime.fromisoformat(update.message.text)
    if user_deadline <= datetime.now():
        update.message.reply_text(text='You can\'t add date in the past')
        return TYPING_TASK_DEADLINE
    global task_num
    task_number = task_num
    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    user_data['TASKS'][element_number].deadline = user_deadline
    user_data[START_OVER] = True
    return tasks_menu(update, context)


def get_task(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    buttons = []

    if 'TASKS' not in user_data or len(user_data['TASKS']) == 0:
        text = 'You have no any tasks'
    else:
        tasks = sorted(user_data['TASKS'], key=lambda x: x.deadline)
        for task in tasks:
            if task.state != DONE:
                if task.time_left is not None:
                    if isinstance(task.time_left, timedelta):
                        time_diff = task.time_left
                    else:
                        time_diff = task.time_left - datetime.now()
                    text = '\nTask №{}: {}, duration: {}, deadline: {}, time left: {}' \
                        .format(task.id, task.name, task.duration,
                                task.deadline, str(timedelta(seconds=time_diff.total_seconds())))
                else:
                    text = '\nTask №{}: {}, duration: {}, deadline: {}' \
                        .format(task.id, task.name, task.duration, task.deadline)
                button = [InlineKeyboardButton(text=text, callback_data=str(task.id))]
                buttons.append(button)

    back_button = [InlineKeyboardButton(text='Back', callback_data=str(BACK_TO_TASK_MENU))]
    buttons.append(back_button)
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text='*Choose the task*', reply_markup=keyboard,
                                            parse_mode=ParseMode.MARKDOWN)

    user_data[START_OVER] = False
    return ALL_TASKS


def start_task(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    task_number = int(update.callback_query.data)
    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    task_description = 'Task №{}: {}, duration: {}, deadline: {}'.format(user_data['TASKS'][element_number].id,
                                                                         user_data['TASKS'][element_number].name,
                                                                         user_data['TASKS'][element_number].duration,
                                                                         user_data['TASKS'][element_number].deadline)

    buttons = [
        [InlineKeyboardButton(text='Start', callback_data=str(STARTED_TASK + '_' + str(task_number)))],
        [InlineKeyboardButton(text='Finish', callback_data=str(FINISH_TASK + '_' + str(task_number)))],
        [InlineKeyboardButton(text='Extend Time', callback_data=str(EXTEND_TASK + '_' + str(task_number)))],
        [InlineKeyboardButton(text='Delete', callback_data=str(DELETE_TASK + '_' + str(task_number)))],
        [InlineKeyboardButton(text='Back', callback_data=str(BACK_TO_TASK_CHOICE))]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=task_description, reply_markup=keyboard,
                                            parse_mode=ParseMode.MARKDOWN)

    user_data[START_OVER] = False

    return ALL_TASKS


def proceed_task(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    callback_data = update.callback_query.data
    text = '*You\'ve successfuly started a task*'
    task_number = int(callback_data.split('_', 3)[2])
    for task in user_data['TASKS']:
        if task.state == IN_PROGRESS:
            buttons = [
                [InlineKeyboardButton(text='Back', callback_data=str(END))]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            context.user_data[START_OVER] = True
            update.callback_query.edit_message_text(text='*You can\'t start a few tasks simultaneously*',
                                                    reply_markup=keyboard,
                                                    parse_mode=ParseMode.MARKDOWN)
            return ALL_TASKS

    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    user_data['TASKS'][element_number].state = IN_PROGRESS
    if datetime.now() + timedelta(hours=user_data['TASKS'][element_number].duration) <= user_data['TASKS'][
        element_number].deadline:
        user_data['TASKS'][element_number].time_left = \
            datetime.now() + timedelta(hours=user_data['TASKS'][element_number].duration)
    else:
        user_data['TASKS'][element_number].time_left = user_data['TASKS'][element_number].deadline - datetime.now()
    set_timer(update, context, user_data['TASKS'][element_number], first_time=True)

    buttons = [
        [InlineKeyboardButton(text='Done', callback_data=str(END))]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard,
                                            parse_mode=ParseMode.MARKDOWN)

    user_data[START_OVER] = True

    return ALL_TASKS


def finish_task(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    callback_data = update.callback_query.data
    text = ''
    task_number = int(callback_data.split('_', 3)[2])

    buttons = [
        [InlineKeyboardButton(text='Done', callback_data=str(BACK_TO_TASK_CHOICE))]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    if user_data['TASKS'][element_number].state != IN_PROGRESS:
        text = 'You can\'t finish the task that you haven\'t started'
    else:
        user_data['TASKS'][element_number].state = DONE
        remove_job_if_exists(user_data['TASKS'][element_number].name + '_timeleft', context)
        remove_job_if_exists(user_data['TASKS'][element_number].name + '_deadline', context)
        text = '*You\'ve marked this task as done*'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard,
                                            parse_mode=ParseMode.MARKDOWN)

    user_data[START_OVER] = True

    return ALL_TASKS


def extend_task_time_left(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    callback_data = update.callback_query.data
    text = 'You\'ve successfully extended time for this task.'
    task_number = int(callback_data.split('_', 3)[2])

    buttons = [
        [InlineKeyboardButton(text='Done', callback_data=str(BACK_TO_TASK_CHOICE))]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    if user_data['TASKS'][element_number].time_left is not None:
        if not isinstance(user_data['TASKS'][element_number].time_left, timedelta) and (
                user_data['TASKS'][element_number].time_left + timedelta(
                hours=user_data['TASKS'][element_number].duration)) \
                < user_data['TASKS'][element_number].deadline:
            user_data['TASKS'][element_number].time_left += timedelta(hours=user_data['TASKS'][element_number].duration)
            set_timer(update, context, user_data['TASKS'][element_number], first_time=False)
        else:
            text = 'You can\'t extend this task because of deadline.'
    else:
        text = 'You can\'t extend the task that you haven\'t started yet.'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard,
                                            parse_mode=ParseMode.MARKDOWN)
    user_data[START_OVER] = True

    return ALL_TASKS


def delete_task(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    callback_data = update.callback_query.data

    task_number = int(callback_data.split('_', 3)[2])

    element_number = 0
    for i in range(0, len(user_data['TASKS'])):
        if user_data['TASKS'][i].id == task_number:
            element_number = i
    del user_data['TASKS'][element_number]

    buttons = [
        [InlineKeyboardButton(text='Done', callback_data=str(BACK_TO_TASK_CHOICE))]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text='*You\'ve deleted a task*', reply_markup=keyboard,
                                            parse_mode=ParseMode.MARKDOWN)

    user_data[START_OVER] = True

    return ALL_TASKS


def remind(context):
    job = context.job
    context.bot.send_message(job.context,
                             text='This is a reminder that you currently do a {} task. If you '
                                  'done with this task, don\'t forget to mark it as done, otherwise extend it\'s time.'
                             .format(job.name[:-9]))


def remind_deadline(context):
    job = context.job
    context.bot.send_message(job.context,
                             text='This is a reminder that you currently do a {} task. You have only 2 hours left for '
                                  'this task, so don\'t forget to mark it as done. '
                             .format(job.name[:-9]))


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext, task, first_time) -> None:
    # for production
    # datetime_with_duration = datetime.today() + timedelta(hours=task.duration)
    # context.job_queue.run_once(remind, datetime_with_duration, context=update.effective_chat.id, name=str(task.name + '_timeleft'))
    # for presentation
    context.job_queue.run_once(remind, timedelta(seconds=25), context=update.effective_chat.id, name=str(task.name + '_timeleft'))
    if first_time:
        context.job_queue.run_once(remind_deadline, task.deadline - timedelta(hours=2),
                                   context=update.effective_chat.id,
                                   name=str(task.name + '_deadline'))


def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [CallbackQueryHandler(show_procrastination, pattern='^' + str(PROCRASTINATION) + '$'),
                               CallbackQueryHandler(tasks_menu, pattern='^' + str(TASKS_MENU) + '$'),
                               CallbackQueryHandler(end, pattern='^' + str(END) + '$')],
            PROCRASTINATION: [CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            SHOW_TASKS: [CallbackQueryHandler(show_all_tasks, pattern='^' + str(ALL_TASKS) + '$'),
                         CallbackQueryHandler(add_new_task_name, pattern='^' + str(ADD_NEW_TASK) + '$'),
                         CallbackQueryHandler(get_task, pattern='^' + str(GET_TASK + '$')),
                         CallbackQueryHandler(start, pattern='^' + str(TYPING_TASK_NAME) + '$'),
                         CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            ALL_TASKS: [CallbackQueryHandler(start_task, pattern='^' + str('\d+') + '$'),
                        CallbackQueryHandler(get_task, pattern='^' + str(BACK_TO_TASK_CHOICE) + '$'),
                        CallbackQueryHandler(tasks_menu, pattern='^' + str(BACK_TO_TASK_MENU) + '$'),
                        CallbackQueryHandler(proceed_task, pattern='^' + str(STARTED_TASK) + '_' + str('\d+') + '$'),
                        CallbackQueryHandler(finish_task, pattern='^' + str(FINISH_TASK) + '_' + str('\d+') + '$'),
                        CallbackQueryHandler(extend_task_time_left,
                                             pattern='^' + str(EXTEND_TASK) + '_' + str('\d+') + '$'),
                        CallbackQueryHandler(delete_task, pattern='^' + str(DELETE_TASK) + '_' + str('\d+') + '$'),
                        CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            TYPING_TASK_NAME: [MessageHandler(Filters.text & ~Filters.command, save_task_name)],
            TYPING_TASK_DURATION: [MessageHandler(Filters.text & ~Filters.command, add_new_task_duration)],
            TYPING_TASK_DEADLINE: [MessageHandler(Filters.text & ~Filters.command, add_new_task_deadline)]
        },
        fallbacks=[CommandHandler('stop', stop)],
        map_to_parent={
            END: SELECTING_ACTION,
        }
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
