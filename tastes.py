# %%
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import spotipy.util as util

# %%
cid = 'ecf3ff7d354741468d66ae216276f305'
secret = '8c3a7ba894f74164a797d3e0512b7f82'
username = '31ksezewtk5zlagthryjgp4sbqwm'
CLIENT_SECRET = 'ecf3ff7d354741468d66ae216276f305'
CLIENT_ID = '8c3a7ba894f74164a797d3e0512b7f82'
spotify_username = '31ksezewtk5zlagthryjgp4sbqwm'
redirect_uri = 'http://localhost:7777/callback'
# %%
scope = 'user-library-read playlist-modify-public playlist-read-private'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                               redirect_uri='http://localhost:7777/callback',
                                               scope=scope, username=spotify_username))

# https://open.spotify.com/playlist/37i9dQZEVXcKtoV0yfWpkH?si=f5bf0eac4e5f43bd
sourcePlaylistID = '37i9dQZEVXcKtoV0yfWpkH'
sourcePlaylist = sp.user_playlist(username, sourcePlaylistID);
tracks = sourcePlaylist["tracks"]
songs = tracks["items"]

track_ids = []
track_names = []

for i in range(0, 24):
    if songs[i]['track']['id'] is not None:
        track_ids.append(songs[i]['track']['id'])
        track_names.append(songs[i]['track']['name'])

features = []

for i in range(0, len(track_ids)):
    audio_features = sp.audio_features(track_ids[i])
    for track in audio_features:
        features.append(track)

playlist_df = pd.DataFrame(features, index=track_names)
# %%
playlist_df = playlist_df[
    ["id", "acousticness", "danceability", "duration_ms", "energy", "instrumentalness", "key", "liveness", "loudness",
     "mode", "speechiness", "tempo", "valence"]]
# %%
playlist_df['ratings'] = [10, 9, 9, 10, 8, 6, 8, 4, 3, 5, 7, 5, 5, 8, 8, 10, 4, 6, 8, 2, 4, 5, 6, 9]
# %%
X_train = playlist_df.drop(['id', 'ratings'], axis=1)
y_train = playlist_df['ratings']
# %%
import numpy as np
from sklearn import decomposition
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns;

sns.set(style='white')

X_scaled = StandardScaler().fit_transform(X_train)

pca = decomposition.PCA().fit(X_scaled)
# %%
# Fit your dataset to the optimal pca
pca = decomposition.PCA(n_components=8)
X_pca = pca.fit_transform(X_scaled)
# %%
from sklearn.feature_extraction.text import TfidfVectorizer

v = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 6),
                    max_features=10000)
X_names_sparse = v.fit_transform(track_names)
# %%
from scipy.sparse import csr_matrix, hstack

X_train_last = csr_matrix(hstack([X_pca, X_names_sparse]))
# %%
from sklearn.model_selection import StratifiedKFold, GridSearchCV

skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
# %%
# from sklearn.neighbors import KNeighborsClassifier
#
# knn_params = {'n_neighbors':range(1,10)}
# knn = KNeighborsClassifier(n_jobs=-1)
#
# knn_grid= GridSearchCV(knn,knn_params,cv=skf,n_jobs =-1,verbose=True)
# knn_grid.fit(X_train_last,y_train)
# knn_grid.best_params_, knn_grid.best_score_
# %%
# from sklearn.ensemble import RandomForestClassifier
# parameters = {'max_features':[4,7,8,10],'min_samples_leaf':[1,3,5,8],'max_depth':[3,5,8]}
# rfc = RandomForestClassifier(n_estimators=100,random_state=42,n_jobs=-1,oob_score=True)
# forest_grid = GridSearchCV(rfc,parameters,n_jobs=-1,cv=skf,verbose=1)
# forest_grid.fit(X_train_last,y_train)
# forest_grid.best_estimator_ , forest_grid.best_score_
# %%
from sklearn.tree import DecisionTreeClassifier

tree = DecisionTreeClassifier()

tree_params = {'max_depth': range(1, 11), 'max_features': range(4, 19)}
tree_grid = GridSearchCV(tree, tree_params, cv=skf, n_jobs=-1, verbose=True)
tree_grid.fit(X_train_last, y_train)
tree_grid.best_estimator_, tree_grid.best_score_
# %%
rec_tracks = []

for i in playlist_df['id'].values.tolist():
    rec_tracks += sp.recommendations(seed_tracks=[i], limit=int(len(playlist_df) / 2))['tracks'];

rec_track_ids = []
rec_track_names = []
for i in rec_tracks:
    rec_track_ids.append(i['id'])
    rec_track_names.append(i['name'])

rec_features = []

for i in range(0, len(rec_track_ids)):
    rec_audio_features = sp.audio_features(rec_track_ids[i])
    for track in rec_audio_features:
        rec_features.append(track)

rec_playlist_df = pd.DataFrame(rec_features, index=rec_track_ids)
# %%
rec_playlist_df = rec_playlist_df[
    ["acousticness", "danceability", "duration_ms", "energy", "instrumentalness", "key", "liveness", "loudness", "mode",
     "speechiness", "tempo", "valence"]]
rec_playlist_df.head()
# %%
tree_grid.best_estimator_.fit(X_train_last, y_train)
rec_playlist_df_scaled = StandardScaler().fit_transform(rec_playlist_df)
X_test_pca = pca.transform(rec_playlist_df_scaled)
X_test_names = v.transform(rec_track_names)
X_test_last = csr_matrix(hstack([X_test_pca, X_test_names]))
y_pred_class = tree_grid.best_estimator_.predict(X_test_last)
# %%
rec_playlist_df['ratings'] = y_pred_class
rec_playlist_df.head()
# %%
rec_playlist_df = rec_playlist_df.sort_values('ratings', ascending=False)
rec_playlist_df = rec_playlist_df.reset_index()
# sort by ratings and add top 15 to recs_to_add
recs_to_add = rec_playlist_df['index'].head(15).values.tolist()
