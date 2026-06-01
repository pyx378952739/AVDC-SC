import requests
import os
from configparser import ConfigParser
import cloudscraper


# ========================================================================获取config
def get_config():
    config_file = ''
    if os.path.exists('../config.ini'):
        config_file = '../config.ini'
    elif os.path.exists('config.ini'):
        config_file = 'config.ini'
    config = ConfigParser()
    config.read(config_file, encoding='UTF-8')
    proxy_type = str(config['proxy']['type'])
    proxy = str(config['proxy']['proxy'])
    timeout = int(config['proxy']['timeout'])
    retry_count = int(config['proxy']['retry'])
    # 获取语言优先级配置，默认简体中文优先
    try:
        lang_priority = str(config['language']['priority'])
    except:
        lang_priority = 'sc,tc,ja'
    return proxy_type, proxy, timeout, retry_count, lang_priority


# ========================================================================获取语言设置
def get_language_priority():
    """获取语言优先级列表，默认 sc,tc,ja"""
    try:
        config_file = ''
        if os.path.exists('../config.ini'):
            config_file = '../config.ini'
        elif os.path.exists('config.ini'):
            config_file = 'config.ini'
        config = ConfigParser()
        config.read(config_file, encoding='UTF-8')
        lang_str = config.get('language', 'priority', fallback='sc,tc,ja')
        return [x.strip().lower() for x in lang_str.split(',') if x.strip()]
    except:
        return ['sc', 'tc', 'ja']


# ========================================================================获取语言对应的 Accept-Language header
def get_lang_header(lang_code):
    """根据语言代码获取 HTTP Accept-Language 值"""
    lang_map = {
        'sc': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,ja;q=0.7',
        'tc': 'zh-TW,zh;q=0.9,zh-CN;q=0.8,ja;q=0.7',
        'ja': 'ja-JP,ja;q=0.9,zh;q=0.8',
        'en': 'en-US,en;q=0.9,zh;q=0.8,ja;q=0.7'
    }
    return lang_map.get(lang_code, lang_map['sc'])


# ========================================================================获取proxies
def get_proxies(proxy_type, proxy):
    proxies = {}
    if proxy == '' or proxy_type == '' or proxy_type == 'no':
        proxies = {}
    elif proxy_type == 'http':
        proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
    elif proxy_type == 'socks5':
        proxies = {"http": "socks5://" + proxy, "https": "socks5://" + proxy}
    return proxies


# ========================================================================网页请求
# 破解cf5秒盾
def get_html_javdb(url):
    scraper = cloudscraper.create_scraper()
    # 发送请求，获得响应
    response = scraper.get(url)
    # 获得网页源代码
    html = response.text
    return html


def get_html(url, cookies=None, lang=None):
    proxy_type = ''
    retry_count = 0
    proxy = ''
    timeout = 0
    try:
        proxy_type, proxy, timeout, retry_count, _ = get_config()
    except Exception as error_info:
        print('Error in get_html :' + str(error_info))
        print('[-]Proxy config error! Please check the config.')
    proxies = get_proxies(proxy_type, proxy)
    
    # 获取语言设置
    lang_priority = get_language_priority()
    if lang:
        accept_lang = get_lang_header(lang)
    else:
        accept_lang = get_lang_header(lang_priority[0] if lang_priority else 'sc')
    
    # 如果是 javbus 网站，自动添加绕过年龄验证的 cookie
    if cookies is None and 'javbus' in str(url).lower():
        cookies = {'existmag': 'all'}
    
    i = 0
    while i < retry_count:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': accept_lang}
            getweb = requests.get(str(url), headers=headers, timeout=timeout, proxies=proxies, cookies=cookies)
            getweb.encoding = 'utf-8'
            return getweb.text
        except Exception as error_info:
            i += 1
            error_str = str(error_info)
            # 简化错误信息
            if 'Read timed out' in error_str:
                print(f'[-]请求超时 ({timeout}秒)')
            elif 'Connection refused' in error_str or 'Connection aborted' in error_str:
                print(f'[-]连接被拒绝，代理可能不可用')
            elif 'Max retries exceeded' in error_str:
                print(f'[-]超过最大重试次数')
            elif 'SSL' in error_str:
                print(f'[-]SSL连接错误')
            else:
                print('Error in get_html :' + error_str[:100])
            print(f'[-]Connect retry {i}/{retry_count}')
            
            # 最后一次重试前等待更长时间
            if i >= retry_count:
                print('[-]Connect Failed! Please check your Proxy or Network!')
                print('[-]建议：1.检查代理是否开启 2.切换代理节点 3.增加超时时间')
    return 'ProxyError'


def post_html(url: str, query: dict):
    proxy_type = ''
    retry_count = 0
    proxy = ''
    timeout = 0
    try:
        proxy_type, proxy, timeout, retry_count, _ = get_config()
    except Exception as error_info:
        print('Error in post_html :' + str(error_info))
        print('[-]Proxy config error! Please check the config.')
    proxies = get_proxies(proxy_type, proxy)
    for i in range(retry_count):
        try:
            result = requests.post(url, data=query, proxies=proxies, timeout=timeout)
            result.encoding = 'utf-8'
            result = result.text
            return result
        except Exception as error_info:
            print('Error in post_html :' + str(error_info))
            print("[-]Connect retry {}/{}".format(i + 1, retry_count))
    print("[-]Connect Failed! Please check your Proxy or Network!")
    return 'ProxyError'
