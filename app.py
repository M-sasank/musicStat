import requestHandler
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
import configparser
import json
import os
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user

app = Flask(__name__)
login_manager = LoginManager(app)
app.config['LOGIN_REDIRECT_VIEW'] = '/'
app.secret_key = os.getenv('SECRET_KEY')
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        
@login_manager.user_loader
def load_user(user_id):
    # Replace this with your code to load a user by ID from your data store
    return User(user_id)

load_dotenv()
DEFAULT_EXP_TIME = os.getenv('DEFAULT_EXP_TIME')
HIST_EXP_TIME = os.getenv('HIST_EXP_TIME')
redis = requestHandler.redis_client
@app.route('/redis', methods=['GET'])
def hello():
    # Example of setting and retrieving data from Redis
    redis.set('check', 'Hi! the redis running in docker is working on port 6370!')
    value = redis.get('check')
    return f'Redis says{value.decode("utf-8")}'

@app.route('/login')
def empty():
    return redirect('/')

@app.before_request
def check_session_timeout():
    req = requestHandler.checkSessionTimeout()
    if request.path == '/':
        print("Login page")
        return
    if request.path == '/login':
        print("Login 11 page")
        return
    if request.path == '/api_callback':
        print("Callback page")
        return
    if request.path == '/session_expired':
        print("Session expired page")
        return
    if req == False:
        return redirect(url_for("session_expired"))
        
    
@app.route('/')
def authenticate():
    global redirect_uri
    redirect_uri = request.base_url + 'api_callback'
    # use config parser to write redirect_uri to config file
    config = configparser.ConfigParser()
    config['SPOTIFY'] = {"REDIRECT_URI": redirect_uri}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    auth_url = f'{requestHandler.API_BASE}/authorize?client_id={requestHandler.CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&scope={requestHandler.scope}&show_dialog={requestHandler.SHOW_DIALOG}'
    return redirect(auth_url)


@app.route('/uri')
def uri():
    config = configparser.ConfigParser()
    config.read('config.ini')
    text = config['SPOTIFY']['REDIRECT_URI']
    return text


@app.route("/api_callback")
def api_callback():
    user_id=requestHandler.getAccessToken(
        request.args.get('code'))
    user = User(user_id)
    login_user(user)
    return redirect("home")

@app.route("/session_expired")
def session_expired():
    return render_template("session_expired.html")

@app.route('/home', methods=['GET'])
@login_required
def home():
    print("Home page")
    if (redis.get('topGlobal') == None):
        print("Cache miss\n")
        top_artist = {}
        top_artist = requestHandler.topGlobal()
        redis.setex('topGlobal', DEFAULT_EXP_TIME, json.dumps(top_artist))
        return render_template('home.html', top_artist=top_artist, len=len(top_artist))
    else:
        print("Cache Hit\n")
        redis_data = redis.get('topGlobal')
        redis_data = json.loads(redis_data)
        return render_template('home.html', top_artist=redis_data, len=len(redis_data))


@app.route('/history', methods=['GET'])
@login_required
def history():
    print(current_user.id)
    if (redis.get('history') == None):
        print("Hisotry Cache miss\n")
        history = requestHandler.getHistory()
        redis.setex('history',HIST_EXP_TIME, json.dumps(history))
        return render_template('history.html', history=history)
    else:
        print("History Cache Hit\n")
        redis_data = redis.get('history')
        redis_data = json.loads(redis_data)
        return render_template('history.html', history=redis_data)


@app.route('/you/artists/<period>', methods=['GET'])
@login_required
def userArtists(period):
    if period == '' or period == 'short':
        period = 'short_term'
    elif period == 'medium':
        period = 'medium_term'
    elif period == 'long':
        period = 'long_term'
    if (redis.get(f'userArtitsts_{period}') == None):
        print("Top User Artists Cache miss\n")
        userArtists = requestHandler.getUserArtists(period)
        redis.setex(f'userArtitsts_{period}', DEFAULT_EXP_TIME, json.dumps(userArtists))
        return render_template('userArtitsts.html', userArtists=userArtists)
    else:
        print("Top User Artists Cache Hit\n")
        redis_data = redis.get(f'userArtitsts_{period}')
        redis_data = json.loads(redis_data)
        return render_template('userArtitsts.html', userArtists=redis_data)
    


@app.route('/search')
@login_required
def artist_application():
    return render_template('input.html')


