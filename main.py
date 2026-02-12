from openai import OpenAI
import telebot
import time
import os
from os import environ
import re
from dotenv import load_dotenv
import requests
import datetime
import locale
import json
import logging
from logging.handlers import RotatingFileHandler

from config import times, chat_id, ai_model

locale.setlocale(locale.LC_ALL, "ru")


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

if not os.path.exists('last_news.txt'):
    with open('last_news.txt', 'w') as f:
        f.write(f"")

headers = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

news_limit = 15

def proxyapi_request(msg, model=ai_model, search_context_size="medium"):
    client = OpenAI(base_url=environ.get('AI_REF'), api_key=environ.get('AI_KEY'))
    # res = client.chat.completions.create(
    #     model=ai_model,   #'tngtech/deepseek-r1t2-chimera:free',
    #     messages=[
    #         {'role': 'user',
    #          'content': msg}
    #     ],
    # )
    res = client.responses.create(
        model=model,
        tools=[{
            "type": "web_search",
            "search_context_size": search_context_size,
            "user_location": {
                "type": "approximate",
                "country": "RU",
                "city": "Moscow",
                "region": "Moscow"
            },
            # "max_tokens": 1000
        }],
        input=msg,
        max_output_tokens=6000
    )
    # return res.choices[0].message.content
    return res.output_text


# def proxyapi_request_ws(msg):
#     client = OpenAI(base_url=environ.get('AI_REF'), api_key=environ.get('AI_KEY'))
#     res = client.chat.completions.create(
#         model="gpt-4o-search-preview",
#         web_search_options={
#             "search_context_size": "medium",
#             "user_location": {
#                 "type": "approximate",
#                 "approximate": {
#                     "country": "RU",
#                     "city": "Moscow",
#                     "region": "Moscow"
#                 }
#             }
#         },
#         messages=[
#             {
#                 "role": "user",
#                 "content": msg
#             }
#         ]
#     )
#     return res.choices[0].message.content


def add_title(title):
    with open('last_news.txt', 'a', encoding='utf8') as f:
        f.write(f'{title}\n')

def get_title():
    with open('last_news.txt', 'r', encoding='utf8') as f:
        last_topics = f.readlines()
    if last_topics:
        last_topics = [str(t).replace('\n', '') for t in last_topics]
        last_topics = f' Новости не должно повторяться, вот массив с предыдущими новостями: {last_topics}).'
    return last_topics or ''

