# shashin

## Features
- Find duplicate images using [perceptual hashing](http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html) which can match similar images even if they have been resized, edited or had changes to their metadata (EXIF) tags, etc.
- Web interface for browsing images and deleting duplicates
- Machine learning analyzes the metadata of images you delete and suggests which images to delete
- Rapid rescanning of directories for new or changed files using database cache
- Images are not modified in any way
- Light weight Python code that can run on low-powered NAS devices

## Required External Libraries
- [ImageMagick with development libraries](http://docs.wand-py.org/en/0.5.8/guide/install.html#install-imagemagick-on-debian-ubuntu)
- [ExifTool](https://exiftool.org)

## Quick Start

```
    git checkout https://github.com/gerdemb/shashin.git
    cd shashin 
    pip -r requirements.txt
    ./shashin.py scan dir1
    ./shashin.py scan dir2
    ./shashin.py serve
```

Open http://localhost:8000/

## Other Commands

Commands for organizing images into `YYYY/MM/DD` folders. `src` directory will be scanned recursively and files organized into `dest/YYYY/MM/DD` directories based in `DateTimeOriginal` tag or `FileModifyDate` if `DateTimeOriginal` tag does not exist. Use `--dry-run` option to test file actions.

```
./shashin.py cp src dest/
./shashin.py mv src dest/
```

## Security
The web interface should be served for local browsers only. There is no security and any external user could view or delete images. Additionally the complete path location of each image (ie. `/Users/admin/photos/album/img_1.jpg`) is exposed to the browser. 

## Architecture
On an import, the md5 hash and dhash of each file is calculated and stored in an sqlite3 database. This database is used to detect identical files and similar images. By default, it is stored in `~/.cache/shashin/shashin.sqlite3`

## Machine Learning
In the web interface, a group of duplicated images is ordered so that the FIRST image is the one predicted to be kept and the following images are to be deleted. The prediction is made by building a machine learning model comparing the metadata of images that were deleted with images that were kept. A new model is built every time the `serve` command is started.

## TODO
- Handle videos
- Allow customization of `YYYY/MM/DD` hierarchy
- Allow renaming of files 
