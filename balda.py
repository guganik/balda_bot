from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery, InputMediaPhoto

from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot import asyncio_filters

from config import BOT_TOKEN, ADMINS, CHANNEL_ID
import utils
import keyboards

import json
import os
import asyncio
import shutil
import logging

class States(StatesGroup):
  typing_balda = State()
  photo_for_balda = State()
  moderation = State()
  create_balda = State()
  saving = State()

# Логирование
logging.basicConfig(level=logging.INFO)

# Определение бота
state_storage = StateMemoryStorage()
bot = AsyncTeleBot(BOT_TOKEN, parse_mode='HTML', state_storage=state_storage)

# ОБРАБОТЧИК КОМАНД
# Отправить балду
@bot.message_handler(commands=['get_balda'])
async def SendBalda(message: Message):
  msg = await bot.send_message(message.chat.id, 'Генерирую балду...')

  file_path = await utils.NewBalda()
  await bot.delete_message(message.chat.id, msg.id)
  await bot.send_photo(message.chat.id, photo=open(file_path, 'rb'), reply_markup=await keyboards.more_generation())

# Создание новой балды
@bot.message_handler(commands=['new_text'])
async def NewBalda(message: Message):
  await bot.send_message(message.chat.id, 'Напиши текст для балды\n/cancel - отмена')
  await bot.set_state(message.chat.id, States.typing_balda)

# Создание фото для новой балды
@bot.message_handler(commands=['new_photo'])
async def NewPhotoForBalda(message: Message):
  await bot.send_message(message.chat.id, 'Отправь фото для балды\n/cancel - отмена')
  await bot.set_state(message.chat.id, States.photo_for_balda)

# Создание своей балды из референсов
@bot.message_handler(commands='create_balda')
async def CreateBalda(message: Message):
  await bot.send_message(message.chat.id, 'Отправь текст для своей балды')
  await bot.set_state(message.chat.id, States.create_balda)

# Открыть избранное
@bot.message_handler(commands='saved')
async def SendSaved(message: Message):
  if not os.path.exists(f'./data/users/{message.from_user.username}/saved'):
    await bot.send_message(message.chat.id, 'У вас нет избранных')
  else:
    await bot.set_state(message.chat.id, States.saving)
    async with bot.retrieve_data(message.chat.id) as data:
      data['plus'] = 0

    saved = os.listdir(f'./data/users/{message.from_user.username}/saved')
    await bot.send_photo(message.chat.id,
                         open(f'./data/users/{message.from_user.username}/saved/{saved[0]}', 'rb'),
                         reply_markup=await keyboards.arrows(1, len(saved)))

# Удаление состояния
@bot.message_handler(commands=['cancel'])
async def Cancel(message: Message):
  await bot.delete_state(message.chat.id)
  await bot.send_message(message.chat.id, 'Состояние удалено')

# Помощь с ботом
@bot.message_handler(commands=['start', 'help'])
async def Main(message: Message):
  msg = "<b>Здарова, друже!</b>\nЗдесь ты можешь получить новоиспеченную \"балду\", сгенерированный из случайных фраз и фотографий.\n\n"
  msg += "/get_balda - Получить балду\n"
  msg += "/new_text - Добавить свою подпись\n"
  msg += "/new_photo - Добавить свое фото\n"
  await bot.send_message(message.chat.id, msg)

  with open('./data/users/all_users.json', 'r', encoding='utf-8') as file:
    all_users = json.load(file)

  if str(message.chat.id) not in all_users:
    all_users[message.chat.id] = message.from_user.username

    with open('./data/users/all_users.json', 'w', encoding='utf-8') as file:
      json.dump(all_users, file, ensure_ascii=False, indent=2)

# Админские штучки
@bot.message_handler(commands=['archive'])
async def Archive(message: Message):
  if message.chat.id in ADMINS:
    if len(os.listdir('./data/baldas')) > 0:
      await bot.set_state(message.from_user.id, States.moderation)
      image = os.listdir('./data/baldas')[0]
      await bot.send_photo(message.chat.id, open(f"./data/baldas/{image}", 'rb'),
                          caption='Пойдет?',
                          reply_markup=await keyboards.archive())

      async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['image'] = image
        data['mod_msg'] = message
    else:
      await bot.send_message(message.chat.id, 'Нечего проверять, отдыхай)')
