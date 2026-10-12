# -*- coding: utf-8 -*-
"""
🎮 FC MOBILE ACCOUNTS BOT - v4.0 FINAL
جميع الميزات: إحالة بالنقاط | سحوبات | قرعة | مكافأة يومية | مستويات |
لوحة متصدرين | تقييم | حالة حساب | حظر | لوحة تحكم كاملة | اشتراك إجباري
"""

import telebot
from telebot import types
import json
import os
import random
import time
from datetime import datetime

# ==================== الإعدادات ====================
API_TOKEN = "8980194257:AAF4z4f1mAhuwfEY4IaxSFJA66DNRQ53hWs"
DEVELOPER_CHAT_ID = 8411461248
BOT_USERNAME = "V_7_a1"

bot = telebot.TeleBot(API_TOKEN)

# ==================== قاعدة البيانات ====================
DATA_DIR = "bot_data"
os.makedirs(DATA_DIR, exist_ok=True)


def load_json(name, default=None):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(name, data):
    path = os.path.join(DATA_DIR, f"{name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


users = load_json("users", {})
channels = load_json("channels", [])
giveaways = load_json("giveaways", {})
settings = load_json("settings", {
    "referral_points": 1,
    "points_for_account": 5,
    "force_sub_enabled": False,
    "welcome_bonus": 0,
})
user_data = {}


def save_all():
    save_json("users", users)
    save_json("channels", channels)
    save_json("giveaways", giveaways)
    save_json("settings", settings)


def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "id": uid,
            "username": "",
            "first_name": "",
            "points": 0,
            "referrals": [],
            "referred_by": None,
            "joined_at": datetime.now().isoformat(),
        }
    return users[uid]


def user_tag(message):
    return f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"


# ==================== الحظر ====================
def is_banned(uid):
    banned = load_json("banned", {})
    return str(uid) in banned


def ban_user(uid, reason=""):
    banned = load_json("banned", {})
    banned[str(uid)] = {"reason": reason, "at": datetime.now().isoformat()}
    save_json("banned", banned)


def unban_user(uid):
    banned = load_json("banned", {})
    banned.pop(str(uid), None)
    save_json("banned", banned)


# ==================== المستويات ====================
def get_level(points):
    if points < 5:
        return "🥉 برونزي"
    elif points < 15:
        return "🥈 فضي"
    elif points < 30:
        return "🥇 ذهبي"
    elif points < 50:
        return "💎 ماسي"
    else:
        return "👑 أسطوري"


# ==================== الاشتراك الإجباري ====================
def check_subscription(user_id):
    if not settings.get("force_sub_enabled") or not channels:
        return []
    not_joined = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(ch)
        except Exception:
            continue
    return not_joined


def sub_required_markup(not_joined):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in not_joined:
        markup.add(types.InlineKeyboardButton(f"📢 {ch['title']}", url=ch["url"]))
    markup.add(types.InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub_again"))
    return markup


def require_subscription(func):
    def wrapper(call):
        uid = call.from_user.id
        if is_banned(uid):
            bot.answer_callback_query(call.id, "🚫 أنت محظور", show_alert=True)
            return
        not_joined = check_subscription(uid)
        if not_joined:
            bot.answer_callback_query(call.id, "⚠️ يجب الاشتراك بالقنوات أولاً", show_alert=True)
            bot.send_message(call.message.chat.id,
                             "⚠️ *يجب الاشتراك بالقنوات التالية أولاً:*",
                             parse_mode="Markdown",
                             reply_markup=sub_required_markup(not_joined))
            return
        return func(call)
    return wrapper


# ==================== القوائم ====================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 شراء حساب", callback_data="menu_buy"),
        types.InlineKeyboardButton("💸 بيع حساب", callback_data="start_sell"),
    )
    markup.add(
        types.InlineKeyboardButton("🔄 تبديل حسابات", callback_data="menu_swap"),
        types.InlineKeyboardButton("📊 استعراض تشكيلات", callback_data="menu_lineups"),
    )
    markup.add(
        types.InlineKeyboardButton("🎁 السحوبات", callback_data="menu_giveaways"),
        types.InlineKeyboardButton("🎰 القرعة", callback_data="menu_lottery"),
    )
    markup.add(
        types.InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="menu_referral"),
        types.InlineKeyboardButton("🏆 نقاطي", callback_data="menu_my_points"),
    )
    markup.add(
        types.InlineKeyboardButton("👤 ملفي الشخصي", callback_data="menu_profile"),
        types.InlineKeyboardButton("🥇 المتصدرون", callback_data="menu_leaderboard"),
    )
    markup.add(
        types.InlineKeyboardButton("⭐ قيّم البوت", callback_data="menu_rate"),
        types.InlineKeyboardButton("🎁 مكافأة يومية", callback_data="menu_daily"),
    )
    markup.add(
        types.InlineKeyboardButton("📋 حالة حسابي", callback_data="menu_my_account"),
    )
    markup.add(
        types.InlineKeyboardButton("📞 الدعم", callback_data="menu_support"),
        types.InlineKeyboardButton("📦 أقسام أخرى", callback_data="menu_other"),
    )
    markup.add(types.InlineKeyboardButton("ℹ️ عن البوت", callback_data="menu_about"))
    return markup


def cancel_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="go_home"))
    return markup


def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home"))
    return markup


