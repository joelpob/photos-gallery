# Google Photos Clone for Amazon S3/Static Hosting

This has a collection of Python scripts, machine learning models, and hacky tricks to create a Google Photos style clone that does not require any server side backend -- it can be hosted as a static site, straight from Amazon S3 or equivalent.

## Features

* Entirely statically generated and hosted (Just some Javascript, HTML and your images)
* Search/group by year photos were taken
* GPS Location search (cities and countries)
* Some deep learning image feature search (e.g. "ski", "skyscraper, "biking")
* Infinite scroll like Google Photos

## Getting started

Sync your photos into a ``img`` directory using the ``sync_directory.py`` script. This script will recursively find and copy images, and deal with any filename conflicts and duplicates.

Call the ``generate_photos_gallery.py`` script, which will do the following:

* Generate thumbnails for your images
* Generate search tokens for photo location
* Generate search tokens for image content
* Create a static website:

```
index.html
search-tokens.csv
photos.csv
img/
thumbnail/
js/
css/
```

Test to see if everything works:

```
python3 -m http.server 8000

# browse to http://localhost:8000/
```

![Screenshot](screenshot.png)

## How does it work?

* Uses [Progressive Image Grid](https://github.com/schlosser/pig.js/) from schlosser for Google Photos like infinite scroll.
* Uses some badly written JQuery, avoiding all the npm Javascript crap.
* Downloads and uses a pre-built [Places365](http://places2.csail.mit.edu/) [PyTorch](https://pytorch.org) model for the machine learning image search
* Generates a big metadata csv file (image, aspect ratio, search tokens) that the Javascript frontend downloads and parses for search and image display.
* Built and run on Linux. Haven't tested it on MacOS or Windows, sorry.

## Scripts

* ``scripts/trim.py`` find and remove photos from your collection that don't meet a minimum size criteria (useful for removing existing thumnails)
* ``scripts/sync_aws.sh`` syncs everything to an Amazon S3 bucket. Every time you add more photos to your collection, just call this script and it'll sync everything for you.
* Want some password prection on your Amazon S3 site? Follow these instructions: http://kynatro.com/blog/2018/01/03/a-step-by-step-guide-to-creating-a-password-protected-s3-bucket/.



