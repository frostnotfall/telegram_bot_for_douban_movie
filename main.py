#!/usr/bin/env python3
# encoding: utf-8


"""
@Python version:3.6
@author: frostnotfall
@license: MIT License
@contact: frostnotfall@gmail.com
@software: douban_movie_tool
"""

import datetime
import logging
from functools import wraps

from flask import Flask, request
from telegram import (Bot, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup,
                      InlineQueryResultArticle, InputTextMessageContent, KeyboardButton, ParseMode,
                      ReplyKeyboardMarkup, Update, TelegramError)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Dispatcher, InlineQueryHandler,
                          Updater, MessageHandler, ChosenInlineResultHandler)

import funcs
import util
from config import host, token

# 使用 webhook 方式
app = Flask(__name__)
bot = Bot(token=token)
dispatcher = Dispatcher(bot, None)

# 使用轮询方式
# updater = Updater(token)
# dispatcher = updater.dispatcher

bot.setWebhook('https://{host}/{token}'.format(host=host, token=token))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


@app.route('/' + token, methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'


# decorater:不用每定义一个函数都要用handler以及add_handler
def command(handler, cmd=None, **kw):
    def decorater(func):
        def wrapper(*args, **kw):
            return func(*args, **kw)

        if cmd is None:
            func_hander = handler(func, **kw)
        else:
            func_hander = handler(cmd, func, **kw)
        dispatcher.add_handler(func_hander)
        return wrapper

    return decorater


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(*args, **kwargs):
        bot, update = args
        bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(bot, update, **kwargs)

    return command_func


# 命令：/start，入口，发送 customKeyboardButton
@command(CommandHandler, 'start')
@send_typing_action
def start(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + '使用机器人')

    button_list = [
        KeyboardButton(text="正在热映"),
        KeyboardButton(text="即将上映"),
        KeyboardButton(text="新片榜"),
        KeyboardButton(text="快捷搜索"),
        KeyboardButton(text="其它搜索方式(旧接口，可能不准确)"),
    ]
    reply_markup = ReplyKeyboardMarkup(util.build_menu(button_list, n_cols=2),
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="请根据下方按钮选择功能",
                     reply_markup=reply_markup)

    end_time = datetime.datetime.now()
    print("入口-执行时间:", end_time - start_time)


# “正在热映”功能，自定义的消息过滤方法，
@command(MessageHandler, util.CustomFilter('正在热映'))
@send_typing_action
def now_playing(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 获取电影列表')

    movie_list, movie_id_list = funcs.load()

    button_list = list()
    range_len_movie_list = range(len(movie_list))
    for i in range_len_movie_list:
        button_list.append(InlineKeyboardButton(movie_list[i], callback_data=movie_id_list[i]))
    reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=2))
    bot.send_message(chat_id=update.message.chat_id,
                     text="以下是正在热映的电影，请点击按钮查看详情，稍后会生成影评关键词",
                     reply_markup=reply_markup)

    end_time = datetime.datetime.now()
    print("正在热映-执行时间:", end_time - start_time)


# “新片榜”功能，自定义的消息过滤方法，发送 InlineKeyboardButton
@command(MessageHandler, util.CustomFilter('新片榜'))
@send_typing_action
def chart(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 使用新片榜')

    movie_list, movie_id_list = funcs.new_movies()
    range_len_movie_list = range(len(movie_list))
    button_list = list()

    for i in range_len_movie_list:
        button_list.append(InlineKeyboardButton(movie_list[i], callback_data=movie_id_list[i]))
    reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=2))

    bot.send_message(chat_id=update.message.chat_id,
                     text="以下是电影新片榜，请点击按钮查看详情",
                     reply_markup=reply_markup)

    end_time = datetime.datetime.now()
    print("新片榜-执行时间:", end_time - start_time)


# “即将上映”功能，自定义的消息过滤方法，发送 InlineKeyboardButton
@command(MessageHandler, util.CustomFilter('即将上映'))
@send_typing_action
def coming(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 使用即将上映')

    movie_list, movie_id_list = funcs.coming()
    range_len_movie_list = range(len(movie_list))
    button_list = list()

    for i in range_len_movie_list:
        button_list.append(InlineKeyboardButton(movie_list[i], callback_data=movie_id_list[i]))
    reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=2))

    bot.send_message(chat_id=update.message.chat_id,
                     text="以下是即将上映的电影，请点击按钮查看详情",
                     reply_markup=reply_markup)

    end_time = datetime.datetime.now()
    print("即将上映-执行时间:", end_time - start_time)


