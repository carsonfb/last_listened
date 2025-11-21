Last Listened
===============

Last Listened generates an image with the last songs a user has listened to.  It is extensible via
plugins to support a variety of services, however, currently, only Last.fm is supported.  More
plugins will be added if I have time, or if any are user-contributed.

* The image size, font faces, colors, and background colors are all customizeable.

* The export file name is customizeable.

* The file can be sent to an SFTP server for updating on a website.  For an example, see
[my website](https://carson.ballweb.org/interests).

* Where the last played songs are pulled from can be customized via plugins written in python (see
below).

* If you have pngcrush installed, it can be used to automatically compress the generated image.

The below image is an example export from Last Listened.

![image of an example output from Last Listened](https://carson.ballweb.org/images/last_listened.png)

Configuration
-------------
A number of default settings are pre-set in the config_template file however none of the credentials
are set.  These will need to be filled out as well as any color, font, and image dimension settings
changes if you don't like the defaults.

Once the changes have been made, the file should be renamed to .config and placed in the same folder
as the program.

Using Plugins
--------------
Plugins allow last played songs to be pulled from a variety of services, or even local databases.
To create and use a different plugin, please note the following:

1. All plugins should be in the plugins sub-folder.

2. An entry will need to be created under "plugins" for the new plugin and any appopriate
configuration values should be added to it.  Note: this entry should be named the same as the plugin
file without the .py extension.

3. The "plugin" entry in the .config will need to be changed to the name of the new plugin.

That should be all there is to it.

Creating Plugins
----------------
1. All plugins should be written in Python.

2. Plugins should have a class named TrackPlugin.

3. This class should have a constructor that accepts the plugin data structure from the .config
file as an argument.

4. This class should have a public method named get_tracks that returns a list of dictionaries
containing the following elements:

* artist: The artist name
* track: The track name
* when: How long ago the track was listened to
* cover: The url of the album cover

If you write a plugin and would like to contribute it, please let me know.

Credits
-------
© 2023 [Carson F. Ball](<mailto://carson@ballweb.org>)

Donations
---------
If you like this project and want to see more projects from me, please contribute if you are able.

[![PayPal donation button](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CT5XNBHGD5TEN)

[![BitCoin Wallet](https://img.shields.io/badge/Bitcoin-000000?style=for-the-badge&logo=bitcoin&logoColor=white)](https://img.shields.io/badge/Bitcoin-000000?style=for-the-badge&logo=bitcoin&logoColor=white) 3QzgUdXzbLY7oy15XeMJ4W37cfBJDeKj6A
