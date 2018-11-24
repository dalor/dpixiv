# dpixiv
Script to simple use pixiv api of site

### Example of using

run on python 3 with aiohttp

```python
from dpixiv import DPixivIllusts

pix = DPixivIllusts('login', 'password') #Auth

pictures = pix.recommender() #Get lists of ids that recommended to user by pixiv
# Has two parameters: (sample_illusts=None, count=100) - by default
# sample_illusts - id or list of ids which help you to find what you want
# count - count of elements which you will get

short_pictures_info = pix.illust_list(pictures) #Get list(or not) of short information of pictures (fast speed)
# Has one parameter: (illusts) - required
# illusts - id or list of ids of pictures

one_picture = picture[0]

full_picture_info = pix.info(one_picture) #Get full information of picture (not so fast)
# Has one parameter: (id) - required
# id - id of picture

#Use next method for a lot of pictures(much faster then one by one)
full_pictures_info = pix.info_packs(picture) #Get list of full information of picture (medium speed)
# Has one parameter: (id) - required
# id - list of ids of pictures

pictures = pix.similar(one_picture) #Get lists of ids of pictures that similar to picture with id (fast speed)
# Has two parameters: (id, limit=10) - by default
# id - id of picture
# limit - max count of elements which you can get

picture_urls = pix.bookmarks(pictures) #Get list of bookmarks of user
# Has four parameters: (page=None, from_page=1, to_page=1000000, step_count=10) - by default
# page - number of page of bookmarks to show one page
# OR 
# from_page - start page of list
# to_page - final page of list
# step_count - count pages to parse in one step(change for your task - can make your program faster)

pix.auth() #Updating session or changing login and password 
# Has two parameters: (login=None, password=None) - by default
# login - if None uses default login
# password - if None uses default password

```
