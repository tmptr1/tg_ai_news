# from google import genai  # pip install google-genai
from openai import OpenAI
import telebot
from bs4 import BeautifulSoup

import time
import os
from os import environ
import re
from dotenv import load_dotenv
import requests
import datetime
import json
import logging
from logging.handlers import RotatingFileHandler

from config import times, chat_id

load_dotenv()

logger = logging.getLogger('logs.log')
logger.setLevel(21)
formater = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

f_handler = RotatingFileHandler('logs.log', maxBytes=5 * 1024 * 1024, backupCount=2, errors='ignore',)
f_handler.setFormatter(formater)
s_handler = logging.StreamHandler()
s_handler.setFormatter(formater)
logger.addHandler(f_handler)
logger.addHandler(s_handler)

bot = telebot.TeleBot(environ.get('TG_TOKEN'))


if not os.path.exists('last_send.txt'):
    with open('last_send.txt', 'w') as f:
        f.write(f"{datetime.datetime(2025, 1,1,0,0,0).strftime('%Y.%m.%d %H:%M:%S')}")

headers = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

news_limit = 15

def openrouter_request(msg):
    client = OpenAI(base_url=environ.get('AI_REF'), api_key=environ.get('AI_KEY'))
    res = client.chat.completions.create(
        model='tngtech/deepseek-r1t2-chimera:free',
        messages=[
            {'role': 'user',
             'content': msg}
        ])
    return res.choices[0].message.content

# Выбери три новости, которые потенциально больше понравятся человеку, который следит за спортом. Вот массив новостных заголовков:

# def test_genai():
#     client = genai.Client(api_key='AIzaSyBxTJYl0zFXhByxEKbB-utqYt7fHw1CcQI')
#     res = client.models.generate_content(model='gemini-3-flash-preview', contents='Максимальное количество символов в запросе к google-genai, gemini-3-flash-preview через python (метод generate_content) с бесплатным тарифом')
#     print(res.text)


# def main():



# @bot.message_handler(content_types=['text'])
# def get_reply_chat_id(message):
#     print(message)

# @bot.message_handler(commands=['start'])
# @bot.message_handler(content_types=['text'])
# def start_command(message):
# #     bot.send_message(message.chat.id, f"Привет, твой ID: {message.chat.id}")
#     # print(message.chat.id)
#     print(message)

def get_sports_ru_news(start_at):
    news = dict()
    try:
        url = r"https://www.sports.ru/news/top/"
        res = requests.get(url=url, headers=headers, timeout=60)
        soup = BeautifulSoup(res.text, 'lxml')
        # print(soup)
        news_p_elements = soup.find("li", class_="panel active-panel").find("div", class_="short-news").find_all("p")
        for id, n in enumerate(news_p_elements):
            if id >= news_limit:
                break
            try:
                post_time = n.find('span', class_='time').text.strip()

                if post_time < f"{start_at}":
                    continue

                post_title = n.find('a', class_='short-text').get('title') or n.find('a', class_='short-text').text.strip()
                post_ref = n.find('a', class_='short-text').get('href', None)

                if len(post_title) == 0 or len(post_ref) == 0:
                    continue

                if not post_ref.startswith('/'):
                    # print('Incorrect REF', post_ref)
                    continue

                news[post_title] = f"https://www.sports.ru{post_ref}"
                    # print(f"[{post_time}] {post_text}", end='\n')
                    # print(f"ref: {post_ref}")
                    # print(n, end='\n')
                    # print('='*20)

            except Exception as n_ex_1:
                logger.error('n_ex:', exc_info=n_ex_1)
                # raise n_ex_1

        # print(news)
        # print(len(news))
        # print()
        logger.log(21, f"{url} [{len(news)}]")

        for n in news:
            logger.log(21, f"{n} ({news[n]})")
        # print('='*30)
        logger.log(21, f"===============")

    except Exception as get_news_ex:
        logger.error('get_news_ex:', exc_info=get_news_ex)
        # raise get_news_ex
        news = None

    return news


def get_championat_com_rss_news(start_at):
    news = dict()
    try:
        url = r'https://www.championat.com/rss/news/'
        res = requests.get(url=url, headers=headers, timeout=60)
        # print(res.status_code)
        soup = BeautifulSoup(res.content, 'xml')
        news_items = soup.find_all('item')
        for id, n in enumerate(news_items):
            if id >= news_limit:
                break
            try:
                row_post_time = n.find('pubDate').text.strip()
                post_time = row_post_time.split()[-2]
                post_day = row_post_time.split()[1]
                if post_time < f"{start_at}" or int(post_day) != datetime.datetime.now().day:
                    continue

                post_title = n.find('title').text.strip()
                post_ref = n.find('link').text.strip()

                if len(post_title) == 0 or len(post_ref) == 0:
                    continue

                # print(f"[{post_time}] {post_title} ({post_ref})")
                news[post_title] = post_ref

            except Exception as n_ex_2:
                logger.error('n_ex_2:', exc_info=n_ex_2)
                # raise n_ex_2

        # print(news)
        # print(len(news))
        # print()
        #
        logger.log(21, f"{url} [{len(news)}]")
        for n in news:
            logger.log(21, f"{n} ({news[n]})")
        # print('='*30)
        logger.log(21, '===============')

    except Exception as get_championat_com_rss_news_ex:
        logger.error('get_championat_com_rss_news_ex:', exc_info=get_championat_com_rss_news_ex)
        # raise get_championat_com_rss_news_ex
        news = None

    return news