@bot.message_handler(commands=['admin'])
async def Moderation(message: Message):
  if message.chat.id in ADMINS:
    await bot.set_state(message.chat.id, States.moderation)
    if len(os.listdir('./data/moderation/images')) > 0:
      image = os.listdir('./data/moderation/images')[0]
      await bot.send_photo(message.chat.id, photo=open(f'./data/moderation/images/{image}', 'rb'), reply_markup=await keyboards.moderation())
      async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['image'] = image
        data['mod_msg'] = message
    elif len(open('./data/moderation/words.txt', 'r').read().split('\n')[:-1]) > 0:
      text = open('./data/moderation/words.txt', 'r', encoding='utf-8').read().split('\n')[:-1][0]
      await bot.send_message(message.chat.id, text=f'Вот цитата: {text}', reply_markup=await keyboards.moderation())
      async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['text'] = text
        data['mod_msg'] = message
    else:
      await bot.send_message(message.chat.id, 'Нечего проверять, отдыхай)')
@bot.message_handler(commands='say')
async def Say(message: Message):
  if message.chat.id in ADMINS:
    if len(message.text.split()) > 1:
      with open('./data/users/all_users.json', 'r', encoding='utf-8') as file:
        all_users = json.load(file)

      msg = ' '.join(message.text.split()[1:])
      for chat_id in all_users.keys():
        await bot.send_message(int(chat_id), msg)
      print(f'Пользователей, получивших сообщение "{msg}":\n{len(all_users)}')
    else:
      await bot.send_message(message.chat.id, 'Напиши команду в виде: /say сообщение**')

# Генерация балды
async def Generate(msg, bot, value=10):
  for i in range(value):
    process = 0.0
    await utils.NewBalda()
    if i % 5 == 0:
      if (i/value)*100 != process:
        process = round((i/value)*100, 2)
      await bot.edit_message_text(f'Процесс: {process}%', msg.chat.id, msg.message_id)
@bot.message_handler(commands='generate')
async def DefGenerate(message: Message):
  if message.chat.id in ADMINS:
    if len(message.text.strip().split()) != 2:
      await bot.send_message(message.chat.id, "Отправь команду в виде: /generate *сколько балды тебе надо*")
    else:
      value = int(message.text.strip().split()[1])
      if value <= 500:
        msg = await bot.send_message(message.chat.id, 'Процесс:')
        await asyncio.create_task(Generate(msg, bot, value))
        await bot.delete_message(msg.chat.id, msg.message_id)
        await bot.send_message(message.chat.id, f'Балд сгенерированно {value}!')
      else:
        value=1
        msg = await bot.send_message(message.chat.id, 'Процесс:')
        await asyncio.create_task(Generate(msg, bot, value))
        await bot.delete_message(msg.chat.id, msg.message_id)
        await bot.send_message(message.chat.id, f'Балд сгенерированно {value}!')

# ОБРАБОТЧИК СОСТОЯНИЙ
# Новый текст для балды
@bot.message_handler(state=States.typing_balda)
async def SaveNewBalda(message: Message):
  with open(f'./data/words.txt', 'r', encoding='utf-8') as file:
    words = file.read()
  if message.text not in words.split('\n')[:-1]:
    if message.chat.id in ADMINS:
      words += message.text + '\n'
      with open(f'./data/words.txt', 'w', encoding='utf-8') as file:
        file.write(words)
      await bot.send_message(message.chat.id, f'Вы добавили: "<b>{message.text}</b>".\n/cancel - закончить.')
    else:
      with open(f'./data/moderation/words.txt', 'r', encoding='utf-8') as file:
        data = file.read()
      data += message.text + '\n'
      with open(f'./data/moderation/words.txt', 'w', encoding='utf-8') as file:
        file.write(data)
      await bot.send_message(message.chat.id, f'Ваш текст: "<b>{message.text}</b>" отправлен на модерацию.\n/cancel - закончить.')
  else:
    await bot.send_message(message.chat.id, f'<b>"{message.text}"</b> уже есть.\n/cancel - закончить.')

