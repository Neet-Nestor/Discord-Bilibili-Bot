# !/usr/bin/python
# -*- coding:utf-8 -*-
# time: 2019/07/02--08:12
# author = 'Henry'
# Modified by 'Neet-Nestor' to make it async and compatible with discord.py


'''
项目: B站视频下载 - 多线程下载

版本1: 加密API版,不需要加入cookie,直接即可下载1080p视频

20190422 - 增加多P视频单独下载其中一集的功能
20190702 - 增加视频多线程下载 速度大幅提升
'''

import aiohttp
import aiofiles
import asyncio
import shutil

import logging
import time, hashlib, urllib.request, re, json
from moviepy.editor import *
import os, sys, threading
from .exceptions import DownloadError, HTTPError, BilibiliError
from .constants import AUDIO_CACHE_PATH

import imageio
imageio.plugins.ffmpeg.download()

log = logging.getLogger(__name__)

BILIBILI_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'bilibili_download')

# 访问API地址
async def get_play_list(start_url, cid, quality):
    entropy = 'rbMCKn@KuamXWlPMoJGsKcbiJKUfkPF_8dABscJntvqhRSETg'
    appkey, sec = ''.join([chr(ord(i) + 2) for i in entropy[::-1]]).split(':')
    params = 'appkey=%s&cid=%s&otype=json&qn=%s&quality=%s&type=' % (appkey, cid, quality, quality)
    chksum = hashlib.md5(bytes(params + sec, 'utf8')).hexdigest()
    url_api = 'https://interface.bilibili.com/v2/playurl?%s&sign=%s' % (params, chksum)
    headers = {
        'Referer': start_url,  # 注意加上referer
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    async with aiohttp.ClientSession() as session:
        # log.info(url_api)
        async with session.get(url_api, headers=headers) as resp:
            data = await resp.json()
            # log.info(json.dumps(data))

    video_list = []
    for i in data['durl']:
        video_list.append(i['url'])
    # log.info(video_list)
    return video_list

# 字节bytes转化K\M\G
def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        log.info("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.3fG" % (G)
        else:
            return "%.3fM" % (M)
    else:
        return "%.3fK" % (kb)


#  下载视频
async def _down_videos(video_list, filename, start_url, page):
    start_time = time.time()
    log.info('[正在下载P{}段视频,请稍等...]:'.format(page) + filename)

    # 创建文件夹存放下载的视频
    video_folder = os.path.join(BILIBILI_DOWNLOAD_FOLDER, filename)
    if not os.path.exists(BILIBILI_DOWNLOAD_FOLDER):
        os.makedirs(BILIBILI_DOWNLOAD_FOLDER)
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)

    for i, uri in enumerate(video_list):
        async with aiohttp.ClientSession() as session:
            # 请求头
            headers = [
                # ('Host', 'upos-hz-mirrorks3.acgvideo.com'),  #注意修改host,不用也行
                ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
                ('Accept', '*/*'),
                ('Accept-Language', 'en-US,en;q=0.5'),
                ('Accept-Encoding', 'gzip, deflate, br'),
                ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
                ('Referer', start_url),  # 注意修改referer,必须要加的!
                ('Origin', 'https://www.bilibili.com'),
                ('Connection', 'keep-alive'),
            ]
            # 开始下载
            async with session.get(uri, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    # 写成mp4也行  title + '-' + num + '.mp4'
                    if len(video_list) > 1:
                        f = await aiofiles.open(os.path.join(video_folder, r'-{}.flv'.format(filename, i)), mode='wb')
                    else:
                        f = await aiofiles.open(os.path.join(video_folder, r'{}.flv'.format(filename)), mode='wb')
                    await f.write(await resp.read())
                    await f.close()
                else:
                    filename = r'{}-{}.flv'.format(filename, i) if len(video_list) > 1 else r'{}.flv'.format(filename)
                    raise DownloadError("Download Fail for %s with status code %s" % (filename, resp.status))

# 合并视频(20190802新版)
def _combine_video(filename, path):
    video_folder = os.path.join(BILIBILI_DOWNLOAD_FOLDER, filename)
    if len(os.listdir(video_folder)) >= 2:
        # 视频大于一段才要合并
        log.info('[下载完成,正在合并视频...]:' + filename)
        # 定义一个数组
        L = []
        # 遍历所有文件
        for file in sorted(os.listdir(video_folder), key=lambda x: int(x[x.rindex("-") + 1:x.rindex(".")])):
            # 如果后缀名为 .mp4/.flv
            if os.path.splitext(file)[1] == '.flv':
                # 拼接成完整路径
                filePath = os.path.join(video_folder, file)
                # 载入视频
                video = VideoFileClip(filePath)
                # 添加到数组
                L.append(video)
        # 拼接视频
        final_clip = concatenate_videoclips(L)
        # 生成目标视频文件
        final_clip.write_videofile(os.path.join(path, r'{}.flv'.format(filename)), fps=24)
        log.info('[视频合并完成]' + filename)
    else:
        # 视频只有一段则直接直接复制到dest
        os.rename(os.path.join(video_folder, filename + '.flv'), os.path.join(path, filename + '.flv'))
        log.info('[视频合并完成]:' + filename)

    # Delete download folder
    shutil.rmtree(video_folder)

# Convert avid to bvid
async def vid_to_bvid(vid):
    if vid[0:2].lower() == 'bv':
        return vid

    elif vid[0:2].lower() == 'av':
        query_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + vid[2:]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, headers=headers) as resp:
                if resp.status >=200 and resp.status < 300:
                    resp_json = await resp.json()
                    return resp_json['data']['bvid']
                else:
                    log.error('get video metadata failed with status code %s' % resp.status)
                    raise HTTPError('HTTP status: {}\n{}'.format(resp.status, resp.reason))
    else:
        raise BilibiliError('incorrect vid format')


async def get_video_metadata(vid):
    if vid.lower().startswith('bv'):
        start_url = 'https://api.bilibili.com/x/web-interface/view?bvid=' + vid
    else:
        start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + vid[2:]

    # 获取视频的cid,title
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(start_url) as resp:
            resp_json = await resp.json()
            return resp_json['data']
    

# 下载主入口
# bvid: the av or BV string for the video to download
# quality: 80, 64, 32, 16
async def download(bvid, quality, path=None, page=None):
    start_time = time.time()
    if not bvid.startswith('BV'):
        raise ValueError('illegal BVid send to download')

    data = await get_video_metadata(bvid)
    start_url = 'https://api.bilibili.com/x/web-interface/view?bvid=' + bvid
    
    # 单独下载分P视频中的一集
    # 如果p不存在就下载第一集
    cid_item = data['pages'][int(page) - 1] if page else data['pages'][0]
    log.info(cid_item)

    cid = str(cid_item['cid'])
    title = cid_item['part']
    title = re.sub(r'[\/\\:*?"<>|]', '', title)  # 替换为空的
    page = str(cid_item['page'])
    start_url = start_url + "/?p=" + page

    filename = '{}_{}'.format(bvid, title)
    if not path:
        path = AUDIO_CACHE_PATH # 下载目录
    full_video_path = os.path.join(path, filename + '.flv')

    # 检测视频文件是否已经存在
    if os.path.exists(full_video_path) and os.path.isfile(full_video_path):
        return filename + '.flv'

    log.info('[下载视频的cid]:' + cid)
    log.info('[下载视频的标题]:' + title)
    log.info('[下载视频至目录]:' + path)
    video_list = await get_play_list(start_url, cid, quality)
    log.info(video_list)
    await _down_videos(video_list, filename, start_url, page)
    
    # 最后合并视频
    log.info(filename)
    _combine_video(filename, path)
    end_time = time.time()  # 结束时间
    log.info('下载总耗时%.2f秒,约%.2f分钟' % (end_time - start_time, int(end_time - start_time) / 60))

    return filename + '.flv'