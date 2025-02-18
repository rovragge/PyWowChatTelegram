# PyWowChatTelegram

Telegram bot for transmitting messages between in-game WoW 3.3.5 chat and a Telegram chat.  
*Does not support Windows Warden handling.*  
*Supports only WoW 3.3.5 (old client!)*

Based on [Anarom/PyWowChat](https://github.com/Anarom/PyWowChat) – big props to Anarom and contributors.

## Environment Variables

The following environment variables must be defined in your OS or in a `params.env` file:

- **TG_TOKEN** — Telegram bot token.
- **TG_CHAT** — Telegram chat ID where messages are exchanged.
- **TG_THREAD** — (Optional) Telegram message thread ID.
- **WOW_LOGON** — WoW logon server address.
- **WOW_ACC** — WoW account name.
- **WOW_PASS** — WoW account password.
- **WOW_REALM** — WoW realm.
- **WOW_CHAR** — WoW character name.

## Quick Start with Docker

Run the container with the required environment variables using:

```bash
docker run --rm -it \
  -e TG_TOKEN=your_telegram_token_here \
  -e TG_CHAT=your_telegram_chat_id_here \
  -e TG_THREAD=your_telegram_thread_id_here \
  -e WOW_LOGON=your_wow_logon_server \
  -e WOW_ACC=your_wow_account \
  -e WOW_PASS=your_wow_password \
  -e WOW_REALM=your_wow_realm \
  -e WOW_CHAR=your_wow_character \
  your_docker_image_name
```

Replace the placeholder values with your actual credentials and configuration.

Enjoy seamless chat integration between WoW 3.3.5 and Telegram!