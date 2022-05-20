from PIL import Image
from uuid import uuid4
import os
from django.core.files.storage import default_storage

import vibly.settings as settings


def image_to_pillow(file):
    return Image.open(file)


def get_renamed_filename(filename):
    # Filename: <uuid>.<extension>
    return f'{uuid4()}.{filename.split(".")[-1]}'


def remove_image(url, check_default=False, field=None):
    # return if url is default image
    url = os.path.join(settings.MEDIA_ROOT, url.replace('/media/', ''))

    if check_default:
        if field is None:
            raise Exception('field is required if check_default is True')

        default = os.path.join(settings.MEDIA_ROOT, field.field.default)

        if url == default:
            return

    try:
        print(f'removing {url}')
        os.remove(url)
    except FileNotFoundError:
        pass


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def resize(pil_img, width=128, height=128):
    return pil_img.resize((width, height), Image.ANTIALIAS)


def save_image(pil_img, filename, field):
    # Create directory for image if it doesn't exist
    directory = os.path.join(settings.MEDIA_ROOT, field.field.upload_to)
    os.makedirs(directory, exist_ok=True)

    url = os.path.join(settings.MEDIA_ROOT, field.field.upload_to, get_renamed_filename(filename))
    pil_img.save(url)

    return url.replace(settings.MEDIA_ROOT, '').replace('/', '', 1)


def reshape_and_save(file, filename, field, width=128, height=128, delete_old=False):
    old_url = field.instance.__getattribute__(field.field.name).name
    pil_img = image_to_pillow(file)
    pil_img = crop_max_square(pil_img)
    pil_img = resize(pil_img, width, height)
    url = save_image(pil_img, filename, field)
    django_file = default_storage.open(url)

    field.instance.cover = django_file.name.replace(settings.MEDIA_ROOT, '').replace('/', '', 1)
    field.instance.save()

    if delete_old:
        remove_image(old_url, check_default=True, field=field)
