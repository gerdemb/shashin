## shashin
Shashin is a command-line based photo library management system inspired by [beets](https://github.com/beetbox/beets).

## Features
- Organize files into a library in a YYYY/MM/DD format based on embedded EXIF data
- Import new files into the library while flagging duplicate files
- Detect potentially duplicate images (resized, different EXIF data, etc.) using [perceptual hashing](http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html)
- Use browser to view duplicate images and delete them
- Supports image and video files. Identical video files are detected, but similar image detection only works on images.

## Required External Libraries
- [ImageMagick with development libraries](http://docs.wand-py.org/en/0.5.8/guide/install.html#install-imagemagick-on-debian-ubuntu)
- [ExifTool](https://exiftool.org)

## Quick Start

    pip -r requirements.txt
    mkdir -p ~/.config/shashin/
    touch ~/.config/shashin/shashin.conf

Edit `shashin.conf` to define location of the library
    
    library: /path/to/store/images

Import Files

    shashin.py import /path/to/new/files
    
Browse duplicate files

    shashin.py browse-duplicates

Open http://0.0.0.0:8000/

## Commands
### Common Arguments
    usage: shashin.py [-h] -l LIBRARY [-c CONFIG] [-d DATABASE]
                      {import,rescan-library,random-snapshots,browse-duplicates}
                      ...
    
    Organize images and videos in a library Args that start with '--' (eg. -l) can
    also be set in a config file (~/.config/shashin/shashin.conf or specified via
    -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
    details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
    than one place, then commandline values override config file values which
    override defaults.
    
    positional arguments:
      {import,rescan-library,random-snapshots,browse-duplicates}
        import              Import files into the library
        rescan-library      Rescan the library for changes and update the database
        random-snapshots    Export a random selection of images as snapshots
        browse-duplicates   Start a server to allow browsing of duplicate images
    
    required arguments:
      -l LIBRARY, --library LIBRARY
                            library path
    
    optional arguments:
      -h, --help            show this help message and exit
      -p HIERARCHY, --hierarchy HIERARCHY
                            directory hierarchy for library
      -c CONFIG, --config CONFIG
                            Config file path (default:
                            ~/.config/shashin/shashin.conf)
      -d DATABASE, --database DATABASE
                            database filename (default:
                            ~/.config/shashin/shashin.db)
                            
#### HIERARCHY
`HIERARCHY` is a jinja2 template that describes the path hierarchy for the library. Default value:

        {% if DateTimeOriginal and not (DateTimeOriginal is string) %}
            {{ DateTimeOriginal.strftime('%Y/%m/%d') }}
        {% else %}
            {{ FileModifyDate.strftime('%Y/%m/%d') }}
        {% endif %}

This will store the files in a `YYYY/MM/DD` hierarchy (example: `2020/03/14`) using the `DateTimeOriginal` tag
if available otherwise using `FileModifyDate`. (The `is string` check is to handle
the case of invalid DateTimeOriginal values like `0000:00:00 00:00:00`)

### `import`
    usage: shashin.py import [-h] [-m] [--import-duplicates | --delete-duplicates]
                             import_path
    
    positional arguments:
      import_path          path of images to import
    
    optional arguments:
      -h, --help           show this help message and exit
      -m, --move           move file on import (default is to copy)
      --import-duplicates  import duplicate files
      --delete-duplicates  delete duplicates from import directory

## Architecture
On an import, the md5 hash and dhash of each file is calculated and stored in an sqlite3 database. This database is
used to detect identical files and similar images.

## FAQ
### How can import files in-place without moving them into a library?

1. Set the library to the existing path with your images in `shashin.conf` and set `hierarchy` to `.`
to prevent the images from being moved.

    library: /path/to/store/images
    hierarchy: .
    
Then run this command:
    
    shashin.py organize-library
    
The files defined in the library path will be scanned without being moved.
    
## TODO
- Allow files to be renamed on import
- Add method to ignore false positive duplicates in browse-duplicates
- Allow detection of similar videos (probably hard)