"""
    This module reads API credentials, image export parameters, and other information from a
    configuration file, connects to a service based on which plugin selected in the configuration,
    generates an image with the user's last listened tracks, and - optionally - copies the image
    to an SFTP server.
"""

import os
import json
import importlib
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
import pysftp

class LastListened:
    """
        This class is the wrapper for the plugins to look up what the user last listened to.
    """

    # The name of the plugin to use to look up the last listened to tracks.
    plugin_name = None

    # The structures to store the config data in.
    sftp = {}
    image = {}
    plugins = []

    # The fonts used by the image creation.
    fonts = {
        'header': None,
        'main': None,
        'small': None
    }

    def __init__(self):
        """ This method is the constructor for the LastListened class. """

        # The list to store the recently listened to tracks in.
        self.tracks = []

        # Read in the user configuration data.
        self.read_config()

        # Setup the plugin to fetch the last tracks listened to.
        self.__get_plugin()

        # Setup the fonts.
        self.__setup_fonts()

    def read_config(self):
        """ The method reads the user's configuration data. """

        with open('.config', 'r', encoding='UTF-8') as config_file:
            # Read in the config file.
            config_data = json.loads(config_file.read())

            # Store the values that were read.
            self.image = config_data['image']
            self.plugin_name = config_data['plugin']
            self.plugins = config_data['plugins']
            self.sftp = config_data['sftp']
            self.pngcrush = None


            if 'pngcrush' in config_data:
                if 'location' in config_data['pngcrush']:
                    self.pngcrush = config_data['pngcrush']['location']

    def __get_plugin(self):
        """ This method sets up the appropriate plugin. """

        # Dynamically load the plugin.
        track_plugin = getattr(
            importlib.import_module(
                '.'.join(['plugins', self.plugin_name])
            ),
            'TrackPlugin'
        )

        # Create a new instance of the track plugin.
        plugin = track_plugin(self.plugins[self.plugin_name])
        plugin.get_tracks()

        self.tracks = plugin.tracks

    def __setup_fonts(self):
        """ This method sets up the fonts used in the image. """

        # Setup the font for the header.
        self.fonts['header'] = ImageFont.truetype(
            self.image['header']['face'],
            size=self.image['header']['size']
        )

        # Setup the font for the first line of the tracks.
        self.fonts['main'] = ImageFont.truetype(
            self.image['font']['face'],
            size=self.image['font']['size']
        )

        # Setup the font for the second line of the tracks.
        self.fonts['small'] = ImageFont.truetype(
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
        center = self.__get_text_alignment(
            self.fonts['header'],
            self.image['header']['text'],
            'center'
        )

        # Write the centered header to the background.
        draw.text(
            (center, 5),
            self.image['header']['text'],
            fill=self.image['header']['color'],
            font=self.fonts['header']
        )

        # Return the header padding.
        return get_text_height(self.fonts['header'], self.image['header']['text'], 20)

    def __write_track(self, img, draw, track, row_y):
        """ This method writes the track information to the image. """

        # Lookup the cover art.
        include = self.__fetch_cover(track)

        # Fill in the album art image or the default image.
        img.paste(include, (5, row_y))

        # Write the first line of track information to the image with padding for the cover art.
        draw.text(
            (self.image['cover_size'] + 10, row_y),
            track['track'],
            fill=self.image['font']['color'],
            font=self.fonts['main']
        )

        # Caculate how many pixels high the line is and add padding.
        padding = get_text_height(self.fonts['main'], track['track'], 3)

        # Adjust the start pixel for the next line so text doesn't get overwritten.
        row_y += padding

        # Write the second line of the track information to the image.
        draw.text(
            (self.image['cover_size'] + 10, row_y),
            track['artist'],
            fill=self.image['sub_font']['color'],
            font=self.fonts['small']
        )

        # Calculate the right-align position for the last listened time.
        right = self.__get_text_alignment(self.fonts['small'], track['when'], 'right', 5)

        # Write the last listened time to the image.
        draw.text(
            (right, row_y),
            track['when'],
            fill=self.image['sub_font']['color'],
            font=self.fonts['small']
        )

        # Calculate the padding before the start of the next track.
        row_y += self.image['cover_size'] + 10 - padding

        # Return the new padding.
        return row_y

    def __fetch_cover(self, track):
        """ This method fetchs and resizes the cover art. """

        try:
            # Lookup the album cover artwork.
            cover_art = requests.get(track['cover'], timeout=30)
            cover_image = Image.open(BytesIO(cover_art.content))
        except requests.exceptions.MissingSchema:
            # There was no cover art so use the default image.
            cover_image = Image.open('resources/blank.png')

        # Resize the cover art to a square.
        cover_image = cover_image.resize((self.image['cover_size'], self.image['cover_size']))

        return cover_image

    def __get_text_alignment(self, font, text, align, padding=0):
        """ This function calculates the left edge of the text. """

        pos = 0

        if align == 'right':
            # The left edge is the width minus the text length and padding.
            pos = self.image['width'] - font.getmask(text).getbbox()[2] - padding
        elif align == 'center':
            # The left edge is half of the width minus the text length.
            pos = (self.image['width'] - font.getmask(text).getbbox()[2]) // 2
        else:
            # The left edge is just the padding.
            pos = padding

        return pos

    def create_image(self):
        """ This method creates the image of the last listened to tracks. """

        # Create the bacground image.
        img, draw = self.__create_background()

        # Write the header to the image.
        header_padding = self.__write_header(draw)

        # Leave room for the header.
        row_y = header_padding

        for track in self.tracks:
            # Write the track to the image.
            row_y = self.__write_track(img, draw, track, row_y)

        # Save the image.
        img.save(self.image['file'])

    def compress_image(self):
        """
            This method compresses the PNG to improve website loading times.  In testing, this
            yielded around a 30% size reduction.
        """

        if self.pngcrush:
            # The user requested that the image be compressed.

            # Compress in silent mode to avoid logging each iteration.
            os.system(
                ' '.join([
                    f'{self.pngcrush}',
                    '-ow -s -brute -reduce',
                    '-rem gAMA -rem cHRM -rem iCCP -rem sRGB -rem alla -rem text',
                    f'"{self.image["file"]}"'
                ])
            )

    def copy_image_to_sftp(self):
        """ This method copies the image file to the SFTP server. """

        if not self.sftp['send']:
            # The user requested for the file to not be sent.
            return

        # Setup the SFTP connection.
        with pysftp.Connection(
            host=self.sftp['server'],
            port=self.sftp['port'],
            username=self.sftp['username'],
            password=self.sftp['password']
        ) as conn:
            # Copy the local file to the SFTP server.
            conn.put(self.image['file'], '/'.join([self.sftp['path'], self.image['file']]))

        # Remove the temporary file.
        os.remove(self.image['file'])

def get_text_height(font, text, extra_space):
    """ This function calculates text height based on the font and the actual text. """

    # Calculate how far below the line the text goes.
    _, descent = font.getmetrics()

    # Calculate the text height.
    padding = font.getmask(text).getbbox()[3] + descent + extra_space

    return padding

def main():
    """ This is the main function of the program. """

    last_listened = LastListened()
    last_listened.create_image()
    last_listened.compress_image()
    last_listened.copy_image_to_sftp()

if __name__ == '__main__':
    # Run the entry point if the script was executed from the command line.
    main()
