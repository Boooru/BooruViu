# BooruViu

A user-friendly GUI application meant to stream collections of images from your favorite artists and repositories. Fetch images from Twitter, Pixiv, or even your favorite Booru!

## Features

BooruViu implements a suite of features, some of which may not be available on certain image sources.

### All
- Save content! A simple click lets you images to your device
- Open in image in browser
- Open source/artist page in browser
- View tags

### Twitter

Supported features: view the images, gifs, and videos posted by a specific user.
Note: Twitter post tags are simply the hashtags used on the post

### Pixiv

Supported features: view all the posts by a specific user.

Coming soon: view the images posted by all your followed artists, view the "popular now" images, filter by severity, filter by tag

### Gelbooru, R34, other Boorus

Supported features: view images sorted by tag, and filtered by blacklist

Coming soon: choose from a variety of sorting modes: score, random, and newest

## Technologies

BooruViu depends on a number of technologies
- Python 3.9: Runtime
- Kivy: General UI implementation
- Selenium: Pixiv Oauth2 authentication
- [PixivPy](https://github.com/upbit/pixivpy): Comprehensive Pixiv API implementation
