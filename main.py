# main.py - Shams Gym Bot - PRODUCTION + AI
import json, os, requests
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not TOKEN:
    raise ValueError("TOKEN مش موجود!")

START_DATE = date(2026, 11, 25)
WEIGHT_FILE = "weight.json"

# ===== الذكاء الاصطناعي =====
SYSTEM_PROMPT = """
انت مدرب جيم وصاحب شمس، اسمك شمس بوت.
شمس ولد، عنده قولون، بيروح الجيم 7 مساء.
هدفه ينزل من وزنه لـ 75 كجم، ويخسس الكرش.
جدوله: يوم 1 بنج + ضهر، يوم 2 كتف + دراع، يوم 3 رجل + بطن، يوم 4 راحة.
أكله: بيض، فول، فراخ، رز، جبنة قريش، زبادي، موز، قهوة.
ممنوع: أكل يهيج القولون زي البصل والثوم الكتير والشطة والبقوليات الكتير.
اتكلم معاه بالمصري، زي صاحبه، باختصار، شجعه، متبقاش رسمي.
لو قال انه عك في الأكل، متأنبوش، قوله يكمل عادي ويعوض ازاي.
لو قال مش هيروح الجيم، اديله بديل البيت.
لو سأل على تمرين، اشرحله الحركة الصح.
ردك ميزيدش عن 4 سطور.
"""

def ask_ai(user_text):
    if not GEMINI_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        data = {
            "contents": [
                {"parts": [{"text": SYSTEM_PROMPT + "\n\nشمس بيقول: " + user_text}]}
            ]
        }
        r = requests.post(url, json=data, timeout=20)
        res = r.json()
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("AI Error:", e)
        return None

EXERCISE_GIFS = {
    "بنش برس": "https://media.giphy.com/media/3o7TKr3nzbh5WgCFxe/giphy.gif",
    "سكوات": "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif",
    "ديدليفت": "https://media.giphy.com/media/l0HlN2x7B0s8wG4xG/giphy.gif",
    "سحب أمامي": "https://media.giphy.com/media/3o7TKr3nzbh5WgCFxe/giphy.gif",
    "كتف دمبل": "https://media.giphy.com/media/3o7TKr3nzbh5WgCFxe/giphy.gif",
}

WORKOUTS = {
    0: {"title": "💪 اليوم 1: بنج + ضهر", "plan": "سوبر 1 (4x): بنش برس 10 + سحب أمامي 10\nسوبر 2 (4x): بنش انكلاين 12 + سحب أرضي 12\nسوبر 3 (3x): تفتيح كابل 15 + ديدليفت 10\nكارديو: مشاية انكلاين 7 سرعة 5 لمدة 20 د"},
    1: {"title": "💪 اليوم 2: كتف + دراع", "plan": "سوبر 1: كتف دمبل 12 + باي بار 12\nسوبر 2: رفرفة جانبي 15 + تراي حبل 12\nسوبر 3: كتف أمامي 12 + باي هامر 12\nسوبر 4: ترابيس 15 + تراي ورا الراس 12\nكارديو: عجلة 20 د"},
    2: {"title": "🔥 اليوم 3: رجل + بطن", "plan": "سوبر 1: سكوات 12 + كرنش 20\nسوبر 2: ليج برس 15 + رفع رجل 15\nسوبر 3: ليج اكستنشن 15 + بلانك 45 ث\nسوبر 4: ليج كيرل 12 + كالف 20\nكارديو: مشاية انكلاين 8 سرعة 5 لمدة 25 د"},
    3: {"title": "😴 اليوم 4: راحة", "plan": "مفيش حديد\nمشي خفيف 20-30 د\nينسون بعد الغدا عشان القولون"},
}

