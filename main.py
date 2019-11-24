# -*- coding: utf-8 -*-

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
from urllib import urlencode, quote
from urlparse import parse_qsl
from urllib2 import urlopen, Request
import json
from datetime import datetime, timedelta


_url = sys.argv[0]
_handle = int(sys.argv[1])


def replace_day(nd):
    n = nd.replace("Monday", "Pondělí").replace("Tuesday", "Úterý").replace("Wednesday", "Středa").replace("Thursday", "Čtvrtek").replace("Friday", "Pátek").replace("Saturday", "Sobota").replace("Sunday", "Neděle")
    return n


def compare_time(t):
    d = (t.replace(" ", "-").replace(":", "-")).split("-")
    now = datetime.now()
    start_time = now.replace(year= int(d[0]), month = int(d[1]), day = int(d[2]), hour=int(d[3]), minute=int(d[4]), second=0, microsecond=0)
    if start_time < now:
        return True


days = {replace_day((datetime.now() + timedelta(days=0)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=0)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-1)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-2)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-2)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-3)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-3)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-4)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-4)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-5)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-5)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-6)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-6)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-7)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-7)).strftime("%Y-%m-%d")}


user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers= {'User-Agent':user_agent,}
dev_list = {"0": "androidportable", "1": "ios", "2": "samsungtv"}


addon = xbmcaddon.Addon(id='plugin.video.archivsledovanitv')
if addon.getSetting("id") == "":
    request = Request("http://sledovanitv.cz/api/create-pairing?username=" + addon.getSetting("username") + "&password=" + addon.getSetting("password") + "&type=" + dev_list[addon.getSetting("idd")], None,headers)
    html = urlopen(request).read()
    data = json.loads(html)
    if data["status"] == 1:
        addon.setSetting(id='id', value=str(data["deviceId"]))
        addon.setSetting(id='passwordid', value=str(data["password"]))
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Nelze se přihlásit", xbmcgui.NOTIFICATION_ERROR, 4000)
        sys.exit()


def getsessid():
    html = urlopen("http://sledovanitv.cz/api/device-login?deviceId=" + addon.getSetting("id") + "&password=" + addon.getSetting("passwordid") + "&version=3.2.004&lang=cs&unit=default").read()
    data = json.loads(html)
    if data["status"] == 1:
        PHPSESSID = data["PHPSESSID"]
        if addon.getSetting("pin") != "":
            pinunlock = urlopen("http://sledovanitv.cz/api/pin-unlock?pin=" + addon.getSetting("pin") + "&PHPSESSID=" + PHPSESSID).read()
            data = json.loads(pinunlock)
            if data["status"] == 0:
                PIN = 0
            else:
                PIN = 1
        else:
            PIN = 1
        return PHPSESSID, PIN
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Nelze se přihlásit", xbmcgui.NOTIFICATION_ERROR, 4000)
        sys.exit()


