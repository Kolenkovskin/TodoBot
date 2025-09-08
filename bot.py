from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import sqlite3
import datetime
import schedule
import time
import threading

# Уникальная метка версии
VERSION = "v3.30"
TOKEN = '8384181109:AAHZ8xVMkg7FGiPWsIP1B0X4LUvl7M5Wopk'

# Вывод версии и времени запуска
print(f"Запуск бота {VERSION} | Дата и время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Переводы
LANGUAGES = {
    "ru": {
        "start_message": "Привет! Я бот для управления задачами. Выбери действие:",
        "language_message": "Выберите язык:",
        "add_task": "Добавить задачу",
        "show_tasks": "Показать задачи",
        "complete_task": "Завершить задачу",
        "delete_task": "Удалить задачу",
        "delete_all_tasks": "Удалить все задачи",
        "confirm_delete_all": "Вы уверены, что хотите удалить все задачи? (Да/Нет)",
        "delete_all_confirmed": "Все задачи удалены!",
        "delete_all_canceled": "Удаление отменено.",
        "yes": "Да",
        "no": "Нет",
        "input_task": "Введите задачу (например, 'Купить молоко 5m' для напоминания):",
        "task_added": "Задача '{task}' добавлена с напоминанием через {reminder}!",
        "task_added_no_reminder": "Задача '{task}' добавлена!",
        "list_empty": "Список задач пуст.",
        "list_tasks": "Список задач:\n{task_list}",
        "select_done": "Выберите номер задачи для завершения (можно несколько через запятую, e.g., 1,3):\n{task_list}",
        "select_delete": "Выберите номер задачи для удаления (можно несколько через запятую, e.g., 1,3):\n{task_list}",
        "task_done": "Задачи {task_ids} помечены как выполненные!",
        "task_already_done": "Эта задача уже завершена!",
        "task_deleted": "Задачи {task_ids} удалены!",
        "task_not_found": "Задача с номером {task_id} не найдена.",
        "invalid_input": "Пожалуйста, введите корректный номер задачи.",
        "invalid_task": "Пожалуйста, укажите задачу с временем (например, 'Купить молоко 5m').",
        "task_reminder": "Напоминание: выполни задачу '{task}'!"
    },
    "en": {
        "start_message": "Hello! I am a task management bot. Choose an action:",
        "language_message": "Choose a language:",
        "add_task": "Add Task",
        "show_tasks": "Show Tasks",
        "complete_task": "Complete Task",
        "delete_task": "Delete Task",
        "delete_all_tasks": "Delete All Tasks",
        "confirm_delete_all": "Are you sure you want to delete all tasks? (Yes/No)",
        "delete_all_confirmed": "All tasks deleted!",
        "delete_all_canceled": "Deletion canceled.",
        "yes": "Yes",
        "no": "No",
        "input_task": "Enter a task (e.g., 'Buy milk 5m' for a reminder):",
        "task_added": "Task '{task}' added with a reminder in {reminder}!",
        "task_added_no_reminder": "Task '{task}' added!",
        "list_empty": "Task list is empty.",
        "list_tasks": "Task list:\n{task_list}",
        "select_done": "Select a task number to complete (can be multiple comma-separated, e.g., 1,3):\n{task_list}",
        "select_delete": "Select a task number to delete (can be multiple comma-separated, e.g., 1,3):\n{task_list}",
        "task_done": "Tasks {task_ids} marked as completed!",
        "task_already_done": "This task is already completed!",
        "task_deleted": "Tasks {task_ids} deleted!",
        "task_not_found": "Task with number {task_id} not found.",
        "invalid_input": "Please enter a valid task number.",
        "invalid_task": "Please enter a task with a time (e.g., 'Buy milk 5m').",
        "task_reminder": "Reminder: complete task '{task}'!"
    }
}

# Функция для инициализации или обновления базы данных
def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(tasks)")
    columns = [info[1] for info in c.fetchall()]
    if not columns:
        c.execute('''CREATE TABLE tasks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_text TEXT, done INTEGER DEFAULT 0, user_id INTEGER, reminder_time TEXT)''')
    elif 'reminder_time' not in columns:
        c.execute("ALTER TABLE tasks ADD COLUMN reminder_time TEXT")
    conn.commit()
    c.execute("PRAGMA table_info(tasks)")
    columns = [info[1] for info in c.fetchall()]
    print(f"Колонки в таблице tasks: {columns}")
    conn.close()

# Функция для отправки напоминаний
async def send_reminder(context):
    job = context.job
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("SELECT user_id, task_text FROM tasks WHERE id = ? AND done = 0", (job.data['task_id'],))
    task = c.fetchone()
    conn.close()
    if task:
        lang = job.data.get('language', 'en')  # Извлекаем язык из job.data
        keyboard = [
            [InlineKeyboardButton(LANGUAGES[lang]["add_task"], callback_data='add_task')],
            [InlineKeyboardButton(LANGUAGES[lang]["show_tasks"], callback_data='list_tasks')],
            [InlineKeyboardButton(LANGUAGES[lang]["complete_task"], callback_data='done_task')],
            [InlineKeyboardButton(LANGUAGES[lang]["delete_task"], callback_data='delete_task')],
            [InlineKeyboardButton(LANGUAGES[lang]["delete_all_tasks"], callback_data='delete_all_tasks')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=task[0], text=LANGUAGES[lang]["task_reminder"].format(task=task[1]), reply_markup=reply_markup)

# Функция для создания клавиатуры
def get_keyboard(context):
    lang = context.user_data.get('language', 'en') if context else 'en'  # Безопасная проверка context
    keyboard = [
        [InlineKeyboardButton(LANGUAGES[lang]["add_task"], callback_data='add_task')],
        [InlineKeyboardButton(LANGUAGES[lang]["show_tasks"], callback_data='list_tasks')],
        [InlineKeyboardButton(LANGUAGES[lang]["complete_task"], callback_data='done_task')],
        [InlineKeyboardButton(LANGUAGES[lang]["delete_task"], callback_data='delete_task')],
        [InlineKeyboardButton(LANGUAGES[lang]["delete_all_tasks"], callback_data='delete_all_tasks')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для создания клавиатуры выбора языка
def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data='set_lang_ru')],
        [InlineKeyboardButton("English", callback_data='set_lang_en')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для команды /start
async def start(update, context):
    init_db()
    lang = context.user_data.get('language', 'en')
    await update.message.reply_text(LANGUAGES[lang]["start_message"], reply_markup=get_keyboard(context))

# Функция для команды /language
async def language(update, context):
    await update.message.reply_text(LANGUAGES['en']["language_message"], reply_markup=get_language_keyboard())

# Функция для обработки выбора языка
async def set_language(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'set_lang_ru':
        context.user_data['language'] = 'ru'
    elif query.data == 'set_lang_en':
        context.user_data['language'] = 'en'
    lang = context.user_data['language']
    await query.edit_message_text(LANGUAGES[lang]["start_message"], reply_markup=get_keyboard(context))

# Функция для обработки нажатий на кнопки
async def button(update, context):
    query = update.callback_query
    print(f"Button clicked: {query.data}")  # Отладка: выводим callback_data
    await query.answer()
    user_id = query.from_user.id
    current_message = query.message.text
    lang = context.user_data.get('language', 'en')

    if query.data == 'add_task':
        if current_message != LANGUAGES[lang]["input_task"]:
            await query.edit_message_text(LANGUAGES[lang]["input_task"])
        context.user_data['expecting_task'] = True
        context.user_data['action'] = 'add'

    elif query.data == 'list_tasks':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = c.fetchall()
        conn.close()
        response = LANGUAGES[lang]["list_empty"] if not tasks else LANGUAGES[lang]["list_tasks"].format(task_list="".join([f"{i+1}. [{'✅' if task[2] else '🩷'}] {task[1]}\n" for i, task in enumerate(tasks)]))
        if current_message != response:
            await query.edit_message_text(response, reply_markup=get_keyboard(context))

    elif query.data == 'done_task':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = c.fetchall()
        conn.close()
        response = LANGUAGES[lang]["list_empty"] if not tasks else LANGUAGES[lang]["select_done"].format(task_list="".join([f"{i+1}. [{'✅' if task[2] else '🩷'}] {task[1]}\n" for i, task in enumerate(tasks)]))
        if current_message != response:
            await query.edit_message_text(response)
            context.user_data['expecting_task_id'] = True
            context.user_data['action'] = 'done'
        elif not tasks:
            await query.edit_message_text(response, reply_markup=get_keyboard(context))

    elif query.data == 'delete_task':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = c.fetchall()
        conn.close()
        response = LANGUAGES[lang]["list_empty"] if not tasks else LANGUAGES[lang]["select_delete"].format(task_list="".join([f"{i+1}. [{'✅' if task[2] else '🩷'}] {task[1]}\n" for i, task in enumerate(tasks)]))
        if current_message != response:
            await query.edit_message_text(response)
            context.user_data['expecting_task_id'] = True
            context.user_data['action'] = 'delete'
        elif not tasks:
            await query.edit_message_text(response, reply_markup=get_keyboard(context))

    elif query.data == 'delete_all_tasks':
        keyboard = [
            [InlineKeyboardButton(LANGUAGES[lang]["yes"], callback_data='confirm_delete_all_yes'),
             InlineKeyboardButton(LANGUAGES[lang]["no"], callback_data='confirm_delete_all_no')]
        ]
        await query.edit_message_text(LANGUAGES[lang]["confirm_delete_all"], reply_markup=InlineKeyboardMarkup(keyboard))

# Функция для подтверждения удаления всех задач
async def confirm_delete_all(update, context):
    query = update.callback_query
    print(f"Confirm delete all clicked: {query.data}")  # Отладка: выводим callback_data
    await query.answer()
    user_id = query.from_user.id
    lang = context.user_data.get('language', 'en')

    if query.data == 'confirm_delete_all_yes':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text(LANGUAGES[lang]["delete_all_confirmed"], reply_markup=get_keyboard(context))
    elif query.data == 'confirm_delete_all_no':
        await query.edit_message_text(LANGUAGES[lang]["delete_all_canceled"], reply_markup=get_keyboard(context))

# Функция для обработки текстовых сообщений (добавление задач или ID)
async def handle_message(update, context):
    lang = context.user_data.get('language', 'en')
    if context.user_data.get('expecting_task'):
        task_text = update.message.text
        reminder = None
        if ' ' in task_text and task_text.split()[-1].endswith(('h', 'm')):
            parts = task_text.split()
            reminder = parts[-1]
            task_text = ' '.join(parts[:-1])
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("INSERT INTO tasks (task_text, user_id, reminder_time) VALUES (?, ?, ?)", (task_text, update.effective_user.id, reminder if reminder else None))
        conn.commit()
        task_id = c.lastrowid
        conn.close()
        if reminder and reminder.endswith(('h', 'm')):
            if reminder.endswith('h'):
                delay = int(reminder[:-1]) * 3600
            elif reminder.endswith('m'):
                delay = int(reminder[:-1]) * 60
            context.job_queue.run_once(send_reminder, delay, data={'task_id': task_id, 'language': lang})  # Передаем язык в job.data
            await update.message.reply_text(LANGUAGES[lang]["task_added"].format(task=task_text, reminder=reminder), reply_markup=get_keyboard(context))
        else:
            await update.message.reply_text(LANGUAGES[lang]["task_added_no_reminder"].format(task=task_text), reply_markup=get_keyboard(context))
        del context.user_data['expecting_task']
        del context.user_data['action']

    elif context.user_data.get('expecting_task_id'):
        input_text = update.message.text.strip()
        task_numbers = []
        if ',' in input_text:
            # Разбираем несколько номеров через запятую
            numbers = input_text.split(',')
            for num in numbers:
                num = num.strip()
                if num.isdigit():
                    task_numbers.append(int(num))
                else:
                    await update.message.reply_text(LANGUAGES[lang]["invalid_input"], reply_markup=get_keyboard(context))
                    return
        elif input_text.isdigit():
            task_numbers.append(int(input_text))
        else:
            await update.message.reply_text(LANGUAGES[lang]["invalid_input"], reply_markup=get_keyboard(context))
            return

        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, done FROM tasks WHERE user_id = ? ORDER BY id", (update.effective_user.id,))
        tasks = c.fetchall()
        completed_tasks = []
        deleted_tasks = []
        valid_numbers = range(1, len(tasks) + 1)

        for task_number in task_numbers:
            if 1 <= task_number <= len(tasks):
                task_id = tasks[task_number - 1][0]
                task_done = tasks[task_number - 1][1]
                if context.user_data['action'] == 'done':
                    if task_done == 1:
                        await update.message.reply_text(LANGUAGES[lang]["task_already_done"], reply_markup=get_keyboard(context))
                    else:
                        c.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
                        conn.commit()
                        completed_tasks.append(str(task_number))
                elif context.user_data['action'] == 'delete':
                    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, update.effective_user.id))
                    conn.commit()
                    deleted_tasks.append(str(task_number))
            else:
                await update.message.reply_text(LANGUAGES[lang]["task_not_found"].format(task_id=task_number), reply_markup=get_keyboard(context))

        # Обновляем список задач
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (update.effective_user.id,))
        tasks = c.fetchall()
        response = LANGUAGES[lang]["list_empty"] if not tasks else LANGUAGES[lang]["list_tasks"].format(task_list="".join([f"{i+1}. [{'✅' if task[2] else '🩷'}] {task[1]}\n" for i, task in enumerate(tasks)]))
        if completed_tasks:
            await update.message.reply_text(LANGUAGES[lang]["task_done"].format(task_ids=', '.join(completed_tasks)), reply_markup=get_keyboard(context))
        if deleted_tasks:
            await update.message.reply_text(LANGUAGES[lang]["task_deleted"].format(task_ids=', '.join(deleted_tasks)), reply_markup=get_keyboard(context))
        await update.message.reply_text(response, reply_markup=get_keyboard(context))
        conn.close()
        del context.user_data['expecting_task_id']
        del context.user_data['action']

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(confirm_delete_all, pattern='^confirm_delete_all_(yes|no)$'))  # Приоритет для подтверждения
    application.add_handler(CallbackQueryHandler(set_language, pattern='^set_lang_'))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
    application.run_polling()

if __name__ == '__main__':
    main()