# ==================== /start ====================
@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id

    if is_banned(chat_id):
        bot.send_message(chat_id, "🚫 أنت محظور من استخدام البوت.")
        return

    args = message.text.split()
    user_data[chat_id] = {}

    u = get_user(chat_id)
    u["username"] = message.from_user.username or ""
    u["first_name"] = message.from_user.first_name or ""

    # معالجة الإحالة
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = args[1][4:]
        if referrer_id != str(chat_id) and u["referred_by"] is None:
            if referrer_id in users:
                u["referred_by"] = referrer_id
                if str(chat_id) not in users[referrer_id]["referrals"]:
                    users[referrer_id]["referrals"].append(str(chat_id))
                    users[referrer_id]["points"] += settings.get("referral_points", 1)
                    try:
                        bot.send_message(
                            int(referrer_id),
                            f"🎉 *شخص جديد انضم عبر رابطك!*\n"
                            f"💰 +{settings.get('referral_points', 1)} نقطة\n"
                            f"🏆 رصيدك: {users[referrer_id]['points']}",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
    save_all()

    not_joined = check_subscription(chat_id)
    if not_joined:
        bot.send_message(
            chat_id,
            "⚠️ *مرحباً بك!*\n\nللوصول إلى البوت، يجب الاشتراك بالقنوات التالية:",
            parse_mode="Markdown",
            reply_markup=sub_required_markup(not_joined),
        )
        return

    welcome_text = (
        "🎮 *مرحباً بك في بوت بيع وشراء حسابات FC Mobile* ⚽\n\n"
        "🔥 وجهتك الأولى لعشاق فيفا موبايل!\n\n"
        "💰 *خدماتنا:*\n"
        "• 🛒 شراء حسابات فيفا\n"
        "• 💸 بيع حسابك بكل سهولة\n"
        "• 🔄 تبديل الحسابات\n"
        "• 📊 استعراض التشكيلات\n"
        "• 🎁 سحوبات وجوائز مجانية\n"
        "• 🎰 قرعة أسبوعية\n"
        "• 👥 اجمع نقاط بدعوة أصدقائك\n\n"
        "🚀 *اختر من القائمة:*"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=main_menu())


@bot.callback_query_handler(func=lambda c: c.data == "check_sub_again")
def check_sub_again(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    not_joined = check_subscription(uid)
    if not_joined:
        bot.send_message(call.message.chat.id, "❌ لم تشترك بكل القنوات بعد.",
                         reply_markup=sub_required_markup(not_joined))
    else:
        bot.send_message(call.message.chat.id, "✅ تم التحقق! أرسل /start للبدء.",
                         reply_markup=main_menu())


@bot.callback_query_handler(func=lambda c: c.data == "go_home")
def go_home(call):
    bot.answer_callback_query(call.id)
    user_data[call.message.chat.id] = {}
    bot.send_message(call.message.chat.id, "🎮 *القائمة الرئيسية*",
                     parse_mode="Markdown", reply_markup=main_menu())


# ==================== السحوبات ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_giveaways")
@require_subscription
def menu_giveaways(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    active = {gid: g for gid, g in giveaways.items() if g.get("active")}
    if not active:
        bot.send_message(
            chat_id,
            "🎁 *قسم السحوبات*\n\nلا توجد سحوبات نشطة حالياً.\nترقب الجوائز القادمة! 🔥",
            parse_mode="Markdown",
            reply_markup=back_button(),
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for gid, g in active.items():
        markup.add(types.InlineKeyboardButton(
            f"🎁 {g['title']} | 🏆 {g['prize']}",
            callback_data=f"join_gw_{gid}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home"))

    bot.send_message(
        chat_id,
        "🎁 *السحوبات النشطة*\n\nاختر السحب للمشاركة:",
        parse_mode="Markdown",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("join_gw_"))
def join_giveaway(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    gid = call.data.replace("join_gw_", "")
    bot.answer_callback_query(call.id)

    if gid not in giveaways:
        bot.send_message(chat_id, "❌ السحب غير موجود.")
        return

    g = giveaways[gid]
    if not g.get("active"):
        bot.send_message(chat_id, "❌ هذا السحب مغلق.")
        return

    if uid in g["participants"]:
        bot.send_message(chat_id, "ℹ️ أنت مشارك بالفعل!",
                         reply_markup=back_button())
        return

    g["participants"].append(uid)
    save_all()

    bot.send_message(
        chat_id,
        f"✅ *تم تسجيلك في السحب!*\n\n"
        f"🎁 السحب: {g['title']}\n"
        f"🏆 الجائزة: {g['prize']}\n"
        f"👥 المشاركون: {len(g['participants'])}\n\n"
        f"بالتوفيق! 🍀",
        parse_mode="Markdown",
        reply_markup=back_button(),
    )

    bot.send_message(
        DEVELOPER_CHAT_ID,
        f"🎁 *مشاركة جديدة*\n"
        f"السحب: {g['title']}\n"
        f"👤 {user_tag(call.message)}",
        parse_mode="Markdown"
    )


# ==================== القرعة ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_lottery")
@require_subscription
def menu_lottery(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        chat_id,
        "🎰 *قسم القرعة*\n\n"
        "📝 أرسل *اسمك الكامل* للمشاركة في القرعة.\n"
        "سيتم اختيار الفائز عشوائياً 🍀\n\n"
        "✍️ أرسل اسمك الآن:",
        parse_mode="Markdown",
        reply_markup=cancel_menu(),
    )
    bot.register_next_step_handler(msg, receive_lottery_name)


def receive_lottery_name(message):
    chat_id = message.chat.id
    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        bot.send_message(chat_id, "❌ الرجاء إرسال اسم صحيح.")
        return

    lottery = load_json("lottery", {"participants": []})
    lottery["participants"].append({
        "user_id": str(chat_id),
        "name": name,
        "username": message.from_user.username or "",
        "at": datetime.now().isoformat(),
    })
    save_json("lottery", lottery)

    bot.send_message(
        DEVELOPER_CHAT_ID,
        f"🎰 *مشاركة جديدة في القرعة*\n\n"
        f"👤 الاسم: {name}\n"
        f"🔗 {user_tag(message)}\n"
        f"🆔 {chat_id}\n"
        f"📊 المجموع: {len(lottery['participants'])}",
        parse_mode="Markdown"
    )

    bot.send_message(
        chat_id,
        f"✅ *تم تسجيل اسمك!*\n\n"
        f"📝 اسمك: {name}\n"
        f"🍀 بالتوفيق!",
        parse_mode="Markdown",
        reply_markup=back_button(),
    )


# ==================== الإحالة ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_referral")
@require_subscription
def menu_referral(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)

    u = get_user(uid)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"

    text = (
        "👥 *نظام الإحالة*\n\n"
        f"🔗 *رابطك:*\n`{link}`\n\n"
        f"📊 *إحصائياتك:*\n"
        f"• 👥 المدعوون: {len(u['referrals'])}\n"
        f"• 🏆 نقاطك: {u['points']}\n\n"
        f"💰 كل شخص = +{settings.get('referral_points', 1)} نقطة\n"
        f"🎁 عند {settings.get('points_for_account', 5)} نقاط → حساب مجاني!"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(
        "📤 مشاركة الرابط",
        url=f"https://t.me/share/url?url={link}&text=انضم لبوت FC Mobile!"
    ))
    if u["points"] >= settings.get("points_for_account", 5):
        markup.add(types.InlineKeyboardButton("🎁 طلب حساب بالنقاط", callback_data="redeem_account"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home"))

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == "menu_my_points")
@require_subscription
def menu_my_points(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)

    u = get_user(uid)
    needed = settings.get("points_for_account", 5)
    bot.send_message(
        chat_id,
        f"🏆 *نقاطك*\n\n"
        f"💰 النقاط: *{u['points']}*\n"
        f"👥 المدعوون: *{len(u['referrals'])}*\n"
        f"🎯 المطلوب: *{needed}*\n\n"
        f"📊 التقدم: {u['points']}/{needed}",
        parse_mode="Markdown",
        reply_markup=back_button(),
    )


@bot.callback_query_handler(func=lambda c: c.data == "redeem_account")
def redeem_account(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)

    u = get_user(uid)
    needed = settings.get("points_for_account", 5)
    if u["points"] < needed:
        bot.send_message(chat_id, f"❌ تحتاج {needed} نقطة.")
        return

    u["points"] -= needed
    save_all()

    bot.send_message(
        DEVELOPER_CHAT_ID,
        f"🎁 *طلب استبدال نقاط بحساب*\n\n"
        f"👤 {user_tag(call.message)}\n"
        f"🆔 {uid}\n"
        f"💰 النقاط المتبقية: {u['points']}",
        parse_mode="Markdown"
    )
    bot.send_message(
        chat_id,
        f"✅ *تم إرسال طلبك!*\n"
        f"سيتواصل معك المطور.\n"
        f"💰 رصيدك: {u['points']}",
        reply_markup=back_button(),
    )


# ==================== الملف الشخصي ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_profile")
@require_subscription
def menu_profile(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)

    u = get_user(uid)
    level = get_level(u["points"])
    total_users = len(users)
    sorted_u = sorted(users.values(), key=lambda x: x["points"], reverse=True)
    rank = next((i for i, x in enumerate(sorted_u, 1) if x["id"] == uid), "-")

    text = (
        f"👤 *ملفي الشخصي*\n\n"
        f"🆔 `{uid}`\n"
        f"📛 {u.get('first_name', '-')}\n"
        f"🔗 @{u.get('username', 'N/A')}\n\n"
        f"💰 النقاط: {u['points']}\n"
        f"👥 المدعوون: {len(u['referrals'])}\n"
        f"⭐ المستوى: {level}\n"
        f"🏅 الترتيب: {rank} من {total_users}"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=back_button())


# ==================== لوحة المتصدرين ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_leaderboard")
@require_subscription
def menu_leaderboard(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    sorted_u = sorted(users.values(), key=lambda x: x["points"], reverse=True)[:10]
    text = "🏆 *لوحة المتصدرين*\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, u in enumerate(sorted_u, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = f"@{u['username']}" if u.get("username") else f"ID:{u['id']}"
        text += f"{medal} {name}\n   💰 {u['points']} | 👥 {len(u['referrals'])} | {get_level(u['points'])}\n\n"

    if not sorted_u:
        text += "لا يوجد مستخدمون بعد."

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=back_button())


# ==================== التقييم ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_rate")
@require_subscription
def menu_rate(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=5)
    markup.add(*[
        types.InlineKeyboardButton("⭐" * i, callback_data=f"rate_{i}")
        for i in range(1, 6)
    ])
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home"))

    bot.send_message(chat_id, "⭐ *قيّم تجربتك*\n\nاختر النجوم:",
                     parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("rate_"))
def process_rate(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    stars = int(call.data.replace("rate_", ""))
    bot.answer_callback_query(call.id, f"شكراً! {stars} ⭐")

    ratings = load_json("ratings", {})
    ratings[uid] = {"stars": stars, "at": datetime.now().isoformat()}
    save_json("ratings", ratings)

    bot.send_message(
        DEVELOPER_CHAT_ID,
        f"⭐ *تقييم جديد*\n👤 {user_tag(call.message)}\n⭐ {stars}/5",
        parse_mode="Markdown"
    )

    avg = sum(r["stars"] for r in ratings.values()) / len(ratings)
    bot.send_message(
        chat_id,
        f"✅ *شكراً!*\n\n"
        f"⭐ تقييمك: {stars}/5\n"
        f"📊 المتوسط العام: {avg:.1f}/5\n"
        f"👥 عدد المقيّمين: {len(ratings)}",
        parse_mode="Markdown",
        reply_markup=back_button()
    )


# ==================== المكافأة اليومية ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_daily")
@require_subscription
def menu_daily_cb(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)

    u = get_user(uid)
    last = u.get("last_daily", 0)
    now = time.time()

    if now - last < 86400:
        remaining = 86400 - (now - last)
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        bot.send_message(chat_id, f"⏳ *عُد بعد:* {h}h {m}m",
                         parse_mode="Markdown", reply_markup=back_button())
        return

    u["last_daily"] = now
    u["points"] += 1
    save_all()

    bot.send_message(chat_id,
                     f"🎁 *مبروك!*\n\n💰 +1 نقطة\n🏆 رصيدك: {u['points']}",
                     parse_mode="Markdown", reply_markup=back_button())


# ==================== حالة حسابي ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_my_account")
@require_subscription
def menu_my_account(call):
    chat_id = call.message.chat.id
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)

    accounts = load_json("accounts", {})
    if uid not in accounts:
        bot.send_message(
            chat_id,
            "📋 *لا يوجد لديك حساب معروض.*\n\nلعرض حسابك اختر 💸 بيع حساب",
            parse_mode="Markdown",
            reply_markup=back_button()
        )
        return

    acc = accounts[uid]
    status_emoji = {
        "pending": "⏳ قيد المراجعة",
        "listed": "🟢 معروض للبيع",
        "sold": "✅ تم بيعه",
        "rejected": "❌ مرفوض"
    }.get(acc.get("status", "pending"), "غير معروف")

    bot.send_message(
        chat_id,
        f"📋 *حالة حسابك*\n\n"
        f"📌 الحالة: {status_emoji}\n"
        f"📅 تاريخ: {acc.get('listed_at', '-')[:10]}\n"
        f"💳 الدفع: {acc.get('price', 'غير محدد')}",
        parse_mode="Markdown",
        reply_markup=back_button()
    )


# ==================== الأقسام القديمة ====================
@bot.callback_query_handler(func=lambda c: c.data == "menu_buy")
@require_subscription
def menu_buy(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        chat_id,
        "🛒 *شراء الحسابات*\n\nأرسل مواصفات الحساب:\n"
        "• 💰 الميزانية\n• ⭐ التقييم\n• 🏆 البطولات\n• 🌍 المنطقة\n\n👇 أرسل الآن:",
        parse_mode="Markdown", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_buy_request)


def receive_buy_request(message):
    chat_id = message.chat.id
    bot.send_message(DEVELOPER_CHAT_ID,
                     f"🛒 *طلب شراء*\n👤 {user_tag(message)}\n🆔 {chat_id}",
                     parse_mode="Markdown")
    bot.forward_message(DEVELOPER_CHAT_ID, chat_id, message.message_id)
    bot.send_message(chat_id, "✅ تم استلام طلب الشراء!", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "menu_swap")
@require_subscription
def menu_swap(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id,
                           "🔄 *تبديل الحسابات*\n\nأرسل التفاصيل:",
                           parse_mode="Markdown", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_swap_request)


def receive_swap_request(message):
    chat_id = message.chat.id
    bot.send_message(DEVELOPER_CHAT_ID,
                     f"🔄 *طلب تبديل*\n👤 {user_tag(message)}\n🆔 {chat_id}",
                     parse_mode="Markdown")
    bot.forward_message(DEVELOPER_CHAT_ID, chat_id, message.message_id)
    bot.send_message(chat_id, "✅ تم الاستلام!", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "menu_lineups")
@require_subscription
def menu_lineups(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id,
                           "📊 *استعراض التشكيلات*\n\nأرسل صورة/وصف:",
                           parse_mode="Markdown", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_lineup)


def receive_lineup(message):
    chat_id = message.chat.id
    bot.send_message(DEVELOPER_CHAT_ID,
                     f"📊 *تشكيلة*\n👤 {user_tag(message)}\n🆔 {chat_id}",
                     parse_mode="Markdown")
    bot.forward_message(DEVELOPER_CHAT_ID, chat_id, message.message_id)
    bot.send_message(chat_id, "✅ تم الإرسال!", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "menu_support")
@require_subscription
def menu_support(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id, "📞 *الدعم*\n\nأرسل رسالتك:",
                           parse_mode="Markdown", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_support)


def receive_support(message):
    chat_id = message.chat.id
    bot.send_message(DEVELOPER_CHAT_ID,
                     f"📞 *دعم*\n👤 {user_tag(message)}\n🆔 {chat_id}",
                     parse_mode="Markdown")
    bot.forward_message(DEVELOPER_CHAT_ID, chat_id, message.message_id)
    bot.send_message(chat_id, "✅ تم الإرسال!", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "menu_other")
@require_subscription
def menu_other(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚠️ الإبلاغ عن مشكلة", callback_data="other_report"),
        types.InlineKeyboardButton("💡 اقتراح", callback_data="other_suggest"),
        types.InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="other_faq"),
        types.InlineKeyboardButton("📜 القوانين", callback_data="other_rules"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="go_home"),
    )
    bot.send_message(chat_id, "📦 *أقسام أخرى*", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == "other_report")
def other_report(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "⚠️ اكتب المشكلة:", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, _handle_other_generic, "⚠️ إبلاغ")


@bot.callback_query_handler(func=lambda c: c.data == "other_suggest")
def other_suggest(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💡 اكتب اقتراحك:", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, _handle_other_generic, "💡 اقتراح")


def _handle_other_generic(message, title):
    chat_id = message.chat.id
    bot.send_message(DEVELOPER_CHAT_ID,
                     f"*{title}*\n👤 {user_tag(message)}\n🆔 {chat_id}",
                     parse_mode="Markdown")
    bot.forward_message(DEVELOPER_CHAT_ID, chat_id, message.message_id)
    bot.send_message(chat_id, "✅ تم الإرسال!", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "other_faq")
def other_faq(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "❓ *الأسئلة الشائعة*\n\n"
        "1️⃣ بيع حساب؟ → 💸 بيع حساب\n"
        "2️⃣ جمع نقاط؟ → ادعُ أصدقاءك\n"
        "3️⃣ حساب مجاني؟ → 5 نقاط\n"
        "4️⃣ سحوبات؟ → 🎁 السحوبات\n"
        "5️⃣ قرعة؟ → 🎰 القرعة",
        parse_mode="Markdown", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "other_rules")
def other_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "📜 *القوانين*\n\n"
        "• 🚫 ممنوع الغش\n• ✅ تأكد من البيانات\n"
        "• 🤝 البوت وسيط فقط\n• 📵 ممنوع الإزعاج\n"
        "• ⚠️ المخالفة = حظر",
        parse_mode="Markdown", reply_markup=back_button())


@bot.callback_query_handler(func=lambda c: c.data == "menu_about")
def menu_about(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "ℹ️ *عن البوت*\n\n"
        "🎮 FC Mobile Accounts Bot\n"
        "الإصدار: *v4.0 FINAL*\n\n"
        "👨‍💻 المطور: @YourUsername\n\n"
        "✨ الميزات:\n"
        "شراء • بيع • تبديل • استعراض\n"
        "سحوبات • قرعة • نقاط • مستويات\n"
        "تقييم • متصدرون • مكافأة يومية\n\n"
        "❤️ شكراً لاستخدامك",
        parse_mode="Markdown", reply_markup=back_button())


# ==================== مسار البيع ====================
@bot.callback_query_handler(func=lambda c: c.data == "start_sell")
@require_subscription
def process_sell_click(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        chat_id,
        "💸 *بيع الحساب*\n\nأرسل مواصفات الحساب (نصوص/صور):",
        parse_mode="Markdown", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_specs)


def receive_specs(message):
    chat_id = message.chat.id
    bot.send_message(DEVELOPER_CHAT_ID,
                     f"📥 *طلب بيع جديد!*\nمن: {user_tag(message)}",
                     parse_mode="Markdown")
    bot.forward_message(DEVELOPER_CHAT_ID, chat_id, message.message_id)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ نعم", callback_data="confirm_yes"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="go_home"),
    )
    bot.send_message(chat_id, "هل تريد متابعة البيع؟", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == "confirm_yes")
def ask_captcha(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("5", callback_data="captcha_wrong"),
        types.InlineKeyboardButton("7", callback_data="captcha_correct"),
        types.InlineKeyboardButton("9", callback_data="captcha_wrong"),
    )
    bot.send_message(chat_id, "🤖 اختبار التحقق:\nكم = 3 + 4 ؟", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("captcha_"))
def process_captcha(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    if call.data == "captcha_correct":
        msg = bot.send_message(chat_id, "✅ نجحت!\nأرسل البريد الإلكتروني:",
                               reply_markup=cancel_menu())
        bot.register_next_step_handler(msg, receive_email)
    else:
        bot.send_message(chat_id, "❌ خطأ! أعد /start", reply_markup=back_button())


def receive_email(message):
    chat_id = message.chat.id
    user_data.setdefault(chat_id, {})
    user_data[chat_id]["email"] = message.text
    msg = bot.send_message(chat_id, "🔐 أرسل كلمة المرور:", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_name)


def receive_name(message):
    chat_id = message.chat.id
    user_data.setdefault(chat_id, {})
    user_data[chat_id]["name"] = message.text
    msg = bot.send_message(chat_id, "💳 أرسل طريقة الدفع:", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, receive_payment)


# ⭐⭐⭐ الدالة المعدلة (الرسالة الجديدة) ⭐⭐⭐
def receive_payment(message):
    chat_id = message.chat.id
    user_data.setdefault(chat_id, {})
    user_data[chat_id]["payment"] = message.text

    name = user_data[chat_id].get("name", "-")
    email = user_data[chat_id].get("email", "-")
    payment = user_data[chat_id].get("payment", "-")

    # إرسال التقرير للمطور
    bot.send_message(
        DEVELOPER_CHAT_ID,
        f"📄 *تقرير بيع كامل:*\n\n"
        f"🔐 المرور: {name}\n"
        f"📧 البريد: {email}\n"
        f"💳 الدفع: {payment}\n"
        f"🔗 {user_tag(message)}\n"
        f"🆔 ID: {chat_id}",
        parse_mode="Markdown"
    )

    # حفظ الحساب
    accounts = load_json("accounts", {})
    accounts[str(chat_id)] = {
        "status": "pending",
        "listed_at": datetime.now().isoformat(),
        "price": payment,
    }
    save_json("accounts", accounts)

    # ✅✅✅ الرسالة النهائية الجديدة ✅✅✅
    bot.send_message(
        chat_id,
        "✅ *تم إرسال بياناتك للمطور بنجاح!*\n\n"
        "💸 سوف يتم بيع حسابك قريباً\n"
        "📩 وسيتم التواصل معك مباشرة.\n\n"
        "🙏 شكراً لثقتك بنا!",
        parse_mode="Markdown",
        reply_markup=back_button(),
    )
    user_data.pop(chat_id, None)


# ==================== لوحة تحكم المطور ====================
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.send_message(message.chat.id, "⛔ للمطور فقط.")
        return
    show_admin_panel(message.chat.id)


def show_admin_panel(chat_id, edit_msg_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 إحصائيات", callback_data="adm_stats"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_broadcast"),
    )
    markup.add(
        types.InlineKeyboardButton("📡 القنوات", callback_data="adm_channels"),
        types.InlineKeyboardButton("🎁 السحوبات", callback_data="adm_giveaways"),
    )
    markup.add(
        types.InlineKeyboardButton("🎰 إدارة القرعة", callback_data="adm_lottery"),
        types.InlineKeyboardButton("👥 المستخدمون", callback_data="adm_users"),
    )
    markup.add(
        types.InlineKeyboardButton("💰 النقاط", callback_data="adm_points"),
        types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="adm_settings"),
    )
    markup.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="adm_refresh"))

    text = (
        "👨‍💻 *لوحة تحكم المطور*\n\n"
        f"👥 المستخدمون: {len(users)}\n"
        f"📡 القنوات: {len(channels)}\n"
        f"🎁 السحوبات النشطة: {sum(1 for g in giveaways.values() if g.get('active'))}\n"
        f"🔒 الاشتراك الإجباري: {'✅' if settings.get('force_sub_enabled') else '❌'}\n\n"
        "اختر إجراء:"
    )
    if edit_msg_id:
        try:
            bot.edit_message_text(text, chat_id, edit_msg_id, parse_mode="Markdown", reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_"))
def admin_callbacks(call):
    if call.from_user.id != DEVELOPER_CHAT_ID:
        bot.answer_callback_query(call.id, "⛔")
        return
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data == "adm_refresh":
        show_admin_panel(chat_id, call.message.message_id)
        return

    if data == "adm_stats":
        total_refs = sum(len(u["referrals"]) for u in users.values())
        total_points = sum(u["points"] for u in users.values())
        ratings = load_json("ratings", {})
        avg = sum(r["stars"] for r in ratings.values()) / len(ratings) if ratings else 0
        banned = load_json("banned", {})
        lottery = load_json("lottery", {"participants": []})
        text = (
            "📊 *إحصائيات تفصيلية*\n\n"
            f"👥 المستخدمون: {len(users)}\n"
            f"🔗 الإحالات: {total_refs}\n"
            f"💰 النقاط: {total_points}\n"
            f"🚫 المحظورون: {len(banned)}\n"
            f"⭐ التقييم: {avg:.1f}/5 ({len(ratings)})\n"
            f"🎰 القرعة: {len(lottery['participants'])}\n"
            f"📡 القنوات: {len(channels)}\n"
            f"🎁 السحوبات: {len(giveaways)}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"))
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
        return

    if data == "adm_broadcast":
        msg = bot.send_message(chat_id, "📢 *الإذاعة*\n\nأرسل الرسالة (نص/صورة/فيديو):",
                               parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_do_broadcast)
        return

    if data == "adm_channels":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة قناة", callback_data="adm_ch_add"),
            types.InlineKeyboardButton("➖ حذف قناة", callback_data="adm_ch_del"),
            types.InlineKeyboardButton(
                f"{'🔴 إيقاف' if settings.get('force_sub_enabled') else '🟢 تفعيل'} الاشتراك الإجباري",
                callback_data="adm_ch_toggle"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"),
        )
        text = "📡 *إدارة القنوات*\n\n"
        if channels:
            for i, ch in enumerate(channels, 1):
                text += f"{i}. {ch['title']} - `{ch['chat_id']}`\n"
        else:
            text += "لا توجد قنوات."
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
        return

    if data == "adm_ch_add":
        msg = bot.send_message(
            chat_id,
            "📡 أرسل: `@username | اسم القناة`\n\nالبوت يجب أن يكون أدمن.",
            parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_add_channel)
        return

    if data == "adm_ch_del":
        if not channels:
            bot.send_message(chat_id, "لا توجد قنوات.")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, ch in enumerate(channels):
            markup.add(types.InlineKeyboardButton(f"❌ {ch['title']}", callback_data=f"adm_chd_{i}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_channels"))
        bot.send_message(chat_id, "اختر القناة للحذف:", reply_markup=markup)
        return

    if data.startswith("adm_chd_"):
        idx = int(data.replace("adm_chd_", ""))
        if 0 <= idx < len(channels):
            removed = channels.pop(idx)
            save_all()
            bot.send_message(chat_id, f"✅ تم حذف: {removed['title']}")
        return

    if data == "adm_ch_toggle":
        settings["force_sub_enabled"] = not settings.get("force_sub_enabled", False)
        save_all()
        state = "✅ مفعل" if settings["force_sub_enabled"] else "❌ معطل"
        bot.send_message(chat_id, f"الاشتراك الإجباري: {state}")
        return

    if data == "adm_giveaways":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ إنشاء سحب", callback_data="adm_gw_add"),
            types.InlineKeyboardButton("📋 عرض السحوبات", callback_data="adm_gw_list"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"),
        )
        bot.send_message(chat_id, "🎁 *إدارة السحوبات*", parse_mode="Markdown", reply_markup=markup)
        return

    if data == "adm_gw_add":
        msg = bot.send_message(
            chat_id,
            "🎁 أرسل: `العنوان | الجائزة`\n\nمثال:\n`سحب أسبوعي | حساب ريت 100`",
            parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_create_giveaway)
        return

    if data == "adm_gw_list":
        if not giveaways:
            bot.send_message(chat_id, "لا توجد سحوبات.")
            return
        text = "📋 *السحوبات:*\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for gid, g in giveaways.items():
            status = "🟢" if g.get("active") else "🔴"
            text += f"• {g['title']} | {g['prize']} | {status} | 👥 {len(g['participants'])}\n"
            markup.add(types.InlineKeyboardButton(
                f"🎲 سحب فائز: {g['title']}", callback_data=f"adm_gw_pick_{gid}"))
            markup.add(types.InlineKeyboardButton(
                f"{'🔴 إغلاق' if g.get('active') else '🟢 تفعيل'}: {g['title']}",
                callback_data=f"adm_gw_tog_{gid}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_giveaways"))
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
        return

    if data.startswith("adm_gw_pick_"):
        gid = data.replace("adm_gw_pick_", "")
        if gid not in giveaways or not giveaways[gid]["participants"]:
            bot.send_message(chat_id, "لا يوجد مشاركون.")
            return
        winner_id = random.choice(giveaways[gid]["participants"])
        winner = users.get(winner_id, {})
        winner_name = f"@{winner.get('username', '')}" if winner.get('username') else f"ID: {winner_id}"
        giveaways[gid].setdefault("winners", []).append(winner_id)
        save_all()

        bot.send_message(chat_id, f"🎉 *الفائز:* {winner_name}", parse_mode="Markdown")
        try:
            bot.send_message(
                int(winner_id),
                f"🎉 *مبروك! فزت في السحب!*\n\n"
                f"🎁 {giveaways[gid]['title']}\n"
                f"🏆 {giveaways[gid]['prize']}\n\n"
                f"سيتواصل معك المطور.",
                parse_mode="Markdown")
        except Exception:
            pass
        return

    if data.startswith("adm_gw_tog_"):
        gid = data.replace("adm_gw_tog_", "")
        if gid in giveaways:
            giveaways[gid]["active"] = not giveaways[gid].get("active", True)
            save_all()
            state = "🟢 نشط" if giveaways[gid]["active"] else "🔴 مغلق"
            bot.send_message(chat_id, f"الحالة: {state}")
        return

    if data == "adm_lottery":
        lottery = load_json("lottery", {"participants": []})
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎲 اختيار فائز", callback_data="adm_lot_pick"),
            types.InlineKeyboardButton("📋 عرض المشاركين", callback_data="adm_lot_list"),
            types.InlineKeyboardButton("🗑️ حذف الكل", callback_data="adm_lot_clear"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"),
        )
        bot.send_message(chat_id,
                         f"🎰 *القرعة*\n\n📊 المشاركون: {len(lottery['participants'])}",
                         parse_mode="Markdown", reply_markup=markup)
        return

    if data == "adm_lot_list":
        lottery = load_json("lottery", {"participants": []})
        if not lottery["participants"]:
            bot.send_message(chat_id, "لا يوجد مشاركون.")
            return
        text = "📋 *المشاركون:*\n\n"
        for i, p in enumerate(lottery["participants"][-50:], 1):
            text += f"{i}. {p['name']} (@{p['username'] or 'N/A'})\n"
        bot.send_message(chat_id, text)
        return

    if data == "adm_lot_pick":
        lottery = load_json("lottery", {"participants": []})
        if not lottery["participants"]:
            bot.send_message(chat_id, "لا يوجد مشاركون.")
            return
        winner = random.choice(lottery["participants"])
        bot.send_message(
            chat_id,
            f"🎉 *الفائز!*\n\n"
            f"👤 {winner['name']}\n"
            f"🔗 @{winner['username'] or 'N/A'}\n"
            f"🆔 {winner['user_id']}",
            parse_mode="Markdown")
        try:
            bot.send_message(int(winner['user_id']),
                             "🎉 *مبروك! فزت في القرعة!*\n\nسيتواصل معك المطور.",
                             parse_mode="Markdown")
        except Exception:
            pass
        return

    if data == "adm_lot_clear":
        save_json("lottery", {"participants": []})
        bot.send_message(chat_id, "✅ تم الحذف.")
        return

    if data == "adm_users":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔝 أكثر 10 نقاط", callback_data="adm_top"),
            types.InlineKeyboardButton("📤 تصدير", callback_data="adm_export"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"),
        )
        bot.send_message(chat_id, f"👥 *المستخدمون* ({len(users)})",
                         parse_mode="Markdown", reply_markup=markup)
        return

    if data == "adm_top":
        sorted_u = sorted(users.items(), key=lambda x: x[1]["points"], reverse=True)[:10]
        text = "🏆 *أعلى 10:*\n\n"
        for i, (uid, u) in enumerate(sorted_u, 1):
            name = f"@{u['username']}" if u['username'] else f"ID:{uid}"
            text += f"{i}. {name} → 💰{u['points']} | 👥{len(u['referrals'])}\n"
        bot.send_message(chat_id, text)
        return

    if data == "adm_export":
        try:
            with open(os.path.join(DATA_DIR, "users.json"), "rb") as f:
                bot.send_document(chat_id, f, caption=f"📤 {len(users)} مستخدم")
        except Exception as e:
            bot.send_message(chat_id, f"خطأ: {e}")
        return

    if data == "adm_points":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ إضافة", callback_data="adm_pt_add"),
            types.InlineKeyboardButton("➖ خصم", callback_data="adm_pt_sub"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"),
        )
        bot.send_message(chat_id,
                         f"💰 *النقاط*\n\nنقاط الإحالة: {settings.get('referral_points', 1)}\n"
                         f"نقاط الحساب: {settings.get('points_for_account', 5)}",
                         parse_mode="Markdown", reply_markup=markup)
        return

    if data in ("adm_pt_add", "adm_pt_sub"):
        action = "add" if data == "adm_pt_add" else "sub"
        msg = bot.send_message(chat_id, "أرسل: `USER_ID AMOUNT`\nمثال: `123456789 5`",
                               parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_points_action, action)
        return

    if data == "adm_settings":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(f"💰 نقاط الإحالة: {settings.get('referral_points', 1)}",
                                       callback_data="adm_set_refp"),
            types.InlineKeyboardButton(f"🎁 نقاط الحساب: {settings.get('points_for_account', 5)}",
                                       callback_data="adm_set_ptacc"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="adm_back"),
        )
        bot.send_message(chat_id, "⚙️ *الإعدادات*", parse_mode="Markdown", reply_markup=markup)
        return

    if data in ("adm_set_refp", "adm_set_ptacc"):
        key = "referral_points" if data == "adm_set_refp" else "points_for_account"
        msg = bot.send_message(chat_id, "أرسل القيمة الجديدة (رقم):")
        bot.register_next_step_handler(msg, admin_set_value, key)
        return

    if data == "adm_back":
        show_admin_panel(chat_id, call.message.message_id)
        return