SESSID, PIN = getsessid()
lq = {"0": "quality=40&capabilities=adaptive%2Ch265", "1": "quality=40&capabilities=adaptive%2Ch264", "2": "quality=10&capabilities=adaptive%2Ch264"}


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def list_records():
    html = urlopen('https://sledovanitv.cz:443/api/get-pvr/?PHPSESSID=' + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        if data["records"] == []:
            xbmcgui.Dialog().notification("Archiv SledovaniTV","Žádné uložené pořady", xbmcgui.NOTIFICATION_INFO, 3000)
            return
        xbmcplugin.setContent(_handle, 'videos')
        for d in data["records"]:
            list_item = xbmcgui.ListItem(label=d["event"]["startTime"][8:10] + "." + d["event"]["startTime"][5:7] + ".  " + d["event"]["startTime"][-5:] + " - " + d["event"]["endTime"][-5:] + "    " + d["title"])
            if addon.getSetting("logo") == "0":
                logo = "https://sledovanitv.cz/cache/biglogos/" + d["channel"] + ".png"
            else:
                logo = "https://sledovanitv.cz/cache/biglogos/" + d["channel"] + "-white.png"
            list_item.setArt({'thumb':logo , 'icon': logo, 'fanart': d["event"]['backdrop']})
            list_item.setInfo('video', {'mediatype' : 'movie', 'title': d["title"], 'plot': d["event"]["description"]})
            url = get_url(action='play_record', eventid = d["id"])
            list_item.setProperty('IsPlayable', 'true')
            if 'ruleId' in d:
                list_item.addContextMenuItems([('Uložit seriál','XBMC.RunPlugin({})'.format(get_url(action = "add_serie", ruleid = d["ruleId"]))), ('Odebrat pořad','XBMC.RunPlugin({})'.format(get_url(action = "del_record", id = d["id"]))), ('Odebrat seriál','XBMC.RunPlugin({})'.format(get_url(action = "del_serie", ruleid = d["ruleId"])))])
            else:
                list_item.addContextMenuItems([('Odebrat pořad','XBMC.RunPlugin({})'.format(get_url(action = "del_record", id = d["id"])))])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Žádné uložené pořady", xbmcgui.NOTIFICATION_INFO, 3000)


def list_search():
    kb = xbmc.Keyboard('', 'Zadejte název pořadu')
    kb.doModal()
    if not kb.isConfirmed(): 
        return
    query = kb.getText()
    html = urlopen('https://sledovanitv.cz:443/api/epg-search?query=' + quote(query) + '&detail=1&PHPSESSID=' + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        if data["events"] != []:
            xbmcplugin.setContent(_handle, 'videos')
            name_list = []
            for d in data["events"]:
                if d["availability"] == "timeshift":
                    if compare_time(d["startTime"]) == True:
                        if addon.getSetting("logo") == "0":
                             logo = "https://sledovanitv.cz/cache/biglogos/" + d["channel"] + ".png"
                        else:
                            logo = "https://sledovanitv.cz/cache/biglogos/" + d["channel"] + "-white.png"
                        name_list.append((d["startTime"][8:10] + "." + d["startTime"][5:7] + ".  " + d["startTime"][-5:] + " - " + d["endTime"][-5:] + "    " + d["title"], d["eventId"], logo, d["description"]))
                        if addon.getSetting("sorting") == "0":
                            name_list.sort(reverse=True)
            for d in name_list:
                list_item = xbmcgui.ListItem(label=d[0])
                list_item.setArt({'thumb': d[2], 'icon': d[2]})
                list_item.setInfo('video', {'mediatype' : 'movie', 'title': d[0], 'plot': d[3]})
                url = get_url(action='play', eventid = d[1])
                list_item.setProperty('IsPlayable', 'true')
                list_item.addContextMenuItems([('Uložit pořad','XBMC.RunPlugin({})'.format(get_url(action = "add_recording", eventid = d[1])))])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
            xbmcplugin.endOfDirectory(_handle)
        else:
            xbmcgui.Dialog().notification("Archiv SledovaniTV","Nenalezeno", xbmcgui.NOTIFICATION_INFO, 3000)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Nenalezeno", xbmcgui.NOTIFICATION_INFO, 3000)



def list_channels():
    html = urlopen('https://sledovanitv.cz:443/api/playlist?format=m3u8&quality=40&capabilities=adaptive%2Ch264&whitelogo=1&PHPSESSID=' + SESSID).read()
    data = json.loads(html)["channels"]
    if addon.getSetting("logo") == "0":
        logo = "logoUrl"
    else:
        logo = "whiteLogoUrl"
    name_list = []
    for d in data:
        if d["timeshiftDuration"] != 0 and d["type"] == "tv":
            name_list.append((d["name"], d["id"], d[logo]))
    for category in name_list:
        list_item = xbmcgui.ListItem(label=category[0])
        list_item.setArt({'thumb':category[2] , 'icon': category[2]})
        url = get_url(action='listing_days', id = category[1], icon = category[2])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)


def list_menu():
    name_list = [("TV archiv", "DefaultAddonPVRClient.png", "0"), ("Uložené pořady", "DefaultVideoPlaylists.png", "1"), ("Hledat pořad", "DefaultAddonsSearch.png", "2")]
    for category in name_list:
        list_item = xbmcgui.ListItem(label=category[0])
        list_item.setArt({'thumb':category[1] , 'icon': category[1]})
        url = get_url(action='listing_menu', id = category[2])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)


