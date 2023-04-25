"""
    This module is the plugin for Last.fm support.  All plugins, at a minimum, must have the
    following:

    1. An __init__ mehod that takes config data read by the main program.

    2. A get_tracks method that returns an list of dictionaries containing:
       a. artist: The artist name
       b. track: The track name
       c. when: How long ago the track was listened to
       d. cover: The url of the album cover

    3. The class must be named TrackPlugin.
"""

import time
from datetime import datetime
import pylast

class TrackPlugin:
    """ This is the class to implement the Last.fm connector. """

    def __init__(self, config_data):
        """ This method is the constructor for the LastFM class. """

        # Generate the password hash from the provided password.
        password_hash = pylast.md5(config_data['password'])

        self.config_data = config_data
        self.tracks = []

        # Connect to LastFM's API.
        self.conn = pylast.LastFMNetwork(
            api_key=config_data['api_key'],
            api_secret=config_data['api_secret'],
            username=config_data['username'],
            password_hash=password_hash
        )

    def get_tracks(self):
        """ This metod looks up the user's most recently listened to tracks. """

        # Lookup the most recent tracks.
        recent_tracks = self.conn.get_user(self.config_data['username']).get_recent_tracks(
            limit=self.config_data['limit']
        )

        for track in recent_tracks:
            # Lookup the album cover for each track.
            album_cover = self.get_artwork(track)

            # Push the information onto the track list.
            self.tracks.append(
                {
                    'artist': track.track.artist.name,
                    'track': track.track.title,
                    'cover': album_cover,
                    'when': self.__get_days(track)
                }
            )

    def get_artwork(self, track):
        """ This method loooks up the cover artwok for the album. """

        # Default to a blank image.
        album_cover = ''

        try:
            album = self.conn.get_album(track.track.artist.name, track.album)
            album_cover = album.get_cover_image()
        except pylast.WSError:
            # No artwork was found for this album.
            pass

        return album_cover

    def __get_days(self, track):
        """ This method generates the human readable time the track was listened to. """

        # Convert the listened timestamp to a datetime object.
        listened = datetime.fromtimestamp(int(track.timestamp))

        # Convert the current timestamp to a datetime object.
        now = datetime.fromtimestamp(time.time())

        # Get the number of seconds between now and when the track was listened to.
        time_diff = now - listened
        seconds = time_diff.total_seconds()

        if seconds // 3600 < 1:
            # This is less than an hour ago.
            return 'Just now'
        elif seconds // 3600 < 24:
            # This is less than a day ago.
            return ' '.join([str(int(seconds // 3600)), 'hours ago'])
        elif 48 > (seconds // 3600) > 23:
            return '1 day ago'
        else:
            # This is at least a day ago.
            return ' '.join([str(int(seconds // 3600 // 24)), 'days ago'])