# Сохранение новой фотографии для балды
@bot.message_handler(state=States.photo_for_balda, content_types=['photo'])
async def SavePhotoForBalda(message: Message):
  if message.chat.id in ADMINS:
    msg = await bot.send_message(message.chat.id, 'Сохранение фотографии...')
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    download_file = await bot.download_file(file_info.file_path)

    with open(f'./data/images/{message.photo[-1].file_unique_id}.jpg', 'wb') as file:
      file.write(download_file)

    await bot.delete_message(message.chat.id, msg.id)
    await bot.reply_to(message, 'Фотография сохранена.\n/cancel - закончить.')
  else:
    msg = await bot.send_message(message.chat.id, 'Сохранение фотографии...')
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    download_file = await bot.download_file(file_info.file_path)

    with open(f'./data/moderation/images/{message.photo[-1].file_unique_id}.jpg', 'wb') as file:
      file.write(download_file)

    await bot.delete_message(message.chat.id, msg.id)
    await bot.reply_to(message, 'Фотография отправлена на модерацию\n/cancel - закончить.')

# Создание балды из референсов
  # Фото для балды
@bot.message_handler(state=States.create_balda, content_types=['photo'])
async def CreatePhoto(message: Message):
  try:
    async with bot.retrieve_data(message.chat.id) as data:
      text = data['create']['text']
    
    await bot.send_message(message.chat.id, 'Генерирую...')
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    download_file = await bot.download_file(file_info.file_path)

    with open(f'./data/images/{message.photo[-1].file_unique_id}.jpg', 'wb') as file:
      file.write(download_file)

    photo_file = f'{message.photo[-1].file_unique_id}.jpg'
    file_path = await utils.NewBalda(image=photo_file,
                                    text=text,
                                    create=True)
    await bot.delete_state(message.chat.id)
    await bot.send_photo(message.chat.id, photo=open(file_path, 'rb'))

    os.remove(f'./data/images/{message.photo[-1].file_unique_id}.jpg')
  except:
    await bot.send_message(message.chat.id, 'Неизвестная ошибка, кто-нибудь точно ее решит!')
  
  # Текст для балды
@bot.message_handler(state=States.create_balda)
async def CreateText(message: Message):
  async with bot.retrieve_data(message.chat.id) as data:
    data['create'] = {"text": message.text}
  
  await bot.send_message(message.chat.id, 'Отправь фото для своей балды')

# ОБРАБОТЧИК CALLBACKS
# Добавить в архив
@bot.callback_query_handler(func=lambda call: call.data == 'to_archive', state=States.moderation)
async def AddToArchive(call: CallbackQuery):
  try:
    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
      image = data['image']
      msg = data['mod_msg']

    cache = open('./data/archive/cache.txt', 'r').read().split('\n')
    if image not in cache:
      cache.append(image)
      with open('./data/archive/cache.txt', 'w') as file:
        file.write('\n'.join(cache))

      shutil.copy(f'./data/baldas/{image}', './data/archive')
      os.remove(f'./data/baldas/{image}')
      
      baldas = len(os.listdir('./data/baldas'))
      await bot.answer_callback_query(call.id, f'Балда добавлена в архив! Осталось еще {baldas}')
    else:
      await bot.answer_callback_query(call.id, 'Эта балда уже была загружена в архив')
      os.remove(f'./data/baldas/{image}')

  except:
    await bot.answer_callback_query(call.id, 'Фотка обработана другим пользователем')

  finally:
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if len(os.listdir('./data/baldas')) > 0:
      await Archive(msg)
    else:
      await bot.delete_state(call.message.chat.id)
      await bot.send_message(call.message.chat.id, 'Балды закончились, харашо поработал)')

