"""
    This module reads API credentials, image export parameters, and other information from a
    configuration file, connects to a service based on which plugin selected in the configuration,
    generates an image with the user's last listened tracks, and - optionally - copies the image
    to an SFTP server.
"""

import json
import importlib
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont

class LastListened:
    """
        This class is the wrapper for the plugins to look up what the user last listened to.
    """

    header_text = 'Last listened tracks'

    sftp = {}
    image = {}
    plugin_name = None
    plugins = []
    tracks = []

    header_font = None
    font = None
    sub_font = None

    def __init__(self):
        """ This method is the constructor for the LastListened class. """

        # Read in the user configuration data.
        self.read_config()

        # Setup the plugin to fetch the last tracks listened to.
        self.__get_plugin()

        # Setup the fonts.
        self.__setup_fonts()

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

        track_plugin = getattr(
            importlib.import_module(
                '.'.join(['plugins', self.plugin_name])
            ),
            'TrackPlugin'
        )

        plugin = track_plugin(self.plugins[self.plugin_name])
        plugin.get_tracks()

        self.tracks = plugin.tracks

    def __setup_fonts(self):
        """ This method sets up the fonts used in the image. """

        # Setup the font for the header.
        self.header_font = ImageFont.truetype(
            self.image['header']['face'],
            size=self.image['header']['size']
        )

        # Setup the font for the first line of the tracks.
        self.font = ImageFont.truetype(
            self.image['font']['face'],
            size=self.image['font']['size']
        )

        # Setup the font for the second line of the tracks.
        self.sub_font = ImageFont.truetype(
            self.image['sub_font']['face'],
            size=self.image['sub_font']['size']
        )

    def __create_background(self):
        """ This method creates the background image for the track list. """

        # Create a new blank image with a transparent background.
        img = Image.new(
            'RGBA',
            (self.image['width'], self.image['height']),
            color=(0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(img)

        # Add a rounded rectangle to the background.
        draw.rounded_rectangle(
            (0, 0, self.image['width'] - 2, self.image['height'] - 2),
            fill=self.image['background'],
            radius=10
        )

        return img, draw

    def __write_header(self, draw):
        """ This method adds the header line to the background. """

        # Calculate the center location for the header.
        center = \
            (self.image['width'] - self.header_font.getmask(self.header_text).getbbox()[2]) // 2

        # Write the centered header to the background.
        draw.text(
            (center, 5),
            self.header_text,
            fill=self.image['header']['color'],
            font=self.header_font
        )

    def __write_track(self, img, draw, track, row_y):
        """ This method writes the track information to the image. """

        # Lookup the cover art.
        include = self.__fetch_cover(track)

        # Fill in the album art image or the default image.
        img.paste(include, (5, row_y))

        # Calculate how far below the line the text goes.
        _, descent = self.font.getmetrics()

        # Write the first line of track information to the image with padding for the cover art.
        draw.text((50, row_y), track['track'], fill=self.image['font']['color'], font=self.font)

        # Caculate how many pixels high the line is and add padding.
        padding = self.font.getmask(track['track']).getbbox()[3] + descent + 3

        # Adjust the start pixel for the next line so text doesn't get overwritten.
        row_y += padding

        # Write the second line of the track information to the image.
        draw.text(
            (50, row_y),
            track['artist'],
            fill=self.image['sub_font']['color'],
            font=self.sub_font
        )

        # Calculate the right-align position for the last listened time.
        right = self.image['width'] - self.sub_font.getmask(track['when']).getbbox()[2] - 5

        # Write the last listened time to the image.
        draw.text(
            (right, row_y),
            track['when'],
            fill=self.image['sub_font']['color'],
            font=self.sub_font
        )

        # Calculate the padding before the start of the next track.
        row_y += 50 - padding

        # Return the new padding.
        return row_y

    def __fetch_cover(self, track):
        """ This method fetchs and resizes the cover art. """

        try:
            # Lookup the album cover artwork.
            cover_art = requests.get(track['cover'])
            include = Image.open(BytesIO(cover_art.content))
        except requests.exceptions.MissingSchema:
            # There was no cover art so use the default image.
            include = Image.open('resources/blank.png')

        # Resize the image that was looked up.
        include = include.resize((self.image['cover_size'], self.image['cover_size']))

        return include

    def create_image(self):
        """ This method creates the image of the last listened to tracks. """

        # Create the bacground image.
        img, draw = self.__create_background()

        # Write the header to the image.
        self.__write_header(draw)

        # Leave room for the header.
        row_y = 40

        for track in self.tracks:
            # Write the track to the image.
            row_y = self.__write_track(img, draw, track, row_y)

        # Save the image.
        img.save('last_listened.png')

def main():
    """ This is the main function of the program. """

    last_listened = LastListened()
    last_listened.create_image()

if __name__ == '__main__':
    main()
