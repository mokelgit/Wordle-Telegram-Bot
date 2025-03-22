from cgitb import text
import telebot
import psycopg2
from psycopg2 import Error
from config import db_config, telegram_token
import re

# Initialize Telegram Bot with your token
bot = telebot.TeleBot(telegram_token)

# Database connection parameters from config.py
db_name = db_config['dbname']
db_user = db_config['user']
db_password = db_config['password']
db_host = db_config['host']
db_port = db_config['port']

def get_db_connection():
    try:
        connection = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name
        )
        return connection
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None

@bot.message_handler(commands=['joinleague'])
def handle_messages(message):
    user_at = message.from_user.username
    chat_id = message.chat.id
    user_id = message.from_user.id
    input_score = message.text.replace("/joinleague ", '').strip()

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s AND chat_id = %s;", (user_id, chat_id))
        users = cursor.fetchone()

        if users is None:
            if re.search(r"^\d{1,4}$", input_score):
                cursor.execute(
                    "INSERT INTO users (user_id, chat_id, score, username) VALUES (%s, %s, %s, %s);",
                    (user_id, chat_id, int(input_score), user_at)
                )
                connection.commit()
                bot.reply_to(message, "Welcome to wordle league!")
            else:
                bot.reply_to(message, "Incorrect score input. Please enter your score when entering the league. If you have no score, please enter 0.")
        else:
            bot.reply_to(message, "You are already in this league.")

        cursor.close()
        connection.close()

@bot.message_handler(commands=["wordle"])
def wordle(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT score FROM users WHERE user_id = %s AND chat_id = %s;", (user_id, chat_id))
        curr_score = cursor.fetchone()

        if curr_score:
            curr_score = curr_score[0]
            if re.search(r"[1-6]/", message.text):
                user_score = re.findall("[1-6]\/", message.text)
                user_score = re.findall("[1-6]", user_score[0])
                user_score = int(user_score[0])
                user_score = 6 - (user_score - 1)
                new_score = curr_score + user_score

                cursor.execute("UPDATE users SET score = %s WHERE user_id = %s AND chat_id = %s;", (new_score, user_id, chat_id))
                connection.commit()
                bot.reply_to(message, f"Congrats Wordler your current score is {new_score}.\n")
            elif re.search(r"X/", message.text):
                bot.reply_to(message, "0 Score?. RIP.")
            else:
                bot.reply_to(message, "Score incorrectly formatted")
        else:
            bot.reply_to(message, "You are not currently in this league please join before entering scores.")

        cursor.close()
        connection.close()

@bot.message_handler(commands=["scoreboard"])
def scoreboard(message):
    chat_id = message.chat.id
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT username, score FROM users WHERE chat_id = %s ORDER BY score DESC;", (chat_id,))
        chat_data = cursor.fetchall()

        message_text = ""
        for idx, (username, score) in enumerate(chat_data, 1):
            message_text += f"{idx}. {username}: {score} pts.\n"

        bot.reply_to(message, message_text)

        cursor.close()
        connection.close()

@bot.message_handler(commands=["resetscore"])
def resetscore(message):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        status = bot.get_chat_member(message.chat.id, message.from_user.id).status

        if status == "creator" or status == "administrator":
            cursor.execute("UPDATE users SET score = 0 WHERE chat_id = %s;", (message.chat.id,))
            connection.commit()
            bot.reply_to(message, "Scores have successfully been reset.")
        else:
            bot.reply_to(message, "Error. You do not have the proper permissions to perform this command.")

        cursor.close()
        connection.close()

@bot.message_handler(commands=["help"])
def help(message):
    bot.reply_to(message, (
        "Welcome to Wordle Bot for Telegram!\n\n"
        "Currently functioning commands are:\n"
        "/joinleague [score] (Enter your overall score for the current league following the joinleague command).\n"
        "/wordle [Wordle Score] (Insert your scores for each day. Copy and paste from the site).\n"
        "/scoreboard (Displays everyone's scores in order).\n"
    ))

bot.infinity_polling()