# Удаление балды
@bot.callback_query_handler(func=lambda call: call.data == 'not_archive', state=States.moderation)
async def DeleteBalda(call: CallbackQuery):
  async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
    image = data['image']
    msg = data['mod_msg']
  try:
    cache = open('./data/archive/cache.txt', 'r').read().split('\n')
    if image not in cache:
      cache.append(image)
      with open('./data/archive/cache.txt', 'w') as file:
        file.write('\n'.join(cache))
      
    os.remove(f'./data/baldas/{image}')
    baldas = len(os.listdir('./data/baldas'))
    await bot.answer_callback_query(call.id, f'Балда опущена! Осталось еще {baldas}')

  except:
    await bot.answer_callback_query(call.id, 'Балда была обработана другим пользователем')

  finally:
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if len(os.listdir('./data/baldas')) > 0:
      await Archive(msg)
    else:
      await bot.delete_state(call.message.chat.id)
      await bot.send_message(call.message.chat.id, 'Балды закончились, харашо поработал)')

# Одобрение модерации
@bot.callback_query_handler(func=lambda call: call.data == 'success', state=States.moderation)
async def AddToArchive(call: CallbackQuery):
  try:
    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
      msg = data['mod_msg']

    if 'image' in data:
      image = data['image']

      shutil.copy(f'./data/moderation/images/{image}', './data/baldas/')
      os.remove(f'./data/moderation/images/{image}')
      
      await bot.answer_callback_query(call.id, 'Фотография одобрена!')

      if len(os.listdir('./data/baldas')) > 0:
        await Moderation(msg)

      else:
        await bot.delete_state(call.message.chat.id)
        await bot.send_message(call.message.chat.id, 'Работа окончена, молодец!')
    if 'text' in data:
      text = data['text']

      words = open('./data/words.txt', 'r', encoding='utf-8').read()
      words += text + '\n'

      with open('./data/words.txt', 'w', encoding='utf-8') as file:
        file.write(words)

      mod_words = open('./data/moderation/words.txt', 'r', encoding='utf-8').read().split('\n')[:-1]
      mod_words.remove(text)
      mod_words_text = '\n'.join(mod_words)
      with open('./data/moderation/words.txt', 'w', encoding='utf-8') as file:
        file.write(mod_words_text)
      await bot.answer_callback_query(call.id, "Текст одобрен!")

      if len(mod_words) > 0:
        await Moderation(msg)

      else:
        await bot.delete_state(call.message.chat.id)
        await bot.send_message(call.message.chat.id, 'Работа окончена, молодец!')

    await bot.delete_message(call.message.chat.id, call.message.message_id)
  except:
    await bot.answer_callback_query(call.id, 'Заявка была обработана другим пользователем')
    await Moderation(msg)

# Отвергание модерации
@bot.callback_query_handler(func=lambda call: call.data == 'not_success', state=States.moderation)
async def AddToArchive(call: CallbackQuery):
  try:
    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
      msg = data['mod_msg']

    if 'image' in data:
      image = data['image']

      os.remove(f'./data/moderation/images/{image}')
      
      await bot.answer_callback_query(call.id, 'Фотография отвергнута!')

      if len(os.listdir('./data/baldas')) > 0:
        await Moderation(msg)

      else:
        await bot.delete_state(call.message.chat.id)
        await bot.answer_callback_query(call.id, 'Работа окончена, молодец!')
    if 'text' in data:
      text = data['text']
      mod_words = open('./data/moderation/words.txt', 'r', encoding='utf-8').read().split('\n')[:-1]
      mod_words.remove(text)
      mod_words_text = '\n'.join(mod_words)
      with open('./data/moderation/words.txt', 'w', encoding='utf-8') as file:
        file.write(mod_words_text)
      await bot.answer_callback_query(call.id, "Текст отвргнут!")

      if len(mod_words) > 0:
        await Moderation(msg)

      else:
        await bot.delete_state(call.message.chat.id)
        await bot.send_message(call.message.chat.id, 'Работа окончена, молодец!')

    await bot.delete_message(call.message.chat.id, call.message.message_id)
  except:
    await bot.answer_callback_query(call.id, 'Заявка была рассмотрена другим пользователем')
    await Moderation(msg)

