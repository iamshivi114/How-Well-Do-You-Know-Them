import urllib.request, urllib.error, urllib.parse, json, webbrowser, random
import flickr_key as flickr_key
from flask import Flask, render_template, request

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safe_get(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("The server couldn't fulfill the request." )
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We failed to reach a server")
        print("Reason: ", e.reason)
    return None

def flickr_rest(baseurl = 'https://api.flickr.com/services/rest/',
    method = 'flickr.photos.search',
    api_key = flickr_key.key,
    responseformat = 'json',
    params={},
    printurl = False
    ):
    fullparams = {
        'method':method,
        'api_key': api_key,
        'format': responseformat
    }
    fullparams.update(params)
    if responseformat == "json": fullparams["nojsoncallback"]=True
    url = baseurl + "?" + urllib.parse.urlencode(fullparams)
    if printurl:
        print(url)
    return safe_get(url)

def itunes(term, limit = 10, media = 'all'):
    paramstr = urllib.parse.urlencode({'term' : term, 'limit' : limit, 'media': media})
    url = "https://itunes.apple.com/search?" + paramstr
    data = safe_get(url)
    if (data == None):
        return None
    return json.loads(data.read())
    

def get_photo_ids(text, n = 100, sort = "relevance", content_type = 1):
    params = {"text": text, "per_page":n}
    flickr = json.loads(flickr_rest(params = params).read())
    idList = [x["id"] for x in flickr["photos"]["photo"]]
    return idList

def get_photo_info(photo_id):
    params = {"photo_id" : photo_id}
    return json.loads(flickr_rest(method = "flickr.photos.getInfo", params = params).read())['photo']

class FlickrPhoto():
    def __init__(self, photo_info):
        self.title = photo_info["title"]["_content"]
        self.author = photo_info["owner"]["username"]
        self.userid = photo_info["owner"]["nsid"]
        self.tags = [x["_content"] for x in photo_info["tags"]["tag"]]
        self.comments = int(photo_info["comments"]["_content"])
        self.views = int(photo_info["views"])
        self.url = photo_info["urls"]["url"][0]["_content"]
        self.server = photo_info["server"]
        self.id = photo_info["id"]
        self.secret = photo_info["secret"]
    def make_photo_url(self, size = "q"):
        return 'https://live.staticflickr.com/{}/{}_{}_{}.jpg'.format(self.server, self.id, self.secret, size)
    def __str__(self):
        return "~~~ {} ~~~\nauthor: {}\nnumber of tags: {}\nviews: {}\ncomments: {}\nurl: {}".format(self.title, self.author, len(self.tags), self.views, self.comments, self.url)

'''itunes_data = itunes('Selena Gomez')
elements = []
for i in range(0,5):
    elements.append(itunes_data['results'][i]['trackCensoredName'])
print(elements)
for element in elements:
    photo_ids = get_photo_ids(element, 5)
print(photo_ids)
list_of_photos = [FlickrPhoto(get_photo_info(ids)) for ids in photo_ids]
for photo in list_of_photos:
    print(photo)'''
app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template('home.html')


@app.route("/gresponse", methods = ['GET', 'POST'])
def search_results():
    if request.method=='POST':
        guess = request.form.get('guess')
        result = open('result.txt').read()
        if guess.lower() == result.lower():
            message = "You are correct!"
        else:
            message = "You're wrong, better luck next time!"
        return render_template('answer.html', guess = guess, result = result, message = message)
    else:
        photos = []
        results = []
        artist_name = request.args.get('artist_name')
        if artist_name:
            itunes_data = itunes(artist_name)
            for data in itunes_data['results']:
                try:
                    results.append(data['trackName'])
                except:
                    results.append(data['collectionName'])
            while True:
                try:
                    file = open('result.txt', 'w')
                    file.write(random.choice(results))
                    file.close()
                except:
                    return render_template('sorry.html')
                result = (open('result.txt')).read()
                if get_photo_ids(result, 1):
                    photos.append(get_photo_ids(result, 1)[0])
                    break
                else:
                    open('result.txt', 'w').close()
                    continue
            photo_id = photos[0]
            flickrphoto = FlickrPhoto(get_photo_info(photo_id))
            url = flickrphoto.make_photo_url()
            return render_template('search-results.html', url = url, artist_name = artist_name)
        else:
            return render_template('home.html')

if __name__ == "__main__":
    app.run(host='localhost', port=8080, debug=True)
