from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import AdminMenuCB, StatsPeriodCB
from bot.filters import IsAdmin
from bot.keyboards import admin_kb
from bot.states.stats_states import StatsStates
from services import stats_service
from services.stats_service import PeriodStats
from utils.formatting import format_money
from utils.timezone import TASHKENT_TZ

router = Router(name="admin_stats")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _period_kb() -> InlineKeyboardMarkup:
    def cb(period: str) -> str:
        return StatsPeriodCB(period=period).pack()

    return admin_kb.with_back_row(
        [
            [
                InlineKeyboardButton(text="Bugun", callback_data=cb("today")),
                InlineKeyboardButton(text="Kecha", callback_data=cb("yesterday")),
            ],
            [
                InlineKeyboardButton(text="Bu hafta", callback_data=cb("week")),
                InlineKeyboardButton(text="Bu oy", callback_data=cb("month")),
            ],
            [
                InlineKeyboardButton(text="Maxsus oraliq", callback_data=cb("custom")),
                InlineKeyboardButton(text="Umumiy", callback_data=cb("all")),
            ],
        ]
    )


def _format_stats(stats: PeriodStats) -> str:
    return (
        f"📊 Statistika — {stats.label}\n\n"
        f"🗳 Ovozlar: {stats.votes_total} ta\n"
        f"  ✅ Tasdiqlangan: {stats.votes_confirmed}\n"
        f"  ❌ Rad etilgan: {stats.votes_rejected}\n"
        f"  ⏳ Kutilmoqda: {stats.votes_pending}\n\n"
        f"💰 Hisoblangan mukofot: {format_money(stats.sum_credited)}\n"
        f"💸 Yechib olingan: {format_money(stats.sum_withdrawn)}\n"
        f"👥 Yangi foydalanuvchilar: {stats.new_users} ta\n"
        f"🎁 Referal bonuslari: {format_money(stats.referral_bonus_paid)}"
    )


@router.callback_query(AdminMenuCB.filter(F.section == "stats"))
async def show_period_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("📊 Davrni tanlang:", reply_markup=_period_kb())


@router.callback_query(StatsPeriodCB.filter(F.period != "custom"))
async def show_stats(
    callback: CallbackQuery, callback_data: StatsPeriodCB, session: AsyncSession
) -> None:
    label, start, end = stats_service.resolve_period(callback_data.period, TASHKENT_TZ)
    stats = await stats_service.get_period_stats(session, label, start, end)
    await callback.message.edit_text(_format_stats(stats), reply_markup=_period_kb())


@router.callback_query(StatsPeriodCB.filter(F.period == "custom"))
async def custom_range_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(StatsStates.waiting_start_date)
    await callback.message.edit_text(
        "Boshlanish sanasini kiriting (kun.oy.yil), masalan: 01.08.2025",
        reply_markup=admin_kb.cancel_kb(),
    )


def _parse_date(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y").replace(tzinfo=TASHKENT_TZ)
    except ValueError:
        return None


@router.message(StatsStates.waiting_start_date, F.text)
async def custom_range_start_received(message: Message, state: FSMContext) -> None:
    start = _parse_date(message.text)
    if start is None:
        await message.answer(
            "❗ Format: kun.oy.yil, masalan 01.08.2025. Qayta kiriting:",
            reply_markup=admin_kb.cancel_kb(),
        )
        return
    await state.update_data(start=start.isoformat())
    await state.set_state(StatsStates.waiting_end_date)
    await message.answer("Tugash sanasini kiriting (kun.oy.yil):", reply_markup=admin_kb.cancel_kb())


@router.message(StatsStates.waiting_end_date, F.text)
async def custom_range_end_received(message: Message, session: AsyncSession, state: FSMContext) -> None:
    end_input = _parse_date(message.text)
    if end_input is None:
        await message.answer(
            "❗ Format: kun.oy.yil, masalan 31.08.2025. Qayta kiriting:",
            reply_markup=admin_kb.cancel_kb(),
        )
        return

    data = await state.get_data()
    start = datetime.fromisoformat(data["start"])
    end = end_input + timedelta(days=1)  # inclusive of the end date

    if end <= start:
        await message.answer(
            "❗ Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak. Qayta kiriting:",
            reply_markup=admin_kb.cancel_kb(),
        )
        return

    await state.clear()
    label = f"{start.strftime('%d.%m.%Y')} — {end_input.strftime('%d.%m.%Y')}"
    stats = await stats_service.get_period_stats(session, label, start, end)
    await message.answer(_format_stats(stats), reply_markup=admin_kb.with_back_row([]))
