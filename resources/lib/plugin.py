# -*- coding: utf-8 -*-

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from urllib import urlencode, quote, unquote
from urlparse import parse_qsl, urlparse
from urllib2 import urlopen, Request
import json
import uuid
import requests
import xbmcvfs
import os
import pickle
import time
import calendar
from datetime import datetime, timedelta


reload(sys)
sys.setdefaultencoding('utf-8')
_url = sys.argv[0]
_handle = int(sys.argv[1])
user_agent = xbmc.getUserAgent()
headers= {'User-Agent':user_agent,}
product_list = {"0": "Xiaomi%3ARedmi+Note+7", "1": "iPhone%3A8+Plus"}
dev_list = {"0": "androidportable", "1": "ios"}
addon = xbmcaddon.Addon(id='plugin.video.archivsledovanitv')
profile = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
history_path = os.path.join(profile, "history")
playing_path = os.path.join(profile, "history_playing")
lng = addon.getLocalizedString


def replace_day(nd):
    n = nd.replace("Monday", lng(30008)).replace("Tuesday", lng(30009)).replace("Wednesday", lng(30010)).replace("Thursday", lng(30011)).replace("Friday", lng(30012)).replace("Saturday", lng(30013)).replace("Sunday", lng(30014))
    return n


days = {replace_day((datetime.now() + timedelta(days=0)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=0)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-1)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-2)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-2)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-3)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-3)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-4)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-4)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-5)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-5)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-6)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-6)).strftime("%Y-%m-%d"), replace_day((datetime.now() + timedelta(days=-7)).strftime("%A  %d.%m.")): (datetime.now() + timedelta(days=-7)).strftime("%Y-%m-%d")}


def compare_time(t):
    d = (t.replace(" ", "-").replace(":", "-")).split("-")
    now = datetime.now()
    start_time = now.replace(year= int(d[0]), month = int(d[1]), day = int(d[2]), hour=int(d[3]), minute=int(d[4]), second=0, microsecond=0)
    if start_time < now:
        return True


def unpair():
    if addon.getSetting("id") != "":
        try:
            request = Request("https://sledovanitv.cz/api/delete-pairing/?deviceId=" + addon.getSetting("id") + "&password=" + addon.getSetting("passwordid") + "&unit=default", None,headers)
            html = urlopen(request).read()
        except:
            xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30024), xbmcgui.NOTIFICATION_ERROR, 4000)
        addon.setSetting(id='id', value= "")
        addon.setSetting(id='passwordid', value= "")
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30024), xbmcgui.NOTIFICATION_ERROR, 4000)


def pairing():
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = ':'.join(mac_num[i : i + 2] for i in range(0, 11, 2))
    request = Request("https://sledovanitv.cz/api/create-pairing?username=" + quote(addon.getSetting("username")) + "&password=" + quote(addon.getSetting("password")) + "&type=" + dev_list[addon.getSetting("idd")] + "&product=" + product_list[addon.getSetting("idd")] + "&serial=" + mac, None,headers)
    html = urlopen(request).read()
    data = json.loads(html)
    if data["status"] == 1:
        addon.setSetting(id='id', value=str(data["deviceId"]))
        addon.setSetting(id='passwordid', value=str(data["password"]))
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30025), xbmcgui.NOTIFICATION_ERROR, 4000)
        sys.exit()


def getsessid():
    if xbmc.getLanguage().lower() == "slovak":
        api_lng = "sk"
    elif xbmc.getLanguage().lower() == "czech":
        api_lng = "cs"
    else:
        api_lng = "en"
    html = urlopen("https://sledovanitv.cz/api/device-login?deviceId=" + addon.getSetting("id") + "&password=" + addon.getSetting("passwordid") + "&version=3.2.004&lang=" + api_lng + "&unit=default").read()
    data = json.loads(html)
    if data["status"] == 1:
        PHPSESSID = data["PHPSESSID"]
    else:
        pairing()
        html = urlopen("https://sledovanitv.cz/api/device-login?deviceId=" + addon.getSetting("id") + "&password=" + addon.getSetting("passwordid") + "&version=3.2.004&lang=" + api_lng + "&unit=default").read()
        data = json.loads(html)
        if data["status"] == 1:
            PHPSESSID = data["PHPSESSID"]
        else:
            xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30025), xbmcgui.NOTIFICATION_ERROR, 4000)
            sys.exit()
    if addon.getSetting("pin") != "":
        pinunlock = urlopen("https://sledovanitv.cz/api/pin-unlock?pin=" + addon.getSetting("pin") + "&PHPSESSID=" + PHPSESSID).read()
        data = json.loads(pinunlock)
        if data["status"] == 0:
            PIN = 0
        else:
            PIN = 1
    else:
        PIN = 1
    return PHPSESSID, PIN


