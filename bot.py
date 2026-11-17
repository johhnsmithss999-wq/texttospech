import os
import sys
import contextlib

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    CallbackQuery,
    Message
)
from aiogram.enums import ChatAction

from config import (
    TELEGRAM_BOT_TOKEN,
    TEMP_DIR
)
from user_manager import UserManager
from audio_utils import (
    convert_to_wav,
    get_audio_duration,
    download_file_from_telegram,
    validate_audio_voice
)
from tts_engine import TTSEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("VoxCPMBot")

if not TELEGRAM_BOT_TOKEN:
    print("\n" + "=" * 60)
    print("❌ ERROR: TELEGRAM_BOT_TOKEN is missing!")
    print("សូមបញ្ចូល Bot Token នៅក្នុង file .env ជាមុនសិន។")
    print("=" * 60 + "\n")

session = AiohttpSession(timeout=120.0) if TELEGRAM_BOT_TOKEN else None
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session) if TELEGRAM_BOT_TOKEN else None
dp = Dispatcher()

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Returns main inline navigation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎙️ សំឡេងរបស់ខ្ញុំ", callback_data="my_voice"),
                InlineKeyboardButton(text="🗑️ លុបសំឡេង", callback_data="clear_voice")
            ],
            [
                InlineKeyboardButton(text="⚙️ ការកំណត់", callback_data="settings"),
                InlineKeyboardButton(text="ℹ️ របៀបប្រើប្រាស់", callback_data="help")
            ]
        ]
    )

