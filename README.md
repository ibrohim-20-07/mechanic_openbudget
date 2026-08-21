# mechanic_openbudget

Open Budget uchun ovozlarni admin tomonidan tasdiqlab qabul qilib balansga tushirib beruvchi bot.

## Talablar

- Python 3.11 yoki 3.12
- PostgreSQL (mahalliy yoki server)
- Telegram bot tokeni ([@BotFather](https://t.me/BotFather) orqali)
- Ovozlarni tasdiqlash uchun nazorat kanal/guruh (bot shu yerga admin sifatida qo'shilishi kerak, post va xabarni tahrirlash huquqi bilan)
- Pul yechish so'rovlari uchun alohida kanal/guruh (bot shu yerga ham admin sifatida qo'shilishi kerak)

## O'rnatish

Standart Python virtual muhit va `pip` orqali:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

(Linux/Mac'da: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`)

`.env.example` faylidan nusxa oling va o'z qiymatlaringiz bilan to'ldiring:

```powershell
copy .env.example .env
```

| O'zgaruvchi | Tavsif |
|---|---|
| `BOT_TOKEN` | BotFather bergan token |
| `ADMIN_ID` | Yagona admin foydalanuvchining Telegram ID raqami |
| `CHANNEL_ID` | Ovoz tasdiqlash uchun nazorat kanal/guruh ID (odatda `-100...`) |
| `PAYMENTS_CHANNEL_ID` | Pul yechish (zayafka) so'rovlari yuboriladigan kanal/guruh ID |
| `DATABASE_URL` | `postgresql+asyncpg://user:password@host:5432/dbname` formatida |
| `TIMEZONE` | Standart: `Asia/Tashkent` |

## Bazani tayyorlash

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
```

Bu barcha jadvallarni yaratadi. `global_settings` jadvaliga standart qiymatlar (`vote_price=2000`, `min_withdrawal=300000`, `referral_bonus=5000`, promo matn) botni birinchi marta ishga tushirganda avtomatik urug'lanadi (agar ular hali mavjud bo'lmasa).

## Ishga tushirish

```powershell
.venv\Scripts\python.exe main.py
```

(venv faollashtirilgan bo'lsa, oddiy `python main.py` ham ishlaydi.)

Muvaffaqiyatli ishga tushsa terminalda shunga o'xshash qatorlar chiqadi:

```
INFO  openbudget: OpenBudget bot ishga tushmoqda (@sizning_bot_username)...
INFO  aiogram.dispatcher: Run polling for bot ...
```

To'xtatish uchun `Ctrl+C`.

## Admin panelga kirish

Admin (`.env` dagi `ADMIN_ID`) botga `/admin` buyrug'ini yuborishi kifoya — inline tugmalardan iborat to'liq boshqaruv paneli ochiladi (loyihalar, balans, statistika, xabar yuborish, zayafkalar, sozlamalar). Har bir ekranda "« Bosh menyu" va "« Bekor qilish" tugmalari orqali istalgan vaqtda ortga qaytish yoki joriy amalni bekor qilish mumkin.

## Loyiha tuzilishi

Batafsil arxitektura va bosqichma-bosqich qurilish rejasi uchun qarang: `C:\Users\HP\.claude\plans\cozy-orbiting-sunbeam.md` (ushbu suhbatda tasdiqlangan reja).

```
mechanic_openbudget/
├── main.py                  # kirish nuqtasi — python main.py bilan ishga tushadi
├── config.py                # .env dan sozlamalarni o'qiydi
├── requirements.txt
├── alembic.ini
├── db/
│   ├── base.py               # SQLAlchemy async engine/session
│   ├── models/                # users, projects, votes, withdrawals, balance_history, referrals, global_settings, broadcasts
│   └── migrations/            # Alembic migratsiyalari
├── repositories/               # sof DB so'rovlari
├── services/                   # biznes-mantiq va tranzaksiyalar
│   └── voting_service.py      # ovoz tasdiqlash, auto-stop, referral bonus barchasi shu yerda
├── bot/
│   ├── routers/
│   │   ├── user/                # /start, ovoz berish, hisobim, pul yechish, referal
│   │   └── admin/                # /admin panel: menu, approval (kanal), loyihalar, balans, statistika...
│   ├── keyboards/
│   ├── middlewares/              # db_session, register_user, role, callback_answer
│   ├── states/                   # FSM holatlari
│   └── callbacks.py              # CallbackData sxemalari
└── utils/                        # timezone, pagination, pul/telefon formatlash
```

## Hozirgi holat

- ✅ Foydalanuvchi ro'yxatdan o'tishi, referal havola orqali bog'lanish
- ✅ Ovoz berish oqimi (telefon → skrinshot → kanalga yuborish)
- ✅ Admin kanalda ✅/❌ orqali tasdiqlash/rad etish, balans hisoblanishi, referal bonusi, loyihalar auto-stop/auto-switch
- ✅ `/admin` — to'liq inline-tugmali admin panel (reply-keyboard emas): loyihalar, global sozlamalar, referal sozlamalari, balans qo'shish/ayirish, hammaga xabar yuborish, statistika (bugun/kecha/hafta/oy/maxsus oraliq/umumiy), ovozlar jurnali, zayafkalar — barchasi sahifalab va "orqaga/bekor qilish" tugmalari bilan
- ✅ Pul yechish (zayafka): foydalanuvchi so'rov yuboradi (balans darhol yechiladi), admin ro'yxatdan "to'landi" deb belgilaydi
- ✅ Har bir inline tugma bosilganda javob kafolatlanadi (xato bo'lsa ham) — tugma "osilib qolmaydi"
- ✅ Global xatolik ushlagich — bitta handler xatosi butun botni to'xtatmaydi

Barcha yuqoridagi mantiq real PostgreSQL bazasiga qarshi integratsion testlar bilan tekshirilgan (balans, referal bonus, auto-stop/auto-switch, pul yechish, statistika agregatsiyasi).