if addon.getSetting("id") == "":
    pairing()
SESSID, PIN = getsessid()
kd = {"0": "h265%2C", "1": ""}
lq = {"0": "quality=10&capabilities=" + kd[addon.getSetting("codec")] + "webvtt%2Cadaptive2", "1": "quality=20&capabilities=" + kd[addon.getSetting("codec")] + "webvtt%2Cadaptive2", "2": "quality=40&capabilities=" + kd[addon.getSetting("codec")] + "webvtt%2Cadaptive2"}


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def available_time(string_time):
    ts = calendar.timegm(time.strptime(string_time, "%Y-%m-%d %H:%M:%S"))
    ct = time.time()
    if ts <= ct:
        return True
    else:
        return False


def sec_to_hours(seconds):
    h = seconds // 3600
    m = seconds % 3600 // 60
    s = seconds % 3600 % 60
    return "%02d:%02d" % (h, m)


def list_tv_tips(id):
    html = urlopen('https://sledovanitv.cz/api/show-category?category=box-homescreen&detail=events%2Csubcategories&eventCount=1&PHPSESSID=' + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        xbmcplugin.setContent(_handle, 'videos')
        for d in data["subcategories"]:
            if d["id"] == id:
                for d in d["items"]:
                    if d["events"][0]["availability"] == "timeshift" and available_time(d["events"][0]["startTime"]) == True:
                        list_item = xbmcgui.ListItem(label=d["events"][0]["startTime"][8:10] + "." + d["events"][0]["startTime"][5:7] + ".  " + d["events"][0]["startTime"][-8:-3] + " - " + d["events"][0]["endTime"][-8:-3] + "    [B]" + d["title"] + "[/B]")
                        list_item.setArt({'thumb': d["poster"], 'icon': d["poster"], 'fanart': d["backdrop"]})
                        list_item.setInfo('video', {'mediatype' : 'movie', 'title': d["title"], 'plot': d["description"], "studio": d["events"][0]["startTime"][8:10] + "." + d["events"][0]["startTime"][5:7] + ".  " + d["events"][0]["startTime"][-8:-3] + " - " + d["events"][0]["endTime"][-8:-3], 'originaltitle': d["title"], 'plotoutline': d["events"][0]["channel"], 'year': d['subtitle'], "duration": d["events"][0]["duration"]})
                        url = get_url(action='play', eventid = d["events"][0]["eventId"])
                        list_item.addContextMenuItems([(lng(30015),'XBMC.RunPlugin({})'.format(get_url(action = "add_recording", eventid = d["events"][0]["eventId"]))), (lng(30016),'XBMC.RunPlugin({})'.format(get_url(action = "downloading", name = d["events"][0]["startTime"][8:10] + "." + d["events"][0]["startTime"][5:7] + ".  " + d["events"][0]["startTime"][-8:-3] + " " + d["title"], eventid = d["events"][0]["eventId"], evt = "0")))])
                        list_item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
                xbmcplugin.endOfDirectory(_handle)


def list_tv_tips_category():
    html = urlopen('https://sledovanitv.cz/api/show-category?category=box-homescreen&detail=events%2Csubcategories&eventCount=1&PHPSESSID=' + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        for d in data["subcategories"]:
            list_item = xbmcgui.ListItem(label=d["title"])
            list_item.setArt({'icon': "DefaultMovies.png"})
            url = get_url(action='listing_tv_tips', eventid = d["id"])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(_handle)


def list_records():
    html = urlopen('https://sledovanitv.cz/api/get-pvr/?detail=description,poster,backdrop&backdropSize=1280&posterSize=234&PHPSESSID=' + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        if data["records"] == []:
            xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30026), xbmcgui.NOTIFICATION_INFO, 3000)
            return
        xbmcplugin.setContent(_handle, 'videos')
        try:
            save_records = lng(30027) + sec_to_hours(data["summary"]["recordedDuration"]) + "/" + sec_to_hours(data["summary"]["availableDuration"]) + lng(30028)
        except:
            save_records = ""
        for d in data["records"]:
            list_item = xbmcgui.ListItem(label=d["event"]["startTime"][8:10] + "." + d["event"]["startTime"][5:7] + ".  " + d["event"]["startTime"][-5:] + " - " + d["event"]["endTime"][-5:] + "    [B]" + d["title"] + "[/B]")
            if addon.getSetting("logo") == "0":
                logo = "https://sledovanitv.cz/cache/biglogos/" + d["channel"] + ".png"
            else:
                logo = "https://sledovanitv.cz/cache/biglogos/" + d["channel"] + "-white.png"
            list_item.setArt({'thumb':d["event"]['poster'] , 'icon': logo, 'fanart': d["event"]['backdrop']})
            list_item.setInfo('video', {'mediatype' : 'movie', 'title': d["title"], 'plot': d["event"]["description"], "studio": d["event"]["startTime"][8:10] + "." + d["event"]["startTime"][5:7] + ".  " + d["event"]["startTime"][-5:] + " - " + d["event"]["endTime"][-5:], 'originaltitle': d["title"], 'plotoutline': save_records, "duration": d["eventDuration"]})
            url = get_url(action='play_record', eventid = d["id"])
            list_item.setProperty('IsPlayable', 'true')
            if 'ruleId' in d:
                list_item.addContextMenuItems([(lng(30019),'XBMC.RunPlugin({})'.format(get_url(action = "add_serie", ruleid = d["ruleId"]))), (lng(30018),'XBMC.RunPlugin({})'.format(get_url(action = "del_record", id = d["id"]))), (lng(30020),'XBMC.RunPlugin({})'.format(get_url(action = "del_serie", ruleid = d["ruleId"]))), (lng(30016),'XBMC.RunPlugin({})'.format(get_url(action = "downloading", name = d["event"]["startTime"][8:10] + "." + d["event"]["startTime"][5:7] + ".  " + d["event"]["startTime"][-5:] + " " + d["title"], eventid = d["id"], evt = "1")))])
            else:
                list_item.addContextMenuItems([(lng(30018),'XBMC.RunPlugin({})'.format(get_url(action = "del_record", id = d["id"]))), (lng(30016),'XBMC.RunPlugin({})'.format(get_url(action = "downloading", name = d["event"]["startTime"][8:10] + "." + d["event"]["startTime"][5:7] + ".  " + d["event"]["startTime"][-5:] + " " + d["title"], eventid = d["id"], evt = "1")))])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30026), xbmcgui.NOTIFICATION_INFO, 3000)


