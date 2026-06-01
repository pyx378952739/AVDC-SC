import re
from pyquery import PyQuery as pq
from lxml import etree
from bs4 import BeautifulSoup
import json
from Function.getHtml import get_html, get_language_priority
from Function.getHtml import post_html


# ========================================================================获取当前语言设置
def get_javbus_lang():
    """获取 javbus 使用的语言代码
    javbus 支持: ja (日文), en (英文), 默认繁体中文
    根据用户优先级返回合适的语言
    优先级: sc/tc -> 默认繁中主页, ja -> /ja/, en -> /en/
    """
    priority = get_language_priority()
    # javbus 支持的语言映射
    # sc (简体中文) -> 使用默认（繁体中文，接近简体）
    # tc (繁体中文) -> 默认
    # ja (日文) -> /ja/
    # en (英文) -> /en/
    
    # 首先检查是否有中文优先（sc 或 tc）
    for lang in priority:
        if lang in ['sc', 'tc']:
            # 简体中文或繁体中文优先，使用默认繁体中文主页
            return ''
    # 如果没有中文优先，检查日文或英文
    for lang in priority:
        if lang == 'ja':
            return 'ja'
        elif lang == 'en':
            return 'en'
    # 默认返回空（使用繁体中文主页）
    return ''


# ========================================================================构建带语言路径的URL
def build_javbus_url(path=''):
    """构建带语言设置的 javbus URL"""
    lang = get_javbus_lang()
    if lang:
        return f'https://www.javbus.com/{lang}{path}'
    return f'https://www.javbus.com{path}'


def getActorInfo(htmlcode):
    """获取演员信息（包括ID、名称、头像URL）
    
    Returns:
        dict: {actor_name: {'id': actor_id, 'photo': photo_url}}
    """
    doc = pq(htmlcode)
    actors = doc('span.genre a[href*="/star/"]')
    
    d = {}
    for actor in actors.items():
        href = actor.attr('href')
        name = actor.text().strip()
        
        if not href or '/star/' not in href:
            continue
            
        # 提取演员ID
        actor_id = href.split('/star/')[-1].rstrip('/')
        
        # 获取演员头像URL（从页面直接获取，不需要额外请求）
        # 先尝试从当前页面的 star-box 获取
        photo_url = ''
        
        # 获取演员页面HTML以获取头像
        try:
            actor_html = get_html(href)
            actor_doc = pq(actor_html)
            img_src = actor_doc('#waterfall .photo-frame img').attr('src')
            if img_src:
                if img_src.startswith('http'):
                    photo_url = img_src
                else:
                    photo_url = 'https://www.javbus.com' + img_src
        except:
            photo_url = ''
        
        d[name] = {
            'id': actor_id,
            'photo': photo_url
        }
    
    return d


def getActorPhoto(htmlcode):
    """兼容旧版：返回 {actor_name: photo_url} 格式"""
    actor_info = getActorInfo(htmlcode)
    return {name: info['photo'] for name, info in actor_info.items()}


def getActorId(htmlcode):
    """获取演员ID字典 {actor_name: actor_id}"""
    actor_info = getActorInfo(htmlcode)
    return {name: info['id'] for name, info in actor_info.items()}


def getTitle(htmlcode):  # 获取标题
    doc = pq(htmlcode)
    title = str(doc('div.container h3').text())
    try:
        title2 = re.sub(r'n\d+-', '', title)
        return title2
    except:
        return title


def getStudio(htmlcode):  # 获取厂商
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"製作商")]/following-sibling::a/text()')).strip(" ['']")
    return result


def getPublisher(htmlcode):  # 获取发行商
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"發行商")]/following-sibling::a/text()')).strip(" ['']")
    return result


def getYear(getRelease):  # 获取年份
    try:
        result = str(re.search(r'\d{4}', getRelease).group())
        return result
    except:
        return getRelease


def getCover(htmlcode):  # 获取封面链接
    doc = pq(htmlcode)
    image = doc('a.bigImage')
    return 'https://javbus.com' + image.attr('href')


def getExtraFanart(htmlcode):  # 获取封面链接
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    extrafanart_list = html.xpath("//div[@id='sample-waterfall']/a/@href")
    return extrafanart_list


def getRelease(htmlcode):  # 获取出版日期
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"發行日期")]/../text()')).strip(" ['']")
    return result


def getRuntime(htmlcode):  # 获取分钟
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"長度")]/../text()')).strip(" ['']")
    return result


def getActor(htmlcode):  # 获取女优
    b = []
    soup = BeautifulSoup(htmlcode, 'lxml')
    a = soup.find_all(attrs={'class': 'star-name'})
    for i in a:
        b.append(i.get_text())
    return b


