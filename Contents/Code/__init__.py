import urllib

JOOST_PLUGIN_PREFIX = "/video/joost"
JOOST_SEARCH_URL = "http://search-dca.joost.com/search/select/?spellcheck=true&json_function=searchPage.handleResponse&q=%s&rows=100"

####################################################################################################

def Start():
	# Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
	Plugin.AddPrefixHandler(JOOST_PLUGIN_PREFIX, MainMenu, "Joost", "icon-default.jpg", "art-default.jpg")
	Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")  
	Plugin.AddViewGroup("_List", viewMode="List", mediaType="items")
	DirectoryItem.art = R('art-default.jpg')
	DirectoryItem.thumb = R('icon-default.jpg')
	MediaContainer.viewGroup = 'Details'
####################################################################################################

def populateFromFeed(url, feedtype, type='', dir=""):
	if feedtype == "directory":
		url = url.replace("?fmt=atom","more/o/text/?fmt=atom")
		feed = RSS.Parse(url)
		for entry in feed["entries"]:
			id = String.Quote(entry.id[0:entry.id.find("/t/")] + "?fmt=atom")
			title = entry.title
			thumb = HTML.ElementFromString(entry.content[0].value).xpath("//img")[0].get("src")
			dir.Append(DirectoryItem(id + "||" + title, title, thumb))
	elif feedtype == "videoitem":
		if type == "film" or type == "music":
			url = url.replace("?fmt=atom", "more/o/text/?fmt=atom")
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
			if type == "shows":
				id = entry.id
			if type == "film" or type == "music":
				id = entry.id.replace("http://www.joost.com/","http://www.joost.com/home?playNow=")
				id = id[0:id.find("/t/")]
				
			if samePrefix:
				title = entry.title.replace(prefix,"")
			else: title = entry.title
			desc = HTML.ElementFromString(entry.content[0].value).text_content().strip()
			#Log.Add(str(desc))
			duration = ""
			try:
				thumb = HTML.ElementFromString(entry.content[0].value).xpath("//img")[0].get("src")
			except:
				thumb = ""
			Log.Add(id)
			dir.Append(WebVideoItem(id, title, desc, duration, thumb))
	return dir

def MainMenu():
	dir = MediaContainer(viewGroup='_List', title1="Joost")  

	dir.Append(Function(DirectoryItem(ShowsMenu, title=L("Shows")), id='/shows'))
	dir.Append(Function(DirectoryItem(ShowsMenu, title=L("Music")), id='/music'))
	dir.Append(Function(DirectoryItem(ShowsMenu, title=L("Film")), id='/film'))
	dir.Append(Function(InputDirectoryItem(Search, prompt=L("Search Joost"), title=L("Search Joost"), thumb=R("search.png"))))
	return dir

def ShowsMenu(sender, id):
	dir = MediaContainer(title2=sender.itemTitle)
	feeds = JSON.ObjectFromString(HTTP.Request('http://www.joost.com/#/shows?type=featured').content.split('_joostCache =')[1].split(';\n')[0])
	section = filter(lambda x: x['id'] == id, feeds['genres'])[0]
	for item in section['children']:
		dir.Append(Function(DirectoryItem(GenreMenu, title=item['name']), id=item['id'])) 
	return dir

def GenreMenu(sender, id):
	dir = MediaContainer(title2=sender.itemTitle)
	f = urllib.urlopen('http://www.joost.com/b/containers/genre?count=20&id=%s&sort=popularity&start=0' % id.replace('/', '%2F'))
	r = f.read()
	f.close()
	for item in JSON.ObjectFromString(r)['items']:
		summary = item['description']
		id = item['id']
		thumb = item['images']['logo']
		title = item['title']
		dir.Append(Function(DirectoryItem(ShowMenu, title=title, thumb=thumb, summary=summary), id=id))
	return dir

def ShowMenu(sender, id):
	pass

def Search(sender, query):
	pass
def HandleVideosRequest(pathNouns, count):
	try:
		title2 = pathNouns[count-1].split("||")[1]
		pathNouns[count-1] = pathNouns[count-1].split("||")[0]
	except:
		title2 = ""
	
	if count == 0: vg="List"
	else: vg="InfoList"
	
	if False: pass
	elif pathNouns[0].startswith("shows"):
		if count == 1:
			pass	
		if count == 2:
			dir = populateFromFeed(String.Unquote(pathNouns[1]), feedtype="directory", dir=dir)
		if count == 3:
			dir = populateFromFeed(String.Unquote(pathNouns[2]).replace("joost.com/","joost.com/api/metadata/get/"), feedtype="videoitem",pathNouns=pathNouns[0], dir=dir) 

	elif pathNouns[0].startswith("film") or pathNouns[0].startswith("music"):
		if count == 1:
			x=0
			for feedlink in HTML.ElementFromURL("http://www.joost.com/feeds/").xpath("//p/a[contains(@href,'epg/" + pathNouns[0] + "/')]"):
				title = feedlink.text
				if x == 0: 
					title = "All " + title
				else:
					title = title.replace("Film: ","").replace("Music: ","")
				dir.Append(DirectoryItem(String.Quote(feedlink.get("href")) + "||" + title, title, ""))
				x+=1
		if count == 2:
			dir = populateFromFeed(String.Unquote(pathNouns[1]),feedtype="videoitem", pathNouns=pathNouns[0], dir=dir)

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
				dir.Append(WebVideoItem("http://www.joost.com/"+item["publicId"], item["title"], item["description"], str(item["duration"]), thumb))
			if dir.ChildCount() == 0:
				dir.Append(DirectoryItem("%s/search" % JOOST_PLUGIN_PREFIX, "(No Results)", ""))
	
	return dir