def get_sport24_ru_news(start_at):
    news = dict()
    try:
        url = r"https://sport24.ru/mobile-news"
        res = requests.get(url=url, headers=headers, timeout=60)
        # print(res.text)
        soup = BeautifulSoup(res.text, 'lxml')
        # print(soup.text)
        # refs = soup.find('main')
        # print(refs)
        # return
        top_news = soup.find('script', id='app-data').text.strip()
        # print(top_news)
        items = json.loads(top_news)['model']['topNews']['items']

        for id, n in enumerate(items):
            if id >= news_limit:
                break
            try:
                post_time = datetime.datetime.fromtimestamp(int(n['publishDate'])/1000).time()
                # post_time = f"{post_time.hour}:{post_time.minute}"
                if f"{post_time}" < f"{start_at}":
                    print(f"{post_time}", f"{start_at}")
                    continue

                post_title = str(n['title']).strip()
                post_ref = str(n['urn']).strip()
                if len(post_title) == 0 or len(post_ref) == 0:
                    continue
                # print(post_title)
                # post_ref = soup.find('span', string=str(n['title']).replace(' ', ''))#.a.get('href')
                # print(post_ref) # https://sport24.ru/football/news-
                # print(f"[{post_time.hour}:{post_time.minute}] {post_title} ({post_ref})")
                news[post_title] = f"https://sport24.ru/football/news-{post_ref}"

            except Exception as n_ex_3:
                logger.error('n_ex_3:', exc_info=n_ex_3)
                # raise n_ex_3

        logger.log(21, f"{url} [{len(news)}]")
        for n in news:
            logger.log(21, f"{n} ({news[n]})")
        # print('='*30)
        logger.log(21, '==================')

    except Exception as get_sport24_ru_news_ex:
        logger.error('get_sport24_ru_news_ex:', exc_info=get_sport24_ru_news_ex)
        # raise get_sport24_ru_news_ex
        news = None

    return news


# def get_sport_express_ru_rss_news(start_at):
#     news = dict()
#     try:
#         url = r"https://www.sport-express.ru/services/materials/news/se/"
#         res = requests.get(url=url, headers=headers, timeout=60)
#         # print(res.status_code)
#         soup = BeautifulSoup(res.content, 'xml')
#
#         news_items = soup.find_all('item')
#         for n in news_items:
#             try:
#                 post_time = n.find('pubDate').text.strip()
#                 post_time = post_time.split()[-2]
#                 if post_time < f"{start_at}":
#                     continue
#
#                 post_title = n.find('title').text.strip()
#                 post_ref = n.find('link').text.strip()
#
#                 if len(post_title) == 0 or len(post_ref) == 0:
#                     continue
#
#                 print(f"[{post_time}] {post_title} ({post_ref})")
#                 news[post_title] = post_ref
#
#             except Exception as n_ex_4:
#                 logger.error('n_ex_4:', exc_info=n_ex_4)
#                 raise n_ex_4
#
#         # print(news)
#         # print(len(news))
#         # print()
#         #
#         # for n in news:
#         #     print(f"{n} ({news[n]})")
#
#     except Exception as get_sport_express_ru_news_rss_ex:
#         logger.error('get_sport_express_ru_news_rss_ex:', exc_info=get_sport_express_ru_news_rss_ex)
#         raise get_sport_express_ru_news_rss_ex
#         news = None
#
#     return news


def get_rssexport_rbc_ru_rss_news(start_at):
    news = dict()
    try:
        url = r"https://rssexport.rbc.ru/sport/news/30/base.rss"
        res = requests.get(url=url, headers=headers, timeout=60)
        # print(res.status_code)
        soup = BeautifulSoup(res.content, 'xml')

        news_items = soup.find_all('item')

        for id, n in enumerate(news_items):
            if id >= news_limit:
                break
            try:
                row_post_time = n.find('pubDate').text.strip()
                post_time = row_post_time.split()[-2]
                post_day = row_post_time.split()[1]
                if post_time < f"{start_at}" or int(post_day) != datetime.datetime.now().day:
                    continue

                post_title = n.find('title').text.strip()
                post_ref = n.find('link').text.strip()

                if len(post_title) == 0 or len(post_ref) == 0:
                    continue

                # print(f"[{post_time}] {post_title} ({post_ref})")
                news[post_title] = post_ref

            except Exception as n_ex_5:
                logger.error('n_ex_5:', exc_info=n_ex_5)
                # raise n_ex_5

        # print(news)
        # print(len(news))
        # print()
        #
        logger.log(21, f"{url} [{len(news)}]")
        for n in news:
            logger.log(21, f"{n} ({news[n]})")
        # print('='*30)
        logger.log(21, '===================')

    except Exception as get_rssexport_rbc_ru_rss_news_ex:
        logger.error('get_rssexport_rbc_ru_rss_news_ex:', exc_info=get_rssexport_rbc_ru_rss_news_ex)
        # raise get_rssexport_rbc_ru_rss_news_ex
        news = None

    return news



def get_news(start_at):
    news = dict()

    sites = [lambda: get_sports_ru_news(start_at), lambda: get_championat_com_rss_news(start_at),
             lambda: get_sport24_ru_news(start_at), lambda: get_rssexport_rbc_ru_rss_news(start_at)]

    for n in sites:
        for i in range(1, 6):
            new_news = n()
            if new_news is not None:
                news.update(new_news)
                break
            logger.log(21, f'Попытка {i}')
            time.sleep(45)

    # news.update(get_sports_ru_news(start_at))
    # news.update(get_championat_com_rss_news(start_at))
    # news.update(get_sport24_ru_news(start_at))
    # news.update(get_rssexport_rbc_ru_rss_news(start_at))

    return news