# “快捷搜索”功能
@command(MessageHandler, util.CustomFilter('快捷搜索'))
@send_typing_action
def shortcut_search(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 使用快捷搜索')

    button_list = list()
    button_list.append(InlineKeyboardButton('开始搜索',
                                            switch_inline_query_current_chat=''))

    reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=1))
    bot.send_message(chat_id=update.message.chat_id,
                     text="点击以下按钮，然后输入要搜索的电影、演员或导演",
                     reply_markup=reply_markup)

    end_time = datetime.datetime.now()
    print("快捷搜索-执行时间:", end_time - start_time)


# “其它搜索方式”功能，自定义的消息过滤方法
@command(MessageHandler, util.CustomFilter('其它搜索方式'))
@send_typing_action
def other_search(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="请输入要搜索的电影或演员\n"
                          "搜索格式：电影|演员搜索 电影|演员名称(中间以空格分隔)\n"
                          "例如，搜索电影：\n"
                          "`电影搜索 变形金刚`\n"
                          "搜索演员：\n"
                          "`演员搜索 姜文`",
                     parse_mode=ParseMode.MARKDOWN)


# “电影搜索”功能
@command(MessageHandler, util.CustomFilter('电影搜索'))
@send_typing_action
def movie_search(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 使用电影搜索')

    try:
        search_type, movie_name = update.message.text.split(' ', 1)
        movie_list, id_list = funcs.movie_search(movie_name)
        range_len_movie_list = range(len(movie_list))
        button_list = list()

        for i in range_len_movie_list:
            button_list.append(InlineKeyboardButton(movie_list[i], callback_data=id_list[i]))
        reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=2))

        bot.send_message(chat_id=update.message.chat_id,
                         text="请选择以下电影查看详情",
                         reply_markup=reply_markup)
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="请输入要搜索的电影\n"
                              "搜索格式：电影搜索 电影名称(中间以空格分隔)\n"
                              "例如：电影搜索 大黄蜂")

    end_time = datetime.datetime.now()
    print("电影搜索-执行时间:", end_time - start_time)


# “演员搜索”功能
@command(MessageHandler, util.CustomFilter('演员搜索'))
@send_typing_action
def actor_search(bot, update):
    start_time = datetime.datetime.now()

    user_name = update.message.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 使用演员搜索')

    try:
        search_type, actor_name = update.message.text.split(' ', 1)
        actor_list, actor_id_list = funcs.actor_search(actor_name)
        range_len_actor_list = range(len(actor_list))
        button_list = list()

        for i in range_len_actor_list:
            button_list.append(InlineKeyboardButton(actor_list[i],
                                                    callback_data=actor_id_list[i]))
        reply_markup = InlineKeyboardMarkup(util.build_menu(button_list, n_cols=2))

        bot.send_message(chat_id=update.message.chat_id,
                         text="请选择以下演员查看详情",
                         reply_markup=reply_markup)
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="请输入要搜索的演员\n"
                              "搜索格式：演员搜索 演员名称(中间以空格分隔)\n"
                              "例如：演员搜索 姜文")

    end_time = datetime.datetime.now()
    print("演员搜索-执行时间:", end_time - start_time)


# InlineKeyButton回调处理，生成电影详情
@command(CallbackQueryHandler, pattern=r'movie\s[0-9]+')
@send_typing_action
def movie_keyboard(bot, update):
    start_time = datetime.datetime.now()

    bot.answer_callback_query(callback_query_id=update.callback_query.id,
                              text="正在获取该电影的详细内容，请稍后")

    movie, id_ = update.callback_query.data.split()
    user_name = update.callback_query.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 查询电影，ID：' + id_)

    url, score = funcs.movie_info(id_)

    bot.send_message(chat_id=update.callback_query.message.chat_id,
                     text=url,
                     reply_markup=InlineKeyboardMarkup(util.build_menu(
                         [InlineKeyboardButton("生成影评词云",
                                               callback_data='comment_wordcloud ' + id_)],
                         n_cols=1)) if score != 0 else None)

    end_time = datetime.datetime.now()
    print("电影详情-执行时间:", end_time - start_time)


