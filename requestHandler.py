import base64
import webbrowser
from urllib.parse import urlencode

import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import secrets # file that contains your API key
import time
import sqlite3
from flask import Flask, render_template

CLIENT_SECRET = 'ecf3ff7d354741468d66ae216276f305'
CLIENT_ID = '8c3a7ba894f74164a797d3e0512b7f82'
spotify_username = '31ksezewtk5zlagthryjgp4sbqwm'
LAST_FM_KEY = '304036bcba16c776159057cf1ea09aa2'

CACHE_FILE_NAME = 'cacheArtistSearch.json'
CACHE_DICT = {}
AUTH_URL = 'https://accounts.spotify.com/api/token'
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})
auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']

headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}

SPOTIFY_BASE = 'https://api.spotify.com/v1/'
LAST_FM_BASE = 'http://ws.audioscrobbler.com/2.0/?'


def load_cache():
    '''opens cache file to store information

    Parameters
    ----------
    None

    Returns
    ----------
    cache: json
    a json that stores previous search results
    '''    
    try:       
        cache_file = open(CACHE_FILE_NAME, 'r')        
        cache_file_contents = cache_file.read()        
        cache = json.loads(cache_file_contents)        
        cache_file.close()    
    except:        
        cache = {}    
    return cache

def save_cache(cache):
    ''' saves existing or new cache to contain previous searches and calls to the nps website
    
    Parameters
    ----------
    cache: json
    cache in which to write the search into

    Returns
    ----------
    None
    '''    
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)    
    cache_file.write(contents_to_write)    
    cache_file.close()

def make_url_request_using_cache(url, cache, search_header=None):
    ''' searches cache to see if search has been made before if search has been made, takes information from cache

    Parameters
    ----------
    url: str
    the url of the request being made

    cache: json
    the json file to search and see if url call has been made previously
    '''    
    if (url in cache.keys()): # the url is our unique key        
        print("Using cache")        
        return cache[url]   
    else:
        if search_header:
            print("Fetching")        
            time.sleep(1)        
            response = requests.get(url, headers=headers)        
            cache[url] = response.json()        
            save_cache(cache)        
            return cache[url]
        else:
            print("Fetching")        
            time.sleep(1)        
            response = requests.get(url)        
            cache[url] = response.json()        
            save_cache(cache)        
            return cache[url]

import sys
def getImageArtist(artist_name):
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET))

    if len(sys.argv) > 1:
        name = ' '.join(sys.argv[1:])
    else:
        name = artist_name

    results = spotify.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
        return artist['images'][0]['url']

def last_fm_search(artist):
    '''creates dictionary of artist and mbid(if one exists)

    Parameters
    ----------
    artist: str
    search term for artist search

    Returns
    ----------
    artist_dict: dict
    a dictionary that lists all entries associated with the search term taken from the LastFM API
    '''   
    response = requests.get(LAST_FM_BASE + f'method=artist.search&artist={artist}&api_key={LAST_FM_KEY}&limit=10&format=json')
    response = response.json()
    results = response['results']['artistmatches']['artist']
    artist_dict = {}
    return results[0]['name']
    # for item in results:
    #     k = item['name']
    #     v = item['mbid']
    #     artist_dict[k] = v
    # return artist_dict,k


def getTopArtists():
    API_KEY = LAST_FM_KEY
    USER_AGENT = 'Sasank'

    url = 'https://ws.audioscrobbler.com/2.0/'
    param = {}
    header = {
        'user-agent': USER_AGENT
    }

    param['api_key'] = API_KEY
    param['method'] = 'chart.gettopartists'
    param['format'] = 'json'
    response = requests.get(url, headers=header, params=param)
    top_artists = []
    for item in range(10):
        x = response.json()['artists']['artist'][item]['name']
        y = response.json()['artists']['artist'][item]['playcount']
        z = getImageArtist(x)
        top_artists.append((x,y,z))
    return top_artists

def getTokenSpotify():


    encoded_credentials = base64.b64encode(CLIENT_ID.encode() + b':' + CLIENT_SECRET.encode()).decode("utf-8")

    token_headers = {
        "Authorization": "Basic " + encoded_credentials,
    }

    token_data = {
        "grant_type": "authorization_code",
    }

    r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    return r
def topGlobal():
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Specify the country code for which you want to fetch the top charts
    country_code = 'IN'
    top_artist = []
    # Get the top 10 tracks for the specified country
    top_tracks = sp.playlist_items('spotify:playlist:37i9dQZEVXbLRQDuF5jeBp', market=country_code, limit=10)
    for i in range(10):
        y = top_tracks['items'][i]['track']['artists'][0]['name']
        x = top_tracks['items'][i]['track']['name']
        z = top_tracks['items'][i]['track']['album']['images'][0]['url']
        top_artist.append((x,y,z))
    return top_artist

def getTopTracksUser(username='sasankmadati'):
    API_KEY = LAST_FM_KEY
    USER_AGENT = 'Sasank'

    url = 'https://ws.audioscrobbler.com/2.0/'
    param = {}
    header = {
        'user-agent': USER_AGENT
    }
    param = {}
    param['method'] = 'user.gettoptracks'
    param['user'] = username
    param['period'] = '7day'
    param['api_key'] = API_KEY
    param['format'] = 'json'
    response = requests.get(url, headers=header, params=param)
    top_tracks = []
    for item in range(10):
        x = response.json()['toptracks']['track'][item]['name']
        y = albumImage(x)
        # y = response.json()['toptracks']['track'][item]['playcount']
        top_tracks.append((x,y))
    return top_tracks


