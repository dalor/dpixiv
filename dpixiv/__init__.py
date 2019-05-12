import re
import json
import aiohttp
import asyncio
from urllib.parse import quote

post_key_search = re.compile(r'name\=\"post_key\" value\=\"([a-z0-9]+)\"')
tt_search = re.compile(r'name\=\"tt\" value\=\"([a-z0-9]+)\"')
reccomend_sample_search = re.compile(r'illustRecommendSampleIllust \= \"([0-9\,]+)\"\;')
info_json_pattern = re.compile(r'\}\)\((\{token\:.+\})\)\;\<\/script\>')
info_fix_json = re.compile(r'([\,\{]) ?(\w+):\ ')
find_data_items = re.compile(r'data\-items\=\"(\[.+\])\"')
find_all_illustId = re.compile(r'\"illustId\"\:\"([0-9]+)\"')
find_token = re.compile(r'token\: \"([0-9a-z]+)\"')


class DPixivIllusts:
    def __init__(self, login, password, session=None, tt=None, proxy=None):
        self.login = login
        self.password = password
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36'}
        self.tt = tt
        self.cookies = {'PHPSESSID': session} if session else {}
        self.proxy = proxy
        self.auth()

    @property
    def session(self):
        return self.cookies['PHPSESSID'] if 'PHPSESSID' in self.cookies else None

    def __make_headers(self, ref, csrf_token):
        headers = {}
        if ref:
            headers['Referer'] = ref
        if csrf_token:
            headers['x-csrf-token'] = csrf_token
        return headers if headers else None

    async def __fetch_get(self, url, session, params=None, ref=None, csrf_token=None):
        async with session.get(url, params=params, headers=self.__make_headers(ref, csrf_token), proxy=self.proxy) as resp:
            return await resp.text()

    async def __fetch_get_with_id(self, url, id_, session, params=None, ref=None, csrf_token=None):
        async with session.get(url, params=params, headers=self.__make_headers(ref, csrf_token), proxy=self.proxy) as resp:
            return {id_: (await resp.text())}

    async def __fetch_post(self, url, session, data=None, ref=None, csrf_token=None):
        async with session.post(url, data=data, headers=self.__make_headers(ref, csrf_token), proxy=self.proxy) as resp:
            return await resp.text()

    async def __fetch_post_with_id(self, url, id_, session, data=None, ref=None, csrf_token=None):
        async with session.post(url, data=data, headers=self.__make_headers(ref, csrf_token), proxy=self.proxy) as resp:
            return {id_: (await resp.text())}

    def __get_list_with_id(self, list_):
        async def __get_list_with_id_prepare(list_):
            new_list_ = {}
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                for resp in (await asyncio.gather(*[
                                                    asyncio.ensure_future(self.__fetch_get_with_id(
                                                                                                    i['url'], i['id'], session,
                                                                                                    i['params'] if 'params' in i else None,
                                                                                                    i['ref'] if 'ref' in i else None,
                                                                                                    i['csrf_token'] if 'csrf_token' in i else None
                                                                                                    )) for i in list_
                                                    ])):
                    new_list_.update(resp)
            return new_list_
        return asyncio.new_event_loop().run_until_complete(__get_list_with_id_prepare(list_))

    def __post_list_with_id(self, list_):
        async def __post_list_with_id_prepare(list_):
            new_list_ = {}
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                for resp in (await asyncio.gather(*[
                                                    asyncio.ensure_future(self.__fetch_post_with_id(
                                                                                                    i['url'], i['id'], session,
                                                                                                    i['data'] if 'data' in i else None,
                                                                                                    i['ref'] if 'ref' in i else None,
                                                                                                    i['csrf_token'] if 'csrf_token' in i else None
                                                                                                    )) for i in list_
                                                    ])):
                    new_list_.update(resp)
            return new_list_
        return asyncio.new_event_loop().run_until_complete(__post_list_with_id_prepare(list_))

    def get(self, url, params=None, ref=None, csrf_token=None):
        async def __get(url, params, ref, csrf_token):
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                return await (self.__fetch_get(url, session, params, ref, csrf_token))
        return asyncio.new_event_loop().run_until_complete(__get(url, params, ref, csrf_token))

    def post(self, url, params=None, ref=None, csrf_token=None):
        async def __post(url, data, ref, csrf_token):
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                return await (self.__fetch_post(url, session, data, ref, csrf_token))
        return asyncio.new_event_loop().run_until_complete(__post(url, params, ref, csrf_token))

    def auth(self): #Use to set up all cookies use again to reauth
        async def work_in_one_session():
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                if not await self.__is_auth(session):
                    login_page = await (self.__fetch_get('https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index', session))
                    prepost_key = post_key_search.search(login_page)
                    login_params = {
                        'password': self.password,
                        'pixiv_id': self.login,
                        'captcha': '',
                        'g_recaptcha_response': '',
                        'post_key': prepost_key[1] if prepost_key else None,
                        'ref': 'wwwtop_accounts_index',
                        'return_to': 'https://www.pixiv.net/',
                        'source': 'pc'
                    }
                    await (self.__fetch_post('https://accounts.pixiv.net/api/login?lang=en', session, data=login_params))
                    await self.__set_tt(session)
                    clear_cookies = {cookie.key:cookie.value for cookie in session.cookie_jar if cookie.key == 'PHPSESSID'}
                    self.cookies = clear_cookies
                elif not self.tt:
                    await self.__set_tt(session)
        asyncio.new_event_loop().run_until_complete(work_in_one_session())

    async def __set_tt(self, session):
        prett = tt_search.search(await (self.__fetch_get('https://www.pixiv.net', session)))
        self.tt = prett[1] if prett else None

    async def __is_auth(self, session):
        get_result = await (self.__fetch_get('https://www.pixiv.net/rpc/index.php?mode=message_thread_unread_count', session))
        result = json.loads(get_result)
        if 'error' in result and not result['error']:
            return True
        else:
            return False

    def recommender(self, sample_illusts=None, count=100): #Return list of recommendations or None if error; sample_illusts - id or list ids; can be executed without parameters and show all recommendations
        rec_params = {
            'type': 'illust',
            'num_recommendations': count,
            'tt': self.tt
        }
        if not sample_illusts:
            rec_params.update({'mode': 'all', 'page': 'discovery'})
        else:
            rec_params.update({'sample_illusts': ','.join(sample_illusts) if type(sample_illusts) == list else sample_illusts})
        rec_resp = json.loads(self.get('http://www.pixiv.net/rpc/recommender.php', params=rec_params, ref='https://www.pixiv.net/discovery'))
        return [i for i in rec_resp['recommendations']] if 'recommendations' in rec_resp else None

    def similar(self, id, limit=10):
        sim_resp = json.loads(self.get('https://www.pixiv.net/ajax/illust/{}/recommend/init?limit={}'.format(id, limit)))
        return [one['workId'] for one in sim_resp['body']['illusts']] if not sim_resp['error'] else None

    def __load_ids_from_pages(self, url, parser, page, from_page, to_page, step_count, params={}):
        if page:
            new_params = params.copy()
            new_params['p'] = page
            return parser(self.get(url, new_params))
        else:
            results = []
            if step_count > to_page: step_count = to_page
            pg = from_page
            end = False
            while not end and pg <= to_page:
                prepared_urls = []
                for i in range(pg, step_count + pg):
                    new_params = params.copy()
                    new_params['p'] = i
                    prepared_urls.append({'id': i, 'url': url, 'params': new_params})
                prepared = self.__get_list_with_id(prepared_urls)
                prepared_items = sorted(prepared.items())
                for key, value in prepared_items:
                    parsed = parser(value)
                    if parsed:
                        results.extend(parsed)
                    else:
                        end = True
                pg += step_count
            return results if results else None

    def __bookmarks_parser(self, page):
        res_parse = reccomend_sample_search.search(page)
        return res_parse[1].split(',') if res_parse else None

    def bookmarks(self, page=None, from_page=1, to_page=1000000, step_count=10): #Get bookmarks of user
        url = 'https://www.pixiv.net/bookmark.php'
        return self.__load_ids_from_pages(url, self.__bookmarks_parser, page, from_page, to_page, step_count)

    def __parser_where_data_items(self, page):
        res_parse = find_data_items.search(page)
        if res_parse:
            return find_all_illustId.findall(res_parse[1].replace('&quot;', '"'))

    def new_work_following(self, page=None, from_page=1, to_page=1000000, step_count=10):
        return self.__load_ids_from_pages('https://www.pixiv.net/bookmark_new_illust.php', self.__parser_where_data_items, page, from_page, to_page, step_count)

    def search(self, word, page=None, from_page=1, to_page=1000000, step_count=10):
        if isinstance(word, list):
            word = ' '.join(word)
        return self.__load_ids_from_pages('https://www.pixiv.net/search.php', self.__parser_where_data_items, page, from_page, to_page, step_count, {'word': word})

    def add_tag(self, pic_id, tag, token): # Put token=True in info to get token
        return json.loads(self.post('https://www.pixiv.net/ajax/tags/illust/{}/{}/add'.format(pic_id, tag), csrf_token=token))

    def del_tag(self, pic_id, tag, token):
        return json.loads(self.post('https://www.pixiv.net/ajax/tags/illust/{}/{}/delete'.format(pic_id, tag), csrf_token=token))

    def illust_list(self, illusts): #Returns list of descriptions of illusts; illusts - one id or list of ids
        list_params = {
            'exclude_muted_illusts': 1,
            'illust_ids': ','.join(illusts),
            'page': 'discover',
            'tt': self.tt
        }
        return json.loads(self.get('https://www.pixiv.net/rpc/illust_list.php', params=list_params, ref='https://www.pixiv.net/discovery'))

    def __parse_info(self, page, token):
        find_json = info_json_pattern.search(page)
        if find_json:
            result = json.loads(info_fix_json.sub(r'\1"\2":', find_json[1].replace(',}','}'))).get('preload')
            if result:
                result = result.get('illust')
                if result:
                    result = result.get(next(iter(result)))
                    if token:
                        token = find_token.search(page)
                        result['token'] = token[1] if token else None
                    return result

    def info(self, id, token=False): #Return all info; get one id
        return self.__parse_info(self.get('https://www.pixiv.net/member_illust.php', params={'mode': 'medium', 'illust_id': id}), token)

    def info_packs(self, ids, token=False): #Return all info; get list of ids
        pages = self.__get_list_with_id([{'id': one, 'url': 'https://www.pixiv.net/member_illust.php', 'params': {'mode': 'medium', 'illust_id': one}} for one in ids])
        return [self.__parse_info(pages[ilust_id], token) for ilust_id in ids]