# InlineKeyButton回调处理，生成影评词云
@command(CallbackQueryHandler, pattern=r'comment_wordcloud\s[0-9]+')
@send_typing_action
def comment_wordcloud(bot, update):
    start_time = datetime.datetime.now()

    *_, id_ = update.callback_query.data.split()
    user_name = update.callback_query.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 生成影评词云，ID：' + id_)

    try:
        print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + "读取预缓存图片")
        bot.send_photo(chat_id=update.callback_query.message.chat_id,
                       photo=open("./img/" + id_ + '.jpg', 'rb'))
        bot.answer_callback_query(callback_query_id=update.callback_query.id)

    except FileNotFoundError:
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text='正在生成影评关键词，请稍后')

        print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') +
              '：电影ID：' + id_ + " 未缓存，正在请求URL获取评论")

        funcs.save_img(id_)
        bot.send_photo(chat_id=update.callback_query.message.chat_id,
                       photo=open("./img/" + id_ + '.jpg', 'rb'))

    end_time = datetime.datetime.now()
    print("生成影评词云-执行时间:", end_time - start_time)


# InlineKeyButton回调处理，生成演员详情
@command(CallbackQueryHandler, pattern=r'actor\s[0-9]+')
@send_typing_action
def actor_keyboard(bot, update):
    start_time = datetime.datetime.now()

    bot.answer_callback_query(callback_query_id=update.callback_query.id,
                              text='正在获取该演员的详细内容，请稍后')

    actor, id_ = update.callback_query.data.split()
    user_name = update.callback_query.from_user.username

    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 查询演员，ID：' + id_)

    url = funcs.actor_info(id_)

    bot.send_message(chat_id=update.callback_query.message.chat_id,
                     text=url)

    end_time = datetime.datetime.now()
    print("演员信息-执行时间:", end_time - start_time)


# InlineKeyButton回调处理，生成获奖情况
@command(CallbackQueryHandler, pattern=r'awards\s[a-z]+\s[0-9]+')
@send_typing_action
def comment_wordcloud(bot, update):
    start_time = datetime.datetime.now()

    *_, type_, id_ = update.callback_query.data.split()
    user_name = update.callback_query.from_user.username
    print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
          user_name + ' 生成获奖情况，类型：' + type_ + ' ID：' + id_)

    result = funcs.awards(type_, id_)

    bot.answer_callback_query(callback_query_id=update.callback_query.id,
                              text='正在获取该{}的详细内容，请稍后'.format(
                                  '电影' if type_ == 'movie' else '人'))

    bot.send_message(chat_id=update.callback_query.message.chat_id,
                     text='{}'.format(result),
                     parse_mode=ParseMode.HTML)

    end_time = datetime.datetime.now()
    print("生成获奖情况-执行时间:", end_time - start_time)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    print('webhook_info "%s" \n'
          'Update "%s" \n'
          'caused error "%s"\n',
          bot.get_webhook_info,
          update,
          error)


# Inline mode回调处理，生成Inline详情
@command(ChosenInlineResultHandler)
def inline_info(bot, update):
    start_time = datetime.datetime.now()

    callback_type, id_ = update.chosen_inline_result.result_id.split()
    user_name = update.chosen_inline_result.from_user.username

    if callback_type == 'movie':
        print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
              user_name + ' 查询电影，ID：' + id_)

        url, score = funcs.movie_info(id_)

        bot.send_message(chat_id=update.chosen_inline_result.from_user.id,
                         text=url,
                         reply_markup=InlineKeyboardMarkup(util.build_menu(
                             [InlineKeyboardButton("生成影评词云",
                                                   callback_data='comment_wordcloud ' + id_)],
                             n_cols=1)) if score != 0 else None)

    if callback_type == 'actor':
        print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S') + '：' + '用户 ' +
              user_name + ' 查询演员，ID：' + id_)

        url = funcs.actor_info(id_)

        bot.send_message(chat_id=update.chosen_inline_result.from_user.id,
                         text=url)

    end_time = datetime.datetime.now()

    print("Inline详情-执行时间:", end_time - start_time)


@command(InlineQueryHandler)
def inline_query(bot, update):
    """Handle the inline query."""
    name = update.inline_query.query
    print(name)

    suggest_result_list = funcs.subject_suggest(name)
    results = list()
    for suggest_result in suggest_result_list:
        result = InlineQueryResultArticle(
            id=suggest_result['type'] + ' ' + str(suggest_result['id']),
            title=suggest_result['title'],
            thumb_url=suggest_result['thumb_url'],
            description=suggest_result['description'],
            input_message_content=InputTextMessageContent(
                suggest_result['title']))
        results.append(result)

    bot.answer_inline_query(update.inline_query.id, results)


if __name__ == '__main__':
    dispatcher.add_error_handler(error)
    util.save_cookie()

    # 定时清除词云图片
    util.removal()

    # 轮询方式
    # updater.start_polling()

    # webhook 方式
    app.run(host='127.0.0.1',
            port=8443)

    # 预缓存正在热映中的电影的影评词云图片，默认不开启
    # util.preload()