def send_tg_post(last_send):
    logger.log(21, 'creating...')
    # last_send_day = last_time.strftime('%d')
    # last_data_before = (last_time - datetime.timedelta(days=7)).strftime('%d %B')
    # print(last_time.strftime('%B'))

    now_data = datetime.datetime.now().date()
    if now_data != last_send.date():
        with open('last_news.txt', 'w', encoding='utf8'):
            pass
        logger.log(21, 'last_news.txt is clear')

    # ai_response = proxyapi_request(f'''Найди самую интересную новость спортивного бизнеса в России за текущий день{last_topic}, найди ссылку на первоисточник, напиши пост для телеграмм канала спортивного журнала. Темы от стройки спортивных объектов до маркетинга спортивных проектов, сделок и соглашений, инвестиций и спонсорства, кадровые изменения, назначения в области менеджмента в спорте, налоговые и юридические изменения в индустрии, креативные активации и работы с болельщиками, исследования в спорте.
    # Ответ помести в многострочную переменную python, например, news_post = """Пост""" . Весть текст поста не должен превышать 1020 символов. Дополнительно напиши заголовок новости по которому можно будет найти картинки к новости, запиши заголовок в переменную: topic = "Заголовок" . В самом тексте поста не должны содержаться двойные кавычки ("). Пост будет отправлен с parse_mode='HTML', то есть можно использовать теги, например, <b>. В конце поста или в тексте вставь рабочую ссылку на первоисточника с помощью: <a href='ссылка'>источник</a> . Можно использовать эмодзи. Если в новости указывается сумма в рублях, то указывай знак рубля перед суммой, например, ₽3,4 млрд или ₽2 500 .
    #
    # Вот пример содержания поста:
    # news_post = """
    # ↗️ <b>Перестановки в руководстве одного из крупнейших букмекеров России</b>
    # <em>Евгений Луговский возьмет управление компанией на себя.</em>
    #
    # 👔 В Pari появилась должность исполнительного директора. <a href='https://www.s-bc.ru/news/pari-lugivsky'>Ее занял</a> Евгений Луговский, который работает в компании с момента основания и до последнего времени занимал позицию директора по развитию бизнеса.
    #
    # CEO Pari Руслан Медведь продолжит руководить компанией в целом, а также сосредоточится на новых направлениях – в частности, на развитии компании Padel+.
    # """
    # ''')
    # И найди рабочую ссылку на картинку в формате .jpg, которая бы подходила к новости, ссылка должна заканчиваться на .jpg, сохрани ссылку в переменную picture = "ссылка на картинку" .
    # Источники: www.sports.ru, championat.com, sport24.ru, sport-express.ru, rbc.ru, vedomosti.ru или можешь взять свои.
    # Дополнительно напиши заголовок новости по которому можно будет найти картинки к новости, запиши заголовок в переменную: topic = "Заголовок" .
    last_titles = get_title()
    request_text = f'''Найди актуальную, интересную новость спортивного бизнеса в России за сегодня (тщательно проверяй дату новости), найди ссылку на первоисточник, напиши пост для телеграмм канала спортивного журнала.{last_titles} Темы от стройки спортивных объектов до маркетинга спортивных проектов, сделок и соглашений, инвестиций и спонсорства, кадровые изменения, назначения в области менеджмента в спорте, налоговые и юридические изменения в индустрии, креативные активации и работы с болельщиками, исследования в спорте.
    Ответ помести в многострочную переменную python, например, news_post = """Пост""" . Весть текст поста не должен превышать 1020 символов. Ещё найди рабочую ссылку на картинку в формате .jpg, которая бы подходила к новости, ссылка должна заканчиваться на .jpg, сохрани ссылку в переменную picture = "ссылка на картинку" . В самом тексте поста не должны содержаться двойные кавычки ("). Пост будет отправлен с parse_mode='HTML', то есть можно использовать теги, например, <b>. В конце поста или в тексте вставь рабочую ссылку на первоисточника с помощью: <a href='ссылка'>источник</a> . Раз в несколько предлодений используй эмодзи. Если в новости указывается сумма в рублях, то указывай знак рубля перед суммой, например, ₽3,4 млрд или ₽2 500 .

    Вот пример поста:
    news_post = """
        ↗️ <b>Перестановки в руководстве одного из крупнейших букмекеров России</b>
        <em>Евгений Луговский возьмет управление компанией на себя.</em>

        👔 В Pari появилась должность исполнительного директора. <a href='https://www.s-bc.ru/news/pari-lugivsky'>Ее занял</a> Евгений Луговский, который работает в компании с момента основания и до последнего времени занимал позицию директора по развитию бизнеса.

        📈 CEO Pari Руслан Медведь продолжит руководить компанией в целом, а также сосредоточится на новых направлениях – в частности, на развитии компании Padel+.
        """
    '''
    ai_response = proxyapi_request(request_text)
    logger.log(21, f"{request_text=}")
    logger.log(21, f"{ai_response=}")
    # print('===========')
    tg_post = re.search(r'""".+"""', ai_response, re.DOTALL).group()[3:-3]

    title = None
    b_1 = re.search(r'<b>', tg_post, re.DOTALL)
    b_2 = re.search(r'</b>', tg_post, re.DOTALL)
    if b_1 and b_2:
        title = tg_post[b_1.span()[1]:b_2.span()[0]]
        logger.log(21, f"{title=}")

    logger.log(21, f"{tg_post=}")
    picture = re.search(r'picture?.=?.".+"', ai_response).group()
    logger.log(21, f"{picture=}")
    picture = picture[8:]
    if picture[0] in (' ', '='):
        picture = picture[1:]
    picture = picture.replace('"', '').strip()
    logger.log(21, f"{picture=}")

    # title = re.search(r'topic?.=?.".+"', ai_response).group()
    # title = title.replace('topic', '').replace('=', '').replace('"', '').replace("'", '').strip()
    # logger.log(21, f"{title=}")

    # res = requests.get(url='picture', timeout=100)
    # if res.status_code != 200:
    #     logger.log(21, 'jpg error')
    #     res = None
    # res = None
    # if res is None:
    # for i in range(3):
    # try:
    #     client = OpenAI(base_url=environ.get('AI_REF'), api_key=environ.get('AI_KEY'))
    #     res = client.chat.completions.create(
    #         model='gpt-4.1-mini',
    #         messages=[
    #             {'role': 'user',
    #              'content': f'К заголовку {title} найди рабочую ссылку на картинку в формате .jpg, которая бы подходила к новости, ссылка должна заканчиваться на .jpg, сохрани ссылку в переменную picture = "ссылка на картинку" ', }
    #         ],
    #     )
    #     ai_response_picture = res.choices[0].message.content
    #
    #     picture = re.search(r'picture?.=?.".+"', ai_response_picture).group()
    #     print(picture)
    #     picture = picture[8:]
    #     if picture[0] in (' ', '='):
    #         picture = picture[1:]
    #     picture = picture.replace('"', '').strip()
    #     logger.log(21, f"{picture=}")
    #     res = requests.get(url=picture, timeout=100)
    #
    #     if res.status_code != 200:
    #         logger.log(21, 'jpg error')
    #         res = None
    #     else:
    #         logger.log(21, 'jpg 1 +')
    # except Exception as jpg_ex:
    #     logger.error('loop_ex:', exc_info=jpg_ex)
    #
    # if res is None:
    #     logger.log(21, 'jpg webdriver')
    #     # return False
    #     driver = webdriver.Chrome(options=option) # service=Service(ChromeDriverManager().install())
    #     try:
    #         # driver = webdriver.Remote(command_executor="http://selenium:4444/wd/hub", options=option) # "/root/tg_ai_news/chromedriver"
    #         driver.set_page_load_timeout(400)
    #         #driver.maximize_window()
    #         url = fr'https://www.google.com/search?as_st=y&hl=ru&as_q={'+'.join(title.split())}&udm=2&as_filetype=jpg'
    #         driver.get(url=url)
    #         time.sleep(5)
    #         search = driver.find_element(By.ID, 'search')
    #         search.find_element(By.TAG_NAME, 'img').click()
    #         print('ckick')
    #         time.sleep(25)
    #         right_side = driver.find_element(By.TAG_NAME, 'c-wiz')
    #         images = right_side.find_elements(By.TAG_NAME, 'img')
    #         print(len(images))
    #         src = None
    #         for img in images:
    #             if img.get_attribute('alt') is not None and img.get_attribute('alt') != '':
    #                 src = img.get_attribute('src')
    #                 break
    #         logger.log(21, f"{src=}")
    #     except Exception as driver_ex:
    #         logger.error('driver_ex:', exc_info=driver_ex)
    #         return False
    #     finally:
    #         driver.quit()
    #
    #     time.sleep(5)
    res = requests.get(url=picture, timeout=100)

    if res.status_code != 200:
        logger.log(21, 'jpg miss')
        bot.send_message(chat_id=chat_id, text=tg_post, parse_mode='HTML', timeout=100)
        add_title(title)
        logger.log(21, f"Новость отправлена")
        return True

    with open('new_img.jpg', 'wb') as f:
        f.write(res.content)
    logger.log(21, 'jpg is done')

    photo_file = open('new_img.jpg', 'rb')
    bot.send_photo(chat_id=chat_id, photo=photo_file, caption=tg_post, parse_mode='HTML', timeout=100)
    logger.log(21, f"Новость отправлена")
    add_title(title)
    return True