def getNum(htmlcode):  # 获取番号
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"識別碼")]/following-sibling::span/text()')).strip(" ['']")
    return result


def getDirector(htmlcode):  # 获取导演
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"導演")]/following-sibling::a/text()')).strip(" ['']")
    return result


def getOutlineScore(number):  # 获取简介
    outline = ''
    score = ''
    try:
        response = post_html("https://www.jav321.com/search", query={"sn": number})
        detail_page = etree.fromstring(response, etree.HTMLParser())
        outline = str(detail_page.xpath('/html/body/div[2]/div[1]/div[1]/div[2]/div[3]/div/text()')).strip(" ['']")
        if re.search(r'<b>平均評価</b>: <img data-original="/img/(\d+).gif" />', response):
            score = re.findall(r'<b>平均評価</b>: <img data-original="/img/(\d+).gif" />', response)[0]
            score = str(float(score) / 10.0)
        else:
            score = str(re.findall(r'<b>平均評価</b>: ([^<]+)<br>', response)).strip(" [',']").replace('\'', '')
        if outline == '':
            dmm_htmlcode = get_html(
                "https://www.dmm.co.jp/search/=/searchstr=" + number.replace('-', '') + "/sort=ranking/")
            if 'に一致する商品は見つかりませんでした' not in dmm_htmlcode:
                dmm_page = etree.fromstring(dmm_htmlcode, etree.HTMLParser())
                url_detail = str(dmm_page.xpath('//*[@id="list"]/li[1]/div/p[2]/a/@href')).split(',', 1)[0].strip(
                    " ['']")
                if url_detail != '':
                    dmm_detail = get_html(url_detail)
                    html = etree.fromstring(dmm_detail, etree.HTMLParser())
                    outline = str(html.xpath('//*[@class="mg-t0 mg-b20"]/text()')).strip(" ['']").replace('\\n',
                                                                                                          '').replace(
                        '\n', '')
    except Exception as error_info:
        print('Error in javbus.getOutlineScore : ' + str(error_info))
    return outline, score


def getSeries(htmlcode):
    html = etree.fromstring(htmlcode, etree.HTMLParser())
    result = str(html.xpath('//span[contains(text(),"系列")]/following-sibling::a/text()')).strip(" ['']")
    return result


def getCover_small(number):  # 从avsox获取封面图
    try:
        # 根据语言优先级选择 avsox 语言版本
        from Function.getHtml import get_language_priority
        priority = get_language_priority()
        lang_code = 'cn'  # 默认简体中文
        for lang in priority:
            if lang in ['sc', 'tc']:
                lang_code = 'cn'
                break
            elif lang == 'ja':
                lang_code = 'jp'
                break
            elif lang == 'en':
                lang_code = 'en'
                break
        htmlcode = get_html(f'https://avsox.website/{lang_code}/search/' + number)
        html = etree.fromstring(htmlcode, etree.HTMLParser())
        counts = len(html.xpath("//div[@id='waterfall']/div/a/div"))
        if counts == 0:
            return ''
        for count in range(1, counts + 1):  # 遍历搜索结果，找到需要的番号
            number_get = html.xpath(
                "//div[@id='waterfall']/div[" + str(count) + "]/a/div[@class='photo-info']/span/date[1]/text()")
            if len(number_get) > 0 and number_get[0].upper() == number.upper():
                cover_small = \
                html.xpath("//div[@id='waterfall']/div[" + str(count) + "]/a/div[@class='photo-frame']/img/@src")[0]
                return cover_small
    except Exception as error_info:
        print('Error in javbus.getCover_small : ' + str(error_info))
    return ''


def getTag(htmlcode):  # 获取标签
    tag = []
    soup = BeautifulSoup(htmlcode, 'lxml')
    a = soup.find_all(attrs={'class': 'genre'})
    for i in a:
        if 'onmouseout' in str(i):
            continue
        tag.append(i.get_text())
    return tag


