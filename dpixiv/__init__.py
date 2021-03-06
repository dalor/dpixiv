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
    def __init__(self, session=None, proxy=None):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36'}
        self._is_auth = False
        self.cookies = {'PHPSESSID': session} if session else {}
        self.proxy = proxy

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

    def auth(self, login, password, captcha_token): #Use to set up all cookies use again to reauth
        async def work_in_one_session():
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                
                login_page = await (self.__fetch_get('https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index', session))
                prepost_key = post_key_search.search(login_page)
                post_key = prepost_key[1] if prepost_key else None

                login_params = {
                        'password': password,
                        'pixiv_id': login,
                        'captcha': '',
                        'g_recaptcha_response': '',
                        'post_key': post_key,
                        'ref': 'wwwtop_accounts_index',
                        'return_to': 'https://www.pixiv.net/',
                        'source': 'pc',
                        'recaptcha_v3_token': captcha_token
                }

                auth = json.loads(await (self.__fetch_post('https://accounts.pixiv.net/api/login?lang=en', session, data=login_params)))
                
                if 'body' in auth and 'success' in auth['body']:
                    self._is_auth = True

                    # await (self.__fetch_get('https://www.pixiv.net', session)) #To get global session

                    self.cookies = {cookie.key:cookie.value for cookie in session.cookie_jar if cookie.key == 'PHPSESSID'}

        asyncio.new_event_loop().run_until_complete(work_in_one_session())

    @property
    def is_auth(self):
        if not self.cookies:
            return False
        if not self._is_auth:
            async def is_auth_fun():
                async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
                    self._is_auth = await self.__is_auth(session)
            asyncio.new_event_loop().run_until_complete(is_auth_fun())
        return self._is_auth


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
            'num_recommendations': count
        }
        if not sample_illusts:
            rec_params.update({'mode': 'all', 'page': 'discovery'})
        else:
            rec_params.update({'sample_illusts': ','.join(sample_illusts) if type(sample_illusts) == list else sample_illusts})
        rec_resp = json.loads(self.get('http://www.pixiv.net/rpc/recommender.php', params=rec_params, ref='https://www.pixiv.net/discovery'))
        return [i for i in rec_resp['recommendations']] if 'recommendations' in rec_resp else None

    def similar(self, id, limit=10):
        sim_resp = json.loads(self.get('https://www.pixiv.net/ajax/illust/{}/recommend/init?limit={}'.format(id, limit)))
        return [one['id'] for one in sim_resp['body']['illusts']] if not sim_resp['error'] else None

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
            'page': 'discover'
        }
        return json.loads(self.get('https://www.pixiv.net/rpc/illust_list.php', params=list_params, ref='https://www.pixiv.net/discovery'))

    def __parse_info_with_token(self, page):
        find_json = info_json_pattern.search(page)
        if find_json:
            result = json.loads(info_fix_json.sub(r'\1"\2":', find_json[1].replace(',}','}'))).get('preload')
            if result:
                result = result.get('illust')
                if result:
                    result = result.get(next(iter(result)))
                    token = find_token.search(page)
                    result['token'] = token[1] if token else None
                    return result

    def __check_json_response(self, response):
        response = json.loads(response)
        if not response['error']:
            return response['body']

    def info(self, id, token=False): #Return all info; get one id
        if token:
            return self.__parse_info_with_token(self.get('https://www.pixiv.net/member_illust.php', params={'mode': 'medium', 'illust_id': id}))
        else:
            return self.__check_json_response(self.get('https://www.pixiv.net/ajax/illust/{}'.format(id)))

    def info_packs(self, ids, token=False): #Return all info; get list of ids
        if token:
            pages = self.__get_list_with_id([{'id': one, 'url': 'https://www.pixiv.net/member_illust.php', 'params': {'mode': 'medium', 'illust_id': one}} for one in ids])
            return [self.__parse_info_with_token(pages[ilust_id]) for ilust_id in ids]
        else:
            responses = self.__get_list_with_id([{'id': id, 'url': 'https://www.pixiv.net/ajax/illust/{}'.format(id)} for id in ids])
            return [self.__check_json_response(responses[ilust_id]) for ilust_id in ids]

    def fast_info(self, id):
        return self.fast_info_packs([id])

    def fast_info_packs(self, ids):
        params = {
            'mode': 'get_illust_detail_by_ids',
            'illust_ids': ','.join(ids)
        }
        response = self.__check_json_response(self.get('https://www.pixiv.net/rpc/index.php', params=params))
        if response:
            return response.values()

    def __checking_ranking_response(self, response):
        response = json.loads(response).get('contents')
        if response:
            return [item['illust_id'] for item in response]

    def ranking(self, mode, page=None, date=None): #Return 50 ids | date YYYYMMDD
        params = {'mode': mode, 'format': 'json'}
        if page: params['p'] = page
        if date: params['date'] = date
        response = json.loads(self.get('https://www.pixiv.net/ranking.php', params=params)).get('contents')
        if response:
            return [item['illust_id'] for item in response]

    def ranking_packs(self, mode, page=None, date=None, from_page=1, to_page=10, step_count=10):
        params = {'mode': mode, 'format': 'json'}
        if page: params['p'] = page
        if date: params['date'] = date
        return self.__load_ids_from_pages('https://www.pixiv.net/ranking.php', self.__checking_ranking_response, page, from_page, to_page, step_count, params)
