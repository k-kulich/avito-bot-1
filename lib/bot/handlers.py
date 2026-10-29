from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
from .commands import start, stop, status
from .callbacks import button_handler
from .messages import handle_message

def setup_handlers(app, bot):
    app.add_handler(CommandHandler("start", lambda u, c: start(u, c, bot)))
    app.add_handler(CommandHandler("stop", lambda u, c: stop(u, c, bot)))
    app.add_handler(CommandHandler("status", lambda u, c: status(u, c, bot)))
    app.add_handler(CallbackQueryHandler(lambda u, c: button_handler(u, c, bot)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_message(u, c, bot)))