def main():
    wait_sec = 15
    while True:
        try:
            time_now = datetime.datetime.now()
            for t in times:
                send_time = datetime.datetime(time_now.year, time_now.month, time_now.day, t.hour, t.minute)
                if time_now > send_time and (time_now - send_time).seconds / 60 < 5:  # время отправки + 3 мин
                    with open('last_send.txt', 'r') as f:
                        last_time = datetime.datetime.strptime(f.read(), '%Y.%m.%d %H:%M:%S')
                        if (time_now - last_time).seconds / 60 > 10: # or last_time.date() != time_now.date():  # если отправлялось больше 10 мин назад
                            if send_tg_post(last_time):
                                with open('last_send.txt', 'w') as f: # 2026.01.26 09:48:24
                                    f.write(f"{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')}")

                    # time.sleep(60)
                # else:
                # print('-', t)
        except Exception as loop_ex:
            logger.error('loop_ex:', exc_info=loop_ex)
        time.sleep(wait_sec)

# @bot.message_handler(content_types=['text'])
# def get_reply_chat_id(message):
#     print(message)

# @bot.message_handler(commands=['start'])
# # @bot.message_handler(content_types=['text'])
# def start_command(message):
# #     bot.send_message(message.chat.id, f"Привет, твой ID: {message.chat.id}")
#     # print(message.chat.id)
#     print(message)


