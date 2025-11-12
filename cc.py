import logging
import os
import sys
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackContext,
    ConversationHandler
)
import requests
import json
import re
import random

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---!!! ज़रूरी !!!---
# --- अपना BOT_TOKEN Render.com के 'Environment Variables' में सेट करें ---
BOT_TOKEN = os.getenv("BOT_TOKEN") 
# ---------------------

PHONE_API_URL = "https://demon.taitanx.workers.dev/?mobile="
AADHAAR_API_URL = "https://family-members-n5um.vercel.app/fetch"

# Conversation states
NUMBER_INPUT, AADHAAR_INPUT = 1, 2

class InfoBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.phone_api_url = PHONE_API_URL
        self.aadhaar_api_url = AADHAAR_API_URL
    
    def validate_phone_number(self, number: str) -> bool:
        pattern = r'^[6-9]\d{9}$'
        return bool(re.match(pattern, number))
    
    def validate_aadhaar_number(self, number: str) -> bool:
        pattern = r'^\d{12}$'
        return bool(re.match(pattern, number))
    
    def create_main_keyboard(self):
        keyboard = [
            [KeyboardButton("📱 Phone Lookup"), KeyboardButton("🆔 Aadhaar Lookup")],
            [KeyboardButton("ℹ️ Help"), KeyboardButton("🚀 Quick Start")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def format_phone_data(self, data, phone_number):
        """Format phone API data into the exact format shown"""
        try:
            logger.info(f"Raw phone API data: {data}")
            
            formatted_text = f"📞 Number Lookup Result for: {phone_number}\n"
            formatted_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            records = []
            if isinstance(data, dict) and 'data' in data:
                records = data['data']
            elif isinstance(data, list):
                records = data
            
            if records:
                for i, record in enumerate(records, 1):
                    formatted_text += "───────────────────────\n"
                    formatted_text += f"{i}. Result\n"
                    
                    if isinstance(record, dict):
                        # --- सभी फोन डिटेल्स ---
                        name = record.get('name', 'Not Available')
                        formatted_text += f"• 👤 Name: {name}\n"
                        
                        mobile = record.get('mobile', 'Not Available')
                        formatted_text += f"• 📱 Mobile: {mobile}\n"
                        
                        fname = record.get('fname', 'Not Available')
                        formatted_text += f"• 👨‍👦 Father's Name: {fname}\n"
                        
                        address = record.get('address', 'Not Available')
                        if address != 'Not Available':
                            # एड्रेस को साफ करना
                            address = str(address).replace('|', ', ').replace('!', ', ').replace('l', ', ')
                            address = re.sub(r',+', ',', address) # डबल कॉमा हटाना
                            address = address.strip(', ')
                            address = ', '.join(word.strip().title() for word in address.split(',')) # कैपिटल करना
                            formatted_text += f"• 🏠 Address: {address}\n"
                        else:
                            formatted_text += f"• 🏠 Address: Not Available\n"
                        
                        alt = record.get('alt', 'Not Available')
                        formatted_text += f"• 📞 Alt Mobile: {alt}\n"
                        
                        circle = record.get('circle', 'Not Available')
                        formatted_text += f"• 🌐 Circle: {circle}\n"
                        
                        id_num = record.get('id', 'Not Available') # यह ID लॉग्स में थी
                        formatted_text += f"• 🆔 ID No: {id_num}\n"
                        
                        formatted_text += f"• 📧 Email: Not Available\n\n"
                
                # डेवलपर क्रेडिट (API रिस्पॉन्स के आधार पर)
                developer = data.get('developer', '')
                if developer:
                    formatted_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    formatted_text += f"💳 API by: {developer}\n"
                
            else:
                logger.warning(f"No valid records found in API response")
                formatted_text += "No data found for this number."
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting phone data: {e}")
            return f"📞 Number Lookup Result for: {phone_number}\n\nError processing data. Please try again."
    
    
    def format_aadhaar_data(self, data, aadhaar_number):
        """Format Aadhaar API data into exact family information format"""
        try:
            logger.info(f"Raw Aadhaar API data: {data}")
            
            formatted_text = "🧬 FAMILY INFORMATION LOOKUP\n"
            formatted_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            if isinstance(data, dict):
                if data.get('error'):
                    formatted_text += f"Error: {data['error']}\n"
                    return formatted_text
                
                # --- असली API डेटा का इस्तेमाल ---
                
                # राशन कार्ड और स्कीम
                ration_card = data.get('rcId', 'Not Available') # असली RC ID
                scheme_name = data.get('schemeName', 'N/A')
                scheme_id = data.get('schemeId', 'N/A')
                fps_id = data.get('fpsId', 'N/A')

                formatted_text += f"🪪 Ration Card: {ration_card}\n"
                formatted_text += f"📦 Scheme Name: {scheme_name}\n"
                formatted_text += f"🆔 Scheme ID: {scheme_id}\n"
                formatted_text += f"🏪 FPS ID: {fps_id}\n"

                # पता
                address = data.get('address', 'Not Available')
                district_name = data.get('homeDistName', 'N/A')
                state_name = data.get('homeStateName', 'N/A')
                district_code = data.get('districtCode')
                state_code = data.get('homeStateCode')

                formatted_text += f"🏠 Address: {address}\n"
                
                if district_code and district_name != 'N/A':
                    formatted_text += f"📍 District: {district_name} ({district_code})\n"
                else:
                    formatted_text += f"📍 District: {district_name}\n"

                if state_code and state_name != 'N/A':
                    formatted_text += f"🌆 State: {state_name} ({state_code})\n"
                else:
                    formatted_text += f"🌆 State: {state_name}\n"

                # अन्य स्टेटस
                eligible_orc = data.get('allowed_onorc', 'N/A')
                duplicate_uid = data.get('dup_uid_status', 'N/A')
                
                formatted_text += f"✅ Eligible for ORC: {eligible_orc}\n"
                formatted_text += f"🔁 Duplicate UID Status: {duplicate_uid}\n"
                
                # --- फिक्स खत्म ---
                
                formatted_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                formatted_text += "👨‍👩‍👧‍👦 Family Members:\n\n"
                
                family_members = data.get('memberDetailsList', []) # लॉग्स के अनुसार
                
                if family_members:
                    for i, member in enumerate(family_members, 1):
                        if isinstance(member, dict):
                            # --- असली मेंबर डेटा ---
                            name = member.get('memberName', 'N/A')
                            relation = member.get('releationship_name', 'N/A')
                            relation_code = member.get('relationship_code', 'N/A')
                            member_id = member.get('memberId', 'N/A') # असली Member ID
                            uid_linked = member.get('uid', 'N/A')
                            
                            formatted_text += f"{i}. {name.title()}\n"
                            formatted_text += f"• 👤 Relation: {relation.title()} (Code: {relation_code})\n"
                            formatted_text += f"• 🆔 Member ID: {member_id}\n"
                            formatted_text += f"• 🔐 UID Linked: {uid_linked}\n\n"
                    
                    formatted_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    formatted_text += "💳"
                    
                else:
                    formatted_text += "No family members found."
                
            else:
                 formatted_text += "No data found for this Aadhaar number."
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting aadhaar data: {e}")
            return "🧬 FAMILY INFORMATION LOOKUP\n\nError processing Aadhaar data. Please try again."
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        
        welcome_text = f"""
👋 Welcome {user.first_name}!

I'm *Multi-Info Bot* — Get information from multiple sources.

🧑‍💻 *Developer:* Smarty Sunny  
⚠️ *Note:* This bot is for educational purposes only.  
Misuse of the bot or its data is strictly prohibited.  
The developer is *not responsible* for any illegal use.

Choose an option below or send:
- 📱 10-digit phone number  
- 🆔 12-digit Aadhaar number

Commands:
/phone - Phone number lookup  
/aadhaar - Aadhaar number lookup  
/help - Help guide
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=self.create_main_keyboard()
        )
    
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        help_text = """
📘 *Help Guide - Multi-Info Bot*

📱 *Phone Lookup:*
- Send 10-digit mobile number  
  Example: 9876543210

🆔 *Aadhaar Lookup:*
- Send 12-digit Aadhaar number  
  Example: 123456789012

Quick Commands:
/phone - Phone lookup  
/aadhaar - Aadhaar lookup  
/help - This message  

Or use the buttons below!
        """
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=self.create_main_keyboard()
        )
    
    async def phone_command(self, update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "📱 Enter 10-digit mobile number:\nExample: 9945789124\n\nType /cancel or 'Cancel' to stop.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
        )
        return NUMBER_INPUT
    
    async def process_phone_lookup(self, update: Update, phone_number: str) -> None:
        processing_msg = await update.message.reply_text(f"🔍 Searching phone: {phone_number}...")
        
        try:
            url = f"{self.phone_api_url}{phone_number}"
            logger.info(f"Calling Phone API: {url}")
            response = requests.get(url, timeout=30) # टाइमआउट बढ़ाया
            
            if response.status_code == 200:
                api_data = response.json()
                formatted_message = self.format_phone_data(api_data, phone_number)
                
                await processing_msg.edit_text(f"✅ Phone data found: {phone_number}")
                await update.message.reply_text(
                    formatted_message,
                    parse_mode=None,
                    reply_markup=self.create_main_keyboard()
                )
            else:
                error_msg = f"❌ Phone API Error - Status: {response.status_code}"
                logger.error(error_msg)
                await processing_msg.edit_text(error_msg)
            
        except requests.exceptions.Timeout:
            logger.error("Phone API request timed out")
            await processing_msg.edit_text("❌ Phone lookup timed out. Please try again later.")
        except Exception as e:
            error_msg = f"❌ Phone Lookup Error - {str(e)}"
            logger.error(error_msg)
            await processing_msg.edit_text("❌ Phone lookup failed. Please try again later.")
    
    async def aadhaar_command(self, update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "🆔 Enter 12-digit Aadhaar number:\nExample: 123456789012\n\nType /cancel or 'Cancel' to stop.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
        )
        return AADHAAR_INPUT
    
    async def process_aadhaar_lookup(self, update: Update, aadhaar_number: str) -> None:
        processing_msg = await update.message.reply_text(f"🔍 Searching Aadhaar: {aadhaar_number}...")
        
        try:
            url = f"{self.aadhaar_api_url}?aadhaar={aadhaar_number}&key=paidchx"
            logger.info(f"Calling Aadhaar API: {url}")
            response = requests.get(url, timeout=30) # टाइमआउट बढ़ाया
            
            if response.status_code == 200:
                api_data = response.json()
                formatted_message = self.format_aadhaar_data(api_data, aadhaar_number)
                
                await processing_msg.edit_text(f"✅ Aadhaar data found: {aadhaar_number}")
                await update.message.reply_text(
                    formatted_message,
                    parse_mode=None,
                    reply_markup=self.create_main_keyboard()
                )
            else:
                error_msg = f"❌ Aadhaar API Error - Status: {response.status_code}"
                logger.error(error_msg)
                await processing_msg.edit_text(f"❌ Aadhaar API Error - Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("Aadhaar API request timed out")
            await processing_msg.edit_text("❌ Aadhaar lookup timed out. Please try again later.")
        except Exception as e:
            error_msg = f"❌ Aadhaar Lookup Error - {str(e)}"
            logger.error(error_msg)
            await processing_msg.edit_text("❌ Aadhaar lookup failed. Please try again later.")
    
    async def handle_phone_input(self, update: Update, context: CallbackContext) -> int:
        text = update.message.text.strip()
        
        if text.lower() == 'cancel' or text == 'Cancel':
            await self.cancel(update, context)
            return ConversationHandler.END

        if self.validate_phone_number(text):
            await self.process_phone_lookup(update, text)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ अमान्य नंबर. कृपया 10 अंकों का मोबाइल नंबर दर्ज करें।\n\n'Cancel' लिखकर रोकने के लिए।",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
            )
            return NUMBER_INPUT
    
    async def handle_aadhaar_input(self, update: Update, context: CallbackContext) -> int:
        text = update.message.text.strip()
        
        if text.lower() == 'cancel' or text == 'Cancel':
            await self.cancel(update, context)
            return ConversationHandler.END

        if self.validate_aadhaar_number(text):
            await self.process_aadhaar_lookup(update, text)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ अमान्य नंबर. कृपया 12 अंकों का आधार नंबर दर्ज करें।\n\n'Cancel' लिखकर रोकने के लिए।",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
            )
            return AADHAAR_INPUT
    
    async def quick_start(self, update: Update, context: CallbackContext) -> None:
        """Handles the 'Quick Start' button"""
        await update.message.reply_text(
                "🚀 Quick Start:\n\n"
                "For Phone Lookup:\n• Send: 9876543210\n• Use: /phone\n\n"
                "For Aadhaar Lookup:\n• Send: 123456789012\n• Use: /aadhaar\n\n"
                "Or use the buttons!",
                reply_markup=self.create_main_keyboard()
            )

    async def handle_unknown_text(self, update: Update, context: CallbackContext) -> None:
        """Handles direct number inputs or any other unknown text"""
        user_input = update.message.text.strip()
        
        if self.validate_phone_number(user_input):
            await self.process_phone_lookup(update, user_input)
        elif self.validate_aadhaar_number(user_input):
            await self.process_aadhaar_lookup(update, user_input)
        elif user_input == "Cancel":
            await self.cancel(update, context)
        else:
            await update.message.reply_text(
                "Please send:\n• 10-digit Phone number\n• 12-digit Aadhaar number\n\nOr use the buttons below!",
                reply_markup=self.create_main_keyboard()
            )
    
    async def cancel(self, update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "❌ Operation cancelled.",
            reply_markup=self.create_main_keyboard()
        )
        return ConversationHandler.END

# -------------------------------------------------------------------
# --- यह MAIN फंक्शन WEBHOOK के लिए बदला गया है (Render.com) ---
# -------------------------------------------------------------------

def main():
    # --- टोकन के लिए सही जाँच ---
    if not BOT_TOKEN:
        logger.error("!!! ERROR: BOT_TOKEN एनवायरनमेंट वेरिएबल सेट नहीं है! !!!")
        logger.error("Please set the BOT_TOKEN in Render's 'Environment' settings.")
        sys.exit(1)
    
    try:
        bot = InfoBot()
        application = Application.builder().token(bot.token).build()
        
        # --- Render Webhook Configuration ---
        PORT = int(os.environ.get("PORT", 8443))
        
        # 'RENDER_EXTERNAL_URL' भी Render द्वारा सेट किया जाता है।
        HOST_URL_FROM_RENDER = os.environ.get("RENDER_EXTERNAL_URL")
        
        if not HOST_URL_FROM_RENDER:
            logger.error("!!! ERROR: RENDER_EXTERNAL_URL एनवायरनमेंट वेरिएबल नहीं मिला! !!!")
            logger.error("सुनिश्चित करें कि आप इसे Render 'Web Service' पर डिप्लॉय कर रहे हैं।")
            sys.exit(1)
        
        # --- !!! यह URL फिक्स है !!! ---
        # यह सुनिश्चित करता है कि URL में 'https://' सिर्फ एक बार हो
        # 'https://cc-jbno.onrender.com' -> 'cc-jbno.onrender.com'
        HOST_URL = HOST_URL_FROM_RENDER.replace("https://", "").replace("http://", "")
        # --- फिक्स खत्म ---
        
        # Webhook का पूरा URL
        # उदा: https://cc-jbno.onrender.com/8490946201:AAFScU...
        WEBHOOK_URL = f"https://{HOST_URL}/{BOT_TOKEN}"

        cancel_filter = filters.Regex("^(Cancel|cancel)$")
        
        phone_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('phone', bot.phone_command),
                MessageHandler(filters.Regex("^📱 Phone Lookup$"), bot.phone_command)
            ],
            states={
                NUMBER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_phone_input)]
            },
            fallbacks=[CommandHandler('cancel', bot.cancel), MessageHandler(cancel_filter, bot.cancel)]
        )
        
        aadhaar_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('aadhaar', bot.aadhaar_command),
                MessageHandler(filters.Regex("^🆔 Aadhaar Lookup$"), bot.aadhaar_command)
            ],
            states={
                AADHAAR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_aadhaar_input)]
            },
            fallbacks=[CommandHandler('cancel', bot.cancel), MessageHandler(cancel_filter, bot.cancel)]
        )
        
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help_command))
        
        application.add_handler(phone_conv_handler)
        application.add_handler(aadhaar_conv_handler)
        
        application.add_handler(MessageHandler(filters.Regex("^ℹ️ Help$"), bot.help_command))
        application.add_handler(MessageHandler(filters.Regex("^🚀 Quick Start$"), bot.quick_start))
        
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_unknown_text))
        
        logger.info("Multi-Info Bot Webhook पर शुरू हो रहा है...")
        logger.info(f"Using Bot Token: {bot.token[:10]}...")
        logger.info(f"Setting webhook url: {WEBHOOK_URL}") # यह लॉग अब सही URL दिखाएगा
        
        # --- Polling को Webhook से बदलना ---
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN, 
            webhook_url=WEBHOOK_URL 
        )
        
        logger.info(f"Multi-Info Bot Webhook पर 0.0.0.0:{PORT} पर चल रहा है।")
    
    except Exception as e:
        logger.critical(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