@app.route('/you/genres/<period>', methods=['GET', 'POST'])
@login_required
def genre(period):
    if period == '' or period == 'short':
        period = 'short_term'
    elif period == 'medium':
        period = 'medium_term'
    elif period == 'long':
        period = 'long_term'
    if (redis.get(f'Genres_{period}') == None):
        print("Genres Cache miss\n")
        genres = requestHandler.getGenres(period)
        redis.setex(f'Genres_{period}', DEFAULT_EXP_TIME, json.dumps(genres))
        return render_template('genre.html', data=genres)
    else:
        print("Genres Cache Hit\n")
        redis_data = redis.get(f'Genres_{period}')
        redis_data = json.loads(redis_data)
        return render_template('genre.html', data=redis_data)

@app.route('/you/tracks/<period>', methods=['GET', 'POST'])
@login_required
def you(period):
    if period == '' or period == 'short':
        period = 'short_term'
    elif period == 'medium':
        period = 'medium_term'
    elif period == 'long':
        period = 'long_term'
    if (redis.get(f'userTracks_{period}') == None):
        print("Top User Tracks Cache miss\n")
        top_tracks = requestHandler.getTopTracksUser(period)
        redis.setex(f'userTracks_{period}', DEFAULT_EXP_TIME, json.dumps(top_tracks))
        return render_template('you.html', top_tracks=top_tracks)
    else:
        print("Top User Tracks Cache Hit\n")
        redis_data = redis.get(f'userTracks_{period}')
        redis_data = json.loads(redis_data)
        return render_template('you.html', top_tracks=redis_data)


@app.route('/moody')
@login_required
def mood():
    return render_template('mood.html')


@app.route('/generate/<genre>', methods=['GET', 'POST'])
@login_required
def generate(genre):
    if genre == 'dance':
        playlistID = '2HhaArHsOiofpUheCRPkLa'
    elif genre == 'pop':
        playlistID = '6gS3HhOiI17QNojjPuPzqc'
    elif genre == 'sad':
        playlistID = '1uN3iCLmAXg6rmS86SJM7g'
    elif genre == 'edm':
        playlistID = '3pDxuMpz94eDs7WFqudTbZ'
    elif genre == 'k-pop':
        playlistID = '3T1Rft817cZ3pguTvaWaz3'
    elif genre == 'anime':
        playlistID = '5fSZTu6aISl80OPrmGu79j'
    elif genre == 'j-pop':
        playlistID = '3leFycE2a7uXZyuC6DQbdQ'
    elif genre == 'rap':
        playlistID = '6s5MoZzR70Qef7x4bVxDO1'
    else:
        playlistID = '5qRiSivbLQ3QI5AH3Zsxg1'
    playlistDetails = requestHandler.getRecommendationsByGenre(playlistID)
    return render_template('generate.html', playlistDetails=playlistDetails, genre=genre)


@app.route('/handle_form', methods=['POST'])
@login_required
def submitted_artist():
    artist = request.form['artist_name']
    if " " in artist:
        artist = artist.replace(" ", "%20")
    artists = requestHandler.last_fm_search(artist)
    return artists


@app.route('/display_results', methods=['POST'])
@login_required
def artist_results():
    chosen_artist = submitted_artist()
    artist_inst = requestHandler.Artist(name=chosen_artist)
    requestHandler.build_artist_profile(artist_inst)
    name = artist_inst.name
    artist_url = artist_inst.artist_url
    top_tracks = artist_inst.top_tracks
    top_albums = artist_inst.top_albums
    top_tags = artist_inst.top_tags
    top_tags_chart = artist_inst.top_songs_by_tag
    similar = artist_inst.similar

    return render_template('results.html', name=name, artist_url=artist_url, top_tracks=top_tracks,
                           top_albums=top_albums, top_tags=top_tags, top_tags_chart=top_tags_chart, similar=similar)


def get_artist_summary():
    conn = sqlite3.connect('requestHandler.sqlite')
    cur = conn.cursor()
    q = '''
        SELECT Artist, ArtistUrl
        FROM artists
    '''
    results = cur.execute(q).fetchall()
    conn.close()
    return results


@app.route('/summary')
@login_required
def summary_artists():
    results = get_artist_summary()
    return render_template('summary.html', results=results)


if __name__ == '__main__':
    # print('starting Flask app', app.name)
    app.run(debug=True)