def tg_bot_test():
    ai_response = proxyapi_request('Найди новости спортивного бизнеса в России с 1 февраля 2026 года по 9 февраля 2026 года, найди ссылку на первоисточник. Темы от стройки спортивных объектов до маркетинга спортивных проектов, сделок и соглашений, инвестиций и спонсорства, кадровые изменения, назначения в области менеджмента в спорте, налоговые и юридические изменения в индустрии, креативные активации и работы с болельщиками, исследования в спорте.') #  Оформи ответ как python список, вот пример: news = ["Новость 1", "Новость 2"]
    # ai_response = proxyapi_request('Найди 2-3 интересные новости спортивного бизнеса в России. Источники можешь брать любые свои или sports.ru, championat.com, sport24.ru, sport-express.ru, sportrbc.ru (РБК), vedomosti.ru/sport (Ведомости), ТАСС, SportBusiness. К каждой новости прикрепи ссылку на страницу с новостью. Темы новостей: от стройки спортивных объектов до маркетинга спортивных проектов, сделок и соглашений, инвестиций и спонсорства, кадровые изменения, назначения в области менеджмента в спорте, налоговые и юридические изменения в индустрии, креативные активации и работы с болельщиками, исследования в спорте.')
    logger.log(21, ai_response)


if __name__ == '__main__':
    logger.log(21, 'start app')
    main()
    # send_tg_post()





    # tg_post = "🎾 <b>Падел выходит на большой рынок: в России запускают первый масштабный фестиваль</b>\n<em>Новый формат на стыке спорта, бизнеса и лайфстайла.</em>\n\n🚀 9 февраля 2026 года в Челябинске анонсировали первый в России всероссийский фестиваль падела. Турнир пройдет с 28 февраля по 1 марта в клубе Padel Space и объединит любителей, корпоративные команды и профессионалов.\n\n💼 В программе — отдельный зачет для команд ведущих компаний региона, открытые тренировки для новичков и показательный матч с игроками из Москвы и Екатеринбурга. Организаторы делают ставку на нетворкинг и вовлечение новой аудитории 🤝\n\n💰 Общий призовой фонд составит ₽300 000, а для гостей подготовлены активации от партнеров и розыгрыши призов 🎁\n\n📈 Падел остается одной из самых быстрорастущих дисциплин в стране и все активнее привлекает бизнес как площадка для брендов и сообществ.\n\n<a href='https://31tv.ru/novosti/391546/'>источник</a>"
    # tg_post = "\n🏗️ <b>Концессии как драйвер роста: Калужская область расширяет спортивную инфраструктуру</b>\n\n⚽️ 9 февраля 2026 года региональные власти подвели итоги реализации федерального проекта Бизнес-спринт и подтвердили продолжение строительства спортивных объектов с участием частных инвесторов.\n\n❄️ Уже реализуются концессионные проекты по созданию школы зимних видов спорта Ильи Авербуха, ледовой арены в Обнинске и фиджитал-центра в Калуге. Последний планируется завершить до конца 2026 года, а готовность соседнего спортклуба быстрого доступа уже достигла 33% 💪\n\n📊 Власти отмечают устойчивый интерес инвесторов к спортивным объектам, что открывает дополнительные источники финансирования и усиливает роль спорта как отдельного сегмента региональной экономики.\n\n➡️ Модель концессий все активнее используется как инструмент развития спортивного бизнеса и городской среды 🚀  \n<a href='https://www.vest-news.ru/news/1000514129'>источник</a>\n"
    # tg_post = "\n🏗️ <b>Бизнес ускоряет стройку спорта в Москве</b>\n<em>Льготные кредиты стали драйвером частных инвестиций в инфраструктуру</em>\n\n💼 Более ₽2 млрд направлено на строительство спортивных объектов в Москве при поддержке города. Инвесторы получают кредиты по ставке от 3 процента годовых через Московский фонд поддержки промышленности и предпринимательства.\n\n🏟️ Средства пошли на футбольные манежи, бассейны и ФОКи. Уже введены в эксплуатацию восемь объектов, еще четыре находятся на стадии строительства и проектирования. До 2030 года программа Москомспорта предполагает создание 300 новых спортивных объектов.\n\n📈 Модель показывает, как финансовые инструменты могут масштабировать рынок частного спорта и снизить барьеры входа для девелоперов.\n\n<a href='https://www.mk.ru/social/2025/06/09/liksutov-bolee-2-mlrd-rubley-napravleno-na-sozdanie-sportivnoy-infrastruktury.html'>источник</a>\n"
    # tg_post="\n🏟️ <b>«Газпром» строит новый стадион в Петербурге</b>\n<em>В Приморском районе появится спорткластер для города и академии «Зенита».</em>\n\n🚧 КГИОП согласовал Фонду Газпром социальные инициативы проект стадиона Олимпийские надежды на улице Аккуратова. В него войдут ФОК с универсальным залом и залом единоборств, а готовый объект безвозмездно передадут Петербургу.\n\n⚽ Рядом построят двухэтажный тренировочный комплекс с полем для ФК Зенит, общая площадь превысит 3 000 кв. м. Власти планируют использовать кластер для городских турниров и массового спорта.\n\n🔗 <a href='https://www.rbc.ru/spb_sz/12/02/2026/698dadb89a7947405cbef6fb'>источник</a>\n"
    # tg_post="\n🏗️ <b>В Белокурихе строят новый спорткомплекс за ₽72,7 млн</b>\n<em>Старый стадион Центральный превратят в современный ФОК открытого типа.</em>\n\n📊 Подряд на строительство получил новосибирский застройщик Архитектурно-строительная компания 1. Контракт по краевой инвестпрограмме оценивается в ₽72,7 млн.\n\n⚽ Проект включает мини-футбольное поле, легкоатлетический овал, экстрим-зону для скейтбордов и самокатов, площадку ГТО, сцену и трибуны. Завершить объект планируют к 7 сентября 2026 года. 🏃\u200d♂️\n\n<a href='https://www.alt.kp.ru/online/news/6815837/'>источник</a>\n"
    # bot.send_message(chat_id=chat_id, text=tg_post, parse_mode='HTML', timeout=100)