def admin_do_broadcast(message):
    chat_id = message.chat.id
    ok, fail = 0, 0
    status = bot.send_message(chat_id, "⏳ جاري الإرسال...")
    for uid in list(users.keys()):
        try:
            bot.copy_message(int(uid), chat_id, message.message_id)
            ok += 1
        except Exception:
            fail += 1
        time.sleep(0.05)
    bot.edit_message_text(f"✅ تم\n\nنجح: {ok}\nفشل: {fail}", chat_id, status.message_id)


def admin_add_channel(message):
    chat_id = message.chat.id
    try:
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) != 2:
            raise ValueError
        ch_id, title = parts
        try:
            bot.get_chat_member(ch_id, bot.get_me().id)
        except Exception:
            bot.send_message(chat_id, "⚠️ لا يمكن الوصول للقناة! تأكد أن البوت أدمن.")
            return
        url = f"https://t.me/{ch_id.replace('@', '')}"
        channels.append({"chat_id": ch_id, "title": title, "url": url})
        save_all()
        bot.send_message(chat_id, f"✅ تم إضافة: {title}")
    except Exception:
        bot.send_message(chat_id, "❌ الصيغة: `@channel | اسم`", parse_mode="Markdown")


def admin_create_giveaway(message):
    chat_id = message.chat.id
    try:
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) != 2:
            raise ValueError
        title, prize = parts
        gid = f"gw_{int(time.time())}"
        giveaways[gid] = {
            "title": title, "prize": prize, "participants": [],
            "active": True, "created_at": datetime.now().isoformat(), "winners": [],
        }
        save_all()
        bot.send_message(chat_id, f"✅ تم: {title}")
    except Exception:
        bot.send_message(chat_id, "❌ الصيغة: `عنوان | جائزة`", parse_mode="Markdown")


