"""
    This module reads API credentials, image export parameters, and other information from a
    configuration file, connects to a service based on which plugin selected in the configuration,
    generates an image with the user's last listened tracks, and - optionally - copies the image
    to an SFTP server.
"""

import json
import requests
import importlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

class LastListened:
    """
        This class is the wrapper for the plugins to look up what the user last listened to.
    """

    sftp = {}
    image = {}
    plugin_name = None
    plugins = []
    tracks = []

    def __init__(self):
        """ This method is the constructor for the LastListened class. """

        self.read_config()
        self.__get_plugin()

    def read_config(self):
        """ The method reads the user's configuration data. """

        with open('.config', 'r') as config_file:
            # Read in the config file.
            config_data = json.loads(config_file.read())

            # Store the values that were read.
            self.image = config_data['image']
            self.plugin_name = config_data['plugin']
            self.plugins = config_data['plugins']

    def __get_plugin(self):
        """ This method sets up the appropriate plugin. """

        TrackPlugin = getattr(
            importlib.import_module(
                '.'.join(['plugins', self.plugin_name])
            ),
            'TrackPlugin'
        )

        plugin = TrackPlugin(self.plugins[self.plugin_name])
        plugin.get_tracks()

        self.tracks = plugin.tracks

    def create_image(self):
        """ This method creates the image of the last listened to tracks. """

        cover_size = self.image['cover_size']
        # TODO: The font-sizes should not be hard-coded.
        img_font_size = self.image['font']['size']
        img_font_face = self.image['font']['face']

        # Create a new blank image.
        img = Image.new(
            'RGBA',
            (self.image['width'], self.image['height']),
            color=(0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((0, 0, self.image['width'] - 2, self.image['height'] - 2), fill=self.image['background'], radius=10)

        # Setup the font for the tracks.
        font = ImageFont.truetype(img_font_face, size=img_font_size)
        sub_font = ImageFont.truetype(img_font_face, size=img_font_size - 2)

        header_font = ImageFont.truetype(img_font_face, size=img_font_size + 6)

        draw.text((5, 5), 'Last listened tracks', fill=self.image['header']['color'], font=header_font)
        
        row_y = 40

        for track in self.tracks:
            try:
                # Lookup the album cover artwork.

                cover_art = requests.get(track['cover'])
                include = Image.open(BytesIO(cover_art.content))
            except requests.exceptions.MissingSchema:
                # There was no cover art so use the default image.

                include = Image.open('resources/blank.png')

            # Resize the image that was looked up.
            include = include.resize((cover_size, cover_size))

            # Fill in the album art image or the default image.
            img.paste(include, (5, row_y))

            _, descent = font.getmetrics()

            padding = font.getmask(track["track"]).getbbox()[3] + descent + 3

            draw.text((50, row_y), track['track'], fill=self.image['font']['color'], font=font)

            row_y += padding

            draw.text((50, row_y), track['artist'], fill=self.image['font']['color'], font=sub_font)

            row_y += 50 - padding

        img.save('lastfm_scrobbles.png')

def main():
    """ This is the main function of the program. """

    last_listened = LastListened()
    last_listened.create_image()

if __name__ == '__main__':
    main()
