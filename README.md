# Productivity Todo Bot
A Telegram bot for task management built with Python using the `python-telegram-bot` library.

## Installation
1. **Install PyCharm Community Edition** (free) from [JetBrains](https://www.jetbrains.com/pycharm/download/).
2. **Create a virtual environment** in your project folder:
   - Open PyCharm, go to `File > Settings > Project > Python Interpreter > Create Virtual Environment`.
3. **Install dependencies**:
   - Activate the virtual environment (e.g., `.\.venv\Scripts\activate` on Windows).
   - Run:
     pip install python-telegram-bot[job-queue] schedule

4. **Get a bot token**:

   -Open Telegram, talk to @BotFather, create a new bot, and copy the API token.
   -Replace the TOKEN variable in bot.py with your token.


5. **Create .python-version**:

    -Create a file named .python-version in the project root with the content 3.13 (no quotes or extra lines).
    -Commit and push this file to your repository.



6. **Usage**

    -/start: Start the bot and see the menu.
    -/language: Switch between Russian and English.
    -Add tasks (e.g., test 1m for a 1-minute reminder).
    -Use buttons to manage tasks (add, show, complete, delete, delete all).
    -Complete or delete multiple tasks by entering numbers separated by commas (e.g., 1,3).

7. **Features**

    -Add, view, complete, and delete tasks.
    -Support for multiple languages (Russian/English).
    -Reminders based on time (minutes or hours).
    -Multiple task completion/deletion (e.g., 1,2,3).
    -Visual indicators: "🩷" for unfinished tasks, "✅" for completed tasks.

8. **Deployment**

    Set up Heroku:

    -Create a Heroku account at heroku.com.
    -Install the Heroku CLI and log in (heroku login).


    Configure the project:
    
    -Ensure a Procfile exists with worker: python bot.py.
    -Add a requirements.txt with:
    -textpython-telegram-bot[job-queue]
    -schedule
    
    Commit all changes to your Git repository.
    
    
    Deploy to Heroku:
    
    Connect your repository to Heroku:
    -heroku git:remote -a productive-todo-bot
    
    Push the code:
    -git push heroku main
    
    Scale the worker:
    -heroku ps:scale worker=1
    
    
    
    Verify:
    
    Check the app status:
    -heroku ps
    
    Test the bot in Telegram (@ProductiveTodoBot).



License
MIT Licenses