# def get_sports_ru_news(start_at):
#     news = dict()
#     try:
#         url = r"https://www.sports.ru/news/top/"
#         res = requests.get(url=url, headers=headers, timeout=60)
#         soup = BeautifulSoup(res.text, 'lxml')
#         # print(soup)
#         news_p_elements = soup.find("li", class_="panel active-panel").find("div", class_="short-news").find_all("p")
#         for id, n in enumerate(news_p_elements):
#             if id >= news_limit:
#                 break
#             try:
#                 post_time = n.find('span', class_='time').text.strip()
#
#                 if post_time < f"{start_at}":
#                     continue
#
#                 post_title = n.find('a', class_='short-text').get('title') or n.find('a', class_='short-text').text.strip()
#                 post_ref = n.find('a', class_='short-text').get('href', None)
#
#                 if len(post_title) == 0 or len(post_ref) == 0:
#                     continue
#
#                 if not post_ref.startswith('/'):
#                     # print('Incorrect REF', post_ref)
#                     continue
#
#                 news[post_title] = f"https://www.sports.ru{post_ref}"
#                     # print(f"[{post_time}] {post_text}", end='\n')
#                     # print(f"ref: {post_ref}")
#                     # print(n, end='\n')
#                     # print('='*20)
#
#             except Exception as n_ex_1:
#                 logger.error('n_ex:', exc_info=n_ex_1)
#                 # raise n_ex_1
#
#         # print(news)
#         # print(len(news))
#         # print()
#         logger.log(21, f"{url} [{len(news)}]")
#
#         for n in news:
#             logger.log(21, f"{n} ({news[n]})")
#         # print('='*30)
#         logger.log(21, f"===============")
#
#     except Exception as get_news_ex:
#         logger.error('get_news_ex:', exc_info=get_news_ex)
#         # raise get_news_ex
#         news = None
#
#     return news


