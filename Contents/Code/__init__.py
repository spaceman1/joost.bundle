import urllib

JOOST_PLUGIN_PREFIX = "/video/joost"
JOOST_SEARCH_URL = "http://www.joost.com/b/search/video?count=8&start=0&q=%s"

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

def MainMenu():
	dir = MediaContainer(viewGroup='_List', title1="Joost")  

	dir.Append(Function(DirectoryItem(ShowsMenu, title=L("Shows")), id='/shows'))
	dir.Append(Function(DirectoryItem(ShowsMenu, title=L("Music")), id='/music'))
	dir.Append(Function(DirectoryItem(ShowsMenu, title=L("Film")), id='/film'))
	dir.Append(Function(InputDirectoryItem(Search, prompt=L("Search Joost"), title=L("Search Joost"), thumb=R("search.png"))))
	return dir

def getGenre(id):
	r = HTTP.Request('http://www.joost.com/b/containers/genre?count=20&id=%s&sort=popularity&start=0' % id.replace('/', '%2F')).content
	return JSON.ObjectFromString(r)['items']	

def ShowsMenu(sender, id):
	dir = MediaContainer(title2=sender.itemTitle)
	feeds = JSON.ObjectFromString(HTTP.Request('http://www.joost.com/#/shows?type=featured').content.split('_joostCache =')[1].split(';\n')[0])
	section = filter(lambda x: x['id'] == id, feeds['genres'])[0]
	for item in section['children']:
		if len(getGenre(item['id'])):
			dir.Append(Function(DirectoryItem(GenreMenu, title=item['name']), id=item['id'])) 
	return dir

def GenreMenu(sender, id):
	dir = MediaContainer(title2=sender.itemTitle)
	for item in getGenre(id):
		summary = item['description']
		id = item['id']
		thumb = item['images']['logo']
		title = item['title']
		dir.Append(Function(DirectoryItem(ShowMenu, title=title, thumb=thumb, summary=summary), id=id))
	return dir

def ShowMenu(sender, id):
	dir = MediaContainer(title2=sender.itemTitle)
	for item in JSON.ObjectFromURL('http://www.joost.com/b/videos/container?count=50&id=%s&start=0' % id)['items']:
		summary = item['description']
		thumb = item['images']['thumbnail']
		title = item['title']
		dir.Append(Function(VideoItem(Play, title=title, thumb=thumb, summary=summary), id=item['id']))
	return dir

def Search(sender, query):
	dir = MediaContainer(title2=sender.itemTitle)
	page = HTTP.Request(JOOST_SEARCH_URL % query).content
	#page = page.lstrip("searchPage.handleResponse(")[:-1].replace(":new",":").replace("Date(",'"').replace("000)",'000"')
	d = JSON.ObjectFromString(page)
	for item in d["items"]:
		dir.Append(Function(VideoItem(Play, title=item["title"], summary=item["description"], duration=int(item["duration"]), thumb=item['images']['thumbnail']), id=item["id"]))
	if len(dir) == 0:
		return MessageContainer('No Results', 'No results.')
	return dir

def Play(sender, id):
	stream = XML.ElementFromURL('http://www.joost.com/player/api/1/metadata/embedded/' + id).xpath('//stream[@profile="STANDARD"]')[0].get('file')
	# Work your magic here
	return Redirect('...')