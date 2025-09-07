from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import sqlite3
import datetime
import schedule
import time
import threading
import os

# Уникальная метка версии
VERSION = "v3.5"
TOKEN = '8384181109:AAHZ8xVMkg7FGiPWsIP1B0X4LUvl7M5Wopk'
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # Укажем в Heroku

# Вывод версии и времени запуска
print(f"Запуск бота {VERSION} | Дата и время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
    c.execute("SELECT user_id, task_text FROM tasks WHERE id = ? AND done = 0", (job.data,))
    task = c.fetchone()
    conn.close()
    if task:
        await context.bot.send_message(chat_id=task[0], text=f"Напоминание: выполни задачу '{task[1]}'!")

# Функция для создания клавиатуры
def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("Добавить задачу", callback_data='add_task')],
        [InlineKeyboardButton("Показать задачи", callback_data='list_tasks')],
        [InlineKeyboardButton("Завершить задачу", callback_data='done_task')],
        [InlineKeyboardButton("Удалить задачу", callback_data='delete_task')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для команды /start
async def start(update, context):
    init_db()
    await update.message.reply_text("Привет! Я бот для управления задачами. Выбери действие:", reply_markup=get_keyboard())

# Функция для обработки нажатий на кнопки
async def button(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    current_message = query.message.text

    if query.data == 'add_task':
        if current_message != "Введите задачу (например, 'Купить молоко 5m' для напоминания):":
            await query.edit_message_text("Введите задачу (например, 'Купить молоко 5m' для напоминания):")
        context.user_data['expecting_task'] = True
        context.user_data['action'] = 'add'

    elif query.data == 'list_tasks':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = c.fetchall()
        conn.close()
        response = "Список задач:\n" if tasks else "Список задач пуст."
        if tasks:
            for task in tasks:
                status = "✅" if task[2] else "⬜"
                response += f"{task[0]}. [{status}] {task[1]}\n"
        if current_message != response:
            await query.edit_message_text(response, reply_markup=get_keyboard())

    elif query.data == 'done_task':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = c.fetchall()
        conn.close()
        response = "Выберите номер задачи для завершения:\n" if tasks else "Список задач пуст."
        if tasks:
            for task in tasks:
                status = "✅" if task[2] else "⬜"
                response += f"{task[0]}. [{status}] {task[1]}\n"
        if current_message != response:
            await query.edit_message_text(response)
            context.user_data['expecting_task_id'] = True
            context.user_data['action'] = 'done'
        elif not tasks:
            await query.edit_message_text(response, reply_markup=get_keyboard())

    elif query.data == 'delete_task':
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = c.fetchall()
        conn.close()
        response = "Выберите номер задачи для удаления:\n" if tasks else "Список задач пуст."
        if tasks:
            for task in tasks:
                status = "✅" if task[2] else "⬜"
                response += f"{task[0]}. [{status}] {task[1]}\n"
        if current_message != response:
            await query.edit_message_text(response)
            context.user_data['expecting_task_id'] = True
            context.user_data['action'] = 'delete'
        elif not tasks:
            await query.edit_message_text(response, reply_markup=get_keyboard())

# Функция для обработки текстовых сообщений (добавление задач или ID)
async def handle_message(update, context):
    if context.user_data.get('expecting_task'):
        task_text = update.message.text
        reminder = None
        if ' ' in task_text and task_text.split()[-1].endswith(('h', 'm')):
            parts = task_text.split()
            reminder = parts[-1]
            task_text = ' '.join(parts[:-1])
        else:
            await update.message.reply_text("Пожалуйста, укажите задачу с временем (например, 'Купить молоко 5m').", reply_markup=get_keyboard())
            return
        if reminder and reminder.endswith(('h', 'm')):
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            c.execute("INSERT INTO tasks (task_text, user_id, reminder_time) VALUES (?, ?, ?)", (task_text, update.effective_user.id, reminder))
            conn.commit()
            task_id = c.lastrowid
            conn.close()
            if reminder.endswith('h'):
                delay = int(reminder[:-1]) * 3600
            elif reminder.endswith('m'):
                delay = int(reminder[:-1]) * 60
            context.job_queue.run_once(send_reminder, delay, data=task_id)
            await update.message.reply_text(f"Задача '{task_text}' добавлена с напоминанием через {reminder}!", reply_markup=get_keyboard())
        del context.user_data['expecting_task']
        del context.user_data['action']

    elif context.user_data.get('expecting_task_id'):
        if update.message.text.isdigit():
            task_id = int(update.message.text)
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            c.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, update.effective_user.id))
            if c.fetchone():
                if context.user_data['action'] == 'done':
                    c.execute("UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?", (task_id, update.effective_user.id))
                    conn.commit()
                    await update.message.reply_text(f"Задача {task_id} помечена как выполненная!", reply_markup=get_keyboard())
                elif context.user_data['action'] == 'delete':
                    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, update.effective_user.id))
                    conn.commit()
                    await update.message.reply_text(f"Задача {task_id} удалена!", reply_markup=get_keyboard())
            else:
                await update.message.reply_text(f"Задача с номером {task_id} не найдена.", reply_markup=get_keyboard())
            conn.close()
        else:
            await update.message.reply_text("Пожалуйста, введите корректный номер задачи.", reply_markup=get_keyboard())
        del context.user_data['expecting_task_id']
        del context.user_data['action']

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    application = Application.builder().token(TOKEN).build()
    if WEBHOOK_URL:
        application.run_webhook(
            listen='0.0.0.0',
            port=int(os.environ.get('PORT', 8443)),
            url_path=TOKEN,
            webhook_url=WEBHOOK_URL + TOKEN
        )
    else:
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        schedule_thread = threading.Thread(target=run_schedule)
        schedule_thread.start()
        application.run_polling()
    application.run_polling()  # Фallback для локального теста

if __name__ == '__main__':
    main()