# def get_championat_com_rss_news(start_at):
#     news = dict()
#     try:
#         url = r'https://www.championat.com/rss/news/'
#         res = requests.get(url=url, headers=headers, timeout=60)
#         # print(res.status_code)
#         soup = BeautifulSoup(res.content, 'xml')
#         news_items = soup.find_all('item')
#         for id, n in enumerate(news_items):
#             if id >= news_limit:
#                 break
#             try:
#                 row_post_time = n.find('pubDate').text.strip()
#                 post_time = row_post_time.split()[-2]
#                 post_day = row_post_time.split()[1]
#                 if post_time < f"{start_at}" or int(post_day) != datetime.datetime.now().day:
#                     continue
#
#                 post_title = n.find('title').text.strip()
#                 post_ref = n.find('link').text.strip()
#
#                 if len(post_title) == 0 or len(post_ref) == 0:
#                     continue
#
#                 # print(f"[{post_time}] {post_title} ({post_ref})")
#                 news[post_title] = post_ref
#
#             except Exception as n_ex_2:
#                 logger.error('n_ex_2:', exc_info=n_ex_2)
#                 # raise n_ex_2
#
#         # print(news)
#         # print(len(news))
#         # print()
#         #
#         logger.log(21, f"{url} [{len(news)}]")
#         for n in news:
#             logger.log(21, f"{n} ({news[n]})")
#         # print('='*30)
#         logger.log(21, '===============')
#
#     except Exception as get_championat_com_rss_news_ex:
#         logger.error('get_championat_com_rss_news_ex:', exc_info=get_championat_com_rss_news_ex)
#         # raise get_championat_com_rss_news_ex
#         news = None
#
#     return news

# def get_sport24_ru_news(start_at):
#     news = dict()
#     try:
#         url = r"https://sport24.ru/mobile-news"
#         res = requests.get(url=url, headers=headers, timeout=60)
#         # print(res.text)
#         soup = BeautifulSoup(res.text, 'lxml')
#         # print(soup.text)
#         # refs = soup.find('main')
#         # print(refs)
#         # return
#         top_news = soup.find('script', id='app-data').text.strip()
#         # print(top_news)
#         items = json.loads(top_news)['model']['topNews']['items']
#
#         for id, n in enumerate(items):
#             if id >= news_limit:
#                 break
#             try:
#                 post_time = datetime.datetime.fromtimestamp(int(n['publishDate'])/1000).time()
#                 # post_time = f"{post_time.hour}:{post_time.minute}"
#                 if f"{post_time}" < f"{start_at}":
#                     print(f"{post_time}", f"{start_at}")
#                     continue
#
#                 post_title = str(n['title']).strip()
#                 post_ref = str(n['urn']).strip()
#                 if len(post_title) == 0 or len(post_ref) == 0:
#                     continue
#                 # print(post_title)
#                 # post_ref = soup.find('span', string=str(n['title']).replace(' ', ''))#.a.get('href')
#                 # print(post_ref) # https://sport24.ru/football/news-
#                 # print(f"[{post_time.hour}:{post_time.minute}] {post_title} ({post_ref})")
#                 news[post_title] = f"https://sport24.ru/football/news-{post_ref}"
#
#             except Exception as n_ex_3:
#                 logger.error('n_ex_3:', exc_info=n_ex_3)
#                 # raise n_ex_3
#
#         logger.log(21, f"{url} [{len(news)}]")
#         for n in news:
#             logger.log(21, f"{n} ({news[n]})")
#         # print('='*30)
#         logger.log(21, '==================')
#
#     except Exception as get_sport24_ru_news_ex:
#         logger.error('get_sport24_ru_news_ex:', exc_info=get_sport24_ru_news_ex)
#         # raise get_sport24_ru_news_ex
#         news = None
#
#     return news


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