def get_settings_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Returns settings inline keyboard."""
    settings = UserManager.get_settings(user_id)
    steps = settings.get("inference_timesteps", 6)
    cfg = settings.get("cfg_value", 2.0)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"⚡ Steps: {steps} (ល្បឿន/គុណភាព)", callback_data="cycle_steps")
            ],
            [
                InlineKeyboardButton(text=f"🎛️ CFG: {cfg:.1f} (ភាពច្បាស់)", callback_data="cycle_cfg")
            ],
            [
                InlineKeyboardButton(text="🔙 ត្រឡប់ក្រោយ", callback_data="main_menu")
            ]
        ]
    )

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user = message.from_user
    has_voice = UserManager.has_voice(user.id)
    voice_status = "✅ បានកំណត់រួចរាល់" if has_voice else "❌ មិនទាន់មានសំឡេង"

    welcome_text = (
        f"👋 **សួស្តី {user.first_name}!**\n\n"
        "សូមស្វាគមន៍មកកាន់ **VoxCPM2 Voice Clone TTS Bot** 🎙️✨\n"
        "Bot នេះអាចបម្លែងអត្ថបទ (Text) ទៅជាសំឡេងនិយាយ (Speech) ដោយប្រើប្រាស់ **សំឡេងផ្ទាល់ខ្លួនរបស់អ្នក**!\n\n"
        f"📌 **ស្ថានភាពសំឡេងរបស់អ្នក:** {voice_status}\n\n"
        "🚀 **របៀបប្រើប្រាស់ងាយៗ:**\n"
        "1️⃣ **ដាក់សំឡេងសម្រាប់ Clone:**\n"
        "   • ផ្ញើ **Voice Message** ឬ **Audio File (.wav, .mp3, .m4a)** មកកាន់ខ្ញុំ\n"
        "   • 💡 *ណែនាំ: ថតសំឡេង 5-15 វិនាទី ឱ្យច្បាស់ល្អ គ្មានសំឡេងរំខាន*\n\n"
        "2️⃣ **បម្លែង Text ទៅជាសំឡេង:**\n"
        "   • គ្រាន់តែវាយអត្ថបទ (Text) ផ្ញើមកទីនេះ\n"
        "   • Bot នឹងនិយាយអត្ថបទនោះដោយប្រើសំឡេងរបស់អ្នកភ្លាមៗ!\n\n"
        "👇 ជ្រើសរើសមុខងារខាងក្រោម៖"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = (
        "📖 **ការណែនាំ និងគន្លឹះប្រើប្រាស់ VoxCPM2 Voice Clone**\n\n"
        "🎙️ **1. របៀបដាក់សំឡេង Clone ឱ្យបានល្អបំផុត:**\n"
        "• ថតសំឡេងនិយាយរបស់អ្នកប្រហែល 5 ទៅ 15 វិនាទី\n"
        "• និយាយឱ្យច្បាស់ ដោយមានទឹកដមធម្មជាតិ\n"
        "• ជៀសវាងកន្លែងដែលមានសំឡេងរំខាន (Noise) ឬតន្ត្រីផ្ទៃខាងក្រោយ\n"
        "• ប្រសិនបើអ្នកផ្ញើ Audio File ហើយសរសេរ Caption ជាអត្ថបទដែលបាននិយាយនោះ នោះម៉ូដែលនឹង Clone កាន់តែច្បាស់ល្អ (Hi-Fi Mode)\n\n"
        "💬 **2. របៀបបម្លែង Text ទៅជាសំឡេង:**\n"
        "• បន្ទាប់ពីបានដាក់សំឡេងរួច អ្នកគ្រាន់តែវាយអត្ថបទផ្ញើមក\n"
        "• គាំទ្រទាំងភាសាអង់គ្លេស ចិន និងភាសាជាច្រើនទៀត\n\n"
        "⚙️ **3. បញ្ជា Command ផ្សេងៗ:**\n"
        "• /myvoice - ស្តាប់សំឡេងដែលបានរក្សាទុក\n"
        "• /clearvoice - លុបសំឡេងចាស់ ដើម្បីដាក់ថ្មី\n"
        "• /settings - កំណត់គុណភាព និងល្បឿន\n"
        "• /help - មើលការណែនាំនេះ"
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("myvoice"))
async def cmd_myvoice(message: Message):
    """Handle /myvoice command."""
    user_id = message.from_user.id
    if not UserManager.has_voice(user_id):
        await message.answer(
            "⚠️ **អ្នកមិនទាន់បានកំណត់សំឡេងសម្រាប់ Clone នៅឡើយទេ។**\n\n"
            "👉 សូមថត **Voice Message** ឬផ្ញើ File Audio មកទីនេះដើម្បីចាប់ផ្តើម!",
            parse_mode="Markdown"
        )
        return

    voice_path = UserManager.get_voice_path(user_id)
    duration = get_audio_duration(voice_path)
    settings = UserManager.get_settings(user_id)
    prompt_text = settings.get("prompt_text")

    caption = f"🎙️ **សំឡេង Clone របស់អ្នក**\n⏱️ រយៈពេល: {duration:.1f} វិនាទី"
    if prompt_text:
        caption += f"\n📝 Transcript: _{prompt_text}_"

    audio_file = FSInputFile(str(voice_path))
    await message.answer_voice(voice=audio_file, caption=caption, parse_mode="Markdown")

@dp.message(Command("clearvoice"))
async def cmd_clearvoice(message: Message):
    """Handle /clearvoice command."""
    user_id = message.from_user.id
    if UserManager.delete_voice(user_id):
        await message.answer(
            "🗑️ **បានលុបសំឡេងរបស់អ្នកដោយជោគជ័យ!**\n\n"
            "ឥឡូវអ្នកអាចផ្ញើសំឡេងថ្មីមកបានគ្រប់ពេល។",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "ℹ️ អ្នកមិនទាន់មានសំឡេងដែលបានរក្សាទុកពីមុនមកទេ។",
            parse_mode="Markdown"
        )

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    """Handle /settings command."""
    user_id = message.from_user.id
    await message.answer(
        "⚙️ **ការកំណត់ការបង្កើតសំឡេង (VoxCPM2 Settings):**\n\n"
        "• **Inference Steps:** ចំនួនជុំបង្កើត (6 គឺល្អនិងលឿន, 10 គុណភាពខ្ពស់)\n"
        "• **CFG Scale:** កម្រិតបញ្ជាភាពច្បាស់ (2.0 គឺកម្រិតស្តង់ដារ)\n\n"
        "ចុចប៊ូតុងខាងក្រោមដើម្បីផ្លាស់ប្តូរ៖",
        parse_mode="Markdown",
        reply_markup=get_settings_keyboard(user_id)
    )

@dp.callback_query(F.data == "my_voice")
async def cb_my_voice(query: CallbackQuery):
    await query.answer()
    await cmd_myvoice(query.message)

@dp.callback_query(F.data == "clear_voice")
async def cb_clear_voice(query: CallbackQuery):
    await query.answer()
    await cmd_clearvoice(query.message)

@dp.callback_query(F.data == "settings")
async def cb_settings(query: CallbackQuery):
    await query.answer()
    user_id = query.from_user.id
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_text(
            "⚙️ **ការកំណត់ការបង្កើតសំឡេង (VoxCPM2 Settings):**\n\n"
            "• **Inference Steps:** ចំនួនជុំបង្កើត (6 គឺល្អនិងលឿន, 10 គុណភាពខ្ពស់)\n"
            "• **CFG Scale:** កម្រិតបញ្ជាភាពច្បាស់ (2.0 គឺកម្រិតស្តង់ដារ)\n\n"
            "ចុចប៊ូតុងខាងក្រោមដើម្បីផ្លាស់ប្តូរ៖",
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard(user_id)
        )

@dp.callback_query(F.data == "cycle_steps")
async def cb_cycle_steps(query: CallbackQuery):
    user_id = query.from_user.id
    settings = UserManager.get_settings(user_id)
    curr_steps = settings.get("inference_timesteps", 6)
    steps_options = [4, 6, 8, 10]
    next_idx = (steps_options.index(curr_steps) + 1) % len(steps_options) if curr_steps in steps_options else 1
    new_steps = steps_options[next_idx]
    UserManager.save_settings(user_id, {"inference_timesteps": new_steps})
    await query.answer(f"បានប្តូរ Steps ទៅ {new_steps}")
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_reply_markup(reply_markup=get_settings_keyboard(user_id))

@dp.callback_query(F.data == "cycle_cfg")
async def cb_cycle_cfg(query: CallbackQuery):
    user_id = query.from_user.id
    settings = UserManager.get_settings(user_id)
    curr_cfg = settings.get("cfg_value", 2.0)
    cfg_options = [1.5, 2.0, 2.5, 3.0]
    next_idx = (cfg_options.index(curr_cfg) + 1) % len(cfg_options) if curr_cfg in cfg_options else 1
    new_cfg = cfg_options[next_idx]
    UserManager.save_settings(user_id, {"cfg_value": new_cfg})
    await query.answer(f"បានប្តូរ CFG ទៅ {new_cfg}")
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_reply_markup(reply_markup=get_settings_keyboard(user_id))

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(query: CallbackQuery):
    await query.answer()
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_text(
            "👇 សូមជ្រើសរើសមុខងារខាងក្រោម៖",
            reply_markup=get_main_keyboard()
        )

@dp.callback_query(F.data == "help")
async def cb_help(query: CallbackQuery):
    await query.answer()
    await cmd_help(query.message)

@dp.message(F.voice | F.audio | (F.document & F.document.mime_type.startswith("audio/")))
async def handle_voice_upload(message: Message):
    """
    Handle user sending voice messages or audio files to clone their voice.
    """
    user_id = message.from_user.id
    status_msg = await message.answer("📥 កំពុងទទួល និងទាញយកសំឡេងរបស់អ្នក...")

    temp_download_path = None
    try:
        if message.voice:
            telegram_file_id = message.voice.file_id
            default_ext = ".oga"
        elif message.audio:
            telegram_file_id = message.audio.file_id
            default_ext = ".mp3"
        else:
            telegram_file_id = message.document.file_id
            default_ext = ".wav"

        file_info = await bot.get_file(telegram_file_id)
        ext = os.path.splitext(file_info.file_path)[1] or default_ext
        temp_download_path = TEMP_DIR / f"dl_{user_id}_{file_info.file_unique_id}{ext}"

        success = await asyncio.to_thread(
            download_file_from_telegram,
            token=TELEGRAM_BOT_TOKEN,
            file_path=file_info.file_path,
            output_path=temp_download_path
        )

        if not success or not temp_download_path.exists():
            await status_msg.edit_text("❌ មិនអាចទាញយក file សំឡេងពី Telegram បានទេ។ សូមសាកល្បងម្តងទៀត។")
            return

        await status_msg.edit_text("⚙️ កំពុងដំណើរការបម្លែងសំឡេង...")

        user_voice_path = UserManager.get_voice_path(user_id)
        converted = convert_to_wav(temp_download_path, user_voice_path)

        if not converted:
            await status_msg.edit_text("❌ មានបញ្ហាក្នុងការបម្លែង file សំឡេង។ សូមសាកល្បងផ្ញើ Voice Message ថ្មីម្តងទៀត។")
            return

        is_valid, v_status, duration, max_amp = validate_audio_voice(user_voice_path)
        if not is_valid:
            if v_status == "SILENT":
                UserManager.delete_voice(user_id)
                await status_msg.edit_text(
                    "⚠️ **សំឡេងដែលបានផ្ញើមកគឺស្ងាត់ (Silent / គ្មានឮសំឡេងនិយាយ)!**\n\n"
                    "👉 សូមពិនិត្យមើល Microphone របស់ទូរស័ព្ទ ឬកុំព្យូទ័ររបស់អ្នក ហើយថតសំឡេងនិយាយឱ្យឮច្បាស់ម្តងទៀត។",
                    parse_mode="Markdown"
                )
                return
            elif v_status == "TOO_SHORT":
                await status_msg.edit_text(
                    f"⚠️ **សំឡេងដែលបានផ្ញើមកខ្លីពេក (ត្រឹម {duration:.1f} វិនាទី)!**\n\n"
                    "👉 សូមថតសំឡេងនិយាយឱ្យបានយ៉ាងហោចណាស់ **5 ទៅ 15 វិនាទី** ដើម្បីឱ្យ AI ចាប់យកទឹកដមសំឡេងរបស់អ្នកបានច្បាស់ល្អ។",
                    parse_mode="Markdown"
                )
                return

        caption_text = message.caption.strip() if message.caption else None
        UserManager.save_settings(user_id, {"prompt_text": caption_text})

        confirm_text = (
            "✅ **បានកំណត់សំឡេងសម្រាប់ Clone រួចរាល់ហើយ!** 🎙️\n\n"
            f"⏱️ រយៈពេលសំឡេង: {duration:.1f} វិនាទី\n"
        )
        if caption_text:
            confirm_text += f"📝 Transcript (Hi-Fi Mode): _{caption_text}_\n\n"
        else:
            confirm_text += "✨ មុខងារ: Zero-Shot Timbre Voice Cloning\n\n"

        confirm_text += "💬 **ឥឡូវអ្នកអាចវាយអត្ថបទ (Text) ផ្ញើមកទីនេះ** ដើម្បីឱ្យ Bot និយាយដោយប្រើសំឡេងរបស់អ្នកបានភ្លាមៗ!"

        await status_msg.edit_text(confirm_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error saving voice: {e}", exc_info=True)
        err_msg = str(e) if str(e) else type(e).__name__
        await status_msg.edit_text(f"❌ កើតមានកំហុស៖ {err_msg}")

    finally:
        if temp_download_path and os.path.exists(temp_download_path):
            try:
                os.unlink(temp_download_path)
            except Exception:
                pass

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_tts(message: Message):
    """
    Handle text message and synthesize speech using the user's cloned voice or default voice.
    """
    user_id = message.from_user.id
    text = message.text.strip()

    if not text:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
    processing_msg = await message.answer("⏳ **កំពុងដំណើរការបង្កើតសំឡេង...**\n_(សូមរង់ចាំបន្តិច)_", parse_mode="Markdown")

    try:
        user_voice = str(UserManager.get_voice_path(user_id)) if UserManager.has_voice(user_id) else None
        
        # Check if the voice file is valid and not silent
        using_clone = False
        if user_voice and os.path.exists(user_voice):
            is_valid, v_status, _, _ = validate_audio_voice(user_voice)
            if is_valid:
                using_clone = True
            else:
                user_voice = None

        settings = UserManager.get_settings(user_id)
        prompt_text = settings.get("prompt_text") if using_clone else None
        cfg_value = settings.get("cfg_value", 2.0)
        timesteps = settings.get("inference_timesteps", 6)
        denoise = settings.get("denoise", False)

        tts = TTSEngine.get_instance()

        if using_clone and prompt_text:
            out_wav, out_ogg = await tts.generate_speech(
                text=text,
                prompt_wav_path=user_voice,
                prompt_text=prompt_text,
                reference_wav_path=user_voice,
                cfg_value=cfg_value,
                inference_timesteps=timesteps,
                denoise=denoise
            )
        elif using_clone:
            out_wav, out_ogg = await tts.generate_speech(
                text=text,
                reference_wav_path=user_voice,
                cfg_value=cfg_value,
                inference_timesteps=timesteps,
                denoise=denoise
            )
        else:
            # Generate using high-quality default voice
            out_wav, out_ogg = await tts.generate_speech(
                text=text,
                reference_wav_path=None,
                cfg_value=cfg_value,
                inference_timesteps=timesteps,
                denoise=denoise
            )

        duration = get_audio_duration(out_wav)
        if using_clone:
            caption = f"🎙️ **សំឡេង Clone របស់អ្នក:** {duration:.1f}s | Steps: {timesteps}"
        else:
            caption = (
                f"🎙️ **សំឡេងស្តង់ដារ (Default):** {duration:.1f}s | Steps: {timesteps}\n"
                "💡 *ដើម្បីឱ្យ Bot និយាយជាសំឡេងផ្ទាល់ខ្លួនរបស់អ្នក សូមផ្ញើ Voice Message (5-15 វិនាទី) មកកាន់ Bot!*"
            )

        voice_file = FSInputFile(str(out_ogg))
        await message.answer_voice(
            voice=voice_file,
            caption=caption,
            parse_mode="Markdown"
        )

        try:
            await processing_msg.delete()
        except Exception:
            pass

        if out_wav.exists():
            out_wav.unlink()
        if out_ogg.exists():
            out_ogg.unlink()

    except Exception as e:
        logger.error(f"Error during TTS generation: {e}", exc_info=True)
        err_msg = str(e) if str(e) else type(e).__name__
        await processing_msg.edit_text(
            f"❌ **កើតមានបញ្ហាក្នុងការបង្កើតសំឡេង៖**\n`{err_msg}`",
            parse_mode="Markdown"
        )

async def main():
    if not bot:
        print("[Bot] Cannot start bot without TELEGRAM_BOT_TOKEN.")
        return

    print("[Bot] Preloading VoxCPM2 model...")
    try:
        tts = TTSEngine.get_instance()
        await asyncio.to_thread(tts.load_model)
    except Exception as e:
        print(f"[Bot] Warning during model pre-loading: {e}")

    print("[Bot] Starting Telegram bot polling...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[Bot] Stopped by user.")
    except Exception as e:
        import traceback
        print(f"\n[Bot] Fatal uncaught error: {e}", file=sys.stderr)
        traceback.print_exc()
