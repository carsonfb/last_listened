"""
    This module is the plugin for Last.fm support.  All plugins, at a minimum, must have the
    following:

    1. An __init__ mehod that takes config data read by the main program.

    2. A get_tracks method that returns an list of dictionaries containing:
       a. artist: The artist name
       b. track: The track name
       c. cover: The url of the album cover

    3. The class must be named TrackPlugin.
"""

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

        # TODO: Make the limit a parameter in the config.
        # Lookup the most recent tracks.
        recent_tracks = self.conn.get_user(self.config_data['username']).get_recent_tracks(limit=5)

        for track in recent_tracks:
            # Lookup the album cover for each track.
            album_cover = self.__get_artwork(track)

            # Push the information onto the track list.
            self.tracks.append(
                {
                    'artist': track.track.artist.name,
                    'track': track.track.title,
                    'cover': album_cover
                }
            )

    def __get_artwork(self, track):
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
