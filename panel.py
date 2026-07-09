# -*- coding: utf-8 -*-
"""
💎 PREMIUM FREE OTP EARNING TELEGRAM BOT (GLOBAL COUNTRY EDITION V8.0 - ULTIMATE UI)
🔒 Powered by Zenex Core Engine V8.0
"""

import os
import re
import time
import json
from pymongo import MongoClient
import logging
import pyotp
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot import types
from flask import Flask

# ==========================================
# ⚙️ CONFIGURATION BLOCK
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8953778024:AAGHEO5lQrcn9wFjzO-TISJLZltqwGGvS9s")
PRIMARY_ADMIN_ID = int(os.environ.get("PRIMARY_ADMIN_ID", "8375006707"))
FORWARD_GROUP_ID = int(os.environ.get("FORWARD_GROUP_ID", "-1003959588492"))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "sm_otpnumberbot")
FORCE_CHANNEL = os.environ.get("FORCE_CHANNEL", "@sm_otpnumber")
FORCE_CHANNEL_LINK = os.environ.get("FORCE_CHANNEL_LINK", "https://t.me/sm_otpnumber")
FORCE_CHANNEL_2 = os.environ.get("FORCE_CHANNEL_2", "@sm_otpnumber")
FORCE_CHANNEL_LINK_2 = os.environ.get("FORCE_CHANNEL_LINK_2", "https://t.me/sm_otpnumber")

# ZENEX_BASE_URL removed, dynamic panel logic used
DB_FILE = "bot_database.db"

# ==========================================
# 📊 LOGGING & INITIALIZATION
# ==========================================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown", threaded=True)
http_session = requests.Session()

def get_active_panel():
    panel = db.panels.find_one({"is_active": True})
    if not panel:
        return {
            "panel_name": "Zenex (Fallback)",
            "base_url": "https://api.zenexnetwork.com",
            "api_key": get_config("zenex_api_key", "API_KEY")
        }
    return panel

def get_api_headers(api_key=None):
    if not api_key:
        api_key = get_active_panel().get("api_key", "")
    return {
        "mapikey": api_key,
        "mauthapi": api_key,
        "api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ZenexCoreClient/8.0"
    }

user_cooldowns = {}
broadcast_state = {}
api_request_lock = threading.Lock()
db_lock = threading.Lock()

# ==========================================
# 🌐 GLOBAL COUNTRY MAP & SHORT CODE GENERATOR
# ==========================================
def get_country_info(phone_number):
    clean_num = str(phone_number).replace("+", "").strip()
    
    country_prefixes = {
        "1242": ("Bahamas", "🇧🇸", "BS"), "1246": ("Barbados", "🇧🇧", "BB"), "1264": ("Anguilla", "🇦🇮", "AI"), 
        "1268": ("Antigua & Barbuda", "🇦🇬", "AG"), "1345": ("Cayman Islands", "🇰🇾", "KY"), "1441": ("Bermuda", "🇧🇲", "BM"), 
        "1473": ("Grenada", "🇬🇩", "GD"), "1649": ("Turks & Caicos", "🇹🇨", "TC"), "1664": ("Montserrat", "🇲🇸", "MS"), 
        "1758": ("Saint Lucia", "🇱🇨", "LC"), "1767": ("Dominica", "🇩🇲", "DM"), "1784": ("St. Vincent", "🇻🇨", "VC"), 
        "1809": ("Dominican Republic", "🇩🇴", "DO"), "1829": ("Dominican Republic", "🇩🇴", "DO"), "1849": ("Dominican Republic", "🇩🇴", "DO"), 
        "1868": ("Trinidad & Tobago", "🇹🇹", "TT"), "1869": ("Saint Kitts & Nevis", "🇰🇳", "KN"), "1876": ("Jamaica", "🇯🇲", "JM"), 
        "1658": ("Jamaica", "🇯🇲", "JM"), "441481": ("Guernsey", "🇬🇬", "GG"), "441534": ("Jersey", "🇯🇪", "JE"), 
        "441624": ("Isle of Man", "🇮🇲", "IM"), "211": ("South Sudan", "🇸🇸", "SS"), "212": ("Morocco", "🇲🇦", "MA"), 
        "213": ("Algeria", "🇩🇿", "DZ"), "216": ("Tunisia", "🇹🇳", "TN"), "218": ("Libya", "🇱🇾", "LY"), 
        "220": ("Gambia", "🇬🇲", "GM"), "221": ("Senegal", "🇸🇳", "SN"), "222": ("Mauritania", "🇲🇷", "MR"), 
        "223": ("Mali", "🇲🇱", "ML"), "224": ("Guinea", "🇬🇳", "GN"), "225": ("Ivory Coast", "🇨🇮", "CI"), 
        "226": ("Burkina Faso", "🇧🇫", "BF"), "227": ("Niger", "🇳🇪", "NE"), "228": ("Togo", "🇹🇬", "TG"), 
        "229": ("Benin", "🇧🇯", "BJ"), "230": ("Mauritius", "🇲🇺", "MU"), "231": ("Liberia", "🇱🇷", "LR"), 
        "232": ("Sierra Leone", "🇸🇱", "SL"), "233": ("Ghana", "🇬🇭", "GH"), "234": ("Nigeria", "🇳🇬", "NG"), 
        "235": ("Chad", "🇹🇩", "TD"), "236": ("Central African Rep.", "🇨🇫", "CF"), "237": ("Cameroon", "🇨🇲", "CM"), 
        "238": ("Cape Verde", "🇨🇻", "CV"), "239": ("Sao Tome & Principe", "🇸🇹", "ST"), "240": ("Equatorial Guinea", "🇬🇶", "GQ"), 
        "241": ("Gabon", "🇬🇦", "GA"), "242": ("Congo", "🇨🇬", "CG"), "243": ("DR Congo", "🇨🇩", "CD"), 
        "244": ("Angola", "🇦🇴", "AO"), "245": ("Guinea-Bissau", "🇬🇼", "GW"), "248": ("Seychelles", "🇸🇨", "SC"), 
        "249": ("Sudan", "🇸🇩", "SD"), "250": ("Rwanda", "🇷🇼", "RW"), "251": ("Ethiopia", "🇪🇹", "ET"), 
        "252": ("Somalia", "🇸🇴", "SO"), "253": ("Djibouti", "🇩🇯", "DJ"), "254": ("Kenya", "🇰🇪", "KE"), 
        "255": ("Tanzania", "🇹🇿", "TZ"), "256": ("Uganda", "🇺🇬", "UG"), "257": ("Burundi", "🇧🇮", "BI"), 
        "258": ("Mozambique", "🇲🇿", "MZ"), "260": ("Zambia", "🇿🇲", "ZM"), "261": ("Madagascar", "🇲🇬", "MG"), 
        "262": ("Reunion", "🇷🇪", "RE"), "263": ("Zimbabwe", "🇿🇼", "ZW"), "264": ("Namibia", "🇳🇦", "NA"), 
        "265": ("Malawi", "🇲🇼", "MW"), "266": ("Lesotho", "🇱🇸", "LS"), "267": ("Botswana", "🇧🇼", "BW"), 
        "268": ("Swaziland", "🇸🇿", "SZ"), "269": ("Comoros", "🇰🇲", "KM"), "290": ("Saint Helena", "🇸🇭", "SH"), 
        "291": ("Eritrea", "🇪🇷", "ER"), "297": ("Aruba", "🇦🇼", "AW"), "298": ("Faroe Islands", "🇫🇴", "FO"), 
        "299": ("Greenland", "🇬🇱", "GL"), "350": ("Gibraltar", "🇬🇮", "GI"), "351": ("Portugal", "🇵🇹", "PT"), 
        "352": ("Lubembourg", "🇱🇺", "LU"), "353": ("Ireland", "🇮🇪", "IE"), "354": ("Iceland", "🇮🇸", "IS"), 
        "355": ("Albania", "🇦🇱", "AL"), "356": ("Malta", "🇲🇹", "MT"), "357": ("Cyprus", "🇨🇾", "CY"), 
        "358": ("Finland", "🇫🇮", "FI"), "359": ("Bulgaria", "🇧🇬", "BG"), "370": ("Lithuania", "🇱🇹", "LT"), 
        "371": ("Latvia", "🇱🇻", "LV"), "372": ("Estonia", "🇪🇪", "EE"), "373": ("Moldova", "🇲🇩", "MD"), 
        "374": ("Armenia", "🇦🇲", "AM"), "375": ("Belarus", "🇧🇾", "BY"), "376": ("Andorra", "🇦🇩", "AD"), 
        "377": ("Monaco", "🇲🇨", "MC"), "378": ("San Marino", "🇸🇲", "SM"), "380": ("Ukraine", "🇺🇦", "UA"), 
        "381": ("Serbia", "🇷🇸", "RS"), "382": ("Montenegro", "🇲🇪", "ME"), "383": ("Kosovo", "🇽🇰", "XK"), 
        "385": ("Croatia", "🇭🇷", "HR"), "386": ("Slovenia", "🇸🇮", "SI"), "387": ("Bosnia", "🇧🇦", "BA"), 
        "389": ("North Macedonia", "🇲🇰", "MK"), "420": ("Czech Republic", "🇨🇿", "CZ"), "421": ("Slovakia", "🇸🇰", "SK"), 
        "423": ("Liechtenstein", "🇱🇮", "LI"), "500": ("Falkland Islands", "🇫🇰", "FK"), "501": ("Belize", "🇧🇿", "BZ"), 
        "502": ("Guatemala", "🇬🇹", "GT"), "503": ("El Salvador", "🇸🇻", "SV"), "504": ("Honduras", "🇭🇳", "HN"), 
        "505": ("Nicaragua", "🇳🇮", "NI"), "506": ("Costa Rica", "🇨🇷", "CR"), "507": ("Panama", "🇵🇦", "PA"), 
        "508": ("St. Pierre & Miquelon", "🇵🇲", "PM"), "509": ("Haiti", "🇭🇹", "HT"), "590": ("Guadeloupe", "🇬🇵", "GP"), 
        "591": ("Bolivia", "🇧🇴", "BO"), "592": ("Guide", "🇬🇾", "GY"), "593": ("Ecuador", "🇪🇨", "EC"), 
        "594": ("French Guiana", "🇬🇫", "GF"), "595": ("Paraguay", "🇵🇾", "PY"), "596": ("Martinique", "🇲🇶", "MQ"), 
        "597": ("Suriname", "🇸🇷", "SR"), "598": ("Uruguay", "🇺🇾", "UY"), "599": ("Curacao", "🇨🇼", "CW"), 
        "670": ("East Timor", "🇹🇱", "TL"), "672": ("Norfolk Island", "🇳🇫", "NF"), "673": ("Brunei", "🇧🇳", "BN"), 
        "674": ("Nauru", "🇳🇷", "NR"), "675": ("Papua New Guinea", "🇵🇬", "PG"), "676": ("Tonga", "🇹🇴", "TO"), 
        "677": ("Solomon Islands", "🇸🇧", "SB"), "678": ("Vanuatu", "🇻🇺", "VU"), "679": ("Fiji", "🇫Jill", "FJ"), 
        "680": ("Palau", "🇵🇼", "PW"), "681": ("Wallis & Futuna", "🇼🇫", "WF"), "682": ("Cook Islands", "🇨🇰", "CK"), 
        "683": ("Niue", "🇳🇺", "NU"), "685": ("Samoa", "🇼🇸", "WS"), "686": ("Kiribati", "🇰🇮", "KI"), 
        "687": ("New Caledonia", "🇳🇨", "NC"), "688": ("Tuvalu", "🇹🇻", "TV"), "689": ("French Polynesia", "🇵🇫", "PF"), 
        "690": ("Tokelau", "🇹🇰", "TK"), "691": ("Micronesia", "🇫🇲", "FM"), "692": ("Marshall Islands", "🇲🇭", "MH"), 
        "850": ("North Korea", "🇰🇵", "KP"), "852": ("Hong Kong", "🇭🇰", "HK"), "853": ("Macau", "🇲🇴", "MO"), 
        "855": ("Cambodia", "🇰🇭", "KH"), "856": ("Laos", "🇱🇦", "LA"), "880": ("Bangladesh", "🇧🇩", "BD"), 
        "886": ("Taiwan", "🇹🇼", "TW"), "960": ("Maldives", "🇲🇻", "MV"), "961": ("Lebanon", "🇱🇧", "LB"), 
        "962": ("Jordan", "🇯🇴", "JO"), "963": ("Syria", "🇸🇾", "SY"), "964": ("Iraq", "🇮🇶", "IQ"), 
        "965": ("Kuwait", "🇰🇼", "KW"), "966": ("Saudi Arabia", "🇸🇦", "SA"), "967": ("Yemen", "🇾🇪", "YE"), 
        "968": ("Oman", "🇴🇲", "OM"), "970": ("Palestine", "🇵🇸", "PS"), "971": ("UAE", "🇦🇪", "AE"), 
        "972": ("Israel", "🇮🇱", "IL"), "973": ("Bahrain", "🇧🇭", "BH"), "974": ("Qatar", "🇶🇦", "QA"), 
        "975": ("Bhutan", "🇧🇹", "BT"), "976": ("Mongolia", "🇲🇳", "MN"), "977": ("Nepal", "🇳🇵", "NP"), 
        "992": ("Tajikistan", "🇹🇯", "TJ"), "993": ("Turkmenistan", "🇹🇲", "TM"), "994": ("Azerbaijan", "🇦🇿", "AZ"), 
        "995": ("Georgia", "🇬🇪", "GE"), "996": ("Kyrgyzstan", "🇰🇬", "KG"), "998": ("Uzbekistan", "🇺🇿", "UZ"), 
        "20": ("Egypt", "🇪🇬", "EG"), "27": ("South Africa", "🇿🇦", "ZA"), "30": ("Greece", "🇬🇷", "GR"), 
        "31": ("Netherlands", "🇳🇱", "NL"), "32": ("Belgium", "🇧🇪", "BE"), "33": ("France", "🇫🇷", "FR"), 
        "34": ("Spain", "🇪🇸", "ES"), "36": ("Hungary", "🇭🇺", "HU"), "39": ("Italy", "🇮🇹", "IT"), 
        "40": ("Romania", "🇷🇴", "RO"), "41": ("Switzerland", "🇨🇭", "CH"), "43": ("Austria", "🇦🇺", "AT"), 
        "44": ("United Kingdom", "🇬🇧", "GB"), "45": ("Denmark", "🇩🇰", "DK"), "46": ("Sweden", "🇸🇪", "SE"), 
        "47": ("Norway", "🇳🇴", "NO"), "48": ("Poland", "🇵🇱", "PL"), "49": ("Germany", "🇩🇪", "DE"), 
        "51": ("Peru", "🇵🇪", "PE"), "52": ("Mexico", "🇲🇽", "MX"), "53": ("Cuba", "🇨🇺", "CU"), 
        "54": ("Argentina", "🇦🇷", "AR"), "55": ("Brazil", "🇧🇷", "BR"), "56": ("Chile", "🇨🇱", "CL"), 
        "57": ("Colombia", "🇨🇴", "CO"), "58": ("Venezuela", "🇻🇪", "VE"), "60": ("Malaysia", "🇲🇾", "MY"), 
        "61": ("Australia", "🇦🇺", "AU"), "62": ("Indonesia", "🇮🇩", "ID"), "63": ("Philippines", "🇵🇭", "PH"), 
        "64": ("New Zealand", "🇳🇿", "NZ"), "65": ("Singapore", "🇸🇬", "SG"), "66": ("Thailand", "🇹🇭", "TH"), 
        "81": ("Japan", "🇯🇵", "JP"), "82": ("South Korea", "🇰🇷", "KR"), "84": ("Vietnam", "🇻🇳", "VN"), 
        "86": ("China", "🇨🇳", "CN"), "90": ("Turkey", "🇹🇷", "TR"), "91": ("India", "🇮🇳", "IN"), 
        "92": ("Pakistan", "🇵🇰", "PK"), "93": ("Afghanistan", "🇦🇫", "AF"), "94": ("Sri Lanka", "🇱🇰", "LK"), 
        "95": ("Myanmar", "🇲🇲", "MM"), "98": ("Iran", "🇮🇷", "IR"), "7": ("Russia", "🇷🇺", "RU"), 
        "1": ("United States", "🇺🇸", "US")
    }
    
    for length in [6, 5, 4, 3, 2, 1]:
        prefix = clean_num[:length]
        if prefix in country_prefixes:
            return country_prefixes[prefix]
            
    return ("Global Node", "🌐", "UN")


MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://tgproesay8273_db_user:m_otpnumber_bot@cluster0.gtv25c1.mongodb.net/?appName=Cluster0") # REPLACE THIS
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client.bot_database
    mongo_client.server_info()
except Exception as e:
    logger.error(f"MongoDB Connection Error: {e}")

# ==========================================
# 💾 MONGODB CONTROLLER
# ==========================================
def init_db():
    defaults = {
        'zenex_api_key': '8953778024:AAGHEO5lQrcn9wFjzO-TISJLZltqwGGvS9s_fake',
        'reward_amount': '0.0002',
        'ref_commission': '0.01',
        'withdraw_group_id': str(FORWARD_GROUP_ID),
        'otp_group_id': str(FORWARD_GROUP_ID),
        'milestone_step': '100',
        'last_milestone': '0',
        'total_otps_processed': '0',
        'otp_group_link': 'https://t.me/FreeOtpMaster',
        'admin_notifications': '1'
    }
    for k, v in defaults.items():
        if not db.config.find_one({"key": k}):
            db.config.insert_one({"key": k, "value": v})
            
    has_primary = False
    for adm in db.admins.find():
        if adm.get('permissions') and '"fullaccess"' in adm['permissions']:
            has_primary = True
            break
            
    if not has_primary:
        founder = db.admins.find_one({"user_id": str(PRIMARY_ADMIN_ID)})
        if not founder:
            db.admins.insert_one({"user_id": str(PRIMARY_ADMIN_ID), "permissions": '["fullaccess"]'})
        else:
            db.admins.update_one({"user_id": str(PRIMARY_ADMIN_ID)}, {"$set": {"permissions": '["fullaccess"]'}})
        
    if db.services.count_documents({}) == 0:
        db.services.insert_many([
            {"service_name": "Instagram", "country_name": "🇺🇸 United States", "range": "1XXXXXXXXXX", "panel_name": "Zenex"},
            {"service_name": "Facebook", "country_name": "🇺🇸 United States", "range": "1XXXXXXXXXX", "panel_name": "Zenex"}
        ])
        
    if db.panels.count_documents({}) == 0:
        db.panels.insert_many([
            {"panel_name": "Zenex", "base_url": "https://api.zenexnetwork.com", "api_key": "8953778024:AAGHEO5lQrcn9wFjzO-TISJLZltqwGGvS9s_fake", "is_active": True, "is_manual": False},
            {"panel_name": "SMSHadi", "base_url": "http://smshadi.net", "api_key": "Qk9PRUFBUzRzVo1pXGhYdH5nimJ3gmBIY42HhVeEdF5pkHZ3dY6MaA", "is_active": False, "is_manual": True}
        ])
    
    if not db.panels.find_one({"panel_name": "Stexsms"}):
        db.panels.insert_one({"panel_name": "Stexsms", "base_url": "https://stexsms.com", "api_key": "MZ6H5CL0O6K", "is_active": False, "is_manual": False})
        
    db.panels.update_many({"panel_name": "Zenex", "is_manual": {"$exists": False}}, {"$set": {"is_manual": False}})
    db.panels.update_many({"panel_name": "SMSHadi", "is_manual": {"$exists": False}}, {"$set": {"is_manual": True}})
    
    db.services.update_many({"panel_name": {"$exists": False}}, {"$set": {"panel_name": "Zenex"}})

init_db()

def get_config(key, default=None):
    row = db.config.find_one({"key": key})
    return row["value"] if row else default

def set_config(key, value):
    db.config.update_one({"key": key}, {"$set": {"value": str(value)}}, upsert=True)

def is_admin(user_id):
    return bool(db.admins.find_one({"user_id": str(user_id)}))

def is_primary_admin(user_id):
    row = db.admins.find_one({"user_id": str(user_id)})
    if row:
        if str(user_id) == str(PRIMARY_ADMIN_ID):
            return True
        if row.get('permissions'):
            try:
                perms = json.loads(row['permissions'])
                if "fullaccess" in perms: return True
            except: pass
    return False

def has_permission(user_id, perm):
    if is_primary_admin(user_id): return True
    row = db.admins.find_one({"user_id": str(user_id)})
    if row and row.get('permissions'):
        try:
            perms = json.loads(row['permissions'])
            return perm in perms
        except: return False
    return False

def register_user(user_id, username="User", referred_by=None):
    uid = str(user_id)
    current_time = time.time()
    row = db.users.find_one({"user_id": uid})
    
    if not row:
        db.users.insert_one({"user_id": uid, "username": username, "balance": 0.0, "completed_otps": 0, "banned": 0, "referred_by": referred_by, "last_active": current_time})
        
        if referred_by:
            try:
                import urllib.parse
                total_refs = db.users.count_documents({"referred_by": referred_by})
                ref_msg = (
                    f"🎉 *নতুন রেফারেল যুক্ত হয়েছে!* 🎉\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *ইউজার:* `{username}`\n"
                    f"📈 *আপনার মোট রেফার:* `{total_refs}` জন\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _আরও বেশি ইনভাইট করুন এবং আনলিমিটেড ইনকাম করুন!_"
                )
                
                ref_link = f"https://t.me/{BOT_USERNAME}?start={referred_by}"
                share_text = f"Get Free OTPs and Earn Money!\n\n{ref_link}"
                encoded_text = urllib.parse.quote(share_text)
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🚀 Share More & Earn", url=f"https://t.me/share/url?url={ref_link}&text={encoded_text}", style="primary"))
                
                bot.send_message(int(referred_by), ref_msg, reply_markup=markup, parse_mode="Markdown")
            except Exception as e:
                pass
                
        total_users = db.users.count_documents({})
        
        milestone_step = int(get_config("milestone_step", "100"))
        last_milestone = int(get_config("last_milestone", "0"))
        
        if total_users >= last_milestone + milestone_step:
            new_milestone = (total_users // milestone_step) * milestone_step
            set_config("last_milestone", str(new_milestone))
            try:
                msg = f"🎉 *MILESTONE REACHED!* 🎉\n━━━━━━━━━━━━━━━━━━━\nCongratulations! Your bot has successfully reached *{new_milestone}* users!\nKeep up the great work! 🚀"
                bot.send_message(PRIMARY_ADMIN_ID, msg)
            except: pass
    else:
        update_fields = {"last_active": current_time}
        if row.get('username') != username:
            update_fields["username"] = username
        db.users.update_one({"user_id": uid}, {"$set": update_fields})

def check_join(user_id):
    if is_admin(user_id): return True
    try:
        channel_1 = get_config("force_channel_1", FORCE_CHANNEL)
        chat_member_1 = bot.get_chat_member(channel_1, user_id)
        
        group_2_username = get_config("otp_group_username", FORCE_CHANNEL_2)
        chat_member_2 = bot.get_chat_member(group_2_username, user_id)
        
        valid_statuses = ['member', 'administrator', 'creator', 'restricted']
        if chat_member_1.status in valid_statuses and chat_member_2.status in valid_statuses:
            return True
        return False
    except Exception as e:
        logger.error(f"Force Join Check Error: {e}")
        print(f"Force Join Check Error for user {user_id}: {e}")
        # If the bot is not admin or fails to check, block the user.
        return False

def force_join_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    link_1 = get_config("force_link_1", FORCE_CHANNEL_LINK)
    otp_link = get_config("otp_group_link", FORCE_CHANNEL_LINK_2)
    
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=link_1, style="success"))
    markup.add(types.InlineKeyboardButton("📢 Join OTP Group", url=otp_link, style="success"))
        
    markup.add(types.InlineKeyboardButton("✅ Verify Access", callback_data="check_verified", style="success"))
    return markup


def cancel_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("? Cancel", callback_data="cancel_step", style="danger"))
    return markup

def reply_cancel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("? Cancel", style="danger"))
    return markup

def main_menu_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_number = types.KeyboardButton("🚀 Get Free Number", style="success")
    btn_balance = types.KeyboardButton("💳 My Wallet", style="primary")
    btn_refer = types.KeyboardButton("🎁 Refer & Earn", style="primary")
    btn_leaderboard = types.KeyboardButton("🏆 Leaderboard", style="primary")
    
    markup.add(btn_number)
    markup.add(btn_balance, btn_refer)
    markup.add(btn_leaderboard)
    
    if is_admin(user_id):
        btn_admin = types.KeyboardButton("👑 Admin Console", style="primary")
        markup.add(btn_admin)
        
    return markup

def service_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    services = db.services.distinct("service_name")
        
    for srv_name in services:
        icon = "📸" if "instagram" in srv_name.lower() else "📘" if "facebook" in srv_name.lower() else "💬"
        markup.add(types.InlineKeyboardButton(f"{icon} {srv_name} Premium", callback_data=f"srv_{srv_name}", style="danger"))
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
    return markup