# def get_rssexport_rbc_ru_rss_news(start_at):
#     news = dict()
#     try:
#         url = r"https://rssexport.rbc.ru/sport/news/30/base.rss"
#         res = requests.get(url=url, headers=headers, timeout=60)
#         # print(res.status_code)
#         soup = BeautifulSoup(res.content, 'xml')
#
#         news_items = soup.find_all('item')
#
#         for id, n in enumerate(news_items):
#             if id >= news_limit:
#                 break
#             try:
#                 row_post_time = n.find('pubDate').text.strip()
#                 post_time = row_post_time.split()[-2]
#                 post_day = row_post_time.split()[1]
#                 if post_time < f"{start_at}" or int(post_day) != datetime.datetime.now().day:
#                     continue
#
#                 post_title = n.find('title').text.strip()
#                 post_ref = n.find('link').text.strip()
#
#                 if len(post_title) == 0 or len(post_ref) == 0:
#                     continue
#
#                 # print(f"[{post_time}] {post_title} ({post_ref})")
#                 news[post_title] = post_ref
#
#             except Exception as n_ex_5:
#                 logger.error('n_ex_5:', exc_info=n_ex_5)
#                 # raise n_ex_5
#
#         # print(news)
#         # print(len(news))
#         # print()
#         #
#         logger.log(21, f"{url} [{len(news)}]")
#         for n in news:
#             logger.log(21, f"{n} ({news[n]})")
#         # print('='*30)
#         logger.log(21, '===================')
#
#     except Exception as get_rssexport_rbc_ru_rss_news_ex:
#         logger.error('get_rssexport_rbc_ru_rss_news_ex:', exc_info=get_rssexport_rbc_ru_rss_news_ex)
#         # raise get_rssexport_rbc_ru_rss_news_ex
#         news = None
#
#     return news