def search(query):
    html = urlopen('https://sledovanitv.cz/api/epg-search?query=' + quote(query) + '&detail=description,poster,backdrop&backdropSize=1280&posterSize=234&PHPSESSID=' + SESSID).read()
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
                        name_list.append((d["startTime"][8:10] + "." + d["startTime"][5:7] + ".  " + d["startTime"][-5:] + " - " + d["endTime"][-5:] + "    [B]" + d["title"] + "[/B]", d["eventId"], logo, d["description"], d["backdrop"], d["poster"], d["title"], d["startTime"][8:10] + "." + d["startTime"][5:7] + ".  " + d["startTime"][-5:] + " - " + d["endTime"][-5:], d["duration"]))
                        if addon.getSetting("sorting") == "0":
                            name_list.sort(reverse=True)
            for d in name_list:
                list_item = xbmcgui.ListItem(label=d[0])
                list_item.setArt({'thumb': d[5], 'icon': d[2], 'fanart': d[4]})
                list_item.setInfo('video', {'mediatype' : 'movie', 'title': d[6], 'plot': d[3], "studio": d[7], 'originaltitle': d[6], "duration": d[8]*60})
                url = get_url(action='play', eventid = d[1])
                list_item.setProperty('IsPlayable', 'true')
                list_item.addContextMenuItems([(lng(30015),'XBMC.RunPlugin({})'.format(get_url(action = "add_recording", eventid = d[1]))), (lng(30016),'XBMC.RunPlugin({})'.format(get_url(action = "downloading", name = d[0].replace("[B]", "").replace("[/B]", ""), eventid = d[1], evt = "0")))])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
            xbmcplugin.endOfDirectory(_handle)
        else:
            xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30023), xbmcgui.NOTIFICATION_INFO, 3000)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30023), xbmcgui.NOTIFICATION_INFO, 3000)


