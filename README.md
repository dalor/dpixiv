# dpixiv
Tool to simple use pixiv api of site

### Install
```
pip install dpixiv
```

### Example of using

```python
from dpixiv import DPixivIllusts

pix = DPixivIllusts(session=None, proxy=None)

### Attributes: ###

pix.is_auth  #(True|False)
pix.session  #session
pix.proxy    #http proxy 'http://{ip}:{port}'

### Methods:    ###

# Auth
pix.auth(login, password, captcha_token, post_key=None)
# To get capthca_token go to https://accounts.pixiv.net/login
# and write in browser console command:
# document.getElementById('recaptcha-v3-token').value
# Do it fast and save pix.session

# Get lists of ids that recommended to user by pixiv
pictures_ids = pix.recommender(sample_illusts=None, count=100)

# Get list(or not) of short information of pictures (fast speed)
short_pictures_info = pix.illust_list(illusts)

# Get full information of picture (not so fast)
full_picture_info = pix.info(id, token=False)

# Use next method for a lot of pictures(much faster then one by one)
# Get list of full information of picture (medium speed)
full_pictures_info = pix.info_packs(ids, token=False)

# Get lists of ids of pictures that similar to picture with id (fast speed)
similar_pictures_ids = pix.similar(id, limit=10)

# Get list of bookmarks
bookmarks_ids = pix.bookmarks(page=None, from_page=1, to_page=1000000, step_count=10)
# Use page to show only one page

# Get list of following
following_ids = pix.new_work_following(page=None, from_page=1, to_page=1000000, step_count=10)
# Use page to show only one page

# Search by name
search_ids = pix.search(word, page=None, from_page=1, to_page=1000000, step_count=10)
# Use page to show only one page

# Add tag (set token=True to info and get by 'token' key)
response = pix.add_tag(pic_id, tag, token)

# Delete tag
response = pix.del_tag(pic_id, tag, token)

```