def list_days(id, icon):
    days = [replace_day((datetime.now() + timedelta(days=0)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-1)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-2)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-3)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-4)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-5)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-6)).strftime("%A  %d.%m.")), replace_day((datetime.now() + timedelta(days=-7)).strftime("%A  %d.%m."))]
    for d in days:
        list_item = xbmcgui.ListItem(label=d)
        list_item.setArt({'thumb':icon , 'icon': icon})
        url = get_url(action='listing_videos', day=d, id = id, icon = icon)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)
	

def list_videos(day,id, icon):
    xbmcplugin.setContent(_handle, 'videos')
    html = urlopen('https://sledovanitv.cz/api/epg?time=' + days[day]+ '+00%3A44&duration=1439&detail=1&channels=' + id + '&PHPSESSID=' + SESSID).read()
    data = json.loads(html)["channels"][id]
    name_list = []
    for d in data:
        if d["availability"] == "timeshift":
            if compare_time(d["startTime"]) == True:
                name_list.append((d["startTime"][-5:] + " - " + d["endTime"][-5:] + "    " + d["title"], d["eventId"], d["description"]))
    if addon.getSetting("sorting") == "0":
        name_list.sort(reverse=True)
    for d in name_list:
        list_item = xbmcgui.ListItem(label=d[0])
        list_item.setArt({'thumb': icon, 'icon': icon})
        list_item.setInfo('video', {'mediatype' : 'movie', 'title': d[0], 'plot': d[2]})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', eventid = d[1])
        list_item.setProperty('IsPlayable', 'true')
        list_item.addContextMenuItems([('Uložit pořad','XBMC.RunPlugin({})'.format(get_url(action = "add_recording", eventid = d[1])))])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
#        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)


def play_records(eventid):
    html = urlopen("https://sledovanitv.cz:443/api/record-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&recordId=" + eventid + "&PHPSESSID=" + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        listitem = xbmcgui.ListItem(path=data["url"])
        xbmcplugin.setResolvedUrl(_handle, True, listitem)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Nedostupné", xbmcgui.NOTIFICATION_INFO, 3000)


def play_video(eventid):
    html = urlopen("https://sledovanitv.cz:443/api/event-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&eventId=" + eventid + "&PHPSESSID=" + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        listitem = xbmcgui.ListItem(path=data["url"])
        xbmcplugin.setResolvedUrl(_handle, True, listitem)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Nedostupné", xbmcgui.NOTIFICATION_INFO, 3000)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "listing_menu":
            if params["id"] == "0":
                list_channels()
            elif params["id"] == "1":
                list_records()
            elif params["id"] == "2":
                list_search()
        elif params['action'] == 'listing_days':
            list_days(params['id'], params['icon'])
        elif params['action'] == 'listing_videos':
            list_videos(params['day'], params['id'], params['icon'])
        elif params['action'] == 'play':
            play_video(params["eventid"])
        elif params['action'] == 'play_record':
            play_records(params["eventid"])
        elif params['action'] == 'add_recording':
            html = urlopen("https://sledovanitv.cz:443/api/record-event?eventId=" + params["eventid"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV","Uloženo", xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
        elif params['action'] == 'add_serie':
            html = urlopen("https://sledovanitv.cz:443/api/activate-rule?ruleId=" + params["ruleid"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV","Uloženo", xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
                xbmc.executebuiltin('Container.Refresh')
        elif params['action'] == 'del_record':
            html = urlopen("https://sledovanitv.cz:443/api/delete-record?recordId=" + params["id"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV","Odebráno", xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
                xbmc.executebuiltin('Container.Refresh')
        elif params['action'] == 'del_serie':
            html = urlopen("https://sledovanitv.cz:443/api/delete-rule?ruleId=" + params["ruleid"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV","Odebráno", xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
                xbmc.executebuiltin('Container.Refresh')
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        if PIN == 0:
            xbmcgui.Dialog().notification("Archiv SledovaniTV","Nesprávný pin", xbmcgui.NOTIFICATION_ERROR, 3000, sound = False)
        list_menu()


if __name__ == '__main__':
    router(sys.argv[2][1:])
