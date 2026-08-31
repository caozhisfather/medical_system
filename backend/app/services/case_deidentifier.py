from __future__ import annotations

import re
from dataclasses import dataclass, field


_SURNAME_CHARS = (
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公"
)

_SURNAME_CLASS = f"[{_SURNAME_CHARS}]"
_NAME = f"{_SURNAME_CLASS}[\u4e00-\u9fa5]{{1,2}}"

_ID_18 = re.compile(r"(?<!\d)(\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?!\d)")
_ID_15 = re.compile(r"(?<!\d)(\d{15})(?!\d)")
_MOBILE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
_LANDLINE = re.compile(r"(?<!\d)(0\d{2,3}[- ]?\d{7,8})(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")

_NAME_TITLE = (
    r"患者姓名|联系人姓名|家属姓名|监护人姓名|经治医师|主治医师|主任医师|住院医师|麻醉医师|报告医师|检查医师|申请医师"
    r"|医师|医生|护士|术者|主刀|记录者|记录人|家属|联系人|监护人|姓名"
)
_NAME_LABEL_PATTERN = re.compile(rf"({_NAME_TITLE})\s*[:：|]*\s*({_NAME})")
_PATIENT_LABEL_PATTERN = re.compile(rf"(患者|病人|患儿|产妇|新生儿)\s*(?:姓名|名字|名)\s*[:：]?\s*({_NAME})")
_PATIENT_BARE_PATTERN = re.compile(
    rf"(?<=患者)({_NAME})(?=[，,。;；\s:：因于以自诉系为否认主诉现病史既往史个人史家族史]|$)"
)
_PATIENT_COMMA_NAME = re.compile(rf"(患者|病人|患儿|产妇|新生儿)\s*[，,]\s*({_NAME})(?=[，,。;；\s:：因于以自诉系为否认主诉现病史既往史个人史家族史]|$)")
_PATIENT_COLON_NAME = re.compile(rf"(患者|病人|患儿|产妇|新生儿)\s*[:：]\s*({_NAME})(?=[，,。;；\s:：因于以自诉系为否认主诉现病史既往史个人史家族史]|$)")
_LEADING_NAME = re.compile(rf"(^|[\r\n])\s*({_NAME})\s*(?=[，,]\s*(?:女|男|女性|男性)|\d{{1,3}}\s*岁)")
_NAME_BEFORE_AGE = re.compile(rf"({_NAME})\s*(?=\d{{1,3}}\s*岁)")

_ADDRESS_LABEL = re.compile(
    r"(家庭住址|现住址|居住地址|户籍地址|通讯地址|住址|地址)\s*[:：]?\s*([^\n\r]{2,80}?)(?=\s*(?:电话|手机|邮编|联系电话|职业|工作单位|民族|婚姻|婚否|联系人|出生|$)|\n|\r)"
)
_ADDRESS_GENERIC = re.compile(
    r"[\u4e00-\u9fa5]{2,10}(?:省|自治区)[\u4e00-\u9fa5]{1,12}(?:市|地区|自治州|盟)[\u4e00-\u9fa5]{1,12}(?:区|县|旗)[\u4e00-\u9fa5\d]{0,28}(?:路|街|道|巷|弄|村|镇|乡|组|队|号|栋|单元|室|楼)"
)
_BIRTHPLACE = re.compile(r"(出生地|籍贯|原籍)\s*[:：]?\s*([^\n\r]{1,40}?)(?=\s*(?:婚姻|民族|职业|文化|出生|$)|\n|\r|[，。；;])")
_BIRTH_DATE = re.compile(r"(出生日期|出生年月|出生|生于)\s*[:：]?\s*\d{4}\s*[年./\-]\s*\d{1,2}\s*[月./\-]?\s*\d{0,2}\s*日?")
_RECORD_NO = re.compile(r"(住院号|病历号|病案号|档案号|门诊号|住院证号|ID号)\s*[:：]?\s*([A-Za-z0-9\-Xx*]{3,20})")
_HOMETOWN = re.compile(r"[\u4e00-\u9fa5]{2,10}(?:省|市|县|区|镇|乡|村)[\u4e00-\u9fa5]{0,16}人")

_DISEASE_KEYWORDS = (
    "间质性肺炎", "短暂性脑缺血", "血管神经性头痛", "急性上呼吸道感染", "上呼吸道感染", "支气管扩张", "类风湿关节炎",
    "腰椎骨质增生", "消化性溃疡", "胸腔积液", "心力衰竭", "神经官能症", "周围神经炎", "面神经麻痹", "过敏性休克",
    "急性胆囊炎", "急性胃肠炎", "急性左心衰", "心功能不全", "干性坏疽", "有机磷", "酒精中毒", "高血压病",
    "冠心病", "心绞痛", "心衰", "心律失常", "室上速", "肺心病", "慢阻肺", "慢支", "支气管哮喘", "哮喘",
    "肺炎", "肺结核", "结核", "胸膜炎", "血气胸", "咯血", "脑梗", "脑梗塞", "脑梗死", "脑出血", "脑膜炎",
    "糖尿病", "痛风", "甲亢", "低钾", "癫痫", "癔病", "神经痛", "面神经", "眩晕", "头痛", "偏瘫", "失语",
    "吞咽障碍", "腹痛", "发热", "腹水", "浮肿", "黄疸", "肾结石", "泌尿系感染", "牙龈炎", "乙肝", "肝炎",
    "过敏性皮炎", "急性荨麻疹", "荨麻疹", "急性胃炎", "胃炎", "急性咽炎", "咽炎", "流产", "骨盆", "新生儿",
    "心肌炎", "颈椎", "腰椎", "上消化道出血", "消化道出血", "贫血"
)


