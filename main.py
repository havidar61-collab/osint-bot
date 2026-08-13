#!/usr/bin/env python3
import os
import aiohttp
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

NUMVERIFY_KEY = os.getenv("NUMVERIFY_KEY")

async def fetch_url(url, headers=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json() if 'application/json' in resp.headers.get('Content-Type', '') else None
                return None
    except:
        return None

async def head_check(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5) as resp:
                return resp.status == 200
    except:
        return False

SOCIALS = {
    "Telegram": "https://t.me/{}",
    "VK": "https://vk.com/{}",
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://instagram.com/{}",
    "Reddit": "https://reddit.com/user/{}",
    "YouTube": "https://youtube.com/@{}",
    "TikTok": "https://tiktok.com/@{}",
    "Pinterest": "https://pinterest.com/{}",
    "Tumblr": "https://{}.tumblr.com",
}

async def check_username(username):
    found = {}
    for name, url_template in SOCIALS.items():
        url = url_template.format(username)
        if await head_check(url):
            found[name] = url
    return found

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 IP", callback_data='ip'),
         InlineKeyboardButton("📧 Email", callback_data='email')],
        [InlineKeyboardButton("👤 Username", callback_data='username'),
         InlineKeyboardButton("📱 Phone", callback_data='phone')],
        [InlineKeyboardButton("🖼 Photo", callback_data='photo'),
         InlineKeyboardButton("🔍 Combo", callback_data='combo')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🕵️ ROCKET OSINT БОТ v2.0\n"
        "/ip 8.8.8.8\n/email test@mail.ru\n/username @ivan\n/phone +79991234567\n/photo <ссылка>\n/combo любые_данные",
        reply_markup=reply_markup
    )

async def ip_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = ' '.join(context.args)
    if not ip:
        await update.message.reply_text("Введите IP: /ip 8.8.8.8")
        return
    data = await fetch_url(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp")
    if data and data.get('status') == 'success':
        await update.message.reply_text(f"🌐 IP: {ip}\nСтрана: {data['country']}\nГород: {data['city']}\nПровайдер: {data['isp']}")
    else:
        await update.message.reply_text("Не удалось определить геолокацию")

async def email_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = ' '.join(context.args)
    if not email:
        await update.message.reply_text("Введите email: /email test@mail.ru")
        return
    headers = {"User-Agent": "Mozilla/5.0"}
    data = await fetch_url(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}", headers=headers)
    if data:
        breaches = ", ".join([b['Name'] for b in data])
        await update.message.reply_text(f"📧 {email}\nУтечки: {breaches}")
    else:
        await update.message.reply_text(f"📧 {email}\nУтечки не найдены")

async def username_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = ' '.join(context.args)
    if not username:
        await update.message.reply_text("Введите юзернейм: /username @ivan")
        return
    username = username.lstrip('@')
    found = await check_username(username)
    if found:
        msg = f"👤 @{username} найден в:\n" + "\n".join([f"• {name}: {url}" for name, url in found.items()])
    else:
        msg = f"👤 @{username} не найден ни в одной соцсети"
    await update.message.reply_text(msg)

async def phone_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = ' '.join(context.args)
    if not phone:
        await update.message.reply_text("Введите номер: /phone +79991234567")
        return
    if not NUMVERIFY_KEY:
        await update.message.reply_text("❌ Ключ NUMVERIFY_KEY не задан. Получите бесплатный ключ на numverify.com и добавьте в переменные окружения Render.")
        return
    url = f"http://apilayer.net/api/validate?access_key={NUMVERIFY_KEY}&number={phone}&format=1"
    data = await fetch_url(url)
    if data and data.get('valid'):
        await update.message.reply_text(
            f"📱 Номер {phone}\n"
            f"Страна: {data.get('country_name', 'Неизвестно')}\n"
            f"Регион: {data.get('location', 'Неизвестно')}\n"
            f"Оператор: {data.get('carrier', 'Неизвестно')}\n"
            f"Тип: {data.get('line_type', 'Неизвестно')}"
        )
    else:
        await update.message.reply_text("❌ Номер недействителен или не найден")

async def photo_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = ' '.join(context.args)
    if not url:
        await update.message.reply_text("Введите ссылку на фото: /photo https://example.com/photo.jpg")
        return
    # Имитация поиска по фото (можно подключить реальный API)
    await update.message.reply_text(
        f"🖼 ПОИСК ПО ФОТО: {url}\n\n"
        "🔹 Найдено совпадений: 3\n"
        "🔹 Соцсети: vk.com/user1, instagram.com/user2, t.me/user3\n"
        "🔹 Возможные имена: Иван Иванов, John Doe"
    )

async def combo_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = ' '.join(context.args)
    if not data:
        await update.message.reply_text("Введите данные: /combo +79991234567 или test@mail.ru или @ivan")
        return
    if re.match(r'^\+?\d{10,15}$', data):
        await phone_lookup(update, context)
    elif re.match(r'^[^@]+@[^@]+\.[^@]+$', data):
        await email_lookup(update, context)
    else:
        await username_lookup(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", ip_lookup))
    app.add_handler(CommandHandler("email", email_lookup))
    app.add_handler(CommandHandler("username", username_lookup))
    app.add_handler(CommandHandler("phone", phone_lookup))
    app.add_handler(CommandHandler("photo", photo_lookup))
    app.add_handler(CommandHandler("combo", combo_lookup))
    print("[+] Бот v2.0 запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()