def create_top_news_post(start_at):
    news = get_news(start_at)
    if not news:
        logger.log(21, f"Не удалось получить новости!")
        return False

    if len(news) < 5:
        logger.log(21, f"Новостей меньше 5!")
        return False

    try:
        logger.log(21, f"Всего новостей: {len(news)}")
        ai_request = f"""Нужно выбрать пять новостей из списка news которые потенциально больше понравятся человеку, следящему за новостями в мире спорта. Напиши индексы выбранных новостей в виде списка на пайтон (отсчёт индексов начинается с 0). Вот пример того, что должно быть в твоём ответе: selected = [0, 1, 2, 3, 4] . А вот список новостей: news = {[*news.keys()]}"""
        logger.log(21, ai_request)
        res = openrouter_request(ai_request)
        logger.log(21, res)
        # res = "```python selected = [5, 10, 58, 19, 27]```"

        indexes = re.search(r'\[.+]', res).group()
        indexes = indexes[1:-1]
        indexes = [int(i) for i in str(indexes).split(',')]
        logger.log(21, f"{indexes=}")

        if len(indexes) != 5:
            logger.log(21, f"Не удалось получить indexes из запроса [1] к ai")
            return False

        selected_news = dict()
        for id, k in enumerate(news):
            if id in indexes:
                selected_news[k] = news[k]
            # print(news[i])

        logger.log(21, f"{selected_news=}")

        ai_request_2 = f"""Есть python список с заголовоками новостей, нужно написать для каждой новости небольшое резюме на русском языке (2-5 предложений), первое предложение будет использоваться как новый заголовок и должно заинтересовывать читателя. Верни новый python список уже с резюме. Вот пример того, что нужно вернуть: result = ["Описание новости 1", "Описание новости 2"] . В самих текстах резюме не должны содержаться двойные кавычки (") и переносы строк. А вот изначальный список c заголовками новостей: {[*selected_news.keys()]}"""
        logger.log(21, ai_request_2)
        res = openrouter_request(ai_request_2)
        logger.log(21, res)
        # result = [
        # "Бразильский полузащитник ..." ,

        raw_answers = re.findall(r'".+"', res)
        if len(raw_answers) != 5:
            logger.log(21, f"Не удалось получить raw_answers из запроса [2] к ai")
            return False

        answers = []
        for a in raw_answers:
            # sentences = str(a[1:-1]).split('.')
            sentences = re.split(r"[\\.!]", str(a[1:-1]))
            sentences[0] = f"<b>{sentences[0]}</b>\n"
            sentences[1] = sentences[1].strip()
            answer = f"{sentences[0]}{'.'.join(sentences[1:])}"
            answers.append(answer)

        tg_post = ""
        for id, ref in enumerate(selected_news.values()):
            tg_post += f"""📍 {answers[id]}\n🔗<a href="{ref}">Источник</a>\n\n"""

        logger.log(21, 'Тг пост:')
        logger.log(21, tg_post)
        # print(tg_post)
        for i in range(5):
            try:
                bot.send_message(chat_id=chat_id, text=tg_post, parse_mode='HTML', disable_web_page_preview=True, timeout=100)
                return True
            except Exception as tg_send_ex:
                logger.error('tg_send_ex:', exc_info=tg_send_ex)
            time.sleep(60)

    except Exception as create_top_news_post_ex:
        logger.error('create_top_news_post_ex:', exc_info=create_top_news_post_ex)

    return False

def main():
    # start_at = datetime.time(0, 0)
    # get_news(start_at)
    # return

    wait_sec = 15
    while True:
        try:
            time_now = datetime.datetime.now()
            for t in times:
                # print(t)
                # if time_now.hour == t.hour and time_now.minute == t.minute:
                send_time = datetime.datetime(time_now.year, time_now.month, time_now.day, t.hour, t.minute)
                if time_now > send_time and (time_now - send_time).seconds / 60 < 3:  # время отправки + 3 мин
                    # print(f"+ Время {t}")
                    with open('last_send.txt', 'r') as f:
                        last_time = datetime.datetime.strptime(f.read(), '%Y.%m.%d %H:%M:%S')
                        if last_time.date() == time_now.date():
                            start_at = last_time.time()
                        else:
                            start_at = datetime.time(0,0)
                        print('+ check', start_at)
                        if (time_now - last_time).seconds / 60 > 10 or last_time.date() != time_now.date():  # если отправлялось больше 10 мин назад
                            if create_top_news_post(start_at):
                            #     print('try to create a post')
                                with open('last_send.txt', 'w') as f:
                                    f.write(f"{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')}")


                    # time.sleep(60)
                # else:
                    # print('-', t)
        except Exception as loop_ex:
            logger.error('loop_ex:', exc_info=loop_ex)
        time.sleep(wait_sec)



if __name__ == '__main__':
    # bot.infinity_polling()
    # n = get_rssexport_rbc_ru_rss_news('01:48:24')
    # print(n)
    # if n is not None:
    #     print('net')
    # print('end')

    logger.log(21, 'start app')
    main()