def query_search():
    kb = xbmc.Keyboard('', lng(30022))
    kb.doModal()
    if not kb.isConfirmed(): 
        return menu_search()
    query = kb.getText()
    if os.path.exists(history_path):
        lh = open(history_path, "r").read().splitlines()
        if query not in lh:
            if len(lh) == 20:
                del lh[-1]
            lh.insert(0, query)
            f = open(history_path, "w")
            for item in lh:
                f.write("%s\n" % item)
            f.close()
    else:
        f = open(history_path, "w")
        f.write(query)
        f.close()
        xbmc.executebuiltin("Container.Update()")
    search(query)


def menu_search():
    if os.path.exists(history_path):
        lh = open(history_path, "r").read().splitlines()
    else:
        lh = []
    lh.insert(0, lng(30021))
    for name in lh:
        list_item = xbmcgui.ListItem(label=name)
        list_item.setArt({'icon': "DefaultAddonsSearch.png"})
        if name == lng(30021):
            url = get_url(action='listing_query')
        else:
            url = get_url(action='listing_search', name = name)
            list_item.addContextMenuItems([(lng(30121),'XBMC.RunPlugin({})'.format(get_url(action = "del_search_history")))])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)


def list_channels():
    html = urlopen('https://sledovanitv.cz/api/playlist?format=m3u8&quality=40&capabilities=adaptive%2Ch264&whitelogo=1&PHPSESSID=' + SESSID).read()
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
        list_item.addContextMenuItems([(lng(30007),'XBMC.RunPlugin({})'.format(get_url(action = "play_live", id = category[1], name = category[0], icon = category[2])))])
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


def history():
    if os.path.exists(playing_path):
        xbmcplugin.setContent(_handle, 'videos')
        filehandle = open(playing_path, 'rb')
        name_list = pickle.load(filehandle)
        filehandle.close()
        for d in name_list:
            try:
                duration = d["duration"]
            except:
                duration = ""
            list_item = xbmcgui.ListItem(label=d["title"])
            list_item.setArt({'thumb': d['thumb'], 'fanart': d['fanart']})
            list_item.setInfo('video', {'mediatype' : 'movie', 'title': d["originaltitle"], 'plot': d['plot'], "studio": d["studio"], "originaltitle": d["originaltitle"], "duration": duration})
            list_item.setProperty('IsPlayable', 'true')
            url = get_url(action='play', eventid = d['eventid'])
            ind = name_list.index(d)
            list_item.addContextMenuItems([(lng(30120),'XBMC.RunPlugin({})'.format(get_url(action = "del_history_item", item_index = ind))), (lng(30016),'XBMC.RunPlugin({})'.format(get_url(action = "downloading", name = d["title"].replace("[B]", "").replace("[/B]", ""), eventid = d['eventid'], evt = "0")))])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30033), xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
	

def list_videos(day,id, icon):
    xbmcplugin.setContent(_handle, 'videos')
    html = urlopen('https://sledovanitv.cz/api/epg?time=' + days[day.encode().decode("utf-8")] + '+00%3A44&duration=1439&detail=description,poster,backdrop&backdropSize=1280&posterSize=234&channels=' + id + '&PHPSESSID=' + SESSID).read()
    data = json.loads(html)["channels"][id]
    name_list = []
    for d in data:
        if d["availability"] == "timeshift":
            if compare_time(d["startTime"]) == True:
                name_list.append((d["startTime"][-5:] + " - " + d["endTime"][-5:] + "    [B]" + d["title"] + "[/B]", d["eventId"], d["description"], d["backdrop"], d["poster"], d["title"], d["startTime"][8:10] + "." + d["startTime"][5:7] + ".  " + d["startTime"][-5:] + " - " + d["endTime"][-5:], d["duration"]))
    if addon.getSetting("sorting") == "0":
        name_list.sort(reverse=True)
    for d in name_list:
        list_item = xbmcgui.ListItem(label=d[0])
        list_item.setArt({'thumb': d[4], 'icon': icon, 'fanart': d[3]})
        list_item.setInfo('video', {'mediatype' : 'movie', 'title': d[5], 'plot': d[2], "studio": d[6], "originaltitle": d[5], "duration": d[7]*60})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', eventid = d[1])
        list_item.addContextMenuItems([(lng(30015),'XBMC.RunPlugin({})'.format(get_url(action = "add_recording", eventid = d[1]))), (lng(30016),'XBMC.RunPlugin({})'.format(get_url(action = "downloading", name = d[0].replace("[B]", "").replace("[/B]", ""), eventid = d[1], evt = "0")))])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)


