import asyncio
import itertools
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from io import BytesIO

import aiohttp
from PIL import Image

IMG_PATTERN = re.compile(r'url\(\/\/(live.staticflickr\.com.+\.jpg)\)')
thread_pool = ThreadPoolExecutor()


def flatten(iterable):
    return list(itertools.chain.from_iterable(iterable))


async def fetch_html(url, session):
    response = await session.get(url, allow_redirects=False)

    if response.status != 200:
        return ''

    return await response.text()


async def find_images_in_page(url, session):
    html = await fetch_html(url, session)

    images = set()
    for img_url in IMG_PATTERN.findall(html):
        images.add(f'https://{img_url}')

    return images


async def find_all_images(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(find_images_in_page(url, session))

        return flatten(await asyncio.gather(*tasks))


def process_image(bytes, filename):
    img = Image.open(BytesIO(bytes))
    img = img.resize((120, 120))
    img = img.convert("L")
    img.save(f'images/{filename}')


async def async_process_image(bytes, filename):
    loop = asyncio.get_event_loop()

    await loop.run_in_executor(
        thread_pool,
        partial(process_image, bytes, filename)
    )


async def download_image(url, session):
    filename = url.split('/')[-1]

    async with session.get(url) as resp:
        if resp.status == 200:
            await async_process_image(await resp.read(), filename)


async def download_images(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(download_image(url, session))

        await asyncio.gather(*tasks)


async def main():
    pages = [
        f'https://www.flickr.com/photos/confoo/page{i}'
        for i in range(1, 100)
    ]

    images = await find_all_images(pages)
    print(f'[+] Found {len(images)} images.')

    await download_images(images)
    print(f'[+] Processed all {len(images)} images.')


if __name__ == '__main__':
    s = time.perf_counter()

    asyncio.run(main())

    delta = time.perf_counter() - s
    print(f"\n[+] Script executed in {delta:0.2f} seconds.")