@dataclass
class DeidentificationResult:
    text: str
    pii_types: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)


def _count_and_replace(pattern: re.Pattern[str], text: str, replacement: str, label: str, result: dict[str, int]) -> str:
    count = len(pattern.findall(text))
    if count:
        result[label] = result.get(label, 0) + count
        return pattern.sub(replacement, text)
    return text


def deidentify_text(text: str) -> DeidentificationResult:
    """Apply deterministic rule-based de-identification for Chinese clinical records."""
    if not text:
        return DeidentificationResult(text="", pii_types=[], counts={}, risk_flags=[])

    counts: dict[str, int] = {}
    masked = text

    masked = _count_and_replace(_ID_18, masked, "[身份证号已脱敏]", "身份证号", counts)
    masked = _count_and_replace(_ID_15, masked, "[身份证号已脱敏]", "身份证号", counts)
    masked = _count_and_replace(_MOBILE, masked, "[手机号已脱敏]", "手机号", counts)
    masked = _count_and_replace(_LANDLINE, masked, "[电话已脱敏]", "电话号码", counts)
    masked = _count_and_replace(_EMAIL, masked, "[邮箱已脱敏]", "邮箱", counts)
    masked = _count_and_replace(_RECORD_NO, masked, r"\1：[病历号已脱敏]", "住院/病历号", counts)
    masked = _count_and_replace(_BIRTH_DATE, masked, r"\1：[出生日期已脱敏]", "出生日期", counts)
    masked = _count_and_replace(_BIRTHPLACE, masked, r"\1：[地点已脱敏]", "出生地/籍贯", counts)
    masked = _count_and_replace(_ADDRESS_LABEL, masked, r"\1：[住址已脱敏]", "住址", counts)
    masked = _count_and_replace(_NAME_LABEL_PATTERN, masked, r"\1：X某", "姓名", counts)
    masked = _count_and_replace(_PATIENT_LABEL_PATTERN, masked, r"\1X某", "姓名", counts)
    masked = _count_and_replace(_PATIENT_BARE_PATTERN, masked, "X某", "姓名", counts)
    masked = _count_and_replace(_PATIENT_COMMA_NAME, masked, r"\1X某", "姓名", counts)
    masked = _count_and_replace(_PATIENT_COLON_NAME, masked, r"\1：X某", "姓名", counts)
    masked = _count_and_replace(_LEADING_NAME, masked, r"\1X某", "姓名", counts)
    masked = _count_and_replace(_NAME_BEFORE_AGE, masked, "X某", "姓名", counts)
    masked = _count_and_replace(_HOMETOWN, masked, "[籍贯已脱敏]", "籍贯", counts)
    masked = _count_and_replace(_ADDRESS_GENERIC, masked, "[住址已脱敏]", "住址", counts)

    pii_types = sorted(counts.keys())
    risk_flags: list[str] = []
    if _ID_18.search(masked) or _ID_15.search(masked):
        risk_flags.append("疑似残留身份证号")
    if _MOBILE.search(masked):
        risk_flags.append("疑似残留手机号")
    if _NAME_LABEL_PATTERN.search(masked) or _PATIENT_LABEL_PATTERN.search(masked):
        risk_flags.append("疑似残留姓名")
    if not pii_types:
        risk_flags.append("未检测到明确敏感字段")

    return DeidentificationResult(text=masked, pii_types=pii_types, counts=counts, risk_flags=risk_flags)


def _looks_like_name(value: str) -> bool:
    value = value.strip(" \u3000-_、，,。()（）|/")
    if not 2 <= len(value) <= 4:
        return False
    if not all("\u4e00" <= char <= "\u9fa5" for char in value):
        return False
    if value[0] not in _SURNAME_CHARS:
        return False
    return not any(keyword in value for keyword in _DISEASE_KEYWORDS)


def looks_like_personal_name(value: str) -> bool:
    return _looks_like_name(value)


def sanitize_label(value: str) -> str:
    """Turn a source folder/file name into a de-identified disease label."""
    label = (value or "").strip()
    label = re.sub(r"^\s*\d+\s*[.\-、_ ]*", "", label)
    label = re.sub(r"\d+床", "", label)
    label = re.split(r"-{2,}|_{2,}", label)[-1]

    for keyword in _DISEASE_KEYWORDS:
        index = label.find(keyword)
        if index > 0 and _looks_like_name(label[:index]):
            label = label[index:]
            break

    label = label.strip(" \u3000,，.、-_：:；;。()（）")
    return label