HOME_WORKOUTS = {
    0: {"title": "🏠 بديل البيت: بنج + ضهر", "plan": "ضغط واسع 15 + سوبرمان 15\nضغط انكلاين 12 + سحب بشنطة 12\nضغط دايموند 10 + سحب بطن 15\nكارديو: جامبنج جاك + هاي نيز 20 د"},
    1: {"title": "🏠 بديل البيت: كتف + دراع", "plan": "بايك بوش اب 12 + باي بأزازة 15\nرفرفة جانبي 15 + تراي كرسي 12\nضغط كتف 12 + هامر 12\nشراج 15 + تراي ورا الراس 12"},
    2: {"title": "🏠 بديل البيت: رجل + بطن", "plan": "سكوات 20 + كرنش 20\nلانجز 12 + رفع رجل 15\nسكوات جامب 12 + بلانك 45 ث\nكالف 20 + بايسكل كرنش 20"},
    3: {"title": "😴 النهارده راحة أصلا", "plan": "ستريتشات 10 د + مشي 20 د\nينسون بعد الغدا عشان القولون"},
}

MEAL_TRAIN = """🍽️ أكل يوم التمرين:
فطار: 3 بيض + فول 4 معالق + نص رغيف + خيار
غدا: فراخ 200ج + رز 5 معالق + سلطة
قبل الجيم: موزة + قهوة
بعد الجيم: زبادي + 3 بيض + موزة
عشا: جبنة قريش 150ج + خيار + طماطم"""

MEAL_REST = """🍽️ أكل يوم الراحة:
فطار: 3 بيض + جبنة قريش + نص رغيف + خيار
غدا: فراخ + رز 4 معالق + سلطة
سناك: زبادي + موزة
عشا: جبنة قريش + خيار + طماطم"""

def get_idx():
    return (date.today() - START_DATE).days % 4

