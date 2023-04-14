import base64
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import time
import sqlite3
from flask import Flask, render_template
CLIENT_ID = '8c3a7ba894f74164a797d3e0512b7f82'
LAST_FM_KEY = '304036bcba16c776159057cf1ea09aa2'
CLIENT_SECRET = 'ecf3ff7d354741468d66ae216276f305'

def init_user():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri='http://localhost:7777/callback', scope='user-top-read'))
    user = sp.current_user()
    spotify_username = user['id']
    return spotify_username

spotify_username = init_user()


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
    """opens cache file to store information from previous searches"""
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    """ saves existing or new cache to contain previous searches and calls to the nps website"""
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache, search_header=None):
    if (url in cache.keys()):  # the url is our unique key
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
    """creates dictionary of artist and mid(if one exists)"""
    response = requests.get(
        LAST_FM_BASE + f'method=artist.search&artist={artist}&api_key={LAST_FM_KEY}&limit=10&format=json')
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
        top_artists.append((x, y, z))
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
    country_code = 'US'
    top_artist = []
    # Get the top 10 tracks for the specified country
    top_tracks = sp.playlist_items('spotify:playlist:37i9dQZEVXbNG2KDcFcKOF', market=country_code, limit=10)
    for i in range(10):
        y = top_tracks['items'][i]['track']['artists'][0]['name']
        x = top_tracks['items'][i]['track']['name']
        z = top_tracks['items'][i]['track']['album']['images'][0]['url']
        top_artist.append((x, y, z))
    return top_artist


def getUserArtists(term):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri='http://localhost:7777/callback', scope='user-top-read',
                                                   username=spotify_username))
    results = sp.current_user_top_artists(limit=10, time_range=term)
    topUserArtists = []
    for item in range(10):
        x = results['items'][item]['name']
        y = results['items'][item]['popularity']
        # image url here
        z = results['items'][item]['images'][0]['url']
        topUserArtists.append((x, y, z))
    return topUserArtists


def getTopTracksUser(username='sasankmadati', term='short_term'):
    # create a SpotifyOAuth object to authenticate the user
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri='http://localhost:7777/callback',
                                                   scope='user-top-read', username=spotify_username))

    # get the user's top 10 tracks
    results = sp.current_user_top_tracks(limit=10, time_range=term)
    topUserTracks = []
    for item in range(10):
        x = results['items'][item]['name']
        # album name here
        y = results['items'][item]['album']['name']
        # image url here
        z = results['items'][item]['album']['images'][0]['url']
        topUserTracks.append((x, y, z))
    print(topUserTracks)
    return topUserTracks


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

    if len(results['tracks']['items']) > 0:
        a = results['tracks']['items'][0]['album']['images'][0]['url']
        return a
    else:
        return None


class Artist:
    def __init__(self, name=None, artist_url=None,
                 top_tracks=[], top_albums=[],
                 similar={}, playlists={},
                 top_tags=[], top_songs_by_tag=[]):
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
        """grabs information about an artist from LastFM API, stores artist url in self.artist_url"""
        url = LAST_FM_BASE + f'method=artist.getinfo&artist={self.search_term}&api_key={LAST_FM_KEY}&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['artist']
        self.artist_url = results['url']
        self.name = self.name

    def get_top_tracks(self):
        """grabs top tracks of an artist from LastFM API, stores tracks in self.top_tracks list
        """
        self.top_tracks.clear()
        url = LAST_FM_BASE + f'method=artist.gettoptracks&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=10&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['toptracks']['track']
        for item in results:
            song = item['name']
            self.top_tracks.append(song)

    def get_top_albums(self):
        """grabs top albums of an artist from LastFM API, stores albums in self.top_albums"""
        self.top_albums.clear()
        url = LAST_FM_BASE + f'method=artist.gettopalbums&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['topalbums']['album']
        for item in results:
            album = item['name']
            self.top_albums.append(album)

    def get_top_tags(self):
        """grabs top tags of an artist from LastFM API, stores tags in self.top_tags"""
        self.top_tags.clear()
        url = LAST_FM_BASE + f'method=artist.gettoptags&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['toptags']['tag']
        for item in results:
            tag = item['name']
            self.top_tags.append(tag)

    def get_similar(self):
        """grabs artists similar to an artist from LastFM API, stores artist names and urls in self.similar"""
        self.similar.clear()
        url = LAST_FM_BASE + f'method=artist.getsimilar&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, CACHE_DICT)
        results = response['similarartists']['artist']
        for item in results:
            related_artist = item['name']
            related_artist_url = item['url']
            self.similar[related_artist] = related_artist_url

    def get_tag_charts(self):
        """searches charts of the first 10 tags in self.top_tags, creates list of touples with the song, rank,
        and chart the song is featured in."""
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


def getHistory():
    # get users listening history using spotipy
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri='http://localhost:7777/callback',
                                                   scope='user-read-recently-played', username=spotify_username))
    results = sp.current_user_recently_played(limit=50)
    history = []
    for item in results['items']:
        artist = item['track']['artists'][0]['name']
        song = item['track']['name']
        # image of the song
        image = item['track']['album']['images'][0]['url']
        timestamp = item['played_at']
        timestamp = timestamp[:19]

        # print(timestamp)
        # convert timestamp from zulu to ist
        timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
        timestamp = timestamp + timedelta(hours=5, minutes=30)
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
        # convert into AM and PM
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
        timestamp = timestamp.strftime('%Y-%m-%d %I:%M %p')






        history.append((artist, song, image, timestamp))
    return history


def getGenres(username, term):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri='http://localhost:7777/callback',
                                                   scope='user-top-read', username=spotify_username))
    topTracks = sp.current_user_top_tracks(limit=50, time_range=term)
    genres = []
    for item in range(50):
        x = topTracks['items'][item]['artists'][0]['id']
        y = sp.artist(x)
        for genre in y['genres']:
            genres.append(genre)
    # count the occurence of each genre
    genreCount = {}
    for genre in genres:
        if genre in genreCount:
            genreCount[genre] += 1
        else:
            genreCount[genre] = 1
    total = sum(genreCount.values())
    top10 = sum(sorted(genreCount.values(), reverse=True)[:15])
    # sort the dictionary by value
    sortedGenres = sorted(genreCount.items(), key=lambda x: x[1], reverse=True)
    data = list()
    for item in sortedGenres[:12]:
        data.append([item[0], item[1]])
    # add to the front of the list, ["Task":"Genres"]
    # data.insert(0, ["Task", "Genres"])
    for item in data:
        print(item[0], int(item[1]))
    return data


def getRecommendationsByGenre(playlist):
    scope = 'user-library-read playlist-modify-public playlist-read-private'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                   redirect_uri='http://localhost:7777/callback',
                                                   scope=scope))
    spotify_username = sp.me()['id']
    sourcePlaylist = sp.playlist(playlist)
    seed_ids = []
    for i in range(0, 10):
        seed_ids.append(sourcePlaylist['tracks']['items'][i]['track']['id'])
    rec_tracks = []
    for i in seed_ids:
        rec_tracks += sp.recommendations(seed_tracks=[i], limit=20)['tracks']
    recs_to_add = []
    for i in range(0, 20):
        recs_to_add.append(rec_tracks[i]['id'])
    playlist_recs = sp.user_playlist_create(spotify_username, name='Songs from {}'.format(sourcePlaylist['name']))
    sp.user_playlist_add_tracks(spotify_username, playlist_recs['id'], recs_to_add)
    return playlist_recs
