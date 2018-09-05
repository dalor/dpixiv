import re
import json
import aiohttp
import asyncio

class DPixivIllusts:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36'}
        self.tt = None
        self.cookies = {}
        self.auth()
    
    def get(self, urls, params=None, ref=None, list=False):
        async def fetch_for_sending(url, session, params=None, dict_=False):
            if dict_:
                async with session.get(url['url'], headers={'Referer': url['url']}) as response:
                    return {'data': await response.text(), 'id': url['id']}
            else:
                async with session.get(url, params=params) as response:
                    self.cookies.update(dict(response.cookies))
                    return await response.text()
        async def sending_one_or_more(url, params, ref, list):
            headers = self.headers
            if ref:
                headers['Referer'] = ref
            async with aiohttp.ClientSession(cookies=self.cookies, headers=headers) as session:
                if list:
                    return await asyncio.gather(*[asyncio.ensure_future(fetch_for_sending(url0, session, dict_=True)) for url0 in url])
                else:
                    return await fetch_for_sending(url, session, params)
        return asyncio.new_event_loop().run_until_complete(sending_one_or_more(urls, params, ref, list))
    
    def post(self, url, data):
        async def post_one(url):
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.post(url, data=data) as response:
                    self.cookies.update(dict(response.cookies))
                    return await response.text()
        return asyncio.get_event_loop().run_until_complete(post_one(url))
        
    
    def auth(self, login=None, password=None): #Use to set up all cookies use again to reauth
        login = self.login if not login else login
        password = self.password if not password else password
        prepost_key = re.search('name\=\"post_key\" value\=\"([a-z0-9]+)\"', self.get('https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index'))
        login_params = {
            'password': password,
            'pixiv_id': login,
            'captcha': '',
            'g_recaptcha_response': '',
            'post_key': prepost_key[1] if prepost_key else None,
            'ref': 'wwwtop_accounts_index',
            'return_to': 'https://www.pixiv.net/',
            'source': 'pc'
        }
        self.post('https://accounts.pixiv.net/api/login?lang=en', data=login_params)
        prett = re.search('name\=\"tt\" value\=\"([a-z0-9]+)\"', self.get('https://www.pixiv.net'))
        self.tt = prett[1] if prett else None

    def recommender(self, sample_illusts=None, count=100): #Return list of recommendations or None if error; sample_illusts - str of id or list of str of id; can be executed without parameters and show all recommendations
        rec_params = {
            'type': 'illust',
            'num_recommendations': count,
            'tt': self.tt
        }
        if not sample_illusts:
            rec_params.update({'mode': 'all', 'page': 'discovery'})
        else:
            rec_params.update({'sample_illusts': ','.join(sample_illusts)})
        rec_resp = json.loads(self.get('http://www.pixiv.net/rpc/recommender.php', params=rec_params, ref='https://www.pixiv.net/discovery'))
        return [str(i) for i in rec_resp['recommendations']] if 'recommendations' in rec_resp else None

    def illust_list(self, illusts): #Returns list of descriptions of illusts; illusts - list of str of id
        list_params = {
            'exclude_muted_illusts': 1,
            'illust_ids': ','.join(illusts),
            'page': 'discover',
            'tt': self.tt
        }
        return json.loads(self.get('https://www.pixiv.net/rpc/illust_list.php', params=list_params, ref='https://www.pixiv.net/discovery'))

    def urls(self, illusts): #Returns list of urls with id
        illus = self.illust_list(illusts)
        pattern_urls = re.compile("\"urls\"\:(\{.+\}),\"tags\"")
        pages = self.get([{'url': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + one['illust_id'], 'id': one['illust_id']} for one in illus], list=True)
        return [{'urls': json.loads(pattern_urls.search(page['data'])[1]), 'id': page['id']} for page in pages]
