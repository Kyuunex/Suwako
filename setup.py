from distutils.core import setup

from suwako.manifest import VERSION

setup(
    name='suwako',
    packages=[
        'suwako',
        'suwako.cogs',
        'suwako.embeds',
        'suwako.modules',
        'suwako.reusables'
    ],
    version=VERSION,
    description='A Discord bot with a focus to manage an osu! player based Discord server',
    author='Kyuunex',
    author_email='kyuunex@protonmail.ch',
    url='https://github.com/Kyuunex/Suwako',
    install_requires=[
        'discord.py[voice]==2.2.2',
        'pycountry',
        'aiosqlite',
        'aiohttp',
        'psutil',
        'aioosuapi @ git+https://github.com/Kyuunex/aioosuapi.git@1.4.1',
        'appdirs'
    ],
)
