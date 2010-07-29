from PMS import Plugin, Log, XML, HTTP, JSON, Prefs, RSS, Utils
from PMS.MediaXML import *
from PMS.FileTypes import PLS
from PMS.Shorthand import _L, _R, _E, _D

JOOST_PLUGIN_PREFIX = "/video/joost"
JOOST_SEARCH_URL = "http://search-dca.joost.com/search/select/?spellcheck=true&json_function=searchPage.handleResponse&q=%s&rows=100"
####################################################################################################
def Start():
  # Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
  Plugin.AddRequestHandler(JOOST_PLUGIN_PREFIX, HandleVideosRequest, "Joost", "icon-default.jpg", "art-default.jpg")
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", contentType="items")  
  Plugin.AddViewGroup("List", viewMode="List", contentType="items")
####################################################################################################

def populateFromFeed(url, feedtype, pathNouns="", dir=""):
  pathNouns = pathNouns.split("||")[0]
  if feedtype == "directory":
    url = url.replace("?fmt=atom","more/o/text/?fmt=atom")
    feed = RSS.Parse(url)
    for entry in feed["entries"]:
      id = _E(entry.id[0:entry.id.find("/t/")] + "?fmt=atom")
      title = entry.title
      thumb = XML.ElementFromString(entry.content[0].value, True).xpath("//img")[0].get("src")
      dir.AppendItem(DirectoryItem(id + "||" + title, title, thumb))
  elif feedtype == "videoitem":
    if pathNouns == "film" or pathNouns == "music":
      url = url.replace("?fmt=atom","more/o/text/?fmt=atom")
    feed = RSS.Parse(url)
    samePrefix = False
    for entry in feed["entries"]: #quick loop to see if all the titles have the same prefix or not
      if not samePrefix:
        prefix = entry.title[:entry.title.find(":")+1]
        samePrefix = True
      else:
        if not prefix == entry.title[:entry.title.find(":")+1]:
          samePrefix = False
          break
    for entry in feed["entries"]:
      if pathNouns == "shows":
        id = entry.id
      if pathNouns == "film" or pathNouns == "music":
        id = entry.id.replace("http://www.joost.com/","http://www.joost.com/home?playNow=")
        id = id[0:id.find("/t/")]
        
      if samePrefix:
        title = entry.title.replace(prefix,"")
      else: title = entry.title
      desc = unicode(XML.ElementFromString(entry.content[0].value,True).text_content()).strip()
      #Log.Add(str(desc))
      duration = ""
      try:
        thumb = XML.ElementFromString(entry.content[0].value, True).xpath("//img")[0].get("src")
      except:
        thumb = ""
      Log.Add(id)
      dir.AppendItem(WebVideoItem(id, title, desc, duration, thumb))
  return dir
  
def HandleVideosRequest(pathNouns, count):
  try:
    title2 = pathNouns[count-1].split("||")[1]
    pathNouns[count-1] = pathNouns[count-1].split("||")[0]
  except:
    title2 = ""
  
  if count == 0: vg="List"
  else: vg="InfoList"
  
  dir = MediaContainer("art-default.jpg", viewGroup=vg, title1="Joost", title2=title2)  
  if count == 0:
    dir.AppendItem(DirectoryItem("shows||" + _L("Shows"), _L("Shows"), ""))
    dir.AppendItem(DirectoryItem("music||" + _L("Music"), _L("Music"), ""))
    dir.AppendItem(DirectoryItem("film||" + _L("Film"), _L("Film"), ""))
    dir.AppendItem(SearchDirectoryItem("search||" + _L("Search Joost"), _L("Search Joost"), _L("Search Joost"), _R("search.png")))

  elif pathNouns[0].startswith("shows"):
    if count == 1:
      x=0
      for feedlink in XML.ElementFromURL("http://www.joost.com/feeds/", True).xpath("//p/a[contains(@href,'epg/" + pathNouns[0] + "/')]"):
        title = feedlink.text_content()
        if x == 0:
          title = "All " + title
        else:
          title = title.replace("Shows: ","")
        dir.AppendItem(DirectoryItem(_E(feedlink.get("href")) + "||" + title, title, ""))
        x+=1
    if count == 2:
      dir = populateFromFeed(_D(pathNouns[1]), feedtype="directory", dir=dir)
    if count == 3:
      dir = populateFromFeed(_D(pathNouns[2]).replace("joost.com/","joost.com/api/metadata/get/"), feedtype="videoitem",pathNouns=pathNouns[0], dir=dir) 

  elif pathNouns[0].startswith("film") or pathNouns[0].startswith("music"):
    if count == 1:
      x=0
      for feedlink in XML.ElementFromURL("http://www.joost.com/feeds/", True).xpath("//p/a[contains(@href,'epg/" + pathNouns[0] + "/')]"):
        title = feedlink.text_content()
        if x == 0: 
          title = "All " + title
        else:
          title = title.replace("Film: ","").replace("Music: ","")
        dir.AppendItem(DirectoryItem(_E(feedlink.get("href")) + "||" + title, title, ""))
        x+=1
    if count == 2:
      dir = populateFromFeed(_D(pathNouns[1]),feedtype="videoitem", pathNouns=pathNouns[0], dir=dir)

  elif pathNouns[0].startswith("search"):
    if count > 1:
      query = pathNouns[1]
      if count > 2:
        for i in range(2, len(pathNouns)): query += "/%s" % pathNouns[i]
      callback = HTTP.Get(JOOST_SEARCH_URL % query)
      if callback is None: return None
      callback = callback.lstrip("searchPage.handleResponse(")[:-1].replace(":new",":").replace("Date(",'"').replace("000)",'000"')
      d = JSON.DictFromString(callback)
      for item in d["response"]["docs"]:
        thumb = item["thumbnail"]
        dir.AppendItem(WebVideoItem("http://www.joost.com/"+item["publicId"], item["title"], item["description"], str(item["duration"]), thumb))
      if dir.ChildCount() == 0:
        dir.AppendItem(DirectoryItem("%s/search" % JOOST_PLUGIN_PREFIX, "(No Results)", ""))
  
  return dir.ToXML()