def download(name, eventid, evt):
    path = addon.getSetting("download_folder")
    if path == '':
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30034), xbmcgui.NOTIFICATION_ERROR, 4000, sound = False)
        return
    if addon.getSetting("dialog") == "true":
        dialog = xbmcgui.DialogProgressBG()
    else:
        dialog = xbmcgui.DialogProgress()
    dialog.create("Archiv SledovaniTV",lng(30035))
    if evt == "0":
        html = urlopen("https://sledovanitv.cz/api/event-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&eventId=" + eventid + "&PHPSESSID=" + SESSID).read()
    else:
        html = urlopen("https://sledovanitv.cz/api/record-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&recordId=" + eventid + "&PHPSESSID=" + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        r = requests.get(data["url"])
        playlist = [line.rstrip() for line in r.text.split() if line.rstrip().startswith('https')]
        u = urlparse(playlist[0])
        url = "http://" + u.netloc + u.path.replace("storage-media.m3u8", "")
        r = requests.get(playlist[0].replace("https", "http"))
        ts_filenames = [line.rstrip() for line in r.text.split() if line.rstrip().startswith('#') is False]
        pocetTSFiles = len(ts_filenames)
        name = name.replace(":", "").replace(" - ", "-").replace(",", "").replace("/", "").replace(".", "").replace("  ", "_")
        name = name.replace(" ", "_") + ".ts"
        f = xbmcvfs.File(path + name, 'w')
        for i in range(int(addon.getSetting("start_min")) * 6, pocetTSFiles - (int(addon.getSetting("end_min")) * 6)):
            if addon.getSetting("dialog") == "false":
                if dialog.iscanceled():
                    break
            r = requests.get(url + ts_filenames[i])
            f.write(r.content)
            dialog.update((i)*100/(pocetTSFiles - (int(addon.getSetting("end_min")) * 6)), lng(30035), name)
        f.close()
        dialog.close()
        del dialog
        yes = xbmcgui.Dialog().yesno("Archiv SledovaniTV", lng(30036), '', name)
        if yes:
            ts_path = path + name
            listitem = xbmcgui.ListItem(path=ts_path)
            player = xbmc.Player()
            player.play(ts_path, listitem)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30032), xbmcgui.NOTIFICATION_INFO, 3000)


def play_pvr_live(id):
    stream = "http://sledovanitv.cz/vlc/api-channel/" + id + ".m3u8?" + lq[addon.getSetting("quality")] + "&PHPSESSID=" + SESSID
    listitem = xbmcgui.ListItem(path=stream)
    if addon.getSetting("inputstream") == "true":
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
    xbmcplugin.setResolvedUrl(_handle, True, listitem)


def play_pvr_epg(ch, d, n):
    url = urlopen("http://sledovanitv.cz/api/epg?time=" + d + "&duration=0&detail=0&channels=" + ch + "&PHPSESSID=" + SESSID).read()
    eventid = json.loads(url)["channels"][ch][0]["eventId"]
    html = urlopen("https://sledovanitv.cz/api/event-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&eventId=" + eventid + "&PHPSESSID=" + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        if addon.getSetting("logo") == "0":
            logo = "https://sledovanitv.cz/cache/biglogos/" + ch + ".png"
        else:
            logo = "https://sledovanitv.cz/cache/biglogos/" + ch + "-white.png"
        listitem = xbmcgui.ListItem(path=data["url"])
        listitem.setArt({'icon': logo})
        listitem.setInfo('video', {'mediatype' : 'video', 'title': n})
        if addon.getSetting("inputstream") == "true":
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        xbmcplugin.setResolvedUrl(_handle, True, listitem)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV","Nedostupné", xbmcgui.NOTIFICATION_INFO, 3000)


def play_live_video(id, name, icon):
    stream = "http://sledovanitv.cz/vlc/api-channel/" + id + ".m3u8?" + lq[addon.getSetting("quality")] + "&PHPSESSID=" + SESSID
    listitem = xbmcgui.ListItem(label=name, path=stream)
    listitem.setArt({'thumb':icon , 'icon': icon})
    listitem.setProperty('IsPlayable', 'true')
    if addon.getSetting("inputstream") == "true":
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
    player = xbmc.Player()
    player.play(stream, listitem)


def play_records(eventid):
    html = urlopen("https://sledovanitv.cz/api/record-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&recordId=" + eventid + "&PHPSESSID=" + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        listitem = xbmcgui.ListItem(path=data["url"])
        if addon.getSetting("inputstream") == "true":
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        xbmcplugin.setResolvedUrl(_handle, True, listitem)
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30032), xbmcgui.NOTIFICATION_INFO, 3000)


