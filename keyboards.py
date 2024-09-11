from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

async def archive():
  keyboard = InlineKeyboardMarkup()
  keyboard.add(InlineKeyboardButton(text='📥 В архив', callback_data='to_archive'),
               InlineKeyboardButton(text='🗑 Удалить', callback_data='not_archive'),
               row_width=2)
  
  return keyboard
  
async def moderation():
  keyboard = InlineKeyboardMarkup()
  keyboard.add(InlineKeyboardButton(text='Одобрить', callback_data='success'),
               InlineKeyboardButton(text='Отвергнуть', callback_data='not_success'),
               row_width=2)
  
  return keyboard

async def more_generation(saved: bool = False):
  keyboard = InlineKeyboardMarkup()
  if not saved:
    keyboard.add(InlineKeyboardButton(text='В избранное', callback_data=f'saving'))
  keyboard.add(InlineKeyboardButton(text='Сгенерировать ещё', callback_data='more_generation'))

  return keyboard

async def saving():
  keyboard = InlineKeyboardMarkup()
  keyboard.add(InlineKeyboardButton(text='В избранное', callback_data=f'saving'))

  return keyboard

async def arrows(plus, len_saved):
  keyboard = InlineKeyboardMarkup()
  keyboard.add(InlineKeyboardButton(text='<', callback_data='back'),
               InlineKeyboardButton(text=f'{plus}/{len_saved}', callback_data='#'),
               InlineKeyboardButton(text='>', callback_data='next'))

  return keyboard