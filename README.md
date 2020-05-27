# Discord Bilibili Bot

[![Python version](https://img.shields.io/badge/python-3.5%2C%203.6%2C%203.7-blue.svg)](https://python.org)

Discord Bilibili Bot is a MusicBot that is extended from [MusicBot](https://github.com/Just-Some-Bots/MusicBot) to make it support songs from [Bilibili](https://www.bilibili.com). It is written for [Python](https://www.python.org "Python homepage") 3.5+ using the [discord.py](https://github.com/Rapptz/discord.py) library. It plays requested songs from Bilibili or YouTube into a Discord server (or multiple servers). Besides, if the queue becomes empty MusicBot will play through a list of existing songs with configuration. The bot features a permission system allowing owners to restrict commands to certain people. As well as playing songs, MusicBot is capable of streaming live media into a voice channel (experimental).

![Main](https://i.imgur.com/FWcHtcS.png)

## Directly invite the hosted bot to your channel

There is a running instance of this discord Bilibili bot called Bilibili Music Bot available for you to directly use in your channel. Simply invite the bot into your server using [this link](https://discordapp.com/oauth2/authorize?client_id=714076313627131946&scope=bot&permissions=70274048). The command prefix is `>` and for all the commands available, please type `>help` in your channel.

## Create your own bilibili bot

### Setup

Setting up the MusicBot is relatively painless - just follow the one of the [guides](https://just-some-bots.github.io/MusicBot/) offered by the original [MusicBot](https://github.com/Just-Some-Bots/MusicBot), and pay attention to the [Bilibili](#bilibili-related) section below. After that, configure the bot to ensure its connection to Discord.

The main configuration file is `config/options.ini`, but it is not included by default. Simply make a copy of `example_options.ini` and rename it to `options.ini`. See `example_options.ini` for more information about configurations.

#### Commands

There are many commands that can be used with the bot. Most notably, the `play <url>` command (preceded by your command prefix) will download, process, and play a song from YouTube or a similar site. A full list of commands is available [here](https://just-some-bots.github.io/MusicBot/using/commands/ "Commands").

#### Bilibili related

The functionality part related to Bilibili video downloading is modified from [Bilibili_video_download](https://github.com/Henryhaohao/Bilibili_video_download). It was rewritten from synchronous multi-threading downloading into asynchronous downloading using python's `asyncio`.

##### options.ini

There is a new opintion named `BilibiliQuality` under the `MusicBot` section which represents the quality of the videos to download from bilibili. The available options includes `80, 64, 32, 16`, which represents `1080p, 720p, 480p, 360p` correspondingly.

### Contributing

Forks and Pull Requests are welcome! Please make sure you tested the code before creating the PR and please include a brief introduction of what you changed in the PR. Thank you.

### Further reading

- [Support Discord server](https://discord.gg/bots)
- [Project license](LICENSE)