def country_menu_keyboard(service_name):
    markup = types.InlineKeyboardMarkup(row_width=2)
    best_range = db.services.find_one({"service_name": service_name}, sort=[("hits", -1)])
    if best_range:
        markup.add(types.InlineKeyboardButton("🔥 Auto Best Route", callback_data=f"sel_{service_name}_AUTO-BEST", style="primary"))
        
    countries = list(db.services.find({"service_name": service_name}).sort([("hits", -1)]).limit(2))
    
    country_totals = {}
    for c in countries:
        c_part = c.get('country_name', '').split(" | ")[0]
        country_totals[c_part] = country_totals.get(c_part, 0) + 1
        
    country_seen = {}
    buttons = []
    for idx_c, c in enumerate(countries):
        raw_c_name = c.get('country_name', 'Unknown')
        parts = raw_c_name.split(" | ")
        c_part = parts[0]
        hits_part = parts[1] if len(parts) > 1 else ""
        
        display_name = c_part
        if country_totals.get(c_part, 0) > 1:
            country_seen[c_part] = country_seen.get(c_part, 0) + 1
            idx = country_seen[c_part]
            display_name = f"{c_part} {idx}"
            
        if idx_c == 0:
            display_name = f"👑 {display_name}"
            
        c_name = f"{display_name} | {hits_part}" if hits_part else display_name
        
        c_range = c.get('range', '')
        cb_data = f"sel_{service_name}_RNG_{c_range}"
        buttons.append(types.InlineKeyboardButton(c_name, callback_data=cb_data, style="danger"))
        
    for btn in buttons:
        markup.add(btn)
        
    markup.add(types.InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services", style="danger"))
    return markup

def admin_panel_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    if has_permission(user_id, "broadcast"):
        buttons.append(types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast", style="danger"))
    if has_permission(user_id, "userinfo"):
        buttons.append(types.InlineKeyboardButton("🔍 Scan Profile", callback_data="adm_userinfo", style="danger"))
    if has_permission(user_id, "ban"):
        buttons.append(types.InlineKeyboardButton("🔴 Ban Node", callback_data="adm_ban", style="danger"))
    if has_permission(user_id, "unban"):
        buttons.append(types.InlineKeyboardButton("🟢 Unban Node", callback_data="adm_unban", style="danger"))
    if has_permission(user_id, "reward"):
        buttons.append(types.InlineKeyboardButton("💰 Config Bounty", callback_data="adm_reward", style="danger"))
    if has_permission(user_id, "ranges"):
        buttons.append(types.InlineKeyboardButton("⚙️ Map Routes", callback_data="adm_ranges_menu", style="primary"))
        buttons.append(types.InlineKeyboardButton("❌ Remove Routes", callback_data="adm_remove_ranges_menu", style="danger"))
    if has_permission(user_id, "withdraw"):
        buttons.append(types.InlineKeyboardButton("💸 Withdraw Group", callback_data="adm_withdraw_group", style="primary"))
    
    buttons.append(types.InlineKeyboardButton("📦 Bulk Get Numbers", callback_data="adm_bulk_order", style="primary"))
    buttons.append(types.InlineKeyboardButton("📊 View Stats", callback_data="adm_stats", style="primary"))
    buttons.append(types.InlineKeyboardButton("⚠️ Stock Out Logs", callback_data="adm_stockouts", style="primary"))
    buttons.append(types.InlineKeyboardButton("📈 OTP Stats", callback_data="adm_otp_stats_today", style="primary"))
    
    markup.add(*buttons)
    if is_primary_admin(user_id):
        notif_status = get_config("admin_notifications", "1")
        notif_text = "🔔 Notifications: ON" if notif_status == "1" else "🔕 Notifications: OFF"
        markup.add(
            types.InlineKeyboardButton("🔑 Set API Key", callback_data="adm_api_key", style="primary"),
            types.InlineKeyboardButton("📢 Set Main Channel", callback_data="adm_main_channel", style="primary"),
            types.InlineKeyboardButton("💬 Set OTP Button Link", callback_data="adm_otp_link", style="primary"),
            types.InlineKeyboardButton("💬 Set OTP Forward Group", callback_data="adm_otp_group_id", style="primary"),
            types.InlineKeyboardButton("🎯 Edit Milestones", callback_data="adm_milestone", style="primary"),
            types.InlineKeyboardButton("👮‍♂️ Manage Team", callback_data="adm_manage_admins", style="primary"),
            types.InlineKeyboardButton("🎛 Manage Panels", callback_data="adm_panels_menu", style="primary"),
            types.InlineKeyboardButton(notif_text, callback_data="adm_toggle_notif", style="primary")
        )
    markup.add(
        types.InlineKeyboardButton("🚪 Leave Admin", callback_data="adm_resign", style="danger"),
        types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger")
    )
    return markup

def panels_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    panels = db.panels.find()
    for p in panels:
        status = "🟢" if p.get("is_active") else "🔴"
        markup.add(types.InlineKeyboardButton(f"{status} {p['panel_name']}", callback_data=f"pnl_toggle_{str(p['_id'])}", style="primary"))
    
    markup.add(types.InlineKeyboardButton("➕ Add New Panel", callback_data="adm_add_panel", style="success"))
    markup.add(types.InlineKeyboardButton("🗑 Delete a Panel", callback_data="adm_del_panel", style="danger"))
    markup.add(types.InlineKeyboardButton("🔙 Return to Home", callback_data="adm_back", style="primary"))
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
    return markup

def panels_del_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    panels = db.panels.find()
    for p in panels:
        markup.add(types.InlineKeyboardButton(f"🗑 {p['panel_name']}", callback_data=f"pnl_del_{str(p['_id'])}", style="danger"))
    
    markup.add(types.InlineKeyboardButton("🔙 Back to Panels", callback_data="adm_panels_menu", style="primary"))
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
    return markup

def admin_ranges_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    services = db.services.distinct("service_name")
    for srv_name in services:
        icon = "📸" if "instagram" in srv_name.lower() else "📘" if "facebook" in srv_name.lower() else "💬"
        markup.add(types.InlineKeyboardButton(f"{icon} Configure {srv_name} Arrays", callback_data=f"setrng_{srv_name}", style="danger"))
    markup.add(types.InlineKeyboardButton("➕ Add New Routing Service", callback_data="adm_add_service", style="danger"))
    markup.add(types.InlineKeyboardButton("🔙 Return to Home", callback_data="adm_back", style="primary"))
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
    return markup

def admin_remove_ranges_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    services = db.services.distinct("service_name")
    for srv_name in services:
        icon = "📸" if "instagram" in srv_name.lower() else "📘" if "facebook" in srv_name.lower() else "💬"
        markup.add(types.InlineKeyboardButton(f"{icon} Wipe {srv_name} Routes", callback_data=f"remrng_{srv_name}", style="danger"))
    markup.add(types.InlineKeyboardButton("🔙 Return to Home", callback_data="adm_back", style="primary"))
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
    return markup

def bulk_service_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    services = db.services.distinct("service_name")
        
    for srv_name in services:
        icon = "📸" if "instagram" in srv_name.lower() else "📘" if "facebook" in srv_name.lower() else "💬"
        markup.add(types.InlineKeyboardButton(f"{icon} {srv_name} Bulk", callback_data=f"bsrv_{srv_name}", style="danger"))
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
    return markup

def bulk_country_menu_keyboard(service_name):
    markup = types.InlineKeyboardMarkup(row_width=2)
    countries = db.services.find({"service_name": service_name})
        
    buttons = []
    for c in countries:
        c_name = c['country_name']
        buttons.append(types.InlineKeyboardButton(c_name, callback_data=f"bsel_{service_name}_{c_name}", style="danger"))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_bulk_services", style="danger"))
    return markup

def perms_keyboard(target_uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    row = db.admins.find_one({"user_id": str(target_uid)})
        
    perms = []
    if row and row['permissions']:
        try: perms = json.loads(row['permissions'])
        except: pass
        
    p_dict = {
        "broadcast": "Broadcast",
        "userinfo": "Scan Profile",
        "ban": "Ban User",
        "unban": "Unban User",
        "reward": "Config Bounty",
        "ranges": "Map/Rem Routes",
        "withdraw": "Withdrawals"
    }
    
    for key, label in p_dict.items():
        state = "✅" if key in perms else "❌"
        markup.add(types.InlineKeyboardButton(f"{state} {label}", callback_data=f"tglperm_{target_uid}_{key}", style="primary"))
        
    if "fullaccess" in perms:
        markup.add(types.InlineKeyboardButton("⏬ Make Secondary (Revoke Access)", callback_data=f"tglperm_{target_uid}_fullaccess", style="danger"))
    else:
        markup.add(types.InlineKeyboardButton("🌟 Make Primary (Full Access)", callback_data=f"tglperm_{target_uid}_fullaccess", style="success"))
        
    markup.add(types.InlineKeyboardButton("🔙 Back to Team", callback_data="adm_manage_admins", style="danger"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "cancel_step")
def handle_cancel_step(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

@bot.message_handler(commands=['admin'])
@bot.message_handler(func=lambda msg: msg.text == "👑 Admin Console")
def admin_panel(message):
    if not is_admin(message.from_user.id): return
    total_users = db.users.count_documents({})
    active_panels = list(db.panels.find({"is_active": True}))
    pnames = ", ".join([p["panel_name"] for p in active_panels]) if active_panels else "Zenex (Legacy)"
    msg = f"👑 *Main Control Console V8.0*\n\n_Manage networks, configurations, and user operations seamlessly._\n\n👥 *Total Users:* `{total_users}`\n⚡ *Active Panels:* `{pnames}`"
    bot.send_message(message.chat.id, msg, reply_markup=admin_panel_keyboard(message.from_user.id))
def show_otp_stats(chat_id, message_id=None, target_date=None):
    import datetime
    if not target_date or target_date == "today":
        target_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    pipeline = [
        {"$match": {"date": target_date}},
        {"$group": {"_id": "$panel", "count": {"$sum": 1}}}
    ]
    results = list(db.otps_history.aggregate(pipeline))
    
    total = sum([r['count'] for r in results])
    
    msg_text = f"📊 *OTP Stats for {target_date}*\n\n"
    if not results:
        msg_text += "No OTPs found for this date.\n"
    else:
        for r in results:
            pname = r['_id'] or "Unknown"
            msg_text += f"🔹 {pname}: {r['count']} OTPs\n"
    msg_text += f"\n*Total:* {total} OTPs"
    
    curr_dt = datetime.datetime.strptime(target_date, '%Y-%m-%d')
    prev_dt = (curr_dt - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    next_dt = (curr_dt + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("⬅️ Prev", callback_data=f"adm_otp_stats_{prev_dt}"),
        types.InlineKeyboardButton("🔄 Today", callback_data=f"adm_otp_stats_today"),
        types.InlineKeyboardButton("Next ➡️", callback_data=f"adm_otp_stats_{next_dt}")
    )
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step"))
    
    if message_id:
        try: bot.edit_message_text(msg_text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="Markdown")
        except: pass
    else:
        bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['otp_stats'])
def cmd_otp_stats(message):
    if not is_admin(message.from_user.id): return
    show_otp_stats(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("2fa_"))
def callback_2fa_handler(call):
    action = call.data
    chat_id = call.message.chat.id
    
    if action == "2fa_new":
        msg = bot.send_message(chat_id, "?? *2FA Code Generator*

Please send me your 2FA Key (Base32 format):", parse_mode="Markdown", reply_markup=reply_cancel_markup())
        bot.register_next_step_handler(msg, process_2fa_key)
        try: bot.answer_callback_query(call.id)
        except: pass
        
    elif action.startswith("2fa_refresh:"):
        key = action.split(":", 1)[1]
        try:
            import pyotp
            import time
            totp = pyotp.TOTP(key)
            code = totp.now()
            remaining = 30 - (int(time.time()) % 30)
            
            reply_text = f"?? *2FA Code Generator*

?? *Key:* {key}

?? *Code:* {code}
? *Expires in:* {remaining}s"
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_refresh = types.InlineKeyboardButton("?? Refresh Code", callback_data=f"2fa_refresh:{key}", style="success")
            btn_new = types.InlineKeyboardButton("? New", callback_data="2fa_new", style="primary")
            markup.add(btn_refresh, btn_new)
            
            if call.message.text and code in call.message.text and f"{remaining}s" in call.message.text:
                try: bot.answer_callback_query(call.id, f"Still valid for {remaining}s")
                except: pass
                return
                
            bot.edit_message_text(reply_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            try: bot.answer_callback_query(call.id, f"Refreshed! Code: {code}")
            except: pass
        except Exception as e:
            try: bot.answer_callback_query(call.id, "Error generating code!", show_alert=True)
            except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith(("adm_", "setrng_", "remrng_", "tglperm_", "pnl_", "up_srv_")))
def handle_admin_callbacks(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    user_id = call.from_user.id
    if not is_admin(user_id): return
    action = call.data
    chat_id = call.message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id)
    
    if action == "adm_scan_ranges":
        bot.send_message(chat_id, "🔍 Scanning Stexsms Console for active Facebook and Instagram ranges...")
        stex_panel = db.panels.find_one({"base_url": {"$regex": "@public"}}) or db.panels.find_one({"panel_name": {"$regex": "Stexsms", "$options": "i"}})
        if not stex_panel:
            bot.send_message(chat_id, "❌ No Stexsms panel found in config.")
            return
        
        base = stex_panel['base_url'].rstrip('/')
        if "@public/api" in base:
            # Some panels use /@public/api, some use standard
            base_v1 = base.replace("@public/api", "api") 
        else:
            base_v1 = base
            
        api_key = stex_panel['api_key']
        headers = {'mauthapi': api_key, 'mapikey': api_key}
        try:
            # Try Zenex-style active-ranges first
            res = http_session.get(base_v1 + '/v1/active-ranges', headers=headers, timeout=10).json()
            if not res or "data" not in res or not res.get("data", {}).get("active_ranges"):
                # Fallback to liveaccess
                res = http_session.get(base + '/liveaccess', headers=headers, timeout=10).json()
                
            active_ranges = res.get("data", {}).get("active_ranges") or res.get("data", {}).get("services", [])
            
            # If both fail, try console (old method)
            if not active_ranges:
                res = http_session.get(base + '/console', headers=headers, timeout=10).json()
                otps = res.get("data", {}).get("otps", [])
                active_ranges = []
                for otp in otps:
                    active_ranges.append({
                        "service": "Facebook" if "facebook" in str(otp.get("sid", "")).lower() else "Instagram" if "instagram" in str(otp.get("sid", "")).lower() else "",
                        "range": otp.get("range", ""),
                        "hits": 1 # Fake hit for console fallback
                    })

            added_count = 0
            for route in active_ranges:
                service_name = str(route.get("service", ""))
                if not service_name:
                    sid = str(route.get("sid", "")).lower()
                    if "facebook" in sid: service_name = "Facebook"
                    elif "instagram" in sid: service_name = "Instagram"
                    
                target_range = str(route.get("range", ""))
                hits = route.get("hits", route.get("success", route.get("count", 0)))
                
                if not service_name or not target_range: continue
                
                c_name = f"🔥 hits {hits}" if hits else f"Auto: {target_range}"
                
                # Update if exists, otherwise insert
                result = db.services.update_one(
                    {"service_name": service_name, "range": target_range},
                    {"$set": {"country_name": c_name, "panel_name": stex_panel['panel_name']}}
                )
                if result.matched_count == 0:
                    db.services.insert_one({
                        "service_name": service_name,
                        "country_name": c_name,
                        "range": target_range,
                        "panel_name": stex_panel['panel_name']
                    })
                    added_count += 1
                    
            bot.send_message(chat_id, f"✅ Stexsms Scan Complete! Updated hits & added {added_count} new ranges.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Scan failed: {e}")
    elif action == "adm_scan_zenex":
        bot.send_message(chat_id, "🔍 Scanning Zenex Live Routes for active ranges...")
        zenex_panel = db.panels.find_one({"panel_name": "Zenex"})
        if not zenex_panel:
            bot.send_message(chat_id, "❌ No Zenex panel found in config.")
            return
            
        base = zenex_panel['base_url'].rstrip('/')
        api_key = zenex_panel['api_key']
        headers = {'mapikey': api_key}
        try:
            res = http_session.get(base + '/v1/active-ranges', headers=headers, timeout=10).json()
            active_ranges = res.get("data", {}).get("active_ranges", [])
            added_count = 0
            for route in active_ranges:
                service_name = str(route.get("service", ""))
                target_range = str(route.get("range", ""))
                hits = route.get("hits", 0)
                if not service_name or not target_range: continue
                
                # Show the hits count right in the button name!
                c_name = f"🔥 hits {hits}"
                
                # Update if exists, otherwise insert
                result = db.services.update_one(
                    {"service_name": service_name, "range": target_range},
                    {"$set": {
                        "country_name": c_name,
                        "panel_name": zenex_panel['panel_name']
                    }},
                    upsert=True
                )
                if result.upserted_id:
                    added_count += 1
            bot.send_message(chat_id, f"✅ Zenex Scan Complete! Automatically updated hit counts & added {added_count} new high-hit routes.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Zenex Scan failed: {e}")

    elif action == "adm_close":
        bot.delete_message(chat_id, call.message.message_id)
        
    elif action == "adm_bulk_order":
        bot.edit_message_text("⚡ *Select Target Protocol for Bulk Order:*", chat_id, call.message.message_id, reply_markup=bulk_service_menu_keyboard())

    elif action == "adm_back":
        total_users = db.users.count_documents({})
        active_panels = list(db.panels.find({"is_active": True}))
        pnames = ", ".join([p["panel_name"] for p in active_panels]) if active_panels else "Zenex (Legacy)"
        msg = f"👑 *Main Control Console V8.0*\n\n_Manage networks, configurations, and user operations seamlessly._\n\n👥 *Total Users:* `{total_users}`\n⚡ *Active Panels:* `{pnames}`"
        bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=admin_panel_keyboard(user_id))
        
    elif action == "adm_add_panel":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "❌ Access Denied", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔥 Stexsms", callback_data="add_pnl_stexsms"),
            types.InlineKeyboardButton("🔥 Zenex", callback_data="add_pnl_zenex")
        )
        markup.add(types.InlineKeyboardButton("⚙️ Custom Panel", callback_data="add_pnl_custom"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_panels_menu"))
        bot.edit_message_text("⚙️ *Select Panel Type to Setup:*", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif action.startswith("add_pnl_"):
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "❌ Access Denied", show_alert=True)
        p_type = action.split("add_pnl_")[1]
        
        if p_type == "custom":
            msg = bot.send_message(chat_id, "⚙️ *Enter Custom Panel Details:*\n\nFormat:\n`PanelName|BaseURL|APIKey`\n\n_(Example: `SMSHadi|http://smshadi.net|XYZ123`)_", reply_markup=cancel_markup(), parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_add_panel)
        else:
            name = p_type.capitalize()
            msg = bot.send_message(chat_id, f"🔑 *Enter API Key for {name}:*\n\nJust send the API Key, no link needed!", reply_markup=cancel_markup(), parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_quick_setup, p_type)

    elif action == "adm_upload_txt":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        services = list(db.services.find())
        markup = types.InlineKeyboardMarkup(row_width=2)
        for srv in services:
            markup.add(types.InlineKeyboardButton(f"{srv['service_name']} ({srv['country_name']})", callback_data=f"up_srv_{str(srv['_id'])}", style="primary"))
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="adm_close", style="danger"))
        bot.send_message(chat_id, "📁 *Select Service to Upload Numbers:*", reply_markup=markup, parse_mode="Markdown")
        
    elif action.startswith("up_srv_"):
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        srv_id = action.split("up_srv_")[1]
        from bson.objectid import ObjectId
        srv = db.services.find_one({"_id": ObjectId(srv_id)})
        msg = bot.send_message(chat_id, f"📎 *Please upload the .txt file for {srv['service_name']} ({srv['country_name']})*\n\n_Note: 1 number per line._", reply_markup=cancel_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_txt_upload, srv_id)

    elif action == "adm_panels_menu":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        bot.edit_message_text("🎛 *PANEL MANAGEMENT SYSTEM*\n\n_Select a panel to activate it, or add/delete panels:_", chat_id, call.message.message_id, reply_markup=panels_menu_keyboard())

    elif action == "adm_add_panel":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "📝 *Enter New Panel Details:*\n\nFormat:\n`PanelName|BaseURL|APIKey`\n\n_(Example: `SMSHadi|http://smshadi.net|XYZ123`)_", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_add_panel)

    elif action == "adm_del_panel":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        bot.edit_message_text("🗑 *DELETE PANEL*\n\n_Select a panel to delete (Active panel cannot be deleted):_", chat_id, call.message.message_id, reply_markup=panels_del_keyboard())

    elif action.startswith("pnl_toggle_"):
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        from bson.objectid import ObjectId
        p_id = action.split("pnl_toggle_")[1]
        panel = db.panels.find_one({"_id": ObjectId(p_id)})
        new_status = not panel.get("is_active", False)
        
        if new_status:
            db.panels.update_many({"_id": {"$ne": ObjectId(p_id)}}, {"$set": {"is_active": False}})
            db.panels.update_one({"_id": ObjectId(p_id)}, {"$set": {"is_active": True}})
            db.services.delete_many({}) 
            
            panel_name = panel.get("panel_name", "")
            base = panel.get("base_url", "").rstrip('/')
            api_key = panel.get("api_key", "")
            bot.answer_callback_query(call.id, f"Scanning {panel_name} routes in real-time...", show_alert=False)
            
            count = 0
            try:
                if panel_name.lower() == "zenex":
                    try:
                        res = http_session.get(base + '/v1/active-ranges', headers={'mapikey': api_key}, timeout=10).json()
                        routes = res.get("data", {}).get("active_ranges", [])
                    except: routes = []
                elif panel_name.lower() == "stexsms":
                    base_v1 = base.replace("@public/api", "api") if "@public/api" in base else base
                    headers = {'mauthapi': api_key}
                    try: res = http_session.get(base_v1 + '/v1/active-ranges', headers=headers, timeout=10).json()
                    except: res = None
                    if not res or "data" not in res or not res.get("data", {}).get("active_ranges"):
                        try: res = http_session.get(base + '/liveaccess', headers=headers, timeout=10).json()
                        except: res = None
                    
                    routes = res.get("data", {}).get("active_ranges") if res else []
                        
                    if not routes:
                        try: 
                            res = http_session.get(base + '/console', headers=headers, timeout=10).json()
                            otps = res.get("data", {}).get("hits") or res.get("data", {}).get("otps", [])
                        except: otps = []
                        routes = []
                        range_counts = {}
                        service_map = {}
                        current_time_ms = time.time() * 1000
                        for otp in otps:
                            if current_time_ms - int(otp.get("time", 0)) > 300000: continue
                            sid = str(otp.get("sid", "")).lower()
                            msg = str(otp.get("message", "")).lower()
                            if "facebook" in sid:
                                s_name = "Instagram" if "instagram" in msg else "Facebook"
                            elif "instagram" in sid: s_name = "Instagram"
                            else: continue
                            tr = str(otp.get("range", ""))
                            if not tr: continue
                            range_counts[tr] = range_counts.get(tr, 0) + 1
                            service_map[tr] = s_name
                        for tr, hits in range_counts.items():
                            routes.append({"service": service_map[tr], "range": tr, "hits": hits})
                else:
                    routes = []
                
                for route in routes:
                    s_name = str(route.get("service", ""))
                    t_range = str(route.get("range", ""))
                    hits = int(route.get("hits", 0))
                    if not s_name or not t_range: continue
                    clean_range = t_range.replace("X", "0").replace("x", "0")
                    try:
                        from panel import get_country_info
                        name, flag, _ = get_country_info("+" + clean_range + "0000000")
                        short_name = name.split()[0][:8] if name else "Unknown"
                        c_name = f"{flag} {short_name} | 🔥 hits {hits}"
                    except:
                        c_name = f"🔥 hits {hits}"
                    db.services.update_one(
                        {"service_name": s_name, "range": t_range},
                        {"$set": {"country_name": c_name, "panel_name": panel_name, "hits": hits}},
                        upsert=True
                    )
                    count += 1
                bot.send_message(chat_id, f"✅ *Successfully connected to {panel_name} and loaded {count} real-time active services!*", parse_mode="Markdown")
            except Exception as e:
                bot.send_message(chat_id, f"❌ *Error scanning {panel_name}:* {e}", parse_mode="Markdown")
        else:
            db.panels.update_one({"_id": ObjectId(p_id)}, {"$set": {"is_active": False}})
            db.services.delete_many({"panel_name": panel.get("panel_name")})
            bot.answer_callback_query(call.id, f"❌ {panel.get('panel_name')} deactivated and routes cleared.", show_alert=True)
            
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=panels_menu_keyboard())

    elif action.startswith("pnl_del_"):
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        from bson.objectid import ObjectId
        p_id = action.split("pnl_del_")[1]
        panel_to_del = db.panels.find_one({"_id": ObjectId(p_id)})
        if panel_to_del and panel_to_del.get("is_active"):
            bot.answer_callback_query(call.id, "🔴 Cannot delete an active panel!", show_alert=True)
        else:
            db.panels.delete_one({"_id": ObjectId(p_id)})
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=panels_del_keyboard())

    elif action.startswith("adm_otp_stats_"):
        target_date = action.replace("adm_otp_stats_", "")
        show_otp_stats(chat_id, call.message.message_id, target_date)

    elif action == "adm_stats":
        today_date = time.strftime('%Y-%m-%d')
        today_otps = db.otps_history.count_documents({"date": today_date})
        total_otps = db.otps_history.count_documents({})
        
        one_min_ago = time.time() - 60
        active_users = db.users.count_documents({"last_active": {"$gte": one_min_ago}})
        
        pipeline = [{"$group": {"_id": "$panel", "count": {"$sum": 1}}}]
        panel_counts = list(db.otps_history.aggregate(pipeline))
        panel_breakdown = "📦 *Panel Breakdown:*\n"
        if not panel_counts:
            panel_breakdown += "- No OTPs yet\n"
        for p in panel_counts:
            p_name = p['_id'] if p.get('_id') else "Legacy"
            panel_breakdown += f"- {p_name}: `{p['count']}`\n"
            
        msg = (
            "📊 *System Statistics:*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 *Active Users (1m):* `{active_users}` Nodes\n"
            f"📅 *Today's Total OTPs:* `{today_otps}`\n"
            f"📈 *All-Time Total OTPs:* `{total_otps}`\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"{panel_breakdown}"
            "━━━━━━━━━━━━━━━━━━━\n"
            "To check a custom date, send the date in `YYYY-MM-DD` format below:\n"
            ""
        )
        msg_obj = bot.send_message(chat_id, msg)
        bot.register_next_step_handler(msg_obj, process_custom_date_stats)
        
    elif action == "adm_toggle_notif":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        current = get_config("admin_notifications", "1")
        new_val = "0" if current == "1" else "1"
        set_config("admin_notifications", new_val)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=admin_panel_keyboard(user_id))
        
    elif action == "adm_stockouts":
        recent_logs = list(db.stock_outs.find().sort("timestamp", -1).limit(10))
        if not recent_logs:
            bot.answer_callback_query(call.id, "✅ No stock outs logged yet.", show_alert=True)
            return
            
        log_msg = "⚠️ *RECENT STOCK OUT LOGS (Last 10)*\n━━━━━━━━━━━━━━━━━━━\n"
        for log in recent_logs:
            dt = time.strftime('%H:%M:%S', time.localtime(log['timestamp']))
            log_msg += f"🕒 `{dt}` | ID: `{log['user_id']}`\n🌍 {log['country']} | ⚡ {log['service']}\n\n"
        log_msg += "━━━━━━━━━━━━━━━━━━━"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_back", style="danger"))
        bot.edit_message_text(log_msg, chat_id, call.message.message_id, reply_markup=markup)
        
    elif action == "adm_ranges_menu":
        if not has_permission(user_id, "ranges"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        status_text = "⚙️ *SYSTEM ROUTING POOL:*\n\n"
        rows = db.services.find().sort("service_name", 1)
            
        current_srv = ""
        for r in rows:
            if r['service_name'] != current_srv:
                current_srv = r['service_name']
                status_text += f"▪️ *{current_srv}:*\n"
            status_text += f"   ➔ {r['country_name']}: `{r['range']}` ({r.get('panel_name', 'Zenex')})\n"
            
        status_text += "\nSelect target service to update/add country range:"
        bot.edit_message_text(status_text, chat_id, call.message.message_id, reply_markup=admin_ranges_keyboard())
        
    elif action == "adm_remove_ranges_menu":
        if not has_permission(user_id, "ranges"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        status_text = "❌ *REMOVE COUNTRY MANAGEMENT:*\n\nSelect target service node:"
        bot.edit_message_text(status_text, chat_id, call.message.message_id, reply_markup=admin_remove_ranges_keyboard())
        
    elif action == "adm_add_service":
        if not has_permission(user_id, "ranges"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "📝 *Enter New Service Name (e.g., Twitter):*")
        bot.register_next_step_handler(msg, process_add_service)
        
    elif action.startswith("setrng_"):
        if not has_permission(user_id, "ranges"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        service = action.split("_")[1]
        msg = bot.send_message(chat_id, f"⚙️ *Type the API Panel Name for {service} (e.g., Zenex or Stexsms):*")
        bot.register_next_step_handler(msg, process_add_service_panel, service)

    elif action.startswith("remrng_"):
        if not has_permission(user_id, "ranges"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        service = action.split("_")[1]
        msg = bot.send_message(chat_id, f"🗑️ *Enter EXACT Country Name with Flag to REMOVE from {service}*:")
        bot.register_next_step_handler(msg, process_remove_range, service)

    elif action == "adm_broadcast":
        if not has_permission(user_id, "broadcast"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "📢 *Enter Broadcast Transmission Message:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_broadcast)
        
    elif action == "adm_userinfo":
        if not has_permission(user_id, "userinfo"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "🔍 *Enter Target User ID:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_user_info)
        
    elif action == "adm_ban":
        if not has_permission(user_id, "ban"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "🔴 *Enter Target ID to Ban:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_ban_user)
        
    elif action == "adm_unban":
        if not has_permission(user_id, "unban"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "🟢 *Enter Target ID to Unban:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_unban_user)
        
    elif action == "adm_reward":
        if not has_permission(user_id, "reward"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "💰 *Enter New Reward Amount (e.g., 0.0002):*")
        bot.register_next_step_handler(msg, process_change_reward)
        
    elif action == "adm_withdraw_group":
        if not has_permission(user_id, "withdraw"): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "💸 *Enter Withdrawal Group ID:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_withdraw_group)

    elif action == "adm_api_key":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        panels = [p["panel_name"] for p in db.panels.find()]
        pnl_str = ", ".join(panels)
        msg = bot.send_message(chat_id, f"⚙️ *Which panel's API do you want to update?*\nAvailable: `{pnl_str}`\n\n_Type the panel name:_")
        bot.register_next_step_handler(msg, process_select_api_panel)
        
    elif action == "adm_main_channel":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "📢 *Enter New Main Channel URL (for users to click):*")
        bot.register_next_step_handler(msg, process_change_main_channel)
        
    elif action == "adm_otp_link":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "🔗 *Enter New OTP Group URL (for users to click):*")
        bot.register_next_step_handler(msg, process_change_otp_link)
        
    elif action == "adm_otp_group_id":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "💬 *Enter New OTP Forward Group ID (where OTPs are forwarded):*")
        bot.register_next_step_handler(msg, process_change_otp_group_id)
        
    elif action == "adm_milestone":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "🎯 *Enter New Milestone Step (e.g., 100):*")
        bot.register_next_step_handler(msg, process_change_milestone)
        
    elif action == "adm_manage_admins":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        
        admin_rows = db.admins.find()
            
        admin_list_text = "👮‍♂️ *Current Admin Team:*\n━━━━━━━━━━━━━━━━━━━\n"
        for idx, row in enumerate(admin_rows):
            uid = row['user_id']
            user = db.users.find_one({"user_id": uid}) or db.users.find_one({"user_id": str(uid)}) or db.users.find_one({"user_id": int(uid) if uid.isdigit() else uid})
            username_display = f"@{user['username']}" if user and user.get('username') else f"`{uid}`"
            
            if is_primary_admin(uid):
                admin_list_text += f"▪️ {username_display} 👑 (Primary)\n"
            else:
                admin_list_text += f"▪️ {username_display} 🛡️ (Secondary)\n"
        admin_list_text += "━━━━━━━━━━━━━━━━━━━\n_Use the buttons below to manage your team._"
                
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Add Admin", callback_data="adm_add_admin", style="primary"),
            types.InlineKeyboardButton("➖ Remove Admin", callback_data="adm_rem_admin", style="danger")
        )
        markup.add(types.InlineKeyboardButton("⚙️ Manage Permissions", callback_data="adm_manage_perms", style="primary"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="adm_back", style="danger"))
        bot.edit_message_text(admin_list_text, chat_id, call.message.message_id, reply_markup=markup)

    elif action == "adm_add_admin":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "➕ *Enter User ID to make Admin:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_add_admin)

    elif action == "adm_rem_admin":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "➖ *Enter User ID to remove Admin:*", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, process_rem_admin)

    elif action == "adm_manage_perms":
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        msg = bot.send_message(chat_id, "⚙️ *Enter Target Admin User ID to edit permissions:*")
        bot.register_next_step_handler(msg, process_ask_perm_uid)

    elif action == "adm_resign":
        if is_primary_admin(user_id):
            primary_count = sum(1 for adm in db.admins.find() if '"fullaccess"' in adm.get('permissions', ''))
            if primary_count <= 1:
                secondaries = [adm for adm in db.admins.find() if '"fullaccess"' not in adm.get('permissions', '')]
                if not secondaries:
                    bot.answer_callback_query(call.id, "🔴 You are the only admin left. Please add another admin first.", show_alert=True)
                    return
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                for sec in secondaries:
                    sec_uid = sec['user_id']
                    user = db.users.find_one({"user_id": sec_uid}) or db.users.find_one({"user_id": str(sec_uid)}) or db.users.find_one({"user_id": int(sec_uid) if sec_uid.isdigit() else sec_uid})
                    uname = f"@{user['username']}" if user and user.get('username') else str(sec_uid)
                    markup.add(types.InlineKeyboardButton(f"Promote {uname}", callback_data=f"adm_pass_prim_{sec_uid}", style="primary"))
                markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_step", style="danger"))
                bot.edit_message_text("⚠️ *আপনাকে লিভ নেওয়ার আগে অন্য কাউকে প্রাইমারি অ্যাডমিন বানাতে হবে।*\nনিচের লিস্ট থেকে একজনকে সিলেক্ট করুন:", chat_id, call.message.message_id, reply_markup=markup)
                return
                
        db.admins.delete_one({"user_id": str(user_id)})
        bot.answer_callback_query(call.id, "✅ You have successfully resigned as admin.", show_alert=True)
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        bot.send_message(chat_id, "✅ You are no longer an admin.")
        
        for adm in db.admins.find():
            if '"fullaccess"' in adm.get('permissions', ''):
                try: bot.send_message(int(adm['user_id']), f"ℹ️ Admin `{user_id}` has resigned.")
                except: pass
                
    elif action.startswith("adm_pass_prim_"):
        if not is_primary_admin(user_id): return
        target_uid = action.split("_")[3]
        
        perms = ["fullaccess", "broadcast", "userinfo", "ban", "unban", "reward", "ranges", "withdraw"]
        db.admins.update_one({"user_id": str(target_uid)}, {"$set": {"permissions": json.dumps(perms)}})
        db.admins.delete_one({"user_id": str(user_id)})
        
        bot.answer_callback_query(call.id, "✅ You have resigned and transferred primary access.", show_alert=True)
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        bot.send_message(chat_id, f"✅ You are no longer an admin. Primary transferred to `{target_uid}`.")
        
        try: bot.send_message(int(target_uid), "🎉 You have been promoted to Primary Admin!")
        except: pass
        for adm in db.admins.find():
            if '"fullaccess"' in adm.get('permissions', ''):
                try: bot.send_message(int(adm['user_id']), f"ℹ️ Admin `{user_id}` resigned and transferred Primary to `{target_uid}`.")
                except: pass
        
    elif action.startswith("tglperm_"):
        if not is_primary_admin(user_id): return bot.answer_callback_query(call.id, "🔴 Access Denied", show_alert=True)
        parts = action.split("_")
        target_uid = parts[1]
        perm_key = parts[2]
        
        row = db.admins.find_one({"user_id": target_uid})
        if not row:
            bot.answer_callback_query(call.id, "🔴 Admin not found.", show_alert=True)
            return
            
        perms = []
        if row.get('permissions'):
            try: perms = json.loads(row['permissions'])
            except: pass
            
        if perm_key == "fullaccess":
            if "fullaccess" in perms:
                if str(target_uid) == str(PRIMARY_ADMIN_ID):
                    bot.answer_callback_query(call.id, "🔴 Cannot revoke primary access from founder.", show_alert=True)
                    return
                perms = []
            else:
                perms = ["fullaccess", "broadcast", "userinfo", "ban", "unban", "reward", "ranges", "withdraw"]
        else:
            if perm_key in perms:
                perms.remove(perm_key)
            else:
                perms.append(perm_key)
                
        db.admins.update_one({"user_id": target_uid}, {"$set": {"permissions": json.dumps(perms)}})
            
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=perms_keyboard(target_uid))

def process_quick_setup(message, p_type):
    if message.text == "/cancel": return
    key = message.text.strip()
    
    if "|" in key:
        bot.send_message(message.chat.id, "❌ Just send the API key, do not use `|` format here!")
        return
        
    if p_type == "stexsms":
        url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
        name = "Stexsms"
    elif p_type == "zenex":
        url = "https://api.zenexnetwork.com"
        name = "Zenex"
    else: return
    
    try:
        existing = db.panels.find_one({"panel_name": {"$regex": name, "$options": "i"}})
        if existing:
            db.panels.update_one({"_id": existing["_id"]}, {"$set": {"api_key": key, "base_url": url}})
        else:
            db.panels.insert_one({"panel_name": name, "base_url": url, "api_key": key, "is_active": False})
            
        bot.send_message(message.chat.id, f"✅ *{name} API Key Setup Successfully!*\n\nGo to Manage Panels to activate it if it is a new panel, or background scanner will use it automatically.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

def process_add_panel(message):
    if message.text == "/cancel": return
    try:
        parts = message.text.split("|")
        name = parts[0].strip()
        
        if len(parts) == 2 and name.lower() == "stexsms":
            url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
            key = parts[1].strip()
        elif len(parts) == 3:
            url = parts[1].strip().rstrip("/")
            key = parts[2].strip()
            if name.lower() == "stexsms":
                url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
        else:
            bot.send_message(message.chat.id, "❌ Invalid format.\nUse: `PanelName|BaseURL|APIKey`\nFor Stexsms, you can just use: `Stexsms|Your_API_Key`", parse_mode="Markdown")
            return
        
        # Check if Stexsms already exists to avoid duplicates
        if name.lower() == "stexsms":
            existing = db.panels.find_one({"panel_name": {"$regex": "Stexsms", "$options": "i"}})
            if existing:
                db.panels.update_one({"_id": existing["_id"]}, {"$set": {"api_key": key, "base_url": url}})
                bot.send_message(message.chat.id, f"✅ *Stexsms API Key Updated Successfully!*\n\nURL: `{url}`\n\nNo need to activate it manually, background scanner will use it.", parse_mode="Markdown")
                return

        db.panels.insert_one({
            "panel_name": name,
            "base_url": url,
            "api_key": key,
            "is_active": False
        })
        bot.send_message(message.chat.id, f"✅ *Panel Added Successfully!*\n\nName: `{name}`\nURL: `{url}`\n\nGo to Manage Panels to activate it.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")


def process_txt_upload(message, srv_id):
    if message.text == "/cancel": return
    if not message.document:
        bot.send_message(message.chat.id, "❌ No document found. Please upload a .txt file.")
        return
    if not message.document.file_name.endswith(".txt"):
        bot.send_message(message.chat.id, "❌ File must be a .txt file.")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8').splitlines()
        
        from bson.objectid import ObjectId
        srv = db.services.find_one({"_id": ObjectId(srv_id)})
        active_panel = get_active_panel()
        
        numbers_to_insert = []
        for line in content:
            num = line.strip()
            if num:
                numbers_to_insert.append({
                    "panel_id": active_panel.get("_id", "default"),
                    "service_name": srv["service_name"],
                    "country_name": srv["country_name"],
                    "number": num,
                    "status": "available",
                    "added_at": time.time()
                })
        
        if numbers_to_insert:
            db.manual_numbers.insert_many(numbers_to_insert)
            bot.send_message(message.chat.id, f"✅ Successfully added {len(numbers_to_insert)} numbers for {srv['service_name']}!")
        else:
            bot.send_message(message.chat.id, "❌ No valid numbers found in file.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error processing file: {e}")

def process_custom_date_stats(message):
    if message.text == "/cancel": return
    target_date = message.text.strip()
    if len(target_date) != 10 or target_date.count("-") != 2:
        bot.send_message(message.chat.id, "❌ Invalid format. Use YYYY-MM-DD.")
        return
        
    count = db.otps_history.count_documents({"date": target_date})
    pipeline = [
        {"$match": {"date": target_date}},
        {"$group": {"_id": "$panel", "count": {"$sum": 1}}}
    ]
    panel_counts = list(db.otps_history.aggregate(pipeline))
    panel_breakdown = "\n📦 *Panel Breakdown:*\n"
    for p in panel_counts:
        p_name = p['_id'] if p.get('_id') else "Legacy"
        panel_breakdown += f"- {p_name}: `{p['count']}`\n"
        
    bot.send_message(message.chat.id, f"📅 *Stats for {target_date}:*\nTotal OTPs received: `{count}`{panel_breakdown}")

def process_ask_perm_uid(message):
    uid = message.text.strip()
    row = db.admins.find_one({"user_id": uid})
    if not row:
        bot.send_message(message.chat.id, "❌ Not found in admins table.")
        return
    bot.send_message(message.chat.id, f"⚙️ *Permissions for Node `{uid}`:*", reply_markup=perms_keyboard(uid))

def process_add_admin(message):
    try:
        uid = str(int(message.text.strip()))
        if not db.admins.find_one({"user_id": uid}):
            db.admins.insert_one({"user_id": uid, "permissions": "[]"})
        bot.send_message(message.chat.id, f"✅ User `{uid}` is now a secondary admin with NO permissions. Please assign permissions from Manage Permissions menu.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID format.")

def process_rem_admin(message):
    try:
        uid = str(int(message.text.strip()))
        db.admins.delete_one({"user_id": uid})
        bot.send_message(message.chat.id, f"✅ User `{uid}` removed from admins.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID format.")

def process_select_api_panel(message):
    panel_name = message.text.strip()
    panel = db.panels.find_one({"panel_name": {"$regex": f"^{panel_name}$", "$options": "i"}})
    if not panel:
        bot.send_message(message.chat.id, "❌ Invalid Panel Name.")
        return
        
    if panel['panel_name'].lower() == "stexsms":
        msg = bot.send_message(message.chat.id, f"🔑 *Enter New API Key for {panel['panel_name']}:*\nJust send the API Key, no link needed!", reply_markup=cancel_markup(), parse_mode="Markdown")
    else:
        msg = bot.send_message(message.chat.id, f"🔑 *Enter New Base URL and API Key for {panel['panel_name']}:*\nFormat: `BaseURL|APIKey`\n_(Example: https://stexsms.com|XYZ123)_", reply_markup=cancel_markup(), parse_mode="Markdown")
        
    bot.register_next_step_handler(msg, process_change_api_v2, panel['panel_name'])

def process_change_api_v2(message, panel_name):
    if message.text == "❌ Cancel": return
    try:
        input_text = message.text.strip()
        if panel_name.lower() == "stexsms" and "|" not in input_text:
            base_url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
            new_api = input_text
        elif panel_name.lower() == "zenex" and "|" not in input_text:
            base_url = "https://api.zenexnetwork.com"
            new_api = input_text
        else:
            parts = input_text.split("|")
            base_url = parts[0].strip()
            new_api = parts[1].strip()
            
        db.panels.update_one({"panel_name": panel_name}, {"$set": {"base_url": base_url, "api_key": new_api}})
        bot.send_message(message.chat.id, f"✅ API URL & Key for {panel_name} Updated Successfully!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Format Error. Use BaseURL|APIKey")

def process_change_main_channel(message):
    new_link = message.text.strip()
    set_config("force_link_1", new_link)
    
    if "t.me/" in new_link:
        username = "@" + new_link.split("t.me/")[-1].split("/")[0].split("?")[0]
        set_config("force_channel_1", username)
        
    bot.send_message(message.chat.id, "✅ Main Channel URL Updated Successfully!")

def process_change_otp_link(message):
    new_link = message.text.strip()
    set_config("otp_group_link", new_link)
    
    if "t.me/" in new_link:
        username = "@" + new_link.split("t.me/")[-1].split("/")[0].split("?")[0]
        set_config("otp_group_username", username)
        
    bot.send_message(message.chat.id, "✅ OTP Group URL Updated Successfully!")

def process_change_otp_group_id(message):
    try:
        g_id = message.text.strip()
        int(g_id)
        set_config("otp_group_id", g_id)
        bot.send_message(message.chat.id, f"✅ OTP Forward Group Updated: `{g_id}`")
    except:
        bot.send_message(message.chat.id, "❌ Invalid Group ID. Must be an integer.")

def process_change_milestone(message):
    try:
        step = int(message.text.strip())
        set_config("milestone_step", step)
        bot.send_message(message.chat.id, f"✅ User Milestone Notification set to every `{step}` users.")
    except:
        bot.send_message(message.chat.id, "❌ Must be an integer.")

def process_add_service(message):
    srv = message.text.strip()
    msg = bot.send_message(message.chat.id, f"⚙️ *Type the API Panel Name for {srv} (e.g., Zenex or Stexsms):*")
    bot.register_next_step_handler(msg, process_add_service_panel, srv)

def process_add_service_panel(message, service):
    panel_name = message.text.strip()
    if not db.panels.find_one({"panel_name": {"$regex": f"^{panel_name}$", "$options": "i"}}):
        bot.send_message(message.chat.id, "❌ Invalid Panel Name. Action Cancelled.")
        return
    msg = bot.send_message(message.chat.id, f"📝 *Enter Country Name with Flag & Range for {service} (Panel: {panel_name})*:\nFormat: `Flag CountryName|Range`\n_(Example: 🇺🇸 United States|1XXXXXXXXXX)_")
    bot.register_next_step_handler(msg, process_change_range, service, panel_name)

def process_withdraw_group(message):
    try:
        g_id = message.text.strip()
        set_config("withdraw_group_id", g_id)
        bot.send_message(message.chat.id, f"✅ Withdrawal Group Updated: `{g_id}`")
    except:
        bot.send_message(message.chat.id, "❌ Invalid Group ID.")

def process_change_range(message, service, panel_name):
    try:
        data = message.text.strip().split("|")
        country = data[0].strip()
        rng = data[1].strip()
        
        db.services.update_one(
            {"service_name": service, "country_name": country},
            {"$set": {"range": rng, "panel_name": panel_name}},
            upsert=True
        )
            
        bot.send_message(message.chat.id, f"✅ *Routing Matrix Registered!*\nService: `{service}`\nCountry: `{country}`\nRange: `{rng}`\nPanel: `{panel_name}`")
        
        reward_amt = get_config("reward_amount", "0.0002")
        notice_text = f"📢 *New Number Added!*\n━━━━━━━━━━━━━━━━━━━\n📱 *Service:* {service}\n🌍 *Country:* {country}\n💰 *Otp Price:* {reward_amt} টাকা\n━━━━━━━━━━━━━━━━━━━\n⚡ *Try Now! Click 'Get Free Number' button below.*"
        threading.Thread(target=internal_notice_broadcast, args=(notice_text,), daemon=True).start()
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Format Error: Use `🇺🇸 United States|1XXXXXXXXXX`")

def process_remove_range(message, service):
    country = message.text.strip()
    res = db.services.delete_one({"service_name": service, "country_name": country})
        
    if res.deleted_count > 0:
        bot.send_message(message.chat.id, f"✅ Removed `{country}` from `{service}`.")
    else:
        bot.send_message(message.chat.id, "❌ Not found.")

def _send_single_msg(uid, text):
    try:
        bot.send_message(int(uid), text, parse_mode="Markdown")
        return True
    except: return False

def internal_notice_broadcast(notice_text):
    users = [r['user_id'] for r in db.users.find({}, {"user_id": 1})]
        
    with ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(lambda uid: _send_single_msg(uid, notice_text), users)

def process_broadcast(message):
    if message.text == "/cancel": return
    users = [r['user_id'] for r in db.users.find({}, {"user_id": 1})]
        
    bot.send_message(message.chat.id, "⏳ *Transmitting global waves...*")
    broadcast_text = message.text
    success, fail = 0, 0
    with ThreadPoolExecutor(max_workers=35) as executor:
        results = executor.map(lambda uid: _send_single_msg(uid, broadcast_text), users)
        for res in results:
            if res: success += 1
            else: fail += 1
            
    bot.send_message(message.chat.id, f"🛰 *Transmission Terminated!*\n🟢 Active: `{success}`\n🔴 Dead: `{fail}`")

def process_user_info(message):
    uid = message.text.strip()
    row = db.users.find_one({"user_id": uid})
        
    if row:
        bot.send_message(message.chat.id, f"👤 *Node Data:* `{uid}`\n💰 Balance: `{row['balance']:.6f} ৳`\n✅ OTPs: `{row['completed_otps']}`\n🚫 Banned: `{bool(row['banned'])}`")
    else:
        bot.send_message(message.chat.id, "❌ Node not found.")

def process_ban_user(message):
    uid = message.text.strip()
    res = db.users.update_one({"user_id": uid}, {"$set": {"banned": 1}})
    if res.modified_count > 0: bot.send_message(message.chat.id, f"🚫 Node `{uid}` blocked.")
    else: bot.send_message(message.chat.id, "⚠️ Node missing.")

def process_unban_user(message):
    uid = message.text.strip()
    res = db.users.update_one({"user_id": uid}, {"$set": {"banned": 0}})
    if res.modified_count > 0: bot.send_message(message.chat.id, f"✅ Node `{uid}` restored.")
    else: bot.send_message(message.chat.id, "⚠️ Node missing.")

def process_change_reward(message):
    try:
        new_amt = float(message.text.strip())
        set_config("reward_amount", new_amt)
        bot.send_message(message.chat.id, f"✅ Reward configured to: `{new_amt} ৳`")
    except:
        bot.send_message(message.chat.id, "❌ Mathematical error.")

@bot.message_handler(commands=['clear_pending'])
def cmd_clear_pending(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return
    try:
        res = db.withdrawals.delete_many({"status": "pending"})
        bot.reply_to(message, f"✅ Cleared {res.deleted_count} pending withdrawals.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    full_name = message.from_user.first_name or "User"
    if message.from_user.last_name:
        full_name += " " + message.from_user.last_name
        
    referred_by = None
    start_args = message.text.split()
    if len(start_args) > 1:
        ref_id = start_args[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            referred_by = str(ref_id)
            
    register_user(user_id, username=full_name, referred_by=referred_by)
    
    if not check_join(user_id):
        bot.send_message(message.chat.id, "🔴 *বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন:*", reply_markup=force_join_keyboard())
        return
        
    welcome_text = (
        f"👋 *হ্যালো {full_name}, আমাদের বটে আপনাকে স্বাগতম!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ *Premium Cloud Nodes ব্যবহার করে খুব সহজেই ফ্রি-তে আনলিমিটেড ইনকাম করুন!*\n\n"
        "🚀 *কীভাবে কাজ করবেন?*\n"
        "১️⃣ নিচে থেকে `🚀 Get Free Number` এ ক্লিক করে আপনার কাঙ্ক্ষিত সার্ভিসের নম্বর নিন।\n"
        "২️⃣ সেই নম্বরটি টার্গেট অ্যাপে বসিয়ে কোড সেন্ড করুন।\n"
        "৩️⃣ আমাদের স্মার্ট সিস্টেম অটোমেটিক OTP রিসিভ করবে এবং সাথে সাথেই আপনার ব্যালেন্সে টাকা জমা হয়ে যাবে!\n\n"
        "🎁 *এক্সট্রা বোনাস:* বন্ধুদের ইনভাইট করে লাইফটাইম রেফার কমিশন উপভোগ করুন!\n\n"
        "💬 _যেকোনো সাহায্যে বা উইথড্র নিয়ে কথা বলতে সাপোর্ট টিমের সাথে যোগাযোগ করুন।_"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "check_verified")
def verify_user_callback(call):
    user_id = call.from_user.id
    if check_join(user_id):
        try: bot.answer_callback_query(call.id, "✅ Node Verified!", show_alert=True)
        except: pass
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ *Verification successful | System ready.*", reply_markup=main_menu_keyboard(user_id))
    else:
        try: bot.answer_callback_query(call.id, "❌ Verification Failed! Join channel.", show_alert=True)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "req_withdraw")
def handle_withdraw_request(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    user_id = str(call.from_user.id)
    u_row = db.users.find_one({"user_id": user_id})
        
    if not u_row or u_row['banned']:
        bot.answer_callback_query(call.id, "🔴 Access Denied!", show_alert=True)
        return
        
    if u_row['balance'] < 100.0:
        bot.answer_callback_query(call.id, f"🔴 ইনসাফিসিয়েন্ট ব্যালেন্স! আপনার ব্যালেন্স: {u_row['balance']:.4f} ৳। ন্যূনতম ১০০ টাকা প্রয়োজন।", show_alert=True)
        return
        
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    msg = bot.send_message(call.message.chat.id, "💸 *উইথড্রাল ফর্ম প্যানেল*\n━━━━━━━━━━━━━━━━━━━\n*ফরম্যাট:* `মেথড নাম | অ্যাকাউন্ট নম্বর | অ্যামাউন্ট` \n_(উদাহরণ: `বিকাশ | 017XXXXXXXX | 150`)_", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, process_withdrawal_request, u_row['balance'])

@bot.message_handler(func=lambda msg: True)
def handle_text_buttons(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "User"
    register_user(user_id, username=username)
    uid = str(user_id)
    
    u_row = db.users.find_one({"user_id": uid})
        
    if u_row and u_row['banned']:
        bot.send_message(message.chat.id, "🔴 *Access Denied! Node blocked.*")
        return
        
    if not check_join(user_id):
        bot.send_message(message.chat.id, "🔴 *বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন:*", reply_markup=force_join_keyboard())
        return
        
    text = message.text
    
    if "GET NUMBER" in text.upper() or "FREE NUMBER" in text.upper():
        bot.send_message(message.chat.id, "📍 Select a service:", reply_markup=service_menu_keyboard())
        
    elif "WITHDRAWAL" in text.upper() or "WALLET" in text.upper():
        total_refs = db.users.count_documents({"referred_by": uid})
        wallet_text = (
            "💳 *DIGITAL WALLET CRYPTX*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Node ID:* `{user_id}`\n"
            f"💵 *Available Balance:* `{u_row['balance']:.4f} ৳`\n"
            f"🎯 *Successful Tasks:* `{u_row['completed_otps']}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📢 _Withdrawals are processed automatically by the system._"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💸 Withdraw Balance", callback_data="req_withdraw", style="danger"))
        markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
        bot.send_message(message.chat.id, wallet_text, reply_markup=markup)
        
    elif "REFER" in text.upper():
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        commission_rate = float(get_config("ref_commission", 0.01))
        
        total_refs = db.users.count_documents({"referred_by": uid})
        total_referrals_otps = sum(u.get("completed_otps", 0) for u in db.users.find({"referred_by": uid}))
        total_referral_earnings = sum(r.get("amount", 0) for r in db.ref_history.find({"referrer_id": uid}))
        current_time = time.time()
        last_24h_earnings = sum(r.get("amount", 0) for r in db.ref_history.find({"referrer_id": uid, "timestamp": {"$gte": current_time - 86400}}))
            
        ref_text = (
            "🎁 *PREMIUM REFERRAL SYSTEM PANEL*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 *আপনার ইনভাইটেশন লিংক:*\n`{ref_link}`\n\n"
            f"💰 *রেফার বোনাস:* প্রতি সফল OTP-তে `{commission_rate}` টাকা।\n\n"
            f"📊 *আপনার স্ট্যাটাস:*\n"
            f"▪️ মোট জয়েনিং: `{total_refs}` জন\n"
            f"▪️ সর্বমোট লাইফটাইম ইনকাম: `{total_referral_earnings:.4f}` ৳\n"
            f"▪️ গত ২৪ ঘণ্টায় ইনকাম: `{last_24h_earnings:.4f}` ৳\n"
            f"▪️ আপনার টিমের সফল ওটিপি: `{total_referrals_otps}` টি\n"
        )
        import urllib.parse
        share_text = "🔥 টেলিগ্রামের সেরা OTP প্যানেল! এখানে OTP আসার সাকসেস রেট ৯০%+। আজই জয়েন করে আনলিমিটেড ফ্রি ইনকাম শুরু করুন!"
        encoded_text = urllib.parse.quote(share_text)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📋 COPY LINK", copy_text=types.CopyTextButton(text=ref_link), style="success"),
            types.InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text={encoded_text}", style="success")
        )
        markup.add(types.InlineKeyboardButton("❌ CLOSE", callback_data="cancel_step", style="danger"))
        bot.send_message(message.chat.id, ref_text, reply_markup=markup)

    elif "LEADERBOARD" in text.upper():
        top_users = list(db.users.find({}, {"user_id": 1, "completed_otps": 1}).sort("completed_otps", -1).limit(10))
            
        leaderboard_msg = "🏆 *TOP 10 LIVE OPERATIONAL NODES (BY OTP)* 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        medals = ["🥇", "🥈", "🥉", "👤", "👤", "👤", "👤", "👤", "👤", "👤"]
        
        for index, row in enumerate(top_users):
            hidden_id = str(row['user_id'])[:4] + "xxxx"
            leaderboard_msg += f"{medals[index]} *Rank {index+1:02d}:* ID: `{hidden_id}` ➔ 🎯 `{row['completed_otps']}` OTPs\n"
            
        leaderboard_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        pipeline = [
            {"$match": {"referred_by": {"$ne": None}}},
            {"$group": {"_id": "$referred_by", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_refs = list(db.users.aggregate(pipeline))
        
        if top_refs:
            leaderboard_msg += "🎁 *TOP 5 REFERRERS* 🎁\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for index, ref in enumerate(top_refs):
                hidden_id = str(ref['_id'])[:4] + "xxxx"
                leaderboard_msg += f"{medals[index]} *Rank {index+1:02d}:* ID: `{hidden_id}` ➔ 👥 `{ref['count']}` Refs\n"
            leaderboard_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
        leaderboard_msg += "🚀 PUSH YOUR SPEED TO SECURE A HIGHER SEAT!"
        bot.send_message(message.chat.id, leaderboard_msg)
        
    elif "SUPPORT" in text.upper():
        support_text = "🤝 *OFFICIAL COMMUNICATIONS SUPPORT*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\nযে কোনো ধরনের সহযোগিতা বা সমস্যার সমাধানের জন্য আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন। অথবা কাস্টম বটের জন্য ডেভেলপারের সাথে কথা বলতে পারেন।"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/developer1100", style="primary"),
            types.InlineKeyboardButton("🎧 Support", url="https://t.me/Mahi99909", style="primary")
        )
        bot.send_message(message.chat.id, support_text, reply_markup=markup, disable_web_page_preview=True)

    elif "GET 2FA" in text.upper():
        msg = bot.send_message(message.chat.id, "?? *2FA Code Generator*

Please send me your 2FA Key (Base32 format):", parse_mode="Markdown", reply_markup=reply_cancel_markup())
        bot.register_next_step_handler(msg, process_2fa_key)

def process_2fa_key(message):
    key = message.text.strip().replace(" ", "")
    if key == "/cancel" or key.lower() == "cancel" or key == "? Cancel":
        bot.send_message(message.chat.id, "? Cancelled.", reply_markup=main_menu_keyboard(message.chat.id))
        return
        
    try:
        import pyotp
        import time
        totp = pyotp.TOTP(key)
        code = totp.now()
        remaining = 30 - (int(time.time()) % 30)
        
        reply_text = f"?? *2FA Code Generator*

?? *Key:* {key}

?? *Code:* {code}
? *Expires in:* {remaining}s"
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_refresh = types.InlineKeyboardButton("?? Refresh Code", callback_data=f"2fa_refresh:{key}", style="success")
        btn_new = types.InlineKeyboardButton("? New", callback_data="2fa_new", style="primary")
        markup.add(btn_refresh, btn_new)
        
        bot.send_message(message.chat.id, "? Success!", reply_markup=main_menu_keyboard(message.chat.id))
        bot.send_message(message.chat.id, reply_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("? Try Again", callback_data="2fa_new", style="primary"))
        bot.send_message(message.chat.id, "? Failed!", reply_markup=main_menu_keyboard(message.chat.id))
        bot.send_message(message.chat.id, f"?? *Invalid 2FA Key!* Make sure it's a valid Base32 secret.", reply_markup=markup, parse_mode="Markdown")

def process_withdrawal_request(message, current_balance):
    try:
        data = message.text.strip().split("|")
        method = data[0].strip()
        account_number = data[1].strip()
        amount = float(data[2].strip())
        
        uid = str(message.from_user.id)
        
        if amount < 100.0:
            bot.send_message(message.chat.id, "🔴 *ত্রুটি!* সর্বনিম্ন উইথড্র ১০০ টাকা।")
            return
            
        if current_balance < amount:
            bot.send_message(message.chat.id, "🔴 *অপর্যাপ্ত ব্যালেন্স!*")
            return
            
        w_id = str(int(time.time()))
        
        db.users.update_one({"user_id": uid}, {"$inc": {"balance": -amount}})
        db.withdrawals.insert_one({"id": w_id, "user_id": uid, "method": method, "account": account_number, "amount": amount, "status": "pending", "timestamp": time.time()})
            
        bot.send_message(message.chat.id, f"✅ *উইথড্র রিকোয়েস্ট সফল!*\nঅ্যামাউন্ট: `{amount}` ৳\nমেথড: {method}\nঅ্যাকাউন্ট: `{account_number}`")
        
        u_name = message.from_user.first_name or "User"
        admin_req_msg = (
            f"💰 *NEW WITHDRAWAL REQUEST* 💰\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {u_name}\n"
            f"🆔 *ID:* `{uid}`\n"
            f"💵 *Amount:* `{amount}` ৳\n"
            f"🏦 *Method:* {method}\n"
            f"📱 *Account:* `{account_number}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve Payment", callback_data=f"wtx_accept_{w_id}", style="success"),
            types.InlineKeyboardButton("❌ Reject & Refund", callback_data=f"wtx_reject_{w_id}", style="danger")
        )
        
        admin_group_id = get_config("withdraw_group_id", str(FORWARD_GROUP_ID))
        bot.send_message(int(admin_group_id), admin_req_msg, reply_markup=markup, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, "🔴 *ইনপুট ফরম্যাট ভুল!* `বিকাশ | 017XXXXXXXX | 150` ")

@bot.callback_query_handler(func=lambda call: call.data.startswith("req_withdraw_"))
def handle_withdraw_method(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    user_id = str(call.from_user.id)
    u_row = db.users.find_one({"user_id": user_id})
    if not u_row or u_row['banned']: return
    if u_row['balance'] < 100.0:
        bot.answer_callback_query(call.id, "🔴 Insufficient Balance! Minimum 100 TK.", show_alert=True)
        return
    method = call.data.split("_")[2].capitalize()
    msg = bot.send_message(call.message.chat.id, f"« 💸 {method} WITHDRAWAL »\n➖➖➖➖➖➖➖➖➖➖\n📝 *Enter your {method} account number:*", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, process_withdrawal_account, method, u_row['balance'])

def process_withdrawal_account(message, method, current_balance):
    if not message.text:
        try: bot.send_message(message.chat.id, "🔴 *Invalid Input! Please provide text.*")
        except: pass
        return
    account = message.text.strip()
    msg = bot.send_message(message.chat.id, f"💰 *Enter amount to withdraw (Max {current_balance:.2f}):*", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, process_withdrawal_final, method, account, current_balance)

def process_withdrawal_final(message, method, account, current_balance):
    try:
        amount = float(message.text.strip())
        if amount < 100.0:
            bot.send_message(message.chat.id, "🔴 *Minimum withdraw is 100 TK!*")
            return
        if current_balance < amount:
            bot.send_message(message.chat.id, "🔴 *Insufficient balance!*")
            return
            
        uid = str(message.from_user.id)
        w_id = str(int(time.time()))
        db.users.update_one({"user_id": uid}, {"$inc": {"balance": -amount}})
        db.withdrawals.insert_one({"id": w_id, "user_id": uid, "method": method, "account": account, "amount": amount, "status": "pending", "timestamp": time.time()})
            
        bot.send_message(message.chat.id, f"✅ *Withdrawal Request Successful!*\nAmount: `{amount}` ৳\nMethod: {method}\nAccount: `{account}`")
        
        u_name = message.from_user.first_name or "User"
        admin_req_msg = (
            f"💰 *NEW WITHDRAWAL* 💰\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"👤 *User:* {u_name}\n"
            f"🆔 *ID:* `{uid}`\n"
            f"💵 *Amount:* `{amount}` ৳\n"
            f"🏦 *Method:* {method}\n"
            f"📱 *Account:* `{account}`\n"
            f"➖➖➖➖➖➖➖➖➖➖"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"wtx_accept_{w_id}", style="danger"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"wtx_reject_{w_id}", style="danger")
        )
        admin_group_id = get_config("withdraw_group_id", str(FORWARD_GROUP_ID))
        bot.send_message(int(admin_group_id), admin_req_msg, reply_markup=markup, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "🔴 *Invalid Amount!*")

@bot.callback_query_handler(func=lambda call: call.data.startswith("wtx_"))
def handle_withdrawal_actions(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    if not has_permission(call.from_user.id, "withdraw"): return bot.answer_callback_query(call.id, "🔴 Permission Denied!", show_alert=True)
    action_data = call.data.split("_")
    action = action_data[1]
    w_id = action_data[2]
    
    row = db.withdrawals.find_one({"id": w_id})
    if not row:
        bot.answer_callback_query(call.id, "🔴 Not found.", show_alert=True)
        return
        
    if row.get('status') != "pending":
        bot.answer_callback_query(call.id, "⚠️ Already processed.", show_alert=True)
        return
        
    target_uid = row['user_id']
    amount = row['amount']
    
    if action == "accept":
        db.withdrawals.update_one({"id": w_id}, {"$set": {"status": "accepted"}})
        bot.edit_message_text(call.message.text + "\n\n✅ *STATUS: PAID*", call.message.chat.id, call.message.message_id, reply_markup=None)
        try: bot.send_message(target_uid, f"🎉 *আপনার উইথড্রাল রিকোয়েস্টটি অ্যাপ্রুভ হয়েছে!*\n💰 Amount: `{amount}` ৳")
        except: pass
        
    elif action == "reject":
        db.withdrawals.update_one({"id": w_id}, {"$set": {"status": "rejected"}})
        db.users.update_one({"user_id": target_uid}, {"$inc": {"balance": amount}})
        bot.edit_message_text(call.message.text + "\n\n❌ *STATUS: REFUNDED*", call.message.chat.id, call.message.message_id, reply_markup=None)
        try: bot.send_message(target_uid, f"🔴 *আপনার উইথড্রাল রিকোয়েস্টটি বাতিল হয়েছে!*\n💰 Amount: `{amount}` ৳ রিফান্ড করা হয়েছে।")
        except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("bsrv_") or call.data == "back_to_bulk_services")
def handle_bulk_service_selection(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    chat_id = call.message.chat.id
    if not is_admin(call.from_user.id): return
    if call.data == "back_to_bulk_services":
        bot.edit_message_text("⚡ *Select Target Protocol for Bulk Order:*", chat_id, call.message.message_id, reply_markup=bulk_service_menu_keyboard())
        return
        
    service_name = call.data.split("_")[1]
    bot.edit_message_text(f"🌍 *Bulk Order Service:* `{service_name}`\n\n_Select Country:_", chat_id, call.message.message_id, reply_markup=bulk_country_menu_keyboard(service_name))

@bot.callback_query_handler(func=lambda call: call.data.startswith("bsel_"))
def handle_bulk_country_selection(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id
    if not is_admin(user_id): return
    
    data_parts = call.data.split("_", 2)
    service_name = data_parts[1]
    country_node = data_parts[2]
    
    msg = bot.send_message(chat_id, f"📦 *Bulk Order*\nService: `{service_name}`\nCountry: `{country_node}`\n\n🔢 *Enter the number of lines/numbers you want to allocate (max 50):*")
    bot.register_next_step_handler(msg, process_bulk_order_quantity, service_name, country_node)

def process_bulk_order_quantity(message, service_name, country_node):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    try:
        qty = int(message.text.strip())
        if qty <= 0 or qty > 50:
            bot.send_message(chat_id, "❌ Please enter a valid quantity between 1 and 50.")
            return
    except:
        bot.send_message(chat_id, "❌ Invalid number.")
        return
        
    s_row = db.services.find_one({"service_name": service_name, "country_name": country_node})
    if not s_row:
        bot.send_message(chat_id, "🔴 Routing pool empty.")
        return
    target_range = s_row['range']
    panel_name = s_row.get("panel_name", "Zenex")
    active_panel = db.panels.find_one({"panel_name": panel_name})
    if active_panel and not active_panel.get("is_active"):
        bot.send_message(chat_id, f"❌ *{panel_name} panel is currently deactivated!*", parse_mode="Markdown")
        return
    if not active_panel: active_panel = get_active_panel()
    if not active_panel or not active_panel.get("is_active"):
        bot.send_message(chat_id, "❌ *No active panels available!*", parse_mode="Markdown")
        return
        
    base_url = active_panel['base_url'].rstrip('/')
    api_url = f"{base_url}/getnum" if "@public" in base_url else f"{base_url}/v1/getnum"
    payload = {"range": target_range, "rid": target_range, "is_national": False, "remove_plus": False}
    
    loading_msg = bot.send_message(chat_id, f"⏳ *Allocating {qty} numbers... Please wait.*")
    
    success_numbers = []
    
    for _ in range(qty):
        with api_request_lock:
            try:
                response_raw = http_session.post(api_url, json=payload, headers=get_api_headers(active_panel['api_key']), timeout=12)
                response = response_raw.json()
                
                if response_raw.status_code == 200 and response.get("meta", {}).get("status") in ["success", "ok"]:
                    number_data = response.get("data", {})
                    allocated_number = number_data.get("number") or number_data.get("full_number")
                    if allocated_number:
                        success_numbers.append(str(allocated_number))
            except Exception as e:
                logger.error(f"Bulk API Error: {e}")
        time.sleep(0.5) 
        
    if success_numbers:
        threading.Thread(target=bulk_free_poll_otp_thread, args=(chat_id, success_numbers, service_name, user_id, active_panel['base_url'], active_panel['api_key']), daemon=True).start()
        
        success_text = f"✅ *Successfully allocated {len(success_numbers)} numbers!*\n━━━━━━━━━━━━━━━━━━━\n"
        for i, num in enumerate(success_numbers, 1):
            success_text += f"{i}. `{num}`\n"
        success_text += "━━━━━━━━━━━━━━━━━━━\n🔄 _Listening for incoming OTPs..._\n_OTPs will be forwarded to the OTP Group._"
        
        numbers_only_str = "\n".join(success_numbers)
        bulk_markup = types.InlineKeyboardMarkup(row_width=1)
        bulk_markup.add(
            types.InlineKeyboardButton(text="📋 Copy All Numbers", copy_text=types.CopyTextButton(text=numbers_only_str, style="success"))
        )
        bulk_markup.add(types.InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_services", style="danger"))
        try: bot.delete_message(chat_id, loading_msg.message_id)
        except: pass
        bot.send_message(chat_id, success_text, reply_markup=bulk_markup)
    else:
        try: bot.edit_message_text("🔴 *Failed to allocate any numbers! API may be out of stock.*", chat_id, loading_msg.message_id)
        except: pass

def bulk_free_poll_otp_thread(chat_id, success_numbers, service_name, user_id, base_url, api_key):
    start_time = time.time()
    country_name, country_flag, country_code = get_country_info(success_numbers[0]) if success_numbers else ("Unknown", "🏳️", "00")
    
    notified_otps = set()
    
    while time.time() - start_time < 900:
        for num in success_numbers:
            check_url = f"{base_url}/success-otp" if "@public" in base_url else f"{base_url}/v1/numsuccess/info"
            try:
                res_raw = http_session.get(check_url, headers=get_api_headers(api_key), timeout=8)
                res = res_raw.json()
                
                if res_raw.status_code == 200 and res.get("meta", {}).get("status") in ["success", "ok"]:
                    data = res.get("data", [])
                    if isinstance(data, list):
                        for item in data:
                            if str(item.get("number")) == str(num):
                                sms = item.get("sms")
                                if sms and str(item.get("id")) not in notified_otps:
                                    notified_otps.add(str(item.get("id")))
                                    otp_code = str(sms).strip()
                                    
                                    panel_doc = db.panels.find_one({"base_url": base_url})
                                    pname = panel_doc["panel_name"] if panel_doc else "Unknown"
                                    db.otps_history.insert_one({
                                        "user_id": user_id,
                                        "service": service_name,
                                        "number": num,
                                        "otp": otp_code,
                                        "date": time.strftime('%Y-%m-%d'),
                                        "timestamp": time.time(),
                                        "panel": pname
                                    })
                                    
                                    group_msg = (
                                        f"🔔 *NEW OTP RECEIVED (BULK)*\n"
                                        f"━━━━━━━━━━━━━━━━━━━\n"
                                        f"📱 *Service:* `{service_name.upper()}`\n"
                                        f"🌍 *Country:* {country_flag} {country_name.upper()} (+{country_code})\n"
                                        f"📞 *Number:* `{num}`\n"
                                        f"💬 *OTP Code:* `{otp_code}`\n"
                                        f"━━━━━━━━━━━━━━━━━━━\n"
                                        f"👤 *User ID:* `{user_id}`"
                                    )
                                    
                                    markup = types.InlineKeyboardMarkup()
                                    markup.add(types.InlineKeyboardButton(text=f"📋 CODE: {otp_code}", copy_text=types.CopyTextButton(text=otp_code, style="primary")))
                                    otp_group_id = get_config("otp_group_id", str(FORWARD_GROUP_ID))
                                    try: bot.send_message(int(otp_group_id), group_msg, reply_markup=markup, parse_mode="Markdown")
                                    except: pass
            except:
                pass
        time.sleep(3)

def threaded_getnum_retry(chat_id, user_id, service_name, country_node, s_row, loading_msg_id, tried_ranges=None):
    if tried_ranges is None:
        tried_ranges = []
    target_range = s_row['range']
    if target_range not in tried_ranges:
        tried_ranges.append(target_range)
    panel_name = s_row.get("panel_name", "Zenex")
    active_panel = db.panels.find_one({"panel_name": panel_name})
    if active_panel and not active_panel.get("is_active"):
        try: bot.edit_message_text(f"❌ *{panel_name} panel is currently deactivated!*", chat_id, loading_msg_id, parse_mode="Markdown")
        except: pass
        return
    if not active_panel: active_panel = get_active_panel()
    if not active_panel or not active_panel.get("is_active"):
        try: bot.edit_message_text("❌ *No active panels available!*", chat_id, loading_msg_id, parse_mode="Markdown")
        except: pass
        return
        
    base_url = active_panel['base_url'].rstrip('/')
    api_url = f"{base_url}/getnum" if "@public" in base_url else f"{base_url}/v1/getnum"
    payload = {"range": target_range, "rid": target_range, "is_national": False, "remove_plus": False}
    
    max_duration = 15
    start_time = time.time()
    success = False
    final_err_msg = ""
    final_err_type = "API says"
    
    while time.time() - start_time < max_duration:
        try:
            with api_request_lock:
                response_raw = http_session.post(api_url, json=payload, headers=get_api_headers(active_panel['api_key']), timeout=12)
                response = response_raw.json()
                
            if response_raw.status_code == 200 and response.get("meta", {}).get("status") in ["success", "ok"]:
                if not is_admin(user_id):
                    user_cooldowns[user_id] = time.time()
                    
                number_data = response.get("data", {})
                allocated_number = number_data.get("number") or number_data.get("full_number")
                
                try: bot.delete_message(chat_id, loading_msg_id)
                except: pass
                
                import urllib.parse
                country_name_disp, country_flag, country_code = get_country_info(allocated_number)
                
                allocated_ui = (
                    "🎯 *NUMBER ALLOCATED SUCCESSFULLY*\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"📱 *Service:* `{service_name.upper()}`\n"
                    f"🌍 *Region:* {country_flag} {country_name_disp.upper()} (+{country_code})\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"📞 *Your Number:* `{allocated_number}`\n"
                    "⏳ *Timeout:* `15 Minutes`\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "🔄 _Status: Listening for incoming OTP..._\n"
                    "⚠️ _(Do not close this menu until OTP arrives)_"
                )
                
                otp_link = get_config("otp_group_link", "https://t.me/FreeOtpMaster")
                allocated_markup = types.InlineKeyboardMarkup(row_width=2)
                allocated_markup.add(
                    types.InlineKeyboardButton("🔄 Change Target", callback_data=f"srv_{service_name}", style="danger"),
                    types.InlineKeyboardButton("↗️ View OTP Group", url=otp_link, style="primary")
                )
                allocated_markup.add(types.InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_services", style="danger"))
                allocated_markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
                
                success_msg = bot.send_message(chat_id, allocated_ui, reply_markup=allocated_markup)
                threading.Thread(target=free_poll_otp_thread, args=(chat_id, success_msg.message_id, allocated_number, service_name, user_id, active_panel['base_url'], active_panel['api_key']), daemon=True).start()
                
                success = True
                break
            else:
                final_err_msg = response.get("message", "Validation Fail")
                final_err_type = "API says"
        except Exception as e:
            err_text = response_raw.text[:150] if 'response_raw' in locals() else "No response"
            final_err_msg = f"{e} | Resp: {err_text}"
            final_err_type = "API/Network Error"
            logger.error(f"API Error: {e} | Text: {err_text}")
        
        remaining = int(max_duration - (time.time() - start_time))
        if remaining > 0:
            try: bot.edit_message_text(f"⏳ *Stock out.* Waiting for new numbers...\n🔄 Retrying in `{remaining}s`\n_(You will get the number automatically if available)_", chat_id, loading_msg_id)
            except: pass
            time.sleep(min(3, remaining))
            
    if not success:
        fallback_route = db.services.find_one({"service_name": service_name, "range": {"$nin": tried_ranges}}, sort=[("hits", -1)])
        if fallback_route:
            try: bot.edit_message_text(f"⏳ *Range {target_range} is out of stock!* Trying another active country/range...", chat_id, loading_msg_id)
            except: pass
            time.sleep(1)
            threaded_getnum_retry(chat_id, user_id, service_name, fallback_route.get("country_name", "AUTO-FALLBACK"), fallback_route, loading_msg_id, tried_ranges)
            return

        if final_err_type == "API says":
            try: bot.edit_message_text(f"🔴 *Failed! API says:* `{final_err_msg}`", chat_id, loading_msg_id)
            except: pass
            db.stock_outs.insert_one({"user_id": user_id, "service": service_name, "country": country_node, "timestamp": time.time()})
            if get_config("admin_notifications", "1") == "1":
                err_notice = f"⚠️ *API/STOCK ALERT*\n👤 User: `{user_id}`\n⚡ Service: `{service_name}`\n🌍 Country: `{country_node}`\n💬 Error: `{final_err_msg}`"
                admin_ids = set([r['user_id'] for r in db.admins.find()])
                admin_ids.add(str(PRIMARY_ADMIN_ID))
                for admin_uid in admin_ids:
                    try: bot.send_message(int(admin_uid), err_notice)
                    except: pass
        else:
            try: bot.edit_message_text(f"🔴 *{final_err_type}:* `{final_err_msg}`", chat_id, loading_msg_id)
            except: pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("srv_") or call.data == "back_to_services")
def handle_service_selection(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    chat_id = call.message.chat.id
    if call.data == "back_to_services":
        bot.edit_message_text("⚡ *Select Target Protocol:*", chat_id, call.message.message_id, reply_markup=service_menu_keyboard())
        return
        
    try:
        service_name = call.data.split("_")[1]
        best_route = db.services.find_one({"service_name": service_name}, sort=[("hits", -1)])
        
        hot_msg = ""
        if best_route and best_route.get("hits", 0) > 10:
            c_part = best_route.get('country_name', '').split(" | ")[0]
            hot_msg = f"\n\n🔥 *HOT ALERT:* বর্তমানে *{c_part}* এ সবচেয়ে ভালো *OTP* দিচ্ছে!"
            
        msg_text = f"🌍 *সার্ভিস:* `{service_name}`{hot_msg}\n\nসবচেয়ে বেশি *Hits* থাকা *Range* সিলেক্ট করুন তাহলে ভালো *OTP* পাবেন।\n*OTP* সেন্ড করার পর ৫ সেকেন্ড অপেক্ষা করুন, কোড না পেলে *Resend* করুন।"
        bot.edit_message_text(msg_text, chat_id, call.message.message_id, reply_markup=country_menu_keyboard(service_name))
    except Exception as e:
        bot.answer_callback_query(call.id, "Session Expired! Please /start", show_alert=True)
        restart_markup = types.InlineKeyboardMarkup()
        restart_markup.add(types.InlineKeyboardButton("🔄 রিস্টার্ট করুন (Restart)", url=f"https://t.me/{BOT_USERNAME}?start=refresh"))
        try: bot.send_message(chat_id, "🤖 *দুঃখিত! আপনার সেশনটি এক্সপায়ার হয়ে গেছে।*\n\n👉 দয়া করে নিচের বাটনে ক্লিক করে আবার রিস্টার্ট করুন।", reply_markup=restart_markup)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def handle_country_and_purchase(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id
    
    try: bot.answer_callback_query(call.id)
    except: pass
    
    u_row = db.users.find_one({"user_id": user_id})
    if u_row:
        last_active = u_row.get("last_active", 0)
        if time.time() - last_active > 86400:
            bot.answer_callback_query(call.id, "Session Expired! Please /start", show_alert=True)
            restart_markup = types.InlineKeyboardMarkup()
            restart_markup.add(types.InlineKeyboardButton("🔄 রিস্টার্ট করুন (Restart)", url=f"https://t.me/{BOT_USERNAME}?start=refresh"))
            bot.send_message(chat_id, "🤖 *আপনার সেশন এক্সপায়ার হয়ে গেছে!*\n\n👉 সার্ভার কন্টিনিউ করতে দয়া করে নিচের বাটনে ক্লিক করে বটটি রিস্টার্ট করুন।", reply_markup=restart_markup)
            return

    data_parts = call.data.split("_", 2)
    service_name = data_parts[1]
    country_node = data_parts[2]
    
    if country_node == "AUTO-BEST":
        s_row = db.services.find_one({"service_name": service_name}, sort=[("hits", -1)])
        if not s_row:
            bot.answer_callback_query(call.id, "❌ No active routes found!", show_alert=True)
            return
        is_custom_range = False
    elif country_node.startswith("RNG_"):
        target_range = country_node.replace("RNG_", "")
        s_row = db.services.find_one({"service_name": service_name, "range": target_range})
        is_custom_range = False
    else:
        s_row = db.services.find_one({"service_name": service_name, "country_name": country_node})
        is_custom_range = False
        
    if not check_join(int(user_id)):
        bot.answer_callback_query(call.id, "⚠️ Please Join Channels First!", show_alert=True)
        bot.send_message(chat_id, "⚠️ *Access Revoked!* You must authenticate membership.", reply_markup=force_join_keyboard())
        return
    
    if not u_row:
        bot.answer_callback_query(call.id, "Session Expired! Please /start", show_alert=True)
        restart_markup = types.InlineKeyboardMarkup()
        restart_markup.add(types.InlineKeyboardButton("🔄 রিস্টার্ট করুন (Restart)", url=f"https://t.me/{BOT_USERNAME}?start=refresh"))
        bot.send_message(chat_id, "🤖 *দুঃখিত! আপনার সেশনটি এক্সপায়ার হয়ে গেছে।*\n\n👉 দয়া করে নিচের বাটনে ক্লিক করে আবার রিস্টার্ট করুন।", reply_markup=restart_markup)
        return
        
    if u_row.get('banned', 0): return
    if not s_row:
        bot.answer_callback_query(call.id, "Service Unavailable", show_alert=True)
        restart_markup = types.InlineKeyboardMarkup()
        restart_markup.add(types.InlineKeyboardButton("🔄 রিস্টার্ট করুন (Restart)", url=f"https://t.me/{BOT_USERNAME}?start=refresh"))
        bot.send_message(chat_id, "🤖 *দুঃখিত! এই সার্ভিসটি এখন এভেইলেবল নেই।*\n\n👉 দয়া করে নিচের বাটনে ক্লিক করে আবার রিস্টার্ট করুন।", reply_markup=restart_markup)
        return
        
    target_range = s_row['range']
    panel_name = s_row.get("panel_name", "Zenex")
    active_panel = db.panels.find_one({"panel_name": panel_name})
    if active_panel and not active_panel.get("is_active"):
        bot.answer_callback_query(call.id, f"❌ {panel_name} is turned OFF!", show_alert=True)
        return
    if not active_panel: active_panel = get_active_panel()
    if not active_panel or not active_panel.get("is_active"):
        bot.answer_callback_query(call.id, "❌ No active panels!", show_alert=True)
        return
    loading_msg = bot.send_message(chat_id, "⏳ *নম্বর লোডিং হচ্ছে...*")
    
    if active_panel.get("is_manual", False):
        manual_num = db.manual_numbers.find_one_and_update(
            {"panel_id": active_panel.get("_id"), "service_name": service_name, "country_name": country_node, "status": "available"},
            {"$set": {"status": "assigned", "assigned_to": user_id, "assigned_at": time.time()}}
        )
        if not manual_num:
            bot.edit_message_text("🔴 *Stock Out! No manual numbers available for this service.*", chat_id, loading_msg.message_id)
            db.stock_outs.insert_one({"user_id": user_id, "service": service_name, "country": country_node, "timestamp": time.time()})
            return
            
        allocated_number = manual_num["number"]
        if not is_admin(user_id):
            user_cooldowns[user_id] = time.time()
            
        try: bot.delete_message(chat_id, loading_msg.message_id)
        except: pass
        
        import urllib.parse
        country_name_disp, country_flag, country_code = get_country_info(allocated_number)
        
        allocated_ui = (
            "🎯 *NUMBER ALLOCATED SUCCESSFULLY*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"📱 *Service:* `{service_name.upper()}`\n"
            f"🌍 *Region:* {country_flag} {country_name_disp.upper()} (+{country_code})\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"📞 *Your Number:* `{allocated_number}`\n"
            "⏳ *Timeout:* `15 Minutes`\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🔄 _Status: Listening for incoming OTP..._\n"
            "⚠️ _(Do not close this menu until OTP arrives)_"
        )
        
        otp_link = get_config("otp_group_link", "https://t.me/FreeOtpMaster")
        allocated_markup = types.InlineKeyboardMarkup(row_width=2)
        allocated_markup.add(
            types.InlineKeyboardButton("🔄 Change Target", callback_data=f"srv_{service_name}", style="danger"),
            types.InlineKeyboardButton("↗️ View OTP Group", url=otp_link, style="primary")
        )
        allocated_markup.add(types.InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_services", style="danger"))
        allocated_markup.add(types.InlineKeyboardButton("❌ Close", callback_data="cancel_step", style="danger"))
        
        success_msg = bot.send_message(chat_id, allocated_ui, reply_markup=allocated_markup)
        threading.Thread(target=free_poll_otp_thread, args=(chat_id, success_msg.message_id, allocated_number, service_name, user_id, active_panel['base_url'], active_panel['api_key']), daemon=True).start()

    else:
        threading.Thread(target=threaded_getnum_retry, args=(chat_id, user_id, service_name, country_node, s_row, loading_msg.message_id), daemon=True).start()
def free_poll_otp_thread(chat_id, message_id, allocated_number, service_name, user_id, base_url, api_key):
    start_time = time.time()
    check_url = f"{base_url}/success-otp" if "@public" in base_url else f"{base_url}/v1/numsuccess/info"
    country_name, country_flag, country_code = get_country_info(allocated_number)

    while time.time() - start_time < 450:
        try:
            res_raw = http_session.get(check_url, headers=get_api_headers(api_key), timeout=8)
            with open("poll_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n[{time.time()}] {check_url} | num: {allocated_number} | resp: {res_raw.text}")
                
            try:
                res = res_raw.json()
            except ValueError:
                time.sleep(2)
                continue
            
            if res_raw.status_code == 200 and isinstance(res, dict) and res.get("meta", {}).get("status") in ["success", "ok"]:
                otp_list = res.get("data", {}).get("otps", [])
                
                for item in otp_list:
                    num_val = str(item.get("number") or item.get("phone") or item.get("phone_number") or "")
                    if num_val in str(allocated_number) or str(allocated_number) in num_val:
                        raw_sms = str(item.get("otp") or item.get("sms") or item.get("message") or "")
                        otp_digits = re.search(r'\b\d{4,8}\b', raw_sms)
                        otp_code = otp_digits.group(0) if otp_digits else "".join(re.findall(r'\d+', raw_sms))[:6]
                        
                        reward_amt = float(get_config("reward_amount", 0.0002))
                        commission = float(get_config("ref_commission", 0.01))
                        
                        db.users.update_one({"user_id": user_id}, {"$inc": {"balance": reward_amt, "completed_otps": 1}})
                        u_data = db.users.find_one({"user_id": user_id})
                        
                        tot_otps = int(get_config("total_otps_processed", 0)) + 1
                        set_config("total_otps_processed", str(tot_otps))
                        
                        panel_doc = db.panels.find_one({"base_url": base_url})
                        pname = panel_doc["panel_name"] if panel_doc else "Unknown"
                        db.otps_history.insert_one({"user_id": user_id, "service": service_name, "timestamp": time.time(), "date": time.strftime('%Y-%m-%d'), "panel": pname})
                        
                        referred_by = u_data.get('referred_by') if u_data else None
                        if referred_by:
                            db.users.update_one({"user_id": referred_by}, {"$inc": {"balance": commission}})
                            db.ref_history.insert_one({"referrer_id": referred_by, "amount": commission, "timestamp": time.time()})
                            
                        current_balance = u_data['balance']
                        premium_ui_msg = (
                            "╔════════════════════════╗\n"
                            "       📩  *NEW OTP RECEIVED* 📩\n"
                            "╚════════════════════════╝\n"
                            f"🌐 *Origin:* {country_flag} {country_name}\n"
                            f"📱 *Phone:* `{allocated_number}`\n"
                            "──────────────────────────\n"
                            f"🔑 *OTP CODE:* `{otp_code}`\n"
                            "──────────────────────────\n"
                            f"⚡ *Service:* {service_name.upper()}\n"
                            f"💰 *Node Bounty:* +{reward_amt:.4f} ৳\n"
                            f"💵 *Net Wallet Balance:* {current_balance:.4f} ৳\n"
                            "──────────────────────────"
                        )
                        
                        try: bot.edit_message_text(premium_ui_msg, chat_id, message_id)
                        except: bot.send_message(chat_id, premium_ui_msg)
                        safe_sms = raw_sms.replace("`", "'")
                        user_otp_msg = (
                            f"✅ *SUCCESSFULLY RECEIVED OTP*\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"📱 *Number:* `{allocated_number}`\n"
                            f"🌍 *Country:* {country_flag} {country_name}\n"
                            f"⚡ *Service:* {service_name.upper()}\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"💬 *SMS Message:*\n"
                            f"`{safe_sms}`\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"👇 _Click the button below to copy OTP_"
                        )
                        otp_markup = types.InlineKeyboardMarkup(row_width=2)
                        otp_markup.add(
                            types.InlineKeyboardButton(f"🟦 Copy OTP: {otp_code}", copy_text=types.CopyTextButton(text=otp_code, style="success"))
                        )
                        otp_group_link = get_config("otp_group_link", "https://t.me/FreeOtpMaster")
                        otp_markup.add(
                            types.InlineKeyboardButton("🟩 Get Another Number", callback_data=f"sel_{service_name}_AUTO-BEST", style="primary"),
                            types.InlineKeyboardButton("📢 OTP GROUP", url=otp_group_link, style="primary")
                        )
                        try: bot.send_message(int(user_id), user_otp_msg, reply_markup=otp_markup, parse_mode="Markdown")
                        except: pass
                        
                        icon = "📸" if "instagram" in service_name.lower() else "📘" if "facebook" in service_name.lower() else "💬"
                        group_msg = (
                            f"🌟 *NEW OTP INTERCEPTED* 🌟\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"🌍 *Region:* {country_flag} {country_name}\n"
                            f"📱 *Service:* {icon} {service_name.upper()}\n"
                            f"📞 *Number:* `{allocated_number}`\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"💬 *SMS:*\n"
                            f"`{safe_sms}`\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"⚡ *Secured by FreeOtpMaster* ⚡"
                        )
                        
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        markup.add(types.InlineKeyboardButton(text=f"📋 CODE: {otp_code}", copy_text=types.CopyTextButton(text=otp_code, style="primary")))
                        markup.add(types.InlineKeyboardButton(text="📞 VIEW BOT", url=f"https://t.me/{BOT_USERNAME}", style="success"))
                        
                        otp_group_id = get_config("otp_group_id", str(FORWARD_GROUP_ID))
                        try: bot.send_message(int(otp_group_id), group_msg, reply_markup=markup, parse_mode="Markdown")
                        except: pass
                        return
        except Exception as poll_err:
            logger.error(f"OTP Poll Error: {poll_err}")
        time.sleep(2)  
    
    try: bot.edit_message_text("🔴 *Session Timeout!* Node failed.", chat_id, message_id)
    except: pass

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


def auto_route_updater_thread():
    previous_tops = {}
    try:
        for s in db.services.distinct("service_name"):
            top = db.services.find_one({"service_name": s}, sort=[("hits", -1)])
            if top: previous_tops[s] = top['range']
    except: pass

    while True:
        try:
            seen_routes = []
            zenex_panel = db.panels.find_one({"panel_name": "Zenex", "is_active": True})
            if zenex_panel:
                base = zenex_panel['base_url'].rstrip('/')
                res = http_session.get(base + '/v1/active-ranges', headers={'mapikey': zenex_panel['api_key']}, timeout=10).json()
                active_ranges = res.get("data", {}).get("active_ranges", [])
                for route in active_ranges:
                    service_name = str(route.get("service", ""))
                    target_range = str(route.get("range", ""))
                    hits = int(route.get("hits", 0))
                    if not service_name or not target_range: continue
                    clean_range = target_range.replace("X", "0").replace("x", "0")
                    try:
                        from panel import get_country_info
                        name, flag, _ = get_country_info("+" + clean_range + "0000000")
                        short_name = name.split()[0][:8] if name else "Unknown"
                        c_name = f"{flag} {short_name} | 🔥 hits {hits}"
                    except:
                        c_name = f"🔥 hits {hits}"
                    db.services.update_one(
                        {"service_name": service_name, "range": target_range},
                        {"$set": {"country_name": c_name, "panel_name": "Zenex", "hits": hits}},
                        upsert=True
                    )
                    seen_routes.append({"service_name": service_name, "range": target_range})
            
            stex_panel = db.panels.find_one({"base_url": {"$regex": "@public"}, "is_active": True}) or db.panels.find_one({"panel_name": {"$regex": "Stexsms", "$options": "i"}, "is_active": True})
            if stex_panel:
                base = stex_panel['base_url'].rstrip('/')
                if "@public/api" in base:
                    base_v1 = base.replace("@public/api", "api")
                else:
                    base_v1 = base
                
                headers = {'mauthapi': stex_panel['api_key'], 'mapikey': stex_panel['api_key']}
                try:
                    res = http_session.get(base_v1 + '/v1/active-ranges', headers=headers, timeout=10).json()
                    active_ranges = res.get("data", {}).get("active_ranges") if res else []
                    
                    if not active_ranges:
                        try: res = http_session.get(base + '/console', headers=headers, timeout=10).json()
                        except: res = {}
                        otps = res.get("data", {}).get("hits") or res.get("data", {}).get("otps", [])
                        range_counts = {}
                        service_map = {}
                        for otp in otps:
                            sid = str(otp.get("sid", "")).lower()
                            msg = str(otp.get("message", "")).lower()
                            if "facebook" in sid: s_name = "Instagram" if "instagram" in msg else "Facebook"
                            elif "instagram" in sid: s_name = "Instagram"
                            else: continue
                            tr = str(otp.get("range", ""))
                            if not tr: continue
                            range_counts[tr] = range_counts.get(tr, 0) + 1
                            service_map[tr] = s_name
                        active_ranges = [{"service": service_map[tr], "range": tr, "hits": hits} for tr, hits in range_counts.items()]
                        
                    for route in active_ranges:
                        service_name = str(route.get("service", ""))
                        if not service_name:
                            sid = str(route.get("sid", "")).lower()
                            if "facebook" in sid: service_name = "Facebook"
                            elif "instagram" in sid: service_name = "Instagram"
                            
                        target_range = str(route.get("range", ""))
                        hits = int(route.get("hits", route.get("success", route.get("count", 0))))
                        if not service_name or not target_range: continue
                        
                        clean_range = target_range.replace("X", "0").replace("x", "0")
                        try:
                            from panel import get_country_info
                            name, flag, _ = get_country_info("+" + clean_range + "0000000")
                            short_name = name.split()[0][:8] if name else "Unknown"
                            c_name = f"{flag} {short_name} | 🔥 hits {hits}" if hits else f"{flag} {short_name} | Auto"
                        except:
                            c_name = f"🔥 hits {hits}" if hits else f"Auto: {target_range}"
                            
                        db.services.update_one(
                            {"service_name": service_name, "range": target_range},
                            {"$set": {"country_name": c_name, "panel_name": stex_panel['panel_name'], "hits": hits}},
                            upsert=True
                        )
                        seen_routes.append({"service_name": service_name, "range": target_range})
                except:
                    pass
            
            if seen_routes:
                all_services = db.services.find({})
                for srv in all_services:
                    if {"service_name": srv.get("service_name"), "range": srv.get("range")} not in seen_routes:
                        db.services.delete_one({"_id": srv["_id"]})
            
            try:
                for s in db.services.distinct("service_name"):
                    new_top = db.services.find_one({"service_name": s}, sort=[("hits", -1)])
                    if not new_top: continue
                    
                    old_top_range = previous_tops.get(s)
                    new_top_range = new_top['range']
                    new_hits = new_top.get('hits', 0)
                    
                    if old_top_range and old_top_range != new_top_range and new_hits >= 20:
                        c_part = new_top.get('country_name', '').split(" | ")[0]
                        msg = f"🔥 *HOT ROUTE ALERT*\n\n🌍 *সার্ভিস:* `{s}`\n🚀 বর্তমানে *{c_part}* এ সবচেয়ে ভালো OTP দিচ্ছে! সবাই এই নাম্বারে কাজ করুন।"
                        otp_group_id = get_config("otp_group_id", str(FORWARD_GROUP_ID))
                        try: bot.send_message(int(otp_group_id), msg, parse_mode="Markdown")
                        except: pass
                        previous_tops[s] = new_top_range
                    elif not old_top_range:
                        previous_tops[s] = new_top_range
            except Exception as ex:
                logger.error(f"Alert Error: {ex}")
                
        except Exception as e:
            logger.error(f"Auto Route Updater Error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    logger.info("=============================================")
    logger.info("⚡ ZENEX GLOBAL MULTI-MATRIX V8.0 ONLINE (ULTIMATE UI)")
    logger.info("=============================================")
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=auto_route_updater_thread, daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)

def process_custom_range_input(message, service_name):
    target_range = message.text.strip()
    class FakeCall:
        def __init__(self, message, data):
            self.message = message
            self.from_user = message.from_user
            self.data = data
            self.id = "0"
    
    fake_call = FakeCall(message, f"sel_{service_name}_RANGE-{target_range}")
    handle_country_and_purchase(fake_call)