def play_video(eventid):
    html = urlopen("https://sledovanitv.cz/api/event-timeshift?format=m3u8&" + lq[addon.getSetting("quality")] + "&eventId=" + eventid + "&PHPSESSID=" + SESSID).read()
    data = json.loads(html)
    if data["status"] == 1:
        listitem = xbmcgui.ListItem(path=data["url"])
        if addon.getSetting("inputstream") == "true":
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        xbmcplugin.setResolvedUrl(_handle, True, listitem)
        originaltitle = xbmc.getInfoLabel("ListItem.OriginalTitle")
        plot = xbmc.getInfoLabel("ListItem.Plot")
        studio = xbmc.getInfoLabel("ListItem.Studio")
        thumb = xbmc.getInfoLabel('ListItem.Art(thumb)')
        fanart = xbmc.getInfoLabel('ListItem.Art(fanart)')
        try:
            duration = xbmc.getInfoLabel('ListItem.Duration(hh:mm:ss)')
            h,m,s = duration.split(':')
            duration = int(timedelta(hours=int(h),minutes=int(m),seconds=int(s)).total_seconds())
        except:
            duration = ""
        if os.path.exists(playing_path):
            filehandle = open(playing_path, 'rb')
            data_history = pickle.load(filehandle)
            filehandle.close()
        else:
            data_history = []
        json_history = {}
        json_history["title"] = studio + "    [B]" + originaltitle + "[/B]"
        json_history["originaltitle"] = originaltitle
        json_history["eventid"] = eventid
        json_history["thumb"] = thumb
        json_history["fanart"] = fanart
        json_history["plot"] = plot
        json_history["studio"] = studio
        json_history["duration"] = duration
        if json_history not in data_history:
            data_history.insert(0, json_history)
        filehandle = open(playing_path, 'wb')
        pickle.dump(data_history, filehandle)
        filehandle.close()
    else:
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30032), xbmcgui.NOTIFICATION_INFO, 3000)


def list_menu():
    name_list = [(lng(30000), "DefaultAddonPVRClient.png", "0"), (lng(30001), "DefaultMovies.png", "1"), (lng(30003), "DefaultVideoPlaylists.png", "2"), (lng(30004), "DefaultAddonsSearch.png", "3"), (lng(30005), "DefaultRecentlyAddedMovies.png", "4")]
    for category in name_list:
        list_item = xbmcgui.ListItem(label=category[0])
        list_item.setArt({'thumb':category[1] , 'icon': category[1]})
        url = get_url(action='listing_menu', id = category[2])
        if category[0] == lng(30005):
            list_item.addContextMenuItems([(lng(30006),'XBMC.RunPlugin({})'.format(get_url(action = "del_history_playing")))])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)


