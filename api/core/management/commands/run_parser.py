import os
import django
import requests
from datetime import datetime
from YandexImagesParser.ImageParser import YandexImage
from bs4 import BeautifulSoup as bs
from random import randint, sample
from transliterate import translit
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Post

# Устанавливаем настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Django_blog_project_REST_API.settings")
django.setup()

class Command(BaseCommand):
    help = 'Runs the parser to fetch astronomy related data and store it in the database'

    def handle(self, *args, **kwargs):
        list_abstract = []
        parser = YandexImage()
        images = iter(parser.search("astronomy", sizes=parser.size.medium))

        while len(list_abstract) < 20:
            URL_TEMPLATE = f"https://yandex.ru/referats/?t=astronomy&s={randint(10000, 99999)}"
            r = requests.get(URL_TEMPLATE)

            if r.status_code != 200:
                continue

            soup = bs(r.text, "html.parser")
            referat = soup.find('div', class_='referats__text')
            text = referat.find_all('p')
            img_b = ''
            refer_image = next(images)

            while True:
                if refer_image.url[-4:] != '.jpg':
                    refer_image = next(images)
                    continue
                try:
                    img_b = requests.get(refer_image.url)
                except:
                    refer_image = next(images)
                    continue
                break

            with open(f'media/{str(refer_image.url).split("/")[-1]}', 'wb') as img:
                img.write(img_b.content)

            list_abstract.append(
                {
                    'h1': referat.find('strong').get_text()[7:-1],
                    'title': referat.find('strong').get_text()[7:-1],
                    'slug': translit(referat.find('strong').get_text()[7:-1], language_code='ru', reversed=True).replace(
                        ' ',
                        '-'),
                    'description': text[0].get_text(),
                    'content': ''.join([p.get_text() for p in text]),
                    'created_at': str(datetime.now().date()),
                    'image': str(refer_image.url).split('/')[-1],
                    'author': User.objects.get(username='root'),
                }
            )

        tags_list = ['astronomy', 'asteroid', 'dark matter', 'gas giant', 'hypernova', 'mass', 'nova', 'meteor', 'pulsar', 'planetoid']

        for post in list_abstract:
            b = Post(**post)
            b.save()
            b.tags.add(*sample(tags_list, 2))
            b.save()
