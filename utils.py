from PIL import Image , ImageDraw, ImageFont 
import os
import random
import hashlib
import asyncio

async def NewBalda(text = None, image = None, create: bool = False):
  list_fonts = os.listdir('./data/fonts')
  font = list_fonts[random.randint(0, len(list_fonts)-1)]
  font_path = f'.data/fonts/{font}'
  try:
    if not create:
      list_images = os.listdir('./data/images')
      list_words = open('./data/words.txt', encoding='utf-8').read().split('\n')[:-1]

      image = list_images[random.randint(0, len(list_images)-1)]
      text = list_words[random.randint(0, len(list_words)-1)]

    data = f'{image[:-4]}:{font[:-4]}:{text}'
    hash_file = hashlib.sha256()
    hash_file.update(data.encode('utf-8'))

    with Image.open(f'./data/images/{image}') as img:
      d = ImageDraw.Draw(img)
      W, H = img.size
      font = ImageFont.truetype(font_path, int(((W-100)-(H/10))//6))
      _, _, w, h = d.textbbox((0, 0), text, font=font)
      if w > W:
        font = ImageFont.truetype(font_path, int(((W-100)-(H/10))//11))
        _, _, w, h = d.textbbox((0, 0), text, font=font)

      offset = 3
      shadowColor = 'black'

      x = (W - w) / 2
      y = H - h - 50

      for off in range(offset):
          #move right
          d.text((x-off, y), text, font=font, fill=shadowColor)
          #move left
          d.text((x+off, y), text, font=font, fill=shadowColor)
          #move up
          d.text((x, y+off), text, font=font, fill=shadowColor)
          #move down
          d.text((x, y-off), text, font=font, fill=shadowColor)
          #diagnal left up
          d.text((x-off, y+off), text, font=font, fill=shadowColor)
          #diagnal right up
          d.text((x+off, y+off), text, font=font, fill=shadowColor)
          #diagnal left down
          d.text((x-off, y-off), text, font=font, fill=shadowColor)
          #diagnal right down
          d.text((x+off, y-off), text, font=font, fill=shadowColor)

      d.text((x,y), text, font=font, fill="#fff")
      del d
      file_path = f'./data/baldas/{hash_file.hexdigest()}.jpg'
      img.save(file_path)

    return file_path
  except:
    print(f'Шрифт хуйня: {font_path}')
    await NewBalda()