def admin_points_action(message, action):
    chat_id = message.chat.id
    try:
        uid, amount = message.text.split()
        amount = int(amount)
        if uid not in users:
            bot.send_message(chat_id, "❌ المستخدم غير موجود.")
            return
        if action == "add":
            users[uid]["points"] += amount
        else:
            users[uid]["points"] = max(0, users[uid]["points"] - amount)
        save_all()
        bot.send_message(chat_id, f"✅ الرصيد: {users[uid]['points']}")
        try:
            bot.send_message(int(uid), f"💰 تم تحديث نقاطك: {users[uid]['points']}")
        except Exception:
            pass
    except Exception:
        bot.send_message(chat_id, "❌ الصيغة خاطئة.")


def admin_set_value(message, key):
    chat_id = message.chat.id
    try:
        settings[key] = int(message.text.strip())
        save_all()
        bot.send_message(chat_id, f"✅ تم: {key} = {settings[key]}")
    except Exception:
        bot.send_message(chat_id, "❌ أرسل رقماً.")


# ==================== أوامر إضافية ====================
@bot.message_handler(commands=["cancel"])
def cancel_cmd(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "✅ تم الإلغاء.", reply_markup=main_menu())


@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    bot.send_message(message.chat.id,
                     f"📊 المستخدمون: {len(users)}\n📡 القنوات: {len(channels)}")