def find_number(number):
    # =======================================================================有码搜索
    if not (re.match(r'^\d{4,}', number) or re.match(r'n\d{4}', number) or 'HEYZO' in number.upper()):
        search_url = build_javbus_url('/search/' + number + '&type=1')
        htmlcode = get_html(search_url)
        html = etree.fromstring(htmlcode, etree.HTMLParser())  # //table/tr[1]/td[1]/text()
        counts = len(html.xpath("//div[@id='waterfall']/div[@id='waterfall']/div"))
        if counts != 0:
            for count in range(1, counts + 1):  # 遍历搜索结果，找到需要的番号
                number_get = html.xpath("//div[@id='waterfall']/div[@id='waterfall']/div[" + str(
                    count) + "]/a[@class='movie-box']/div[@class='photo-info']/span/date[1]/text()")[0]
                number_get = number_get.upper()
                number = number.upper()
                if number_get == number or number_get == number.replace('-', '') or number_get == number.replace('_',
                                                                                                                 ''):
                    result_url = html.xpath(
                        "//div[@id='waterfall']/div[@id='waterfall']/div[" + str(
                            count) + "]/a[@class='movie-box']/@href")[0]
                    return result_url
    # =======================================================================无码搜索
    uncensored_search_url = build_javbus_url('/uncensored/search/' + number + '&type=1')
    htmlcode = get_html(uncensored_search_url)
    html = etree.fromstring(htmlcode, etree.HTMLParser())  # //table/tr[1]/td[1]/text()
    counts = len(html.xpath("//div[@id='waterfall']/div[@id='waterfall']/div"))
    if counts == 0:
        return 'not found'
    for count in range(1, counts + 1):  # 遍历搜索结果，找到需要的番号
        number_get = html.xpath("//div[@id='waterfall']/div[@id='waterfall']/div[" + str(
            count) + "]/a[@class='movie-box']/div[@class='photo-info']/span/date[1]/text()")[0]
        number_get = number_get.upper()
        number = number.upper()
        if number_get == number or number_get == number.replace('-', '') or number_get == number.replace('_', ''):
            result_url = html.xpath(
                "//div[@id='waterfall']/div[@id='waterfall']/div[" + str(count) + "]/a[@class='movie-box']/@href")[0]
            return result_url
        elif number_get == number.replace('-', '_') or number_get == number.replace('_', '-'):
            result_url = html.xpath(
                "//div[@id='waterfall']/div[@id='waterfall']/div[" + str(count) + "]/a[@class='movie-box']/@href")[0]
            return result_url
    return 'not found'


def main(number, appoint_url):
    try:
        if appoint_url:
            result_url = appoint_url
        else:
            result_url = find_number(number)
        if result_url == 'not found':
            raise Exception('Movie Data not found in javbus.main!')
        htmlcode = get_html(result_url)
        if str(htmlcode) == 'ProxyError':
            raise TimeoutError
        outline, score = getOutlineScore(number)
        number = getNum(htmlcode)
        
        # 获取演员信息（包含ID和头像）
        actor_info = getActorInfo(htmlcode)
        actor_list = list(actor_info.keys())
        actor_photo = {name: info['photo'] for name, info in actor_info.items()}
        # 标准化演员ID格式：javbus:1234
        actor_id = {name: f"javbus:{info['id']}" for name, info in actor_info.items() if info['id']}
        
        dic = {
            'title': str(getTitle(htmlcode)).replace(number, '').strip().replace(' ', '-'),
            'studio': getStudio(htmlcode),
            'publisher': getPublisher(htmlcode),
            'year': getYear(getRelease(htmlcode)),
            'outline': outline,
            'score': score,
            'runtime': getRuntime(htmlcode).replace('分鐘', '').strip(),
            'director': getDirector(htmlcode),
            'actor': actor_list,
            'actor_id': actor_id,
            'release': getRelease(htmlcode),
            'number': number,
            'cover': getCover(htmlcode),
            'extrafanart': getExtraFanart(htmlcode),
            'imagecut': 1,
            'tag': getTag(htmlcode),
            'series': getSeries(htmlcode),
            'actor_photo': actor_photo,
            'website': result_url,
            'source': 'javbus.py',
        }
    except TimeoutError:
        dic = {
            'title': '',
            'website': 'timeout',
        }
    except Exception as error_info:
        print('Error in javbus.main : ' + str(error_info))
        dic = {
            'title': '',
            'website': '',
        }
    js = json.dumps(dic, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ':'), )  # .encode('UTF-8')
    return js


