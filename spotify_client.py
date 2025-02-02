import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv, set_key
import os
import random
import time

class SpotifyClient(object):
    def __init__(self):
        self.sp = auth()
        self.api_token = self.sp.auth_manager.get_access_token()['access_token']
        # Get playlists and store only the items list
        response = self.sp.current_user_playlists()
        self.playlists = response['items'] if 'items' in response else []
        self.filtered_playlists = self.playlists
        if("Spotify Shuffle" not in [playlist['name'] for playlist in self.playlists]):
            self.sp.user_playlist_create(user=self.sp.current_user()['id'], name="Spotify Shuffle")

    def search_for_playlists(self, search_term):
        if(search_term == ""):
            self.filtered_playlists = self.playlists
        else:
            # Filter playlists by name
            self.filtered_playlists = [
                playlist for playlist in self.playlists 
                if search_term.lower() in playlist['name'].lower()
            ]
    
    def shuffle_playlist(self, playlist_name):
        try:
            # Find the clicked playlist from our filtered list
            playlist = next((p for p in self.filtered_playlists if p['name'] == playlist_name), None)
            
            if not playlist:
                print(f"No playlist found matching '{playlist_name}'")
                return None
            
            playlist_id = playlist['id']
            print(f"Found playlist with ID: {playlist_id}")
            
            # Get all tracks using pagination
            tracks = []
            results = self.sp.playlist_tracks(playlist_id)
            tracks.extend(results['items'])
            
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])
            
            # Filter out None tracks and get URIs
            track_uris = []
            for item in tracks:
                try:
                    if (item and 
                        item.get('track') and 
                        item['track'].get('uri') and 
                        isinstance(item['track']['uri'], str) and 
                        item['track']['uri'].startswith('spotify:track:')):
                        track_uris.append(item['track']['uri'])
                except (TypeError, KeyError):
                    continue
                    
            print(f"Found {len(track_uris)} valid tracks in playlist")
            
            if not track_uris:
                print("No valid tracks found in playlist")
                return None
            
            random.shuffle(track_uris)
            
            # Get the Spotify Shuffle playlist
            user_playlists = self.sp.current_user_playlists()
            shuffle_playlist = next(playlist for playlist in user_playlists['items'] if playlist['name'] == "Spotify Shuffle")
            
            # Remove all songs from Spotify Shuffle
            self.sp.playlist_replace_items(playlist_id=shuffle_playlist['id'], items=[])
            
            # Add shuffled songs in smaller chunks
            chunk_size = 50  # Reduced from 100 to be safer
            for i in range(0, len(track_uris), chunk_size):
                try:
                    chunk = track_uris[i:i+chunk_size]
                    self.sp.playlist_add_items(playlist_id=shuffle_playlist['id'], items=chunk)
                    time.sleep(0.5)  # Add a small delay between chunks
                except Exception as e:
                    print(f"Error adding chunk {i//chunk_size + 1}: {str(e)}")
                    continue
            
            # Add a small delay to ensure all songs are added
            time.sleep(1)
            
            # Start playback with the shuffle playlist
            devices = self.sp.devices()
            if devices['devices']:
                self.sp.start_playback(device_id=devices['devices'][0]['id'], 
                                     context_uri=shuffle_playlist['uri'])
            else:
                print("No active devices found")
            
        except Exception as e:
            print(f"Error shuffling playlist: {str(e)}")
            return None


def auth():
    load_dotenv()

    # Check if environment variables are set
    required_vars = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")

    scope = (
        "user-library-read "
        "user-library-modify "
        "user-read-playback-state "
        "user-modify-playback-state "
        "playlist-read-private "
        "playlist-read-collaborative "
        "playlist-modify-public "
        "playlist-modify-private"
    )

    try:
        auth_manager = SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope=scope,
            open_browser=True  # This might help with authentication
        )
        
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test the connection explicitly
        try:
            results = sp.current_user()
            print(f"Connected to Spotify as {results['display_name']}")
        except Exception as e:
            print(f"Failed to get current user: {e}")
            print("Please check your Spotify credentials and try again")
            raise

        # Get and save the token
        token_info = auth_manager.get_cached_token()
        if token_info:
            set_key('.env', 'SPOTIFY_AUTH_TOKEN', token_info['access_token'])
            print("Successfully obtained and cached token")
        else:
            print("Failed to get token info")
            raise ValueError("Authentication failed - no token received")

        return sp

    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        print("Please ensure your .env file contains valid Spotify API credentials")
        raise