def menu():
    kb = [
        [InlineKeyboardButton("🏋️ تمرين النهارده", callback_data="workout")],
        [InlineKeyboardButton("🏠 مش هروح الجيم - اتمرن في البيت", callback_data="home")],
        [InlineKeyboardButton("🎬 فيديو التمرين", callback_data="videos")],
        [InlineKeyboardButton("🍽️ أكل النهارده", callback_data="meal")],
        [InlineKeyboardButton("💧 شربت مياه", callback_data="water")],
        [InlineKeyboardButton("😬 عكيت في الأكل", callback_data="cheat")],
        [InlineKeyboardButton("⚖️ سجل وزنك", callback_data="ask_weight")],
        [InlineKeyboardButton("📊 تقدمي", callback_data="progress")],
        [InlineKeyboardButton("🤖 اسأل الذكاء الاصطناعي", callback_data="ask_ai")],
    ]
    return InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلا يا شمس 💪\nانا بقيت بذكاء اصطناعي، اسألني أي حاجة\nالجيم بتاعك 7 مساء، هفكرك 6 بالقهوة والموزة\nاختار:", reply_markup=menu())

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = get_idx()
    d = q.data

    if d == "workout":
        w = WORKOUTS[idx]
        await q.message.reply_text(f"{w['title']}\n\n{w['plan']}", reply_markup=menu())
    elif d == "home":
        h = HOME_WORKOUTS[idx]
        await q.message.reply_text(f"{h['title']}\n\n{h['plan']}\n\nولا يهمك انك مروحتش، المهم انك اتمرنت 💪", reply_markup=menu())
    elif d == "videos":
        kb = [
            [InlineKeyboardButton("بنش برس", callback_data="vid_بنش برس")],
            [InlineKeyboardButton("سكوات", callback_data="vid_سكوات")],
            [InlineKeyboardButton("ديدليفت", callback_data="vid_ديدليفت")],
            [InlineKeyboardButton("سحب أمامي", callback_data="vid_سحب أمامي")],
            [InlineKeyboardButton("كتف دمبل", callback_data="vid_كتف دمبل")],
        ]
        await q.message.reply_text("اختار التمرين اللي عايز تشوفه فيديو:", reply_markup=InlineKeyboardMarkup(kb))
    elif d.startswith("vid_"):
        name = d.replace("vid_", "")
        gif = EXERCISE_GIFS.get(name, EXERCISE_GIFS["بنش برس"])
        await q.message.reply_animation(animation=gif, caption=f"{name} - العبها كده بالظبط 👆")
        await q.message.reply_text("عايز تمرين تاني؟", reply_markup=menu())
    elif d == "meal":
        txt = MEAL_TRAIN if idx != 3 else MEAL_REST
        await q.message.reply_text(txt, reply_markup=menu())
    elif d == "water":
        context.user_data['water'] = context.user_data.get('water', 0) + 1
        total = context.user_data['water']
        await q.message.reply_text(f"💧 شربت {total} / 12 كوباية\nعاش يا وحش 💪", reply_markup=menu())
    elif d == "cheat":
        await q.message.reply_text("ولا يهمك، اليوم مباظش 😌\nكمل وجباتك عادي، اشرب 2 كوباية مياه، العشا جبنة قريش وخيار بس، وزود الكارديو 10 د.", reply_markup=menu())
    elif d == "ask_weight":
        await q.message.reply_text("ابعت وزنك بالأرقام بس، مثلا: 84.5")
        context.user_data['waiting_weight'] = True
    elif d == "progress":
        weights = []
        if os.path.exists(WEIGHT_FILE):
            with open(WEIGHT_FILE) as f: weights = json.load(f)
        if not weights:
            await q.message.reply_text("لسه مسجلتش وزن", reply_markup=menu())
        else:
            first, last = weights[0]['weight'], weights[-1]['weight']
            await q.message.reply_text(f"📊 بدأت: {first}\nدلوقتي: {last}\nنزلت: {first-last:.1f} كجم\nالهدف: 75", reply_markup=menu())
    elif d == "ask_ai":
        context.user_data['waiting_ai'] = True
        await q.message.reply_text("🤖 اسألني أي حاجة يا شمس، أكل، تمرين، قولون، أي حاجة...\nاكتب سؤالك دلوقتي:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # 1. لو مستني وزن
    if context.user_data.get('waiting_weight'):
        try:
            w = float(text.replace(',', '.'))
            data = []
            if os.path.exists(WEIGHT_FILE):
                with open(WEIGHT_FILE) as f: data = json.load(f)
            data.append({"date": str(date.today()), "weight": w})
            with open(WEIGHT_FILE, 'w') as f: json.dump(data, f)
            context.user_data['waiting_weight'] = False
            await update.message.reply_text(f"تم ✅ وزنك: {w}", reply_markup=menu())
        except:
            await update.message.reply_text("ابعت رقم بس زي 84.5")
        return

    # 2. لو مستني سؤال للذكاء الاصطناعي
    if context.user_data.get('waiting_ai'):
        context.user_data['waiting_ai'] = False
        await update.message.reply_text("ثانية واحدة بفكر... 🤔")
        ans = ask_ai(text)
        if ans:
            await update.message.reply_text(ans, reply_markup=menu())
        else:
            await update.message.reply_text("معلش، الذكاء الاصطناعي مش شغال دلوقتي، جرب تاني بعد شوية", reply_markup=menu())
        return

    # 3. أي كلام تاني -> الذكاء الاصطناعي يرد عليه على طول
    # لو الكلام قصير زي ازيك، رد سريع من غير AI عشان السرعة
    low = text.lower()
    if low in ["ازيك", "هاي", "hi", "hello", "عامل ايه"]:
        await update.message.reply_text("انا تمام يا وحش 💪 وانت؟ جاهز للتمرين ولا هتتمرن في البيت؟", reply_markup=menu())
        return

    await update.message.reply_text("ثانية واحدة بفكر... 🤔")
    ans = ask_ai(text)
    if ans:
        await update.message.reply_text(ans, reply_markup=menu())
    else:
        await update.message.reply_text("انا معاك يا شمس 💪\nقولي عايز ايه؟ تمرين، أكل، مياه، ولا هتتمرن في البيت؟", reply_markup=menu())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("البوت شغال... AI + PRODUCTION")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()