@bot.message_handler(commands=["live"])
def live_stats(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    ratings = load_json("ratings", {})
    avg = sum(r["stars"] for r in ratings.values()) / len(ratings) if ratings else 0
    banned = load_json("banned", {})
    lottery = load_json("lottery", {"participants": []})
    bot.send_message(
        message.chat.id,
        f"📊 *إحصائيات مباشرة*\n\n"
        f"👥 المستخدمون: {len(users)}\n"
        f"🚫 المحظورون: {len(banned)}\n"
        f"⭐ التقييم: {avg:.1f}/5\n"
        f"🎰 القرعة: {len(lottery['participants'])}\n"
        f"📡 القنوات: {len(channels)}",
        parse_mode="Markdown")


@bot.message_handler(commands=["reply"])
def reply_cmd(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        target = int(parts[1])
        text = parts[2]
        bot.send_message(target, f"📩 *من المطور:*\n\n{text}", parse_mode="Markdown")
        bot.send_message(DEVELOPER_CHAT_ID, "✅ تم.")
    except Exception:
        bot.send_message(DEVELOPER_CHAT_ID, "`/reply USER_ID النص`", parse_mode="Markdown")


@bot.message_handler(commands=["ban"])
def ban_cmd(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        ban_user(parts[1], parts[2] if len(parts) > 2 else "")
        bot.send_message(DEVELOPER_CHAT_ID, f"🚫 تم حظر {parts[1]}")
    except Exception:
        bot.send_message(DEVELOPER_CHAT_ID, "`/ban USER_ID [سبب]`", parse_mode="Markdown")


@bot.message_handler(commands=["unban"])
def unban_cmd(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    try:
        uid = message.text.split()[1]
        unban_user(uid)
        bot.send_message(DEVELOPER_CHAT_ID, f"✅ تم إلغاء حظر {uid}")
    except Exception:
        bot.send_message(DEVELOPER_CHAT_ID, "`/unban USER_ID`", parse_mode="Markdown")


@bot.message_handler(commands=["sold"])
def sold_cmd(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    try:
        uid = message.text.split()[1]
        bot.send_message(
            int(uid),
            "🎉 *مبروك!*\n\n"
            "✅ تم بيع حسابك بنجاح!\n"
            "💰 سيتواصل معك المطور لاستلام المبلغ.\n\n"
            "شكراً لك ❤️",
            parse_mode="Markdown")
        accounts = load_json("accounts", {})
        if str(uid) in accounts:
            accounts[str(uid)]["status"] = "sold"
            save_json("accounts", accounts)
        bot.send_message(DEVELOPER_CHAT_ID, f"✅ تم إشعار {uid}")
    except Exception:
        bot.send_message(DEVELOPER_CHAT_ID, "`/sold USER_ID`", parse_mode="Markdown")


@bot.message_handler(commands=["reject"])
def reject_cmd(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        uid = parts[1]
        reason = parts[2] if len(parts) > 2 else "لم يتم تحديد السبب"
        bot.send_message(int(uid),
                         f"❌ *تم رفض حسابك*\n\n📌 السبب: {reason}",
                         parse_mode="Markdown")
        accounts = load_json("accounts", {})
        if str(uid) in accounts:
            accounts[str(uid)]["status"] = "rejected"
            save_json("accounts", accounts)
        bot.send_message(DEVELOPER_CHAT_ID, f"✅ تم إشعار {uid}")
    except Exception:
        bot.send_message(DEVELOPER_CHAT_ID, "`/reject USER_ID [سبب]`", parse_mode="Markdown")


# ==================== fallback ====================
@bot.message_handler(func=lambda m: True,
                     content_types=["text", "photo", "video", "document", "audio", "voice"])
def fallback(message):
    if message.chat.id == DEVELOPER_CHAT_ID:
        return
    if is_banned(message.chat.id):
        bot.send_message(message.chat.id, "🚫 أنت محظور.")
        return
    bot.send_message(message.chat.id, "🤖 استخدم القائمة 👇", reply_markup=main_menu())


# ==================== تشغيل ====================
if __name__ == "__main__":
    try:
        me = bot.get_me()
        BOT_USERNAME = me.username
        print(f"✅ البوت يعمل: @{BOT_USERNAME}")
    except Exception as e:
        print(f"⚠️ {e}")
    bot.infinity_polling()