#     res = """Вот результирующий список с краткими резюме для каждой новости:
#
# ```python
# result = [
#     "Даниил Медведев совершил невероятный камбэк в матче против Марожана на Australian Open, выиграв три сета подряд после 0:2. Российский теннисист продемонстрировал характер, выйдя в следующий круг турнира. В это же время Андрей Рублев не смог одолеть Франсиско Серундоло, завершив выступление.",
#     "Унаи Эмери вошел в историю, став первым тренером с 100 матчами в Лиге Европы! Испанский специалист достиг рубежа в матче против своего бывшего клуба. Этот рекорд подчеркивает его многолетний опыт в турнирах УЕФА.",
#     "Хамзат Чимаев прокомментировал смонтированное видео фанатов, где он проигрывает Топурии. Боец отметил, что даже в фантазиях не представляет такого исхода. Чимаев подчеркнул уверенность в своих силах при реальной встрече.",
#     "Лыжник Сергей Тихонов отказался от приглашения на Олимпиаду-2026 в качестве почетного гостя. Он объяснил решение нежеланием легитимизировать европейских организаторов. Спортсмен добавил, что не хочет быть частью их шоу.",
#     "Локомотив сохранил ключевого игрока, продлив контракт с двукратным обладателем Кубка Гагарина. Клуб не раскрывает имя хоккеиста, но подчеркивает его важность для команды. Соглашение укрепляет состав перед новым сезоном КХЛ."
# ]
# ```"""
#     raw_answers = re.findall(r'".+"', res)
#     answers = []
#     for a in raw_answers:
#         sentences = re.split(r"[\\.!]", str(a[1:-1]))
#         sentences[0] = f"<b>{sentences[0]}</b>\n"
#         sentences[1] = sentences[1].strip()
#         answer = f"{sentences[0]}{'.'.join(sentences[1:])}"
#         answers.append(answer)
#
#     selected_news = {
#         'Даниил Медведев отыгрался с 0:2 по сетам в матче с Фабианом Марожаном в третьем круге Australian Open, Андрей Рублев уступил Франсиско Серундоло.': 'https://www.sports.ru/tennis/1117049373-australian-open-2026-muzhchiny-rezultaty-23-yanvarya.html',
#         'Унаи Эмери стал первым тренером со 100 матчами в Лиге Европы': 'https://www.championat.com/football/news-6328036-unai-emeri-stal-pervym-trenerom-so-100-matchami-v-lige-evropy.html',
#         '«Даже в своих мечтах не смог бы». Чимаев — о видео фанатов, где Топурия победил Хамзата': 'https://www.championat.com/boxing/news-6328182-dazhe-v-svoih-mechtah-ne-smog-by-chimaev-o-video-fanatov-gde-topuriya-pobedil-hamzata.html',
#         'Тихонова пригласили почетным гостем на Олимпиаду-2026: «Я отказался\xa0— не надо смотреть на европейских клоунов»': 'https://sport24.ru/football/news-818856-tikhonova-priglasili-pochetnym-gostem-na-olimpiadu-2026-ya-otkazalsya-ne-nado-smotret-na-yevropeyskikh-klounov',
#         '«Локомотив» продлил контракт с двукратным обладателем Кубка Гагарина': 'https://sportrbc.ru/news/6973488c9a79476f91199850'}
#     tg_post = ""
#     for id, ref in enumerate(selected_news.values()):
#         tg_post += f"""📢 {answers[id]}\n🔗<a href="{ref}">Источник</a>\n\n"""
#     print(tg_post)

    # t1 = datetime.time(hour=12, minute=53)
    # # t2 = datetime.time(hour=12, minute=25)
    # # print(t1 > t2)
    # now = datetime.datetime.now()
    # send_time = datetime.datetime(now.year, now.month, now.day, t1.hour, t1.minute)
    # last_send = datetime.datetime.strptime('2026.01.23 12:40:53', '%Y.%m.%d %H:%M:%S')
    #
    # print(now > send_time, (now - send_time).seconds/60, (now - last_send).seconds/60)
    # if now > send_time and (now - send_time).seconds/60 < 3: # время отправки + 3 мин
    #     if (now - last_send).seconds/60 > 10: # если отправлялось больше 10 мин назад
    #         print('send')
    #     else:
    #         print('dont send 2')
    # else:
    #     print('dont send')
    # print(send_time < now)
    # diff = (now-send_time).seconds/60
    # print(diff)


    # news = get_news()
    # print(news)
    # news = {'Полузащитник сборной России  Арсен Захарян  входит в число игроков, которые могут покинуть «Реал Сосьедад».': 'https://www.sports.ru/football/1117049420-zaxaryan-mozhet-pokinut-real-sosedad-xavbek-ne-vxodit-v-plany-mataracz.html', 'В регулярном чемпионате НХЛ « Вегас » сыграет с « Бостоном », « Каролина » примет « Чикаго », « Питтсбург » встретится с «Эдмонтоном», « Миннесота » будет противостоять «Детройту».': 'https://www.sports.ru/hockey/1117048778-nxl.html', 'Вендел  пропустил 72 дня сборов за время выступлений за « Зенит ».': 'https://www.sports.ru/football/1117049397-vendel-propustil-72-dnya-sborov-za-vremya-vystuplenij-za-zenit.html', 'В 7-м туре Лиги Европы в четверг « Фенербахче » дома уступил « Астон Вилле » (0:1), ПАОК Федора Чалова и Магомеда Оздоева на своем поле выиграл у « Бетиса » (2:0), а « Рома » играет со « Штутгартом » в Риме.': 'https://www.sports.ru/football/1117048767-liga-evropy-aston-villa-protiv-fenerbaxche-paok-chalova-i-ozdoeva-sygr.html', '« Трактор » хотел обменять форварда  Джоша Ливо  в «Ак Барс» на нападающего\xa0  Дмитрия Яшкина , но получил отказ.': 'https://www.sports.ru/hockey/1117049360-traktor-xotel-obmenyat-livo-na-yashkina-ak-bars-otkazalsya.html', 'Главный тренер « Зенита »\xa0 Сергей Семак  высказался об опозданиях Вендела на сборы.': 'https://www.sports.ru/football/1117049363-semak-o-pozdnix-priezdax-vendela-na-sbory-zenita-k-sozhaleniyu-chelove.html', 'Российским спортсменам будет разрешено общаться со СМИ и\xa0принимать участие в пресс-конференциях в случае завоевания медалей на Олимпиаде-2026 в Италии.': 'https://www.sports.ru/figure-skating/1117049289-rossijskie-sportsmeny-smogut-obshhatsya-so-smi-na-olimpiade-2026.html', 'В FONBET КХЛ « Авангард » победил « Автомобилист » (2:1 ОТ), « Металлург » проиграл « Сибири » (1:2),\xa0ЦСКА выиграл у «Барыса» (1:0),\xa0 СКА  уступил « Спартаку » (1:2), « Торпедо » разгромило « Шанхай » (7:2).': 'https://www.sports.ru/hockey/1117048452-kxl.html', 'СКА проиграл «Спартаку» – 1:2. ВидеоСпортс’’ показывал матч Fonbet КХЛ': 'https://www.sports.ru/hockey/1117048628-ska-sygraet-so-spartakom-videosports-pokazhet-match-fonbet-kxl.html', 'Француз Эрик Перро победил в короткой индивидуальной гонке на этапе Кубка мира по биатлону в Нове-Место.': 'https://www.sports.ru/biathlon/1117048282-kubok-mira-korotkaya-individualnaya-gonka-botn-startuet-38-m-dzhakomel.html', 'Бывший полузащитник сборной России\xa0Александр Мостовой прокомментировал результаты\xa0 Доменико Тедеско  на посту главного тренера «Фенербахче».': 'https://www.sports.ru/football/1117049313-mostovoj-ob-uspexe-tedesko-v-fenerbaxche-ya-ne-udivlen-posmotrite-kako.html', 'Игрок сборной России по футболу слепых Андрей Куклин будет бить пенальти за медиаклуб «Альтерон» на новом турнире Напике.': 'https://www.sports.ru/mediafootball/1117049184-igrok-sbornoj-rossii-po-futbolu-slepyx-kuklin-budet-bit-penalti-za-med.html', 'Результаты матчей МХЛ на 22 января 2026 года': 'https://www.championat.com/hockey/news-6327612-rezultaty-matchej-mhl-na-22-yanvarya-2026-goda.html', 'Тренер «Шанхая» Лав: мне абсолютно всё равно, какой у нас сейчас баланс побед и поражений': 'https://www.championat.com/hockey/news-6327626-trener-shanhaya-lav-mne-absolyutno-vsyo-ravno-kakoj-u-nas-sejchas-balans-pobed-i-porazhenij.html', '«Мне ещё многому предстоит научиться». Швёнтек — о трудностях топовых теннисистов': 'https://www.championat.com/tennis/news-6327618-mne-eschyo-mnogomu-predstoit-nauchitsya-shvyontek-o-trudnostyah-topovyh-tennisistov.html', 'Результаты матчей ВХЛ на 22 января 2026 года': 'https://www.championat.com/hockey/news-6327606-rezultaty-matchej-vhl-na-22-yanvarya-2026-goda.html', 'FURIA обыграла HEROIC и вышла в полуфинал BLAST Bounty Winter по CS 2': 'https://www.championat.com/cybersport/news-6327624-furia-obygrala-heroic-i-vyshla-v-polufinal-blast-bounty-winter-po-cs-2.html', 'Охотюк прокомментировал встречу с «Барысом», где защитник ЦСКА забил победный гол': 'https://www.championat.com/hockey/news-6327622-ohotyuk-prokommentiroval-vstrechu-s-barysom-gde-zaschitnik-cska-zabil-pobednyj-gol.html', '«Дима — потрясающий волейболист». Клец — о завершении карьеры Дмитрия Мусэрского': 'https://www.championat.com/volleyball/news-6327600-dima-potryasayuschij-volejbolist-klec-o-zavershenii-karery-dmitriya-muserskogo.html', 'Буффон сравнил Месси и Роналду, подчеркнув их различия в функционале на футбольном поле': 'https://www.championat.com/football/news-6327610-buffon-sravnil-messi-i-ronaldu-podcherknuv-ih-razlichiya-v-funkcionale-na-futbolnom-pole.html', 'Пол Гаскойн сообщил, что был госпитализирован после падения и перелома шести рёбер': 'https://www.championat.com/football/news-6327590-pol-gaskojn-soobschil-o-tom-chto-byl-gospitalizirovan-posle-padeniya-i-pereloma-shesti-ryober.html', 'Пимблетт: когда я подписал контракт с UFC, понял, что стану чемпионом лиги. Это неизбежно': 'https://www.championat.com/boxing/news-6327574-pimblett-kogda-ya-podpisal-kontrakt-s-ufc-ponyal-chto-stanu-chempionom-ligi-eto-neizbezhno.html', '«На задней линии стоят трое либеро». Клец — о специфике чемпионата Японии': 'https://www.championat.com/volleyball/news-6327596-na-zadnej-linii-stoyat-troe-libero-klec-o-specifike-chempionata-yaponii.html', 'Результаты матчей КХЛ на 22 января 2026 года': 'https://www.championat.com/hockey/news-6327604-rezultaty-matchej-khl-na-22-yanvarya-2026-goda.html', 'Кирилл Клец рассказал, почему решил продолжить карьеру в чемпионате Японии': 'https://www.championat.com/volleyball/news-6327588-kirill-klec-rasskazal-pochemu-reshil-prodolzhit-kareru-v-chempionate-yaponii.html', 'Александр Зверев — Кэмерон Норри: во сколько начало, где смотреть матч Australian Open': 'https://www.championat.com/tennis/news-6327608-aleksandr-zverev-kemeron-norri-vo-skolko-nachalo-gde-smotret-match-australian-open-2026-23-yanvarya.html', 'Семак высказался о победном матче «Зенита» с «Шанхай Порт»': 'https://www.championat.com/football/news-6327602-semak-vyskazalsya-o-pobednom-matche-zenita-s-shanhaj-port.html', '«Реал Сосьедад» ищет Захаряну новый клуб: главный тренер Матараццо сообщил россиянину, что не рассчитывает на него': 'https://sport24.ru/football/news-818725-real-sosyedad-ishchet-zakharyanu-novyy-klub-glavnyy-trener-mataratstso-soobshchil-rossiyaninu-chto-ne-rasschityvayet-na-nego', 'Разин\xa0— об игре «Металлурга» с «Сибирью»: «Я рад этому поражению, но не совсем. Хорошо, что нас опустили носом»': 'https://sport24.ru/football/news-818723-razin-ob-igre-metallurga-s-sibiryu-ya-rad-etomu-porazheniyu-no-ne-sovsem-khorosho-chto-nas-opustili-nosom', 'Гол Мэйтленда-Найлза принес «Лиону» победу над «Янг Бойз» и выход в 1/8 финала Лиги Европы': 'https://sport24.ru/football/news-818720-gol-meytlenda-naylza-prines-lionu-pobedu-nad-yang-boyz-i-vykhod-v-18-finala-ligi-yevropy', 'ПАОК Оздоева всухую выиграл у «Бетиса» в Лиге Европы': 'https://sport24.ru/football/news-818716-paok-ozdoyeva-vsukhuyu-vyigral-u-betisa-v-lige-yevropy', '«Астон Вилла» обыграла «Фенербахче» и вышла в 1/8 финала Лиги Европы': 'https://sport24.ru/football/news-818718-aston-villa-obygrala-fenerbakhche-i-vyshla-v-18-finala-ligi-yevropy', 'Источник: Анчелотти продлит контракт со сборной Бразилии до 2030 года': 'https://sport24.ru/football/news-818709-istochnik-anchelotti-prodlit-kontrakt-so-sbornoy-brazilii-do-2030-goda', 'Семак: «Вендел платит за свои опоздания, причем платит много»': 'https://sport24.ru/football/news-818706-semak-vendel-platit-za-svoi-opozdaniya-prichem-platit-mnogo', '«Торпедо» разгромило «Шанхай», Ткачев оформил 1+3': 'https://sport24.ru/football/news-818701-torpedo-razgromilo-shankhay-tkachev-oformil-13', 'ЦСКА добыл победу над «Барысом», забив победный гол на последних минутах': 'https://sport24.ru/football/news-818695-tsska-dobyl-pobedu-nad-barysom-zabiv-pobednyy-gol-na-poslednikh-minutakh', '«Спартак» победил СКА в Санкт-Петербурге благодаря голу Пивчулина за 2 минуты до финальной сирены': 'https://sport24.ru/football/news-818704-spartak-pobedil-ska-v-sankt-peterburge-blagodarya-golu-pivchulina-za-2-minuty-do-finalnoy-sireny', 'Нападающий сборной России Чишкала подписал контракт со «Спортингом»': 'https://sport24.ru/football/news-818698-napadayushchiy-sbornoy-rossii-chishkala-podpisal-kontrakt-so-sportingom', 'Тренер Гуменника разъяснила ситуацию с визой фигуриста на Олимпиаду-2026: «Петя может не переживать»': 'https://sport24.ru/football/news-818661-trener-gumennika-razyasnila-situatsiyu-s-vizoy-figurista-na-oi-2026-petya-mozhet-ne-perezhivat', 'Российские спортсмены смогут общаться с журналистами на Олимпийских играх\xa0— 2026\xa0— МОК': 'https://sport24.ru/football/news-818691-rossiyskiye-sportsmeny-smogut-obshchatsya-s-zhurnalistami-na-olimpiyskikh-igrakh-v-italii-mok', 'Плескачева выиграла турнир памяти П. С.\xa0Грушмана среди юниорок, у Костылевой только 9-е место': 'https://sport24.ru/football/news-818687-pleskacheva-vyigrala-turnir-pamyati-ps-grushmana-u-kostylevoy-tolko-9-ye-mesto', 'Кириленко\xa0— о допуске российских баскетболистов: «Все идет к положительному решению»': 'https://sport24.ru/football/news-818682-kirilenko-o-dopuske-rossiyskikh-basketbolistov-vse-idet-k-polozhitelnomu-resheniyu', 'СКА вел 1:0 почти весь матч, но в концовке проиграл «Спартаку»': 'https://sportrbc.ru/news/69726d119a7947590eb46228', 'Каземиро летом покинет «Манчестер Юнайтед»': 'https://sportrbc.ru/news/697263de9a7947a4e8f486b3', 'Тренер лидера КХЛ оценил проигрыш фразой «опустили носом в дерьмо»': 'https://sportrbc.ru/news/697262de9a79471e7acd42a4', 'ФХР назвала неактуальными доводы IIHF в пользу отстранения хоккеистов': 'https://sportrbc.ru/news/69725a079a7947ad881542de', '«Зенит» разгромил чемпиона Китая в товарищеском матче': 'https://sportrbc.ru/news/697257d99a7947c15f4d7ca7', '«Авангард» прервал четырехматчевую победную серию «Автомобилиста»': 'https://sportrbc.ru/news/69724e229a7947764e82fbeb', 'Фанатам «Брюгге» дали 5 суток ареста за костюмы в стиле «Бората» в Астане': 'https://sportrbc.ru/news/697248789a7947b9a1c64f47', 'Тренер Гуменника исключила проблемы с визой для Олимпиады-2026': 'https://sportrbc.ru/news/697247189a794753f21af030', 'Лыжники Коростелев и Непряева приняли приглашение МОК на Олимпиаду': 'https://sportrbc.ru/news/6972427b9a79471ceabbb20c', '«Реал» возглавил рейтинг клубов с самым высоким доходом': 'https://sportrbc.ru/news/6972336c9a79475748687fa7', 'Гол Дзюбы не спас «Акрон» от проигрыша ЦСКА': 'https://sportrbc.ru/news/69722d8b9a79471f04ca0e34', 'Рекордсмен сборной Боснии перешел в немецкий «Шальке» до конца сезона': 'https://sportrbc.ru/news/6972347c9a7947b380515bef', 'Смолов начнет обучение на тренерские лицензии УЕФА в марте': 'https://sportrbc.ru/news/69722e479a794717026bf2c4', 'Игрок или контрабандист. Чем известен герой Шаламе в «Марти Великолепный»': 'https://sportrbc.ru/news/6964cac89a79474dba28ea67', 'Агент подтвердил переговоры «Спартака» о трансфере хавбека «Балтики»': 'https://sportrbc.ru/news/697227b99a79472351ba1787'}
    # print([*news.keys()])
    # news = ['Игрок сборной России по футболу слепых Андрей Куклин будет бить пенальти за медиаклуб «Альтерон» на новом турнире Напике.', 'В FONBET КХЛ « Авангард » победил « Автомобилист » (2:1 ОТ), « Металлург » проиграл « Сибири » (1:2),  СКА  играет со « Спартаком », « Торпедо » противостоит « Шанхаю ».', 'СКА  проводит домашний матч со « Спартаком » в FONBET чемпионате КХЛ.', '22 января на этапе Кубка мира по биатлону в Нове-Место пройдет короткая индивидуальная гонка у мужчин.', 'ФХР выступила с заявлением о решении ИИХФ продлить отстранение российских сборных от международных соревнований.', 'Каземиро уйдет из « Манчестер Юнайтед » после этого сезона.', '«Авангард» обыграл «Автомобилист» (2:1 ОТ) в матче Фонбет Чемпионата КХЛ.', '«Сибирь» обыграла «Металлург» (2:1) в игре\xa0Фонбет Чемпионата КХЛ.', '« ЦСКА » победил « Акрон » (3:1) в товарищеском матче, «Зенит» разгромил «Шанхай Порт» (4:1), махачкалинское « Динамо » уступило «Железничару» (0:1).', 'Боец UFC Шара Буллет присоединился к медиафутбольной команде  Fight Nights  для участия в новом турнире Напике.', 'Винисиус – лучший игрок недели в ЛЧ. Вингер «Реала» набрал 3 (1+2) очка в матче с «Монако» и опередил Фермина, Суареса и Наварро', '«Колорадо» и «Вашингтон» – главные претенденты на Панарина (Винс Меркольяно)', 'Вероника Дайнеко, тренер  Петра Гуменника , заявила, что у фигуриста не должно быть проблем с визой на  Олимпиаде -2026 в Милане.', 'Председатель правления « Манчестер Сити »  Хальдон\xa0аль Мубарак \xa0подписал соглашение о присоединении ОАЭ к Совету мира.', 'ФХБ возмутила непоследовательная позиция Тардифа по срокам возвращения национальных команд', 'Forza Horizon 6 выйдет 19 мая — трейлер и детали гонки', '«Игорь, а тебе идёт». «Зенит» опубликовал фото Дивеева в игровой форме', 'Плескачёва выиграла Мемориал Грушмана среди юниорок, Костылева — девятая', 'Вихлянцева: Наоми Осака не такая милашка, какой может показаться в своих модных костюмах', 'Фигейреду: если пройду Умара, уверен, что реванш с Петром Яном состоится', 'Агент Скопинцева отреагировал на слова Гусева о штрафе защитника за неявку на сбор', '«МЮ» рассчитывает освободить место в фонде заработной платы после ухода Каземиро — Уилер', 'Заварухин: Спронг должен понимать философию «Автомобилиста»', 'Заварухин — о поражении в игре с «Авангардом»: «грязное» удаление повлияло на исход', 'В «Мерседесе» показали качественные фото с обкатки машины 2026 года', 'В «Мерседесе» прокомментировали первую обкатку болида 2026 года', 'Дастин Порье дал категоричный прогноз на возможный бой Царукян — Топурия', 'Татьяна Тарасова высказалась о шансе Аделии Петросян на пьедестал Олимпиады-2026', 'Дрэймонд Грин обвинил европейских баскетболистов в использовании грязных приёмов', 'Тренер Гуменника разъяснила ситуацию с визой фигуриста на Олимпиаду-2026: «Петя может не переживать»', 'Российские спортсмены смогут общаться с журналистами на Олимпийских играх\xa0— 2026\xa0— МОК', 'Плескачева выиграла турнир памяти П. С.\xa0Грушмана, у Костылевой только 9-е место', 'Кириленко\xa0— о допуске российских баскетболистов: «Все идет к положительному решению»', 'ФХР о решении IIHF: «Не имеет под собой никаких оснований и является лишь формальным поводом для отказа»', 'Шарипзянов во второй раз в карьере набрал 50 очков за сезон КХЛ', 'Букмекеры оценили вероятность уверенной победы Мирры Андреевой над румынкой Русе на АО', '«Зенит» выиграл у лучшей команды Китая на сборе в Катаре', '«Авангард» обыграл «Автомобилист» в овертайме и одержал четвертую победу подряд', 'Журова включила Исинбаеву в список лучших спортсменов за 25 лет: «Остается великой, несмотря ни на что»', '«Сибирь» обыграла «Металлург» и прервала победную серию магнитогорского клуба', 'Роднина стала одним из инициаторов выплаты олимпийской пенсии в России: «Других таких стран я не знаю»', 'Гол Дзюбы не спас «Акрон» от поражения в игре с ЦСКА', 'Вендел присоединился к «Зениту» на сборе в Дохе спустя неделю после его начала', 'Винисиус признан лучшим игроком 7-го тура Лиги чемпионов', 'Тренер лидера КХЛ оценил проигрыш фразой «опустили носом в дерьмо»', 'ФХР назвала неактуальными доводы IIHF в пользу отстранения хоккеистов', '«Зенит» разгромил чемпиона Китая в товарищеском матче', '«Авангард» прервал четырехматчевую победную серию «Автомобилиста»', 'Фанатам «Брюгге» дали 5 суток ареста за костюмы в стиле «Бората» в Астане', 'Тренер Гуменника исключила проблемы с визой для Олимпиады-2026', 'Лыжники Коростелев и Непряева приняли приглашение МОК на Олимпиаду', '«Реал» возглавил рейтинг клубов с самым высоким доходом', 'Гол Дзюбы не спас «Акрон» от проигрыша ЦСКА', 'Рекордсмен сборной Боснии перешел в немецкий «Шальке» до конца сезона', 'Смолов начнет обучение на тренерские лицензии УЕФА в марте', 'Игрок или контрабандист. Чем известен герой Шаламе в «Марти Великолепный»', 'Агент подтвердил переговоры «Спартака» о трансфере хавбека «Балтики»', 'Гусев и Слуцкий помирились перед матчем «Динамо» и «Шанхай Шэньхуа»', '«Барселона» потеряла Педри на месяц из-за травмы']