def playlist():
    path = addon.getSetting("playlist_folder")
    if path == '':
        xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30037), xbmcgui.NOTIFICATION_ERROR, 4000, sound = False)
        return
    id_path = os.path.join(xbmc.translatePath('special://home/addons/plugin.video.archivsledovanitv'),'resources', 'id.txt')
    file_id = open(id_path).read().splitlines()
    dict_id = {}
    for x in file_id:
        x = x.split("=")
        if x[1] != "":
            dict_id[x[0]] = x[1]
    f = open(path + "sledovanitv.m3u", "w")
    f.write("#EXTM3U\n")
    html = urlopen("https://sledovanitv.cz/api/playlist?format=m3u8&" + lq[addon.getSetting("quality")] + "&whitelogo=1&PHPSESSID=" + SESSID).read()
    data = json.loads(html)["channels"]
    for d in data:
        if d["timeshiftDuration"] != 0 and d["type"] == "tv" and d["locked"] == "none":
            if addon.getSetting("tvgid_enable") == "true":
                if dict_id.has_key(d["id"]):
                    f.write('#EXTINF:-1 tvg-id="' + dict_id[d["id"]] + '",'+ d["name"] +'\n' + 'plugin://plugin.video.archivsledovanitv/?action=play_pvr&id=' + d["id"] + '\n')
                else:
                    f.write("#EXTINF:-1,"+ d["name"] +"\n" + "plugin://plugin.video.archivsledovanitv/?action=play_pvr&id=" + d["id"] + "\n")
            else:
                f.write("#EXTINF:-1,"+ d["name"] +"\n" + "plugin://plugin.video.archivsledovanitv/?action=play_pvr&id=" + d["id"] + "\n")
    f.close()
    xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30017), xbmcgui.NOTIFICATION_INFO, 4000, sound = False)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "listing_menu":
            if params["id"] == "0":
                list_channels()
            elif params["id"] == "1":
                list_tv_tips_category()
            elif params["id"] == "2":
                list_records()
            elif params["id"] == "3":
                menu_search()
            elif params["id"] == "4":
                history()
        elif params['action'] == 'listing_search':
            search(params['name'])
        elif params['action'] == 'listing_query':
            query_search()
        elif params['action'] == 'listing_days':
            list_days(params['id'], params['icon'])
        elif params['action'] == 'listing_videos':
            list_videos(params['day'], params['id'], params['icon'])
        elif params['action'] == 'play':
            play_video(params["eventid"])
        elif params['action'] == 'play_record':
            play_records(params["eventid"])
        elif params['action'] == 'play_live':
            play_live_video(params["id"], params["name"], params["icon"])
        elif params['action'] == 'play_pvr':
            play_pvr_live(params["id"])
        elif params['action'] == 'play_pvre':
            play_pvr_epg(params["channel"], params["date"], params["title"])
        elif params['action'] == 'downloading':
            download(params["name"], params["eventid"], params["evt"])
        elif params['action'] == 'add_recording':
            html = urlopen("https://sledovanitv.cz/api/record-event?eventId=" + params["eventid"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30017), xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
        elif params['action'] == 'add_serie':
            html = urlopen("https://sledovanitv.cz/api/activate-rule?ruleId=" + params["ruleid"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30017), xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
                xbmc.executebuiltin('Container.Refresh')
        elif params['action'] == 'del_record':
            html = urlopen("https://sledovanitv.cz/api/delete-record?recordId=" + params["id"] + "&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30030), xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
                xbmc.executebuiltin('Container.Refresh')
        elif params['action'] == 'del_serie':
            html = urlopen("https://sledovanitv.cz/api/delete-rule?ruleId=" + params["ruleid"] + "&cascade=1&PHPSESSID=" + SESSID).read()
            data = json.loads(html)
            if data["status"] == 1:
                xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30030), xbmcgui.NOTIFICATION_INFO, 3000, sound = False)
                xbmc.executebuiltin('Container.Refresh')
        elif params['action'] == 'un_pair':
            unpair()
        elif params['action'] == 'listing_tv_tips':
            list_tv_tips(params["eventid"])
        elif params['action'] == 'del_history_playing':
            if os.path.exists(playing_path):
                xbmcvfs.delete(playing_path)
            xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30029), xbmcgui.NOTIFICATION_INFO, 2000, sound = False)
        elif params['action'] == 'del_history_item':
            filehandle = open(playing_path, 'rb')
            name_list = pickle.load(filehandle)
            filehandle.close()
            del name_list[int(params["item_index"])]
            filehandle_save = open(playing_path, 'wb')
            pickle.dump(name_list, filehandle_save)
            filehandle_save.close()
            xbmc.executebuiltin('Container.Refresh')
        elif params['action'] == 'playlist':
            playlist()
        elif params['action'] == 'del_search_history':
                if os.path.exists(history_path):
                    xbmcvfs.delete(history_path)
                    xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30029), xbmcgui.NOTIFICATION_INFO, 2000, sound = False)
                    xbmc.executebuiltin('Container.Refresh')
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        if PIN == 0:
            xbmcgui.Dialog().notification("Archiv SledovaniTV",lng(30031), xbmcgui.NOTIFICATION_ERROR, 3000, sound = False)
        list_menu()