# def get_news(start_at):
#     news = dict()
#
#     sites = [lambda: get_sports_ru_news(start_at), lambda: get_championat_com_rss_news(start_at),
#              lambda: get_sport24_ru_news(start_at), lambda: get_rssexport_rbc_ru_rss_news(start_at)]
#
#     for n in sites:
#         for i in range(1, 6):
#             new_news = n()
#             if new_news is not None:
#                 news.update(new_news)
#                 break
#             logger.log(21, f'Попытка {i}')
#             time.sleep(45)
#
#     # news.update(get_sports_ru_news(start_at))
#     # news.update(get_championat_com_rss_news(start_at))
#     # news.update(get_sport24_ru_news(start_at))
#     # news.update(get_rssexport_rbc_ru_rss_news(start_at))
#
#     return news
#
#
# def create_top_news_post(start_at):
#     news = get_news(start_at)
#     if not news:
#         logger.log(21, f"Не удалось получить новости!")
#         return False
#
#     if len(news) < 5:
#         logger.log(21, f"Новостей меньше 5!")
#         return False
#
#     try:
#         logger.log(21, f"Всего новостей: {len(news)}")
#         ai_request = f"""Нужно выбрать пять новостей из списка news которые потенциально больше понравятся человеку, следящему за новостями в мире спорта. Напиши индексы выбранных новостей в виде списка на пайтон (отсчёт индексов начинается с 0). Вот пример того, что должно быть в твоём ответе: selected = [0, 1, 2, 3, 4] . А вот список новостей: news = {[*news.keys()]}"""
#         logger.log(21, ai_request)
#         res = proxyapi_request(ai_request)
#         logger.log(21, res)
#         # res = "```python selected = [5, 10, 58, 19, 27]```"
#
#         indexes = re.search(r'\[.+]', res).group()
#         indexes = indexes[1:-1]
#         indexes = [int(i) for i in str(indexes).split(',')]
#         logger.log(21, f"{indexes=}")
#
#         if len(indexes) != 5:
#             logger.log(21, f"Не удалось получить indexes из запроса [1] к ai")
#             return False
#
#         selected_news = dict()
#         for id, k in enumerate(news):
#             if id in indexes:
#                 selected_news[k] = news[k]
#             # print(news[i])
#
#         logger.log(21, f"{selected_news=}")
#
#         ai_request_2 = f"""Есть python список с заголовоками новостей, нужно написать для каждой новости небольшое резюме на русском языке (2-5 предложений), первое предложение будет использоваться как новый заголовок и должно заинтересовывать читателя. Верни новый python список уже с резюме. Вот пример того, что нужно вернуть: result = ["Описание новости 1", "Описание новости 2"] . В самих текстах резюме не должны содержаться двойные кавычки (") и переносы строк. А вот изначальный список c заголовками новостей: {[*selected_news.keys()]}"""
#         logger.log(21, ai_request_2)
#         res = proxyapi_request(ai_request_2)
#         logger.log(21, res)
#         # result = [
#         # "Бразильский полузащитник ..." ,
#
#         raw_answers = re.findall(r'".+"', res)
#         if len(raw_answers) != 5:
#             logger.log(21, f"Не удалось получить raw_answers из запроса [2] к ai")
#             return False
#
#         answers = []
#         for a in raw_answers:
#             # sentences = str(a[1:-1]).split('.')
#             sentences = re.split(r"[\\.!]", str(a[1:-1]))
#             sentences[0] = f"<b>{sentences[0]}</b>\n"
#             sentences[1] = sentences[1].strip()
#             answer = f"{sentences[0]}{'.'.join(sentences[1:])}"
#             answers.append(answer)
#
#         tg_post = ""
#         for id, ref in enumerate(selected_news.values()):
#             tg_post += f"""📍 {answers[id]}\n🔗<a href="{ref}">Источник</a>\n\n"""
#
#         logger.log(21, 'Тг пост:')
#         logger.log(21, tg_post)
#         # print(tg_post)
#         for i in range(5):
#             try:
#                 bot.send_message(chat_id=chat_id, text=tg_post, parse_mode='HTML', disable_web_page_preview=True, timeout=100)
#                 return True
#             except Exception as tg_send_ex:
#                 logger.error('tg_send_ex:', exc_info=tg_send_ex)
#             time.sleep(60)
#
#     except Exception as create_top_news_post_ex:
#         logger.error('create_top_news_post_ex:', exc_info=create_top_news_post_ex)
#
#     return False
#
# def main_old():
#     # start_at = datetime.time(0, 0)
#     # get_news(start_at)
#     # return
#
#     wait_sec = 15
#     while True:
#         try:
#             time_now = datetime.datetime.now()
#             for t in times:
#                 # print(t)
#                 # if time_now.hour == t.hour and time_now.minute == t.minute:
#                 send_time = datetime.datetime(time_now.year, time_now.month, time_now.day, t.hour, t.minute)
#                 if time_now > send_time and (time_now - send_time).seconds / 60 < 3:  # время отправки + 3 мин
#                     # print(f"+ Время {t}")
#                     with open('last_send.txt', 'r') as f:
#                         last_time = datetime.datetime.strptime(f.read(), '%Y.%m.%d %H:%M:%S')
#                         if last_time.date() == time_now.date():
#                             start_at = last_time.time()
#                         else:
#                             start_at = datetime.time(0,0)
#                         print('+ check', start_at)
#                         if (time_now - last_time).seconds / 60 > 10 or last_time.date() != time_now.date():  # если отправлялось больше 10 мин назад
#                             if create_top_news_post(start_at):
#                             #     print('try to create a post')
#                                 with open('last_send.txt', 'w') as f:
#                                     f.write(f"{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')}")
#
#
#                     # time.sleep(60)
#                 # else:
#                     # print('-', t)
#         except Exception as loop_ex:
#             logger.error('loop_ex:', exc_info=loop_ex)
#         time.sleep(wait_sec)
