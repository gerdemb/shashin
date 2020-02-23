shashin
=======

Shashin is a command-line based photo library management system inspired by [beets](https://github.com/beetbox/beets).

Features
--------
- Organize files into a library in a YYYY/MM/DD format based on embedded EXIF data
- Import new files into the library while ignoring identical files
- Detect potentially duplicate images (resized, different EXIF data, etc.) using [perceptual hashing](http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html)
- Use browser to view duplicate images and delete them
- Supports image and video files. Identical video files are detected, but similar image detection only works on images.

Example
-------
    shashin.py import camera-import/
    shashin.py browse-duplicates

External Libraries
------------------
- [ImageMagick with development libraries](http://docs.wand-py.org/en/0.5.8/guide/install.html#install-imagemagick-on-debian-ubuntu)
- [ExifTool](https://exiftool.org)

Quick Installation
------------------
    pip -r requirements.txt
    mkdir -p ~/.config/shashin/
    touch ~/.config/shashin/shashin.conf

shashin.conf
    library = /path/to/store/images

    shashin.py import /path/to/new/files

TODO
----
- Allow custom path hierarchies for the library other than YYYY/MM/DD
- Allow files to be renamed on import
- Allow files to be copied instead of moved on import
- Allow handling of duplicate files in import (ignore, delete, import anyway, etc.)
- Allow groups of duplicate images to be hidden when browsing. Useful for ignoring false positive duplicates
- Allow detection of similar videos (probably hard)