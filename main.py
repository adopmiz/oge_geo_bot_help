import telebot
from telebot import types
import random
from questions_data import (
    TASKS_13_SALINE, TASKS_13_PRESSURE, TASKS_13_TEMPERATURE,
    TASKS_23_DEMOGRAPHY,
    MOTIVATION_WRONG, MOTIVATION_RIGHT,
    THEORY_13, THEORY_23
)

API_TOKEN = '8783036380:AAHCkDUl_U3L_8sSiVrZVSC7onQiyJuiHxs'

bot = telebot.TeleBot(API_TOKEN)

user_states = {}


def get_task_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🌊 №13. Соленость", callback_data="start_task_13_saline"),
        types.InlineKeyboardButton("⛰️ №13. Давление", callback_data="start_task_13_pressure"),
        types.InlineKeyboardButton("🌡️ №13. Температура", callback_data="start_task_13_temperature"),
        types.InlineKeyboardButton("👥 №23. Демография", callback_data="start_task_23_demography"),
        types.InlineKeyboardButton("📚 Теория (№13)", callback_data="theory_13"),
        types.InlineKeyboardButton("📚 Теория (№23)", callback_data="theory_23")
    )
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]

    bot.send_message(
        chat_id,
        "🌍 *Привет! Я твой помощник по подготовке к ОГЭ по географии!*\n\n"
        "Я помогу отработать вычислительные навыки для заданий №13 и №23.\n\n"
        "Выбери, какое задание хочешь порешать:",
        reply_markup=get_task_keyboard(),
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('start_task_'))
def start_quiz_callback(call):
    chat_id = call.message.chat.id
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass

    task_key = call.data.replace('start_task_', '')
    
    if task_key == '13_saline':
        questions = TASKS_13_SALINE.copy()
        task_name = "№13. Соленость воды"
    elif task_key == '13_pressure':
        questions = TASKS_13_PRESSURE.copy()
        task_name = "№13. Атмосферное давление"
    elif task_key == '13_temperature':
        questions = TASKS_13_TEMPERATURE.copy()
        task_name = "№13. Температура воздуха"
    elif task_key == '23_demography':
        questions = TASKS_23_DEMOGRAPHY.copy()
        task_name = "№23. Демографические расчеты"
    else:
        bot.send_message(chat_id, "❌ Неизвестный тип задания.")
        return

    if len(questions) < 10:
        bot.send_message(
            chat_id,
            f"Извините, в базе пока только {len(questions)} вопросов для {task_name}. "
            f"Нужно минимум 10 вопросов."
        )
        return

    random.shuffle(questions)
    quiz_questions = questions.copy()

    user_states[chat_id] = {
        'questions': quiz_questions,
        'index': 0,
        'score': 0,
        'last_msg_id': None,
        'task_name': task_name,
        'task_key': task_key
    }

    send_next_question(chat_id)


