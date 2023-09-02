# musicStat
 Webapp to display your top tracks, artists, your fav genre, and many more
 Webapp to display details about your songs, artists, and genres using Spotify API and Spotipy library, with an additional feature of genre-based recommendations.

Depending on your mood, you would like to listen to a specific genre right? Say you broke up, you listen to sad songs genre. or you are happy, you listen to dance songs, the main thing about your discover is that it does not differentiate the genres. It gives a vibey song right after a sad song which kinda ruins the mood.

In Tastes Page you  can select a genre and get recommendations solely from that genre. Currently, the following 8 Genres are supported:
1. Dance
2. Pop
3. Rap
4. Electronic Dance
5. K-Pop
6. J-Pop
7. Sad Lofi
8. Anime

# How to run
If you have Docker you can run the application very easily.

First create an ```.env``` file in the same location as the ```docker-compose.yaml``` file with the following details:

```
CLIENT_ID = 'xxxxxxxxxxxxxxxxx'
LAST_FM_KEY = 'xxxxxxxxxxxxxxxxx'
CLIENT_SECRET = 'xxxxxxxxxxxxxxxxx'
API_BASE = 'https://accounts.spotify.com'
scope = 'user-read-recently-played user-top-read user-library-read playlist-modify-public playlist-read-private'
SHOW_DIALOG = True
DEFAULT_EXP_TIME = 3600
HIST_EXP_TIME=600
SECRET_KEY='xxxxxxxxxxxxxxxxx'
REDIS_HOST = 'redis'
```
Fill in the ```CLIENT_ID``` and ```CLIENT_SECRET``` from your spotify developer dashboard, ```LAST_FM_KEY``` from the lastFM website, and ```SECRET_KEY``` as any string of your choice. Feel free to change other attributes as well, only if you know what you are doing.

After filling in respective details in .env file. Simply run the following command:

```docker compose up --build```

Once the build is complete, you can access the app by going to the following link in any browser:

```http://127.0.0.1:5000/```

The application will ask you to login to spotify using OAuth, after which you can access the application.
