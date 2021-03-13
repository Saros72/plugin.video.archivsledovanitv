# -*- coding: utf-8 -*-


import xbmc
import xbmcgui
import xbmcaddon
import os
import sys
from datetime import datetime, timedelta
from urllib import urlencode, quote, unquote


addon = xbmcaddon.Addon(id='plugin.video.archivsledovanitv')


def run():
    epg_path = os.path.join(xbmc.translatePath('special://home/addons/plugin.video.archivsledovanitv'),'resources', 'channels.txt')
    f = open(epg_path, 'r').read().splitlines()
    channels = {}
    for x in f:
       x = x.split(",")
       channels[x[0]] = x[1]
    title = xbmc.getInfoLabel('Listitem.Title')
    name = xbmc.getInfoLabel('Listitem.ChannelName')
    if name in channels:        
        date = xbmc.getInfoLabel('Listitem.Date')
        dt = date.split(" ")
        d = dt[0].split(".")
        t = dt[1].split(":")
        datetime_original = datetime(year=int(d[2]), month=int(d[1]), day=int(d[0]), hour=int(t[0]), minute=int(t[1]))
        datetime_new = datetime_original + timedelta(minutes = 1)
        ndate = quote(datetime_new.strftime("%Y-%m-%d+%H:%M"))
        url = "plugin://plugin.video.archivsledovanitv/?action=play_pvre&channel=%s&date=%s&title=%s" % (channels[name], ndate, title)
        xbmc.executebuiltin('PlayMedia("{url}")'.format(url=url))
    else:
        xbmcgui.Dialog().notification(name,"Nedostupné", xbmcgui.NOTIFICATION_INFO, 4000, sound = False)


run()
