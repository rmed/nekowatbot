# Nekowat

A WAT bot for Telegram.

To launch the bot simply run

```
NEKOWAT_CONF=path_to_conf_file python3 nekowatbot.py
```

## How?

Either start a conversation with the bot and use the inline mode to get a reaction image (a *WAT*) or use the `/wat <expression>` command to get a random image that matches the expression.

## Configuration

The bot is configured through JSON using the following structure:

```json
{
    "tg": {
        "token": "MY_TG_TOKEN",
        "owner": MY_USER_ID,
        "use_whitelist": true,
        "whitelist": {}
    },
    "db": "PATH_TO_DATABASE_FILE"
}
```

Note that if `use_whitelist` is `false` every user will be able to interact with the bot. Otherwise, only those users in the `whitelist` will be able to interact with the bot. The whitelist is modified through the bot itself by the owner.

