# Состояния для ConversationHandler
(CHOOSING,
 TYPING_NAME,
 TYPING_EXPIRY_DATE,
 TYPING_DISEASE_GROUP,
 TYPING_ORGAN_GROUP,
 SAVE_RECORD_IN_DB,
 TYPING_HTML_LINK,
 TYPING_quantity,
 REDUCING_QUANTITY) = range(9)

# Глобальная переменная для хранения chat_id всех пользователей
chat_ids = set()