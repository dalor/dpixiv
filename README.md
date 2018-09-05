# dpixiv
Script to simple use pixiv api of site

### Example of using

run on python 3 with aiohttp

```python
from dpixiv import DPixivIllusts

pix = DPixivIllusts('login', 'password') #Auth

pictures = pix.recommender() #Get lists of ids
# Has two parameters: (sample_illusts=None, count=100) - by default
# sample_illusts - list of ids(str) which help you to find what you want
# count - count of elements which you will get

pictures_info = pix.illust_list(pictures) #Get list of information of pictures
# Has one parameter: (illusts) - required
# illusts - list of ids of pictures

picture_urls = pix.urls(pictures) #Get list of urls with ids of pictures
# Has one parameter: (illusts) - required
# illusts - list of ids of pictures

```