def send_next_question(chat_id):
    if chat_id not in user_states:
        bot.send_message(chat_id, "Кажется, я забыл, на чем мы остановились. Нажми /start для начала.")
        return

    user_data = user_states[chat_id]
    index = user_data['index']
    questions = user_data['questions']
    task_name = user_data['task_name']

    if index >= len(questions):
        score = user_data['score']
        total = len(questions)
        bot.send_message(
            chat_id,
            f"🎉 *Решение завершено!* 🎉\n\n"
            f"📊 Твой результат: **{score} из {total}**.\n"
            f"📈 Процент правильных ответов: **{score * 100 // total}%**\n\n"
            f"Отличная работа! Можешь начать заново с помощью команды /start.",
            parse_mode='Markdown'
        )
        del user_states[chat_id]
        return

    question_data = questions[index]
    question_text = (
        f"📌 *{task_name}*\n"
        f"**Вопрос {index + 1}/{len(questions)}:**\n\n"
        f"{question_data['question']}"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for option in question_data['options']:
        callback_data = f"answer_{index}_{option}"
        keyboard.add(types.InlineKeyboardButton(option, callback_data=callback_data))
    keyboard.add(types.InlineKeyboardButton("🏠 Меню", callback_data="stop_quiz"))

    msg = bot.send_message(chat_id, question_text, reply_markup=keyboard, parse_mode='Markdown')
    user_states[chat_id]['last_msg_id'] = msg.message_id


@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def handle_answer_callback(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states:
        bot.send_message(chat_id, "Решение уже завершено или не начиналось. Нажмите /start.")
        return

    user_data = user_states[chat_id]
    index = user_data['index']

    if call.message.message_id != user_data.get('last_msg_id'):
        bot.answer_callback_query(call.id, "Вы отвечаете на старый вопрос!")
        return

    parts = call.data.split('_', 2)
    q_index_str = parts[1]
    user_answer = parts[2]

    if int(q_index_str) != index:
        bot.answer_callback_query(call.id, "Вы отвечаете на старый вопрос! Смотрите последнее сообщение.")
        return

    current_question = user_data['questions'][index]
    correct_answer = current_question['answer']

    if user_answer == correct_answer:
        user_data['score'] += 1
        motivation = random.choice(MOTIVATION_RIGHT)

        choice_keyboard = types.InlineKeyboardMarkup()
        choice_keyboard.add(types.InlineKeyboardButton("📋 Показать решение", callback_data=f"solution_{index}"))
        choice_keyboard.add(types.InlineKeyboardButton("➡️ Продолжить решать", callback_data="next_question"))
        choice_keyboard.add(types.InlineKeyboardButton("🏠 Меню", callback_data="stop_quiz"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"{call.message.text}\n\n✅ {motivation}",
            parse_mode='Markdown',
            reply_markup=None
        )

        msg_choice = bot.send_message(chat_id, "Что дальше?", reply_markup=choice_keyboard)
        user_states[chat_id]['last_msg_id'] = msg_choice.message_id

    else:
        motivation = random.choice(MOTIVATION_WRONG)

        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"**Вопрос {index + 1}:**\n{current_question['question']}\n\n❌ {motivation} Попробуй еще раз!",
                parse_mode='Markdown',
                reply_markup=call.message.reply_markup
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" not in str(e):
                pass

        bot.answer_callback_query(call.id, text="Неверно! Попробуй еще раз.")


@bot.callback_query_handler(func=lambda call: call.data == 'next_question')
def next_question_callback(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states:
        return

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass

    user_states[chat_id]['index'] += 1
    send_next_question(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('solution_'))
def show_solution_callback(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states:
        bot.answer_callback_query(call.id, "Решение завершено. Нажмите /start.")
        return

    try:
        index_str = call.data.split('_')[-1]
        index = int(index_str)

        question_data = user_states[chat_id]['questions'][index]
        solution_text = question_data.get('solution', 'Решение пока не добавлено.')

        if len(solution_text) > 4000:
            solution_text = solution_text[:4000] + "\n\n... (текст обрезан)"

        continue_keyboard = types.InlineKeyboardMarkup()
        continue_keyboard.add(types.InlineKeyboardButton("➡️ Продолжить решать", callback_data="next_question"))
        continue_keyboard.add(types.InlineKeyboardButton("🏠 Меню", callback_data="stop_quiz"))

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except telebot.apihelper.ApiTelegramException:
            pass

        try:
            msg_solution = bot.send_message(
                chat_id,
                f"📖 *Решение:*\n\n{solution_text}",
                parse_mode='Markdown',
                reply_markup=continue_keyboard
            )
            user_states[chat_id]['last_msg_id'] = msg_solution.message_id
        except telebot.apihelper.ApiTelegramException as e:
            if "parse" in str(e).lower() or "markdown" in str(e).lower():
                msg_solution = bot.send_message(
                    chat_id,
                    f"Решение:\n{solution_text}",
                    reply_markup=continue_keyboard
                )
                user_states[chat_id]['last_msg_id'] = msg_solution.message_id
            else:
                raise

        bot.answer_callback_query(call.id)
    except (ValueError, KeyError, IndexError) as e:
        bot.answer_callback_query(call.id, "Ошибка при загрузке решения. Попробуйте еще раз.")
        bot.send_message(chat_id, "Произошла ошибка. Нажмите /start для начала нового решения.")
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка.")
        bot.send_message(chat_id, f"Ошибка: {str(e)}. Нажмите /start для начала нового решения.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('theory_'))
def show_theory_callback(call):
    chat_id = call.message.chat.id
    task_type = call.data.split('_')[-1]

    if task_type == '13':
        theory_text = THEORY_13
        task_name = "Задание №13 (Расчетные задачи)"
    else:
        theory_text = THEORY_23
        task_name = "Задание №23 (Демографические расчеты)"

    back_keyboard = types.InlineKeyboardMarkup()
    back_keyboard.add(types.InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_menu"))

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"📚 *{task_name}*\n\n{theory_text}",
            parse_mode='Markdown',
            reply_markup=back_keyboard
        )
    except telebot.apihelper.ApiTelegramException as e:
        try:
            bot.send_message(
                chat_id=chat_id,
                text=f"{task_name}\n\n{theory_text}",
                reply_markup=back_keyboard
            )
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'stop_quiz')
def stop_quiz_callback(call):
    chat_id = call.message.chat.id

    if chat_id in user_states:
        user_data = user_states[chat_id]
        index = user_data.get('index', 0)
        score = user_data.get('score', 0)

        del user_states[chat_id]

        try:
            bot.answer_callback_query(call.id, f"Решение остановлено. Результат: {score} из {index}")
        except:
            pass

        try:
            bot.send_message(
                chat_id,
                f"⏸ *Решение остановлено!*\n\n"
                f"Твой промежуточный результат: **{score} из {index}** решенных вопросов.\n\n"
                f"Можешь продолжить позже или начать новое решение.",
                parse_mode='Markdown'
            )
        except:
            pass
    else:
        try:
            bot.answer_callback_query(call.id, "Решение уже завершено")
        except:
            pass

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass

    bot.send_message(
        chat_id,
        "🌍 *Привет! Я твой помощник по подготовке к ОГЭ по географии!*\n\n"
        "Выбери, какое задание хочешь порешать:",
        reply_markup=get_task_keyboard(),
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu_callback(call):
    chat_id = call.message.chat.id
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass
    bot.send_message(
        chat_id,
        "🌍 *Привет! Я твой помощник по подготовке к ОГЭ по географии!*\n\n"
        "Выбери, какое задание хочешь порешать:",
        reply_markup=get_task_keyboard(),
        parse_mode='Markdown'
    )


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    if message.chat.id not in user_states:
        bot.send_message(message.chat.id, "Нажмите /start, чтобы начать подготовку к ОГЭ по географии!")



import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

Thread(target=run_health_server, daemon=True).start()


if __name__ == '__main__':
    print("🤖 Бот для подготовки к ОГЭ по географии запущен...")
    bot.infinity_polling()