# Сгенерировать еще
@bot.callback_query_handler(func=lambda call: call.data == 'more_generation')
async def MoreGeneration(call: CallbackQuery):
  await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=await keyboards.saving())
  await SendBalda(call.message)

# Добавить в избранное
@bot.callback_query_handler(func=lambda call: call.data == 'saving')
async def SavingBalda(call: CallbackQuery):
  photo = call.message.photo[-1]
  file_info = await bot.get_file(photo.file_id)
  download_file = await bot.download_file(file_info.file_path)

  if not os.path.exists(f'./data/users/{call.from_user.username}'):
    os.mkdir(f'./data/users/{call.from_user.username}')
    os.mkdir(f'./data/users/{call.from_user.username}/saved')

  with open(f'./data/users/{call.from_user.username}/saved/{call.message.photo[-1].file_unique_id}.jpg', 'wb') as file:
    file.write(download_file)

  if len(call.message.reply_markup.keyboard) == 1:
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
  else:
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=await keyboards.more_generation(True))
  await bot.answer_callback_query(call.id, 'Балда добавлена в избранное!')

# Стрелочки
@bot.callback_query_handler(func=lambda call: call.data == 'next', state=States.saving)
async def Next(call: CallbackQuery):
  saved = os.listdir(f'./data/users/{call.from_user.username}/saved')

  async with bot.retrieve_data(call.message.chat.id) as data:
    if data['plus']+1 < len(saved):
      data['plus'] += 1
      plus = data['plus']

      await bot.edit_message_media(InputMediaPhoto(open(f'./data/users/{call.from_user.username}/saved/{saved[plus]}', 'rb')),
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=await keyboards.arrows(plus+1, len(saved)))

@bot.callback_query_handler(func=lambda call: call.data == 'back', state=States.saving)
async def Back(call: CallbackQuery):
  async with bot.retrieve_data(call.message.chat.id) as data:
    if data['plus'] > 0:
      data['plus'] -= 1
      plus = data['plus']
    
      saved = os.listdir(f'./data/users/{call.from_user.username}/saved')

      await bot.edit_message_media(InputMediaPhoto(open(f'./data/users/{call.from_user.username}/saved/{saved[plus]}', 'rb')),
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=await keyboards.arrows(plus+1, len(saved)))

# ДРУГИЕ ПРОЦЕССЫ
# Автопостинг
async def AutoPosting():
  while True:
    list_photo = os.listdir('./data/archive')
    list_photo.remove('cache.txt')
    if len(list_photo) > 0:
      photo = f"./data/archive/{list_photo[0]}"
      msg = '<a href="https://t.me/lutie_mem">@Смежные мемы</a>'
      await bot.send_photo(CHANNEL_ID, photo=open(photo, 'rb'), caption=msg)
      os.remove(photo)
    else:
      for chat_id in ADMINS:
        await bot.send_message(chat_id, 'Закончился архив, клипай балды!\n/get_balda - Сгенерируй новую\n/archive - Отправь в архив готовую')
    await asyncio.sleep(60*30)

# Напоминания
async def Notification():
  while True:
    if len(os.listdir('./data/baldas')) > 0:
      value_baldas = len(os.listdir('./data/baldas'))
      msg = f'Осталось еще {value_baldas} непроверенных балд!\n/archive'
      for chat_id in ADMINS:
        await bot.send_message(chat_id, msg, disable_notification=True)
    if len(os.listdir('./data/moderation/images')) > 0 or len(open('./data/moderation/words.txt').read().split('\n')[:-1]):
      msg = 'Есть еще непроверенные фото и текста\n/admin'
      for chat_id in ADMINS:
        await bot.send_message(chat_id, msg, disable_notification=True)
    await asyncio.sleep(60*30)

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())

# Запуск
async def main():
  print("Бот опущен...")
  asyncio.create_task(AutoPosting())
  asyncio.create_task(Notification())
  await bot.infinity_polling()

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print('Бот остановлен')