#     ai_request = f"""Нужно выбрать пять новостей из списка news которые потенциально больше понравятся человеку, следящему за новостями в мире спорта. Напиши индексы выбранных новостей в виде списка на пайтон (отсчёт индексов начинается с 0). Вот пример того, что должно быть в твоём ответе: selected = [0, 1, 2, 3, 4] . А вот список новостей: news = {[*news.keys()]}"""
#     print(ai_request)
#     res = openrouter_request(ai_request)
#     logger.log(21, res)
#
# #     res = """```python
# # selected = [5, 10, 58, 19, 27]
# # ```"""
#     indexes = re.search(r'\[.+]', res).group()
#     indexes = indexes[1:-1]
#     indexes = [int(i) for i in str(indexes).split(',')]
#     print('IND', indexes)
#
#     selected_news = dict()
#     for id, k in enumerate(news):
#         if id in indexes:
#             selected_news[k] = news[k]
#         # print(news[i])
#
#     print(selected_news)
#     # selected_news = {'Каземиро уйдет из « Манчестер Юнайтед » после этого сезона.': 'https://www.sports.ru/football/1117049239-myu-obyavil-ob-uxode-kazemiro-letom-xavbek-stanet-svobodnym-agentom.html',
#     #                  'Винисиус – лучший игрок недели в ЛЧ. Вингер «Реала» набрал 3 (1+2) очка в матче с «Монако» и опередил Фермина, Суареса и Наварро': 'https://www.sports.ru/football/1117049178-vinisius-luchshij-igrok-nedeli-v-lch-vinger-reala-nabral-3-12-ochka-v-.html',
#     #                  '«Барселона» потеряла Педри на месяц из-за травмы': 'https://sportrbc.ru/news/69721cc89a79474c0f1ef11b',
#     #                  'Фигейреду: если пройду Умара, уверен, что реванш с Петром Яном состоится': 'https://www.championat.com/boxing/news-6327422-figejredu-esli-projdu-umara-uveren-chto-revansh-s-petrom-yanom-sostoitsya.html',
#     #                  'Татьяна Тарасова высказалась о шансе Аделии Петросян на пьедестал Олимпиады-2026': 'https://www.championat.com/figureskating/news-6327408-tatyana-tarasova-vyskazalas-o-shanse-adelii-petrosyan-na-pedestal-olimpiady-2026.html'
#     #                  }
#     # selected_news = {"Каземиро уйдет из « Манчестер Юнайтед » после этого сезона.": "Описание новости 1",
#     #                  "Винисиус – лучший игрок недели в ЛЧ. Вингер «Реала» набрал 3 (1+2) очка в матче с «Монако» и опередил Фермина, Суареса и Наварро": "Описание новости 1",
#     #                  "«Барселона» потеряла Педри на месяц из-за травмы": "Описание новости 3",
#     #                  "Фигейреду: если пройду Умара, уверен, что реванш с Петром Яном состоится": "Описание новости 4",
#     #                  "Татьяна Тарасова высказалась о шансе Аделии Петросян на пьедестал Олимпиады-2026": "Описание новости 5"
#     #                  }
#
#
#
#     ai_request_2 = f"""Есть python список с заголовоками новостей, нужно написать для каждой новости небольшое резюме на русском языке (2-5 предложений), первое предложение будет использоваться как новый заголовок и должно заинтересовывать читателя. Верни новый python список уже с резюме. Вот пример того, что нужно вернуть: result = ["Описание новости 1", "Описание новости 2"] . В самих текстах резюме не должны содержаться двойные кавычки (") и переносы строк. А вот изначальный список c заголовками новостей: {[*selected_news.keys()]}"""
#     print(ai_request_2)
#     res = openrouter_request(ai_request_2)
#     logger.log(21, res)
#
#
#
#     # res = """
#     # result = [
#     # # Каземиро и Манчестер Юнайтед
#     # "Бразильский полузащитник Каземиро покинет «Манчестер Юнайтед» по окончании сезона. Этот шаг связан с планами клуба по омоложению состава и финансовой оптимизацией. Уход опытного игрока потребует от команды поиска достойной замены в трансферное окно.",
#     #
#     # # Винисиус - лучший игрок недели
#     # "Винисиус Жуниор признан лучшим игроком недели в Лиге чемпионов после блестящей игры против «Монако». Набрав 3 очка (гол и две голевые передачи), вперёд «Реала» обошёл таких звёзд как Фермин и Суарес. Этот результат подтверждает статус бразильца как одного из ключевых игроков мадридского клуба.",
#     #
#     # # Травма Педри
#     # "Полузащитник «Барселоны» Педри получил травму, которая выведет его из строя на месяц. Это уже четвёртое серьёзное повреждение игрока за последние три сезона, что вызывает тревогу у тренерского штаба. Отсутствие испанца существенно ослабит центр поля каталонцев в важных матчах апреля.",
#     #
#     # # Фигейреду и реванш с Петром Яном
#     # "Бразильский боец MMA Девесон Фигейреду заявил о планах на реванш с Петром Яном после потенциальной победы над Умаром Нурмагомедовым. Спортсмен уверен, что организация этого боя станет логичным продолжением их соперничества. По его словам, новый поединок определит истинного лидера в легчайшем весе.",
#     #
#     # # Перспективы Аделии Петросян
#     # "Легендарный тренер Татьяна Тарасова высоко оценила олимпийские перспективы юной фигуристки Аделии Петросян. Она отметила уникальную технику прыжков и артистизм спортсменки, но предупредила о жёсткой конкуренции. По мнению эксперта, двух лет подготовки достаточно для борьбы за медали в 2026 году."
#     # ]"""
#
#
#
#     raw_answers = re.findall(r'".+"', res)
#     answers = []
#     for a in raw_answers:
#         sentences = str(a[1:-1]).split('.')
#         sentences[0] = f"<b>{sentences[0]}</b>\n"
#         answers.append('.'.join(sentences))
#
#
#     tg_post = ""
#     for id, ref in enumerate(selected_news.values()):
#         tg_post += f"""📢 {answers[id]}\n🔗<a href="{ref}">Источник</a>\n\n"""
#
#     print(tg_post)





    # print(len(x))
    # d = {'a': 1, 'b':3}
    # print(d)
    # logger.log(21, [*d.keys()])
    # url = r'https://www.sport-express.ru/cybersport/videogames/news/podarki-v-steam-stali-vygodnee-bandly-so-skidkami-bez-rasprodazh-2391952/'
    # res = requests.get(url, headers=headers)
    # print(res.text)
    # get_sport_express_ru_news_rss(1)
    # get_rssexport_rbc_ru_rss_news()


    # d = {'test': 1, 't2': 2}
    # print(json.dumps(d))



    # url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    # res = requests.get(url)
    # print(res.json())
    # print(bot.)