def getTags(artist):
    param = {}
    url = 'https://ws.audioscrobbler.com/2.0/'
    USER_AGENT = 'sasank'
    param['api_key'] = LAST_FM_KEY
    param['method'] = 'artist.gettoptags'
    param['format'] = 'json'
    param['artist'] = artist
    header = {
        'user-agent': USER_AGENT
    }

    response = requests.get(url, headers=header, params=param)
    tags = [response.json()['toptags']['tag'][i]['name'] for i in range(5)]
    return tags

def albumImage(song):
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET))

    if len(sys.argv) > 1:
        name = ' '.join(sys.argv[1:])
    else:
        name = song

    results = spotify.search(q='track:' + name, type='track')

    if len(results['tracks']['items'])>0:
        a = results['tracks']['items'][0]['album']['images'][0]['url']
        return a
    else:
        return None
class Artist:
    def __init__(self, name= None, artist_url= None,
                 top_tracks = [], top_albums= [], 
                 similar= {}, playlists= {}, 
                 top_tags= [], top_songs_by_tag = []):
        self.artist_url = artist_url
        self.name = name
        self.top_tracks = top_tracks
        self.top_albums = top_albums
        self.similar = similar
        self.playlists = playlists
        self.top_tags = top_tags
        self.search_term = None
        self.top_songs_by_tag = top_songs_by_tag

        stop_characters = {' ': '%20', '&': '%26'}
        for character, value in stop_characters.items():
         if character in self.name:
                self.search_term = self.name.replace(character, value)
        else:
            self.search_term = self.name


    
    def artist_info(self):
        '''grabs information about an artist from LastFM API, stores artist url in self.artist_url

        Parameters
        ----------

        Returns
        ----------
        '''
        url = LAST_FM_BASE + f'method=artist.getinfo&artist={self.search_term}&api_key={LAST_FM_KEY}&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['artist']
        self.artist_url = results['url']
        self.name = self.name
    
    def get_top_tracks(self):
        '''grabs top tracks of an artist from LastFM API, stores tracks in self.top_tracks list

        Parameters
        ----------

        Returns
        ----------
        '''
        self.top_tracks.clear()
        url = LAST_FM_BASE + f'method=artist.gettoptracks&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=10&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['toptracks']['track']
        for item in results:
            song = item['name']
            self.top_tracks.append(song)

    def get_top_albums(self):
        '''grabs top albums of an artist from LastFM API, stores albums in self.top_albums

        Parameters
        ----------

        Returns
        ----------
        '''
        self.top_albums.clear()
        url = LAST_FM_BASE + f'method=artist.gettopalbums&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['topalbums']['album']
        for item in results:
            album = item['name']
            self.top_albums.append(album)

    def get_top_tags(self):
        '''grabs top tags of an artist from LastFM API, stores tags in self.top_tags

        Parameters
        ----------

        Returns
        ----------
        '''
        self.top_tags.clear()
        url = LAST_FM_BASE + f'method=artist.gettoptags&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['toptags']['tag']
        for item in results:
            tag = item['name']
            self.top_tags.append(tag)

    def get_similar(self):
        '''grabs artists similar to an artist from LastFM API, stores artist names and urls in self.similar

        Parameters
        ----------

        Returns
        ----------
        '''
        self.similar.clear()
        url = LAST_FM_BASE + f'method=artist.getsimilar&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['similarartists']['artist']
        for item in results:
            related_artist = item['name']
            related_artist_url = item['url']
            self.similar[related_artist] = related_artist_url
    
    def get_tag_charts(self):
        '''searches charts of the first 10 tags in self.top_tags, creates list of touples with the song, rank, and chart the song is featured in.

        Parameters
        ----------

        Returns
        ----------
        '''
        self.top_songs_by_tag.clear()
        for tag in self.top_tags[0:10]:
            url = LAST_FM_BASE + f'method=tag.gettoptracks&tag={tag}&api_key={LAST_FM_KEY}&limit=05&format=json'
            response = make_url_request_using_cache(url, CACHE_DICT)
            results = response['tracks']['track']
            for song in results:
                track = song['name']
                rank = song['@attr']['rank']
                if song['artist']['name'].lower() == self.name.lower():
                    self.top_songs_by_tag.append((track, rank, tag))


    def get_playlists(self):
        '''grabs top playlists of an artist from Spotify API, stores playlists in self.playlists

        Parameters
        ----------

        Returns
        ----------
        '''
        self.playlists.clear()
        url = SPOTIFY_BASE + 'search?q=' + self.search_term + '&type=playlist&limit=10'
        response = make_url_request_using_cache(url, CACHE_DICT, search_header=headers)
        results = response['playlists']['items']
        for item in results:
            playlist = item['name']
            playlist_url = item['external_urls']['spotify']
            self.playlists[playlist] = playlist_url

def build_artist_profile(artist_inst):
    '''builds up artist instantiation by implementing all functions within the class.

        Parameters
        ----------
        artist_inst = class instance

        Returns
        ----------
        '''
    artist_inst.artist_info()
    artist_inst.get_top_tracks()
    artist_inst.get_top_albums()
    artist_inst.get_top_tags()
    artist_inst.get_tag_charts()
    artist_inst.get_similar()
    artist_inst.get_playlists()

