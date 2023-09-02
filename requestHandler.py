import sys
import base64
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os
from redis import Redis
from dotenv import load_dotenv
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_client = Redis(host=redis_host, port=6379)
import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time

import configparser

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
LAST_FM_KEY = os.getenv('LAST_FM_KEY')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
API_BASE = os.getenv('API_BASE')
scope = os.getenv('scope')
SHOW_DIALOG = os.getenv('SHOW_DIALOG')

def checkSessionTimeout():
    try:
        req = sp.playlist_items(
            'spotify:playlist:37i9dQZEVXbNG2KDcFcKOF', market='US', limit=10)
        print("Session is active")
        return True
    except:
        return False
    
def getAccessToken(code):
    config = configparser.ConfigParser()
    config.read('config.ini')
    REDIRECT_URI = config['SPOTIFY']['REDIRECT_URI']
    print(REDIRECT_URI, "sda")
    auth_token_url = f"{API_BASE}/api/token"
    res = requests.post(auth_token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    })
    access_token = res.json().get("access_token")
    global sp
    sp = spotipy.Spotify(auth=access_token)
    user = sp.current_user()
    global spotify_username
    spotify_username = user['id']
    return spotify_username



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


def make_url_request_using_cache(url, type, search_header=None):
    if search_header:
        if redis_client.get(f'{url}_{type}'):
            print("Cache Hit")
            return json.loads(redis_client.get(f'{url}_{type}'))
        else:
            print("Cache Miss")
            print("Fetching")
            response = requests.get(url, headers=headers)
            json_data= response.json()
            redis_client.setex(f'{url}_{type}',3600, json.dumps(json_data))
            return json_data
    else:
        if redis_client.get(f'{url}_{type}'):
            print("Cache Hit")
            return json.loads(redis_client.get(f'{url}_{type}'))
        else:
            print("Cache Miss")
            print("Fetching")
            time.sleep(1)
            response = requests.get(url)
            json_data = response.json()
            redis_client.setex(f'{url}_{type}',3600, json.dumps(json_data))
            return json_data


def getImageArtist(artist_name):
    spotify = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET))

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


def topGlobal():
    # auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    # sp = spotipy.Spotify(auth_manager=auth_manager)

    # Specify the country code for which you want to fetch the top charts
    country_code = 'IN'
    top_artist = []
    # Get the top 10 tracks for the specified country
    # simple try catch block to handle exceptions
    top_tracks = sp.playlist_items(
            'spotify:playlist:37i9dQZEVXbNG2KDcFcKOF', market=country_code, limit=10)
    for i in range(10):
        y = top_tracks['items'][i]['track']['artists'][0]['name']
        x = top_tracks['items'][i]['track']['name']
        z = top_tracks['items'][i]['track']['album']['images'][0]['url']
        top_artist.append([x, y, z])
    return top_artist


def getUserArtists(term):
    results = sp.current_user_top_artists(limit=10, time_range=term)
    topUserArtists = []
    for item in range(len(results['items'])):
        # print(len(results['items']))
        x = results['items'][item]['name']
        y = results['items'][item]['popularity']
        # image url here
        z = results['items'][item]['images'][0]['url']
        topUserArtists.append([x, y, z])
    return topUserArtists


def getTopTracksUser(term='short_term'):
    # create a SpotifyOAuth object to authenticate the user

    # get the user's top 10 tracks
    results = sp.current_user_top_tracks(limit=10, time_range=term)
    topUserTracks = []
    for item in range(10):
        x = results['items'][item]['album']['name']
        y = results['items'][item]['name']
        # image url here
        z = results['items'][item]['album']['images'][0]['url']
        topUserTracks.append([x, y, z])
    # print(topUserTracks)
    return topUserTracks



def albumImage(song):
    spotify = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET))

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
        url = LAST_FM_BASE + \
            f'method=artist.getinfo&artist={self.search_term}&api_key={LAST_FM_KEY}&format=json'
        response = make_url_request_using_cache(url, "info")
        results = response['artist']
        self.artist_url = results['url']
        self.name = self.name

    def get_top_tracks(self):
        """grabs top tracks of an artist from LastFM API, stores tracks in self.top_tracks list
        """
        self.top_tracks.clear()
        url = LAST_FM_BASE + \
            f'method=artist.gettoptracks&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=10&format=json'
        response = make_url_request_using_cache(url, "tracks")
        results = response['toptracks']['track']
        for item in results:
            song = item['name']
            self.top_tracks.append(song)

    def get_top_albums(self):
        """grabs top albums of an artist from LastFM API, stores albums in self.top_albums"""
        self.top_albums.clear()
        url = LAST_FM_BASE + \
            f'method=artist.gettopalbums&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, "albums")
        results = response['topalbums']['album']
        for item in results:
            album = item['name']
            self.top_albums.append(album)

    def get_top_tags(self):
        """grabs top tags of an artist from LastFM API, stores tags in self.top_tags"""
        self.top_tags.clear()
        url = LAST_FM_BASE + \
            f'method=artist.gettoptags&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, "tags")
        results = response['toptags']['tag']
        for item in results:
            tag = item['name']
            self.top_tags.append(tag)

    def get_similar(self):
        """grabs artists similar to an artist from LastFM API, stores artist names and urls in self.similar"""
        self.similar.clear()
        url = LAST_FM_BASE + \
            f'method=artist.getsimilar&artist={self.search_term}&api_key={LAST_FM_KEY}&limit=05&format=json'
        response = make_url_request_using_cache(url, "similar")
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
            url = LAST_FM_BASE + \
                f'method=tag.gettoptracks&tag={tag}&api_key={LAST_FM_KEY}&limit=05&format=json'
            response = make_url_request_using_cache(url, "tag_charts")
            results = response['tracks']['track']
            for song in results:
                track = song['name']
                rank = song['@attr']['rank']
                if song['artist']['name'].lower() == self.name.lower():
                    self.top_songs_by_tag.append([track, rank, tag])


def build_artist_profile(artist_inst):
    artist_inst.artist_info()
    artist_inst.get_top_tracks()
    artist_inst.get_top_albums()
    artist_inst.get_top_tags()
    # artist_inst.get_tag_charts()
    artist_inst.get_similar()


def getHistory():
    # get users listening history using spotipy
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

        history.append([artist, song, image, timestamp])
    return history


def getGenres(term):
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
    return data


def getRecommendationsByGenre(playlist):
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
    playlist_recs = sp.user_playlist_create(
        spotify_username, name='Songs from {}'.format(sourcePlaylist['name']))
    sp.user_playlist_add_tracks(
        spotify_username, playlist_recs['id'], recs_to_add)
    return playlist_recs
