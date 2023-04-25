"""
    This module is the plugin for Last.fm support.  All plugins, at a minimum, must have the
    following:

    1. The class must be named TrackPlugin.

    2. An __init__ mehod that takes plugin config data read by the main program.

    3. A get_tracks method that returns an list of dictionaries containing:
       a. artist: The artist name
       b. track: The track name
       c. when: How long ago the track was listened to
       d. cover: The url of the album cover
"""

import time
from datetime import datetime
import pylast

# The number of seconds in an hour.
HOUR = 3600

# The number of hours in a day.
DAY = HOUR * 24

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
                    'when': get_days(track)
                }
            )

    def get_artwork(self, track):
        """ This method loooks up the cover artwok for the album. """

        # Default to a blank image.
        album_cover = ''

        try:
            # Lookup the album cover from Last.fm.
            album = self.conn.get_album(track.track.artist.name, track.album)
            album_cover = album.get_cover_image()
        except pylast.WSError:
            # No artwork was found for this album.
            pass

        return album_cover

def get_days(track):
    """ This function generates the human readable time the track was listened to. """

    # Convert the listened timestamp to a datetime object.
    listened = datetime.fromtimestamp(int(track.timestamp))

    # Convert the current timestamp to a datetime object.
    now = datetime.fromtimestamp(time.time())

    # Get the number of seconds between now and when the track was listened to.
    time_diff = now - listened
    seconds = time_diff.total_seconds()

    when = ''

    if seconds // HOUR < 1:
        # This was listened to less than an hour ago.
        when = 'Just now'
    elif seconds // HOUR < 2:
        # This was listened to around an hour ago.
        when = '1 hour ago'
    elif seconds // HOUR < 24:
        # This was listened to less than a day ago.
        when = ' '.join([str(int(seconds // HOUR)), 'hours ago'])
    elif 48 > seconds // HOUR > 23:
        # This was listened to a day ago.
        when = '1 day ago'
    else:
        # This was listened to more than a day ago.
        when = ' '.join([str(int(seconds // DAY)), 'days ago'])

    return when