def main_uncensored(number, appoint_url):
    try:
        result_url = ''
        if appoint_url == '':
            result_url = find_number(number)
        else:
            result_url = appoint_url
        if result_url == 'not found':
            raise Exception('Movie Data not found in javbus.main_uncensored!')
        htmlcode = get_html(result_url)
        if str(htmlcode) == 'ProxyError':
            raise TimeoutError
        number = getNum(htmlcode)
        outline = ''
        score = ''
        if 'HEYZO' in number.upper():
            outline, score = getOutlineScore(number)
        dic = {
            'title': getTitle(htmlcode).replace(number, '').strip().replace(' ', '-'),
            'studio': getStudio(htmlcode),
            'publisher': '',
            'year': getYear(getRelease(htmlcode)),
            'outline': outline,
            'score': score,
            'runtime': getRuntime(htmlcode).replace('分鐘', '').strip(),
            'director': getDirector(htmlcode),
            'actor': getActor(htmlcode),
            'release': getRelease(htmlcode),
            'number': getNum(htmlcode),
            'cover': getCover(htmlcode),
            'extrafanart': getExtraFanart(htmlcode),
            'tag': getTag(htmlcode),
            'series': getSeries(htmlcode),
            'imagecut': 3,
            'cover_small': getCover_small(number),  # 从avsox获取封面图
            'actor_photo': getActorPhoto(htmlcode),
            'website': result_url,
            'source': 'javbus.py',
        }
        if dic['cover_small'] == '':
            dic['imagecut'] = 0
    except TimeoutError:
        dic = {
            'title': '',
            'website': 'timeout',
        }
    except Exception as error_info:
        print('Error in javbus.main_uncensored : ' + str(error_info))
        dic = {
            'title': '',
            'website': '',
        }
    js = json.dumps(dic, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ':'), )  # .encode('UTF-8')
    return js


def main_us(number, appoint_url=''):
    try:
        if appoint_url:
            result_url = appoint_url
        else:
            # javbus.one 是欧美版，使用相同的语言设置
            lang = get_javbus_lang()
            if lang:
                search_url = f'https://www.javbus.one/{lang}/search/' + number
            else:
                search_url = 'https://www.javbus.one/search/' + number
            htmlcode = get_html(search_url)
            if str(htmlcode) == 'ProxyError':
                raise TimeoutError
            html = etree.fromstring(htmlcode, etree.HTMLParser())  # //table/tr[1]/td[1]/text()
            counts = len(html.xpath("//div[@class='row']/div[@id='waterfall']/div"))
            if counts == 0:
                raise Exception('Movie Data not found in javbus.main_us!')
            result_url = ''
            cover_small = ''
            for count in range(1, counts + 1):  # 遍历搜索结果，找到需要的番号
                number_get = html.xpath("//div[@id='waterfall']/div[" + str(
                    count) + "]/a[@class='movie-box']/div[@class='photo-info']/span/date[1]/text()")[0]
                if number_get.upper() == number.upper() or number_get.replace('-', '').upper() == number.upper():
                    result_url = html.xpath(
                        "//div[@id='waterfall']/div[" + str(count) + "]/a[@class='movie-box']/@href")[0]
                    cover_small = html.xpath(
                        "//div[@id='waterfall']/div[" + str(
                            count) + "]/a[@class='movie-box']/div[@class='photo-frame']/img[@class='img']/@src")[0]
                    break
            if result_url == '':
                raise Exception('Movie Data not found in javbus.main_us!')
        htmlcode = get_html(result_url)
        if str(htmlcode) == 'ProxyError':
            raise TimeoutError
        number = getNum(htmlcode)
        dic = {
            'title': getTitle(htmlcode).replace(number, '').strip(),
            'studio': getStudio(htmlcode),
            'year': getYear(getRelease(htmlcode)),
            'runtime': getRuntime(htmlcode).replace('分鐘', '').strip(),
            'director': getDirector(htmlcode),
            'actor': getActor(htmlcode),
            'release': getRelease(htmlcode),
            'number': getNum(htmlcode),
            'tag': getTag(htmlcode),
            'series': getSeries(htmlcode),
            'cover': getCover(htmlcode),
            'extrafanart': getExtraFanart(htmlcode),
            'cover_small': '',
            'imagecut': 0,
            'actor_photo': getActorPhoto(htmlcode),
            'publisher': '',
            'outline': '',
            'score': '',
            'website': result_url,
            'source': 'javbus.py',
        }
    except TimeoutError:
        dic = {
            'title': '',
            'website': 'timeout',
        }
    except Exception as error_info:
        print('Error in javbus.main_us : ' + str(error_info))
        dic = {
            'title': '',
            'website': '',
        }
    js = json.dumps(dic, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ':'), )  # .encode('UTF-8')
    return js


'''
print(find_number('KA-001'))
print(main_uncensored('010115-001'))
print(main('ssni-644'))
print(main_uncensored('012715-793'))
print(main_us('sexart.15.06.10'))
print(main_uncensored('heyzo-1031'))
'''

# print(main('ssni-644', "https://www.javbus.com/SSNI-644"))
# print(main('ssni-802', ""))
# print(main_us('DirtyMasseur.20.07.26', "https://www.javbus.one/DirtyMasseur-20-07-26"))
