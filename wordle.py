from cgitb import text
import telebot
import config
import re
from pymongo import MongoClient
from bson.objectid import ObjectId

cluster = MongoClient(config.connect_mongodb())
bot = telebot.TeleBot(config.get_api())

@bot.message_handler(commands=['joinleague'])
def handle_messages(message):
    input_data = cluster.wordle_db.user_data
    user_at = message.from_user.username
    chat_id = message.chat.id
    user_id = message.from_user.id
    #pull user data from message
    input_score = message.text.replace("/joinleague ", '')
    if input_data.find_one({"user_id": int(user_id), "chat_id": int(chat_id)}) == None:
        if re.search("[0-9]{1,4}", input_score):
            input_data.insert_one({"user_id": int(user_id), "chat_id": int(chat_id), "score": int(input_score), "user_at": str(user_at)})
            bot.reply_to(message, "Welcome to wordle league!")
            #if user is not found in query enter their new data
        else:
            bot.reply_to(message, "Incorrect score input. Please enter your score when entering \nthe league. If you have no score please enter 0.")
    else:
        bot.reply_to(message, "You are already in this league.")



@bot.message_handler(commands=["wordle"])
def wordle(message):
    input_data = cluster.wordle_db.user_data
    chat_id = message.chat.id
    user_id = message.from_user.id
    curr_score = input_data.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})

    if curr_score != None:
        if len(re.findall("[1-6]\/", message.text)) != 0:
            user_score = re.findall("[1-6]\/", message.text)
            user_score = re.findall("[1-6]", user_score[0])
            user_score = int(user_score[0])
            user_score = 6 - (user_score - 1)
            #extract the score using regex

            user_score += int(curr_score['score'])
            input_data.update_one({"user_id": int(user_id), "chat_id": int(chat_id)}, {"$set": {"score": user_score}})
            bot.reply_to(message, "Congrats Wordler your current score is " + str(user_score) + ".\n")
        elif len(re.findall("[X]\/", message.text)) != 0:
            bot.reply_to(message, "0 Score?. RIP.")
        else:
            bot.reply_to(message, "Score incorrectly formatted")
    else:
        bot.reply_to(message, "You are not currently in this league please join befor entering scores.")
    

@bot.message_handler(commands=["scoreboard"])
def scoreboard(message):
    chat_id = message.chat.id
    chat_data = cluster.wordle_db.user_data.find({"chat_id": int(chat_id)})
    scores = []
    names = []
    message_text = ""
    for user in chat_data:
        scores.append(user['score'])
        names.append(user['user_at'])
    #assign user values to lists for sorting
    for i in range(len(scores)):
    
        # Find the minimum element in remaining
        # unsorted array
        min_idx = i
        for j in range(i+1, len(scores)):
            if scores[min_idx] < scores[j]:
                min_idx = j
            
        # Swap the found minimum element with
        # the first element  
        scores[i], scores[min_idx] = scores[min_idx], scores[i]
        names[i], names[min_idx] = names[min_idx], names[i]
    #selection sort names and scores
    
    for i in range(len(scores)):
        score_index = i + 1
        if i != 0:
            if scores[i] == scores[i - 1]:
                score_index = i


        message_text += str(score_index) + ". " + str(names[i]) + ":    " + str(scores[i]) + " pts.\n"
            
    

    bot.reply_to(message, message_text)

@bot.message_handler(commands=["help"])
def help(message):
    bot.reply_to(message, (" Welcome to Wordle Bot for Telegram!\n" 
                    
                             
                          "Currently functioning commands are\n\n"
                          "/joinleague [score] (Enter your overall score for the current league following the joinleague command).\n\n"
                          "/wordle [Wordle Score] This is where you insert your scores for each day. This can just be your same old wordle copy and pasted from the site.\n\n"
                          "/scoreboard(Displays everyones scores in order)\n\n"
                          
                           ))
        



bot.infinity_polling()