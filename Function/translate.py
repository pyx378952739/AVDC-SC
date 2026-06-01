#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译模块 - 支持日文、繁体中文翻译为简体中文
使用 Google Translate API (通过 googletrans 库或备用方案)
"""

import re
import json
import urllib.request
import urllib.parse
import ssl
import time

try:
    from googletrans import Translator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def translate_text_googletrans(text, src='ja', dest='zh-cn'):
    if not text or text.strip() == '':
        return text
    try:
        translator = Translator()
        result = translator.translate(text, src=src, dest=dest)
        return result.text
    except Exception as e:
        print(f'[-] googletrans 翻译失败: {e}')
        return None


def translate_text_urllib(text, src='ja', dest='zh-cn'):
    if not text or text.strip() == '':
        return text
    
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={dest}&dt=t&q={encoded_text}"
        
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with urllib.request.urlopen(request, context=ssl_context, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            translated_text = ''
            if data and len(data) > 0 and data[0]:
                for sentence in data[0]:
                    if sentence and len(sentence) > 0:
                        translated_text += sentence[0]
            
            return translated_text if translated_text else text
            
    except Exception as e:
        print(f'[-] urllib 翻译失败: {e}')
        return None


def translate_text(text, src='ja', dest='zh-cn'):
    if not text or text.strip() == '':
        return text
    
    if is_chinese_text(text):
        return text
    
    if is_japanese_text(text):
        src = 'ja'
    else:
        src = 'ja'
    
    if HAS_GOOGLETRANS:
        result = translate_text_googletrans(text, src, dest)
        if result:
            return result
    
    result = translate_text_urllib(text, src, dest)
    if result:
        return result
    
    print(f'[!] 翻译失败，使用原文: {text[:50]}...')
    return text


def is_chinese_text(text):
    if not text:
        return False
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
    korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
    
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return False
    
    if japanese_chars > 0 or korean_chars > 0:
        return False
    
    return (chinese_chars / total_chars) > 0.4


def is_japanese_text(text):
    if not text:
        return False
    
    japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return False
    
    return (japanese_chars / total_chars) > 0.3


def simple_tc_to_sc(text):
    if not text:
        return text
    
    tc_chars = {
        '製作': '制作', '發行': '发行', '導演': '导演', '編劇': '编剧',
        '片商': '片商', '片長': '片长', '預告': '预告', '封面': '封面',
        '下載': '下载', '評論': '评论', '分類': '分类', '年份': '年份',
        '時間': '时间', '級別': '级别', '評分': '评分', '人氣': '人气',
        '收藏': '收藏', '觀看': '观看', '喜歡': '喜欢', '搜索': '搜索',
        '結果': '结果', '抱歉': '抱歉', '沒有': '没有', '找到': '找到',
        '相關': '相关', '內容': '内容', '影片': '影片', '视频': '视频',
        '名稱': '名称', '標題': '标题', '作者': '作者', '主演': '主演',
        '演員': '演员', '男优': '男优', '女优': '女优', '出品': '出品',
        '上映': '上映', '發售': '发售', '發行日期': '发行日期', '發布': '发布',
        '公司': '公司', '系列': '系列', '風格': '风格', '類型': '类型',
        '標籤': '标签', '類別': '类别', '題材': '题材', '簡介': '简介',
        '描述': '描述', '說明': '说明', '解說': '解说', '故事': '故事',
        '大綱': '大纲', '剧情': '剧情', '劇情': '剧情', '章節': '章节',
        '片段': '片段', '畫質': '画质', '畫面': '画面', '解析': '解析',
        '尺寸': '尺寸', '大小': '大小', '容量': '容量', '格式': '格式',
        '編碼': '编码', '語言': '语言', '字幕': '字幕', '配音': '配音',
        '配樂': '配乐', '音樂': '音乐', '特效': '特效', '場景': '场景',
        '鏡頭': '镜头', '截圖': '截图', '預覽': '预览', '預告片': '预告片',
        '宣傳': '宣传', '海報': '海报', '寫真': '写真', '照片': '照片',
        '圖片': '图片', '影像': '影像', '資料': '资料', '信息': '信息',
        '情報': '情报', '元數據': '元数据', '屬性': '属性', '特徵': '特征',
        '特點': '特点', '特色': '特色', '詳情': '详情', '詳細': '详细',
        '具體': '具体', '全部': '全部', '其他': '其他', '更多': '更多',
        '類似': '类似', '推薦': '推荐', '熱門': '热门', '最新': '最新',
        '隨機': '随机', '順序': '顺序', '排序': '排序', '篩選': '筛选',
        '過濾': '过滤', '設置': '设置', '選項': '选项', '配置': '配置',
        '功能': '功能', '模式': '模式', '狀態': '状态', '問題': '问题',
        '錯誤': '错误', '失敗': '失败', '成功': '成功', '完成': '完成',
        '處理': '处理', '正在': '正在', '加載': '加载', '讀取': '读取',
        '寫入': '写入', '保存': '保存', '存儲': '存储', '刪除': '删除',
        '移除': '移除', '新增': '新增', '編輯': '编辑', '修改': '修改',
        '更新': '更新', '升級': '升级', '上傳': '上传', '導入': '导入',
        '導出': '导出', '備份': '备份', '還原': '还原', '恢復': '恢复',
        '初始化': '初始化', '重置': '重置', '取消': '取消', '確認': '确认',
        '開啟': '开启', '關閉': '关闭', '啟用': '启用', '停用': '停用',
        '開始': '开始', '停止': '停止', '暫停': '暂停', '繼續': '继续',
        '前進': '前进', '後退': '后退', '上一個': '上一个', '下一個': '下一个',
        '返回': '返回', '退出': '退出', '關於': '关于', '幫助': '帮助',
        '方法': '方法', '步驟': '步骤', '教程': '教程', '指南': '指南',
        '手冊': '手册', '文檔': '文档', '文獻': '文献', '參考': '参考',
        '鏈接': '链接', '連接': '连接', '網址': '网址', '地址': '地址',
        '位置': '位置', '目錄': '目录', '文件': '文件', '資料夾': '文件夹',
        '磁盤': '磁盘', '內存': '内存', '緩存': '缓存', '系統': '系统',
        '程序': '程序', '進程': '进程', '線程': '线程', '任務': '任务',
        '作業': '作业', '用戶': '用户', '管理': '管理', '控制': '控制',
        '監控': '监控', '維護': '维护', '優化': '优化', '調試': '调试',
        '測試': '测试', '驗證': '验证', '標準': '标准', '規範': '规范',
        '規格': '规格', '型號': '型号', '版本': '版本', '代碼': '代码',
        '構建': '构建', '編譯': '编译', '執行': '执行', '運行': '运行',
        '日誌': '日志', '記錄': '记录', '跟蹤': '跟踪', '排查': '排查',
        '解決': '解决', '事務': '事务', '操作': '操作', '事件': '事件',
        '通知': '通知', '提醒': '提醒', '警告': '警告', '提示': '提示',
        '訊息': '信息', '消息': '消息', '通訊': '通讯', '郵件': '邮件',
        '短信': '短信', '電話': '电话', '會議': '会议', '日曆': '日历',
        '日程': '日程', '約會': '约会', '待辦': '待办', '備忘': '备忘',
        '筆記': '笔记', '歸檔': '归档', '標記': '标记', '書籤': '书签',
        '關注': '关注', '粉絲': '粉丝', '好友': '好友', '分享': '分享',
        '轉發': '转发', '點贊': '点赞', '打賞': '打赏', '捐贈': '捐赠',
        '資助': '资助', '讚助': '赞助', '推廣': '推广', '公關': '公关',
        '品牌': '品牌', '形象': '形象', '聲譽': '声誉', '口碑': '口碑',
        '評價': '评价', '評級': '评级', '評分': '评分', '評選': '评选',
        '評估': '评估', '建議': '建议', '意見': '意见', '反饋': '反馈',
        '投訴': '投诉', '舉報': '举报', '表揚': '表扬', '批評': '批评',
        '處罰': '处罚', '獎勵': '奖励', '表彰': '表彰', '感謝': '感谢',
        '道歉': '道歉', '遺憾': '遗憾', '抱歉': '抱歉', '祝賀': '祝贺',
        '歡迎': '欢迎', '再見': '再见', '明天': '明天', '後天': '后天',
        '昨天': '昨天', '前天': '前天', '今天': '今天', '現在': '现在',
        '剛才': '刚才', '稍後': '稍后', '馬上': '马上', '立即': '立即',
        '即將': '即将', '立刻': '立刻', '在此': '在此', '此處': '此处',
        '那裡': '那里', '這裡': '这里', '哪裡': '哪里', '哪個': '哪个',
        '這個': '这个', '那個': '那个', '這些': '这些', '那些': '那些',
        '自己': '自己', '別人': '别人', '什麼': '什么', '怎麼': '怎么',
        '為什麼': '为什么', '怎樣': '怎样', '如何': '如何', '應該': '应该',
        '必須': '必须', '需要': '需要', '可以': '可以', '不行': '不行',
        '不要': '不要', '別': '别', '也許': '也许', '可能': '可能',
        '大概': '大概', '認為': '认为', '相信': '相信', '確定': '确定',
        '肯定': '肯定', '一定': '一定', '當然': '当然', '自然': '自然',
        '這樣': '这样', '那樣': '那样', '這麼': '这么多', '那麼': '那么多',
        '長度': '长度', '寬度': '宽度', '高度': '高度', '深度': '深度',
        '厚度': '厚度', '角度': '角度', '溫度': '温度', '濕度': '湿度',
        '速度': '速度', '頻率': '频率', '強度': '强度', '亮度': '亮度',
        '對比度': '对比度', '飽和度': '饱和度', '色調': '色调',
        '解析度': '解析度', '分辨率': '分辨率', '像素': '像素',
        '識別碼': '识别码', '有碼': '有码', '無碼': '无码', '流出': '流出',
        '盜攝': '盗摄', '盜錄': '盗录', '寫真': '写真', '短片': '短片',
        '寫真集': '写真集', '作品': '作品', '商品': '商品', '發售': '发售',
        '公開': '公开', '上映': '上映', '播出': '播出', '播放': '播放',
        '線上': '线上', '線下': '线下', '優惠': '优惠', '折扣': '折扣',
        '特價': '特价', '促銷': '促销', '活動': '活动', '比賽': '比赛',
        '競賽': '竞赛', '挑戰': '挑战', '獎品': '奖品', '獎金': '奖金',
        '獎項': '奖项', '榮譽': '荣誉', '稱號': '称号', '等級': '等级',
        '級別': '级别', '排名': '排名', '榜單': '榜单', '排行榜': '排行榜',
        '趨勢': '趋势', '預測': '预测', '報告': '报告', '統計': '统计',
        '數據': '数据', '數字': '数字', '數值': '数值', '數量': '数量',
        '質量': '质量', '效率': '效率', '效益': '效益', '成果': '成果',
        '成績': '成绩', '成就': '成就', '貢獻': '贡献', '價值': '价值',
        '價格': '价格', '成本': '成本', '利潤': '利润', '收益': '收益',
        '投資': '投资', '回報': '回报', '風險': '风险', '機會': '机会',
        '可能性': '可能性', '概率': '概率', '比率': '比率', '比例': '比例',
        '百分比': '百分比', '總計': '总计', '合計': '合计', '總數': '总数',
        '總量': '总量', '平均值': '平均值', '最大值': '最大值', '最小值': '最小值',
        '總和': '总和', '差異': '差异', '偏差': '偏差', '誤差': '误差',
        '腳': '脚', '腿': '腿', '手': '手', '臂': '臂', '肩': '肩',
        '背': '背', '腰': '腰', '腹': '腹', '胸': '胸', '頸': '颈',
        '頭': '头', '臉': '脸', '眼': '眼', '睛': '睛', '眉毛': '眉毛',
        '鼻子': '鼻子', '嘴': '嘴', '唇': '唇', '牙齒': '牙齿', '舌': '舌',
        '耳': '耳', '頭髮': '头发', '皮膚': '皮肤', '骨': '骨', '肉': '肉',
        '血': '血', '心': '心', '心臓': '心脏', '肝': '肝', '肺': '肺',
        '腎': '肾', '胃': '胃', '腸': '肠', '腦': '脑', '神經': '神经',
        '修復': '修复', '癒合': '愈合', '康復': '康复', '成長': '成长',
        '發育': '发育', '老化': '老化', '衰老': '衰老', '死亡': '死亡',
        '誕生': '诞生', '出生': '出生', '去世': '去世', '逝世': '逝世',
        '犧牲': '牺牲', '遇難': '遇难', '殉職': '殉职',
        '素人': '素人', '美腳': '美脚', '巨乳': '巨乳', '人妻': '人妻',
        '熟女': '熟女', '蘿莉': '萝莉', '少女': '少女', '辣妹': '辣妹',
        '清純': '清纯', '淫蕩': '淫荡', '醜聞': '丑闻', '偷拍': '偷拍',
        '企劃': '企划', '合輯': '合辑', '總集': '总集', '特別': '特别',
        '篇': '篇', '集': '集', '部': '部', '話': '话', '卷': '卷',
        '冊': '册', '號': '号', '期': '期', '版': '版', '級': '级',
        '等': '等', '類': '类', '種': '种', '項': '项', '件': '件',
        '筆': '笔', '宗': '宗', '例': '例', '案': '案', '起': '起',
        '次': '次', '回': '回', '屆': '届', '輪': '轮', '週': '周',
        '星期': '星期', '月份': '月份', '年度': '年度', '世紀': '世纪',
        '年代': '年代', '時期': '时期', '階段': '阶段', '層次': '层次',
        '品質': '品质', '效果': '效果', '反饋': '反馈',
    }
    
    result = text
    for tc, sc in tc_chars.items():
        result = result.replace(tc, sc)
    
    return result


def translate_movie_data(movie_data, config=None):
    if config is None:
        config = {'enabled': True}
    
    if not config.get('enabled', True):
        for key in movie_data:
            if isinstance(movie_data[key], str):
                movie_data[key] = simple_tc_to_sc(movie_data[key])
        return movie_data
    
    translated_data = {}
    
    fields_to_translate = [
        'title', 'outline', 'director', 'publisher',
        'series', 'studio', 'publisher', 'label',
        'genres', 'actors', 'tags', 'criticReview',
        'releaseDate', 'year', 'runtime', 'rating',
        'coverUrl', 'thumbnailUrl', 'extrafanart',
        'website', 'trailer', 'orig_title'
    ]
    
    for key, value in movie_data.items():
        if value is None or value == '':
            translated_data[key] = value
            continue
        
        if key == 'num':
            translated_data[key] = value
            continue
        
        if isinstance(value, str):
            if key in ['coverUrl', 'thumbnailUrl', 'extrafanart', 'website', 'trailer']:
                translated_data[key] = value
            elif key == 'releaseDate':
                translated_data[key] = simple_tc_to_sc(value)
            else:
                sc_value = simple_tc_to_sc(value)
                
                if is_japanese_text(value):
                    translated_value = translate_text(sc_value)
                    translated_data[key] = translated_value
                else:
                    translated_data[key] = sc_value
                    
        elif isinstance(value, list):
            translated_list = []
            for item in value:
                if isinstance(item, str):
                    if key in ['coverUrl', 'thumbnailUrl', 'extrafanart']:
                        translated_list.append(item)
                    else:
                        sc_item = simple_tc_to_sc(item)
                        if is_japanese_text(item):
                            translated_item = translate_text(sc_item)
                            translated_list.append(translated_item)
                        else:
                            translated_list.append(sc_item)
                else:
                    translated_list.append(item)
            translated_data[key] = translated_list
        else:
            translated_data[key] = value
    
    return translated_data
