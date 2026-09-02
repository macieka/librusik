<img src="screenshots/librusik.png" alt="Preview photo" width="600"/>

### Check out the [wiki](https://github.com/dani3l0/librusik/wiki) for more detailed information!

-----

## Features

The coolest ones:

📋 **Grades** with independent average calculation - works even if school has disabled it

✉️ **Messages** with downloading attachments

✅ **Attendances** with per-semester per-subject frequency %% calculation

🏠 **School free days** with countdown to next holiday

🍪 **Cookies** - you won't be logged out each time you close the browser

🧹 **Grades cleanup** - removes subjects without grades from Grades page

⌛ Cool **countdown gauges** on home screen

🌙 **Dark theme**

🎉 **Confetti**

🔔 **Message notifications** - get a Telegram, ntfy or Discord ping when a new Librus message arrives

-----

## Installation

__1. Clone the repo:__
```
git clone https://github.com/dani3l0/librusik && cd librusik
```

__2. Install required dependencies:__

```
pip install -r requirements.txt
```

__3. And, finally run it:__
```
python3 librusik.py
```

The first run asks a couple of questions (listen address and port) and creates `./data/`. To skip that and take the defaults:

```
python3 librusik.py --skip-wizard
```

Done! Librusik is now running at [localhost:7777](http://localhost:7777).

-----

## Configuration

Go to [localhost:7777/panel](http://localhost:7777/panel) to manage your Librusik instance. Default user is `admin` and password is `admin`.

Interface is friendly enough to painlessly configure your Librusik instance.

-----

## Message notifications 🔔

Librusik can check your Librus inbox in the background and push new messages to your phone. It uses [Apprise](https://github.com/caronc/apprise), so **Telegram**, **ntfy** and **Discord** all work out of the box - all three are free.

Librusik sends to **one destination per user**. To notify several people (both parents, for example), point it at a Telegram group, an ntfy topic or a Discord channel - everyone subscribed there gets the message.

### Telegram (recommended)

__1. Create a bot.__ Open [@BotFather](https://t.me/botfather) in Telegram, send `/newbot` and follow the prompts. It replies with a token that looks like:

```
123456789:AAHfaKeToKeNfAkEtOkEnFaKeToKeN123
```

__2. Say hi to your bot.__ Open the chat with your new bot and send it any message (`/start` is fine). **The bot will not reply** - there is no code behind it yet, and that is expected. A Telegram bot cannot message you first, so this step is what opens the chat.

__3. Find your chat ID.__ Open this in a browser, or:

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
```

Look for `"chat":{"id":123456789` - that number is your chat ID.

__4. Paste the URL into Librusik.__ Go to *Settings → Notification destination* and enter the token and chat ID together:

```
tgram://123456789:AAHfaKeToKeNfAkEtOkEnFaKeToKeN123/987654321
```

Hit **Send a test** to confirm it works, then flip on **Message notifications** in *Settings*.

__To notify several people:__ create a Telegram group, add your bot to it, send one message in the group, then take the group's chat ID from the same `getUpdates` call - it starts with `-`:

```
tgram://123456789:AAHfaKeToKeNfAkEtOkEnFaKeToKeN123/-1001234567890
```

> **Always include the chat ID.** Apprise also accepts a bare `tgram://<token>` and will auto-detect a chat, but it picks *the sender of the first pending update* - and every Telegram bot is publicly reachable, with no way to restrict who may message it. If a stranger writes to your bot first, your school messages get delivered to them. Auto-detection also breaks after about 24 hours, when Telegram discards the update it relies on. Fine for a quick test, wrong for something that runs for months.

Your bot token is a credential - anyone who has it controls the bot. If it leaks, revoke it with `/revoke` in BotFather.

### ntfy

Install the [ntfy](https://ntfy.sh) app, subscribe to a topic, and use:

```
ntfy://my-secret-topic-name
```

Anyone subscribed to that topic gets the notifications. On the public `ntfy.sh` server topic names are effectively public, so **pick something long and hard to guess**.

### Discord

Channel settings → *Integrations* → *Webhooks* → *New Webhook*. From the webhook URL `https://discord.com/api/webhooks/<id>/<token>`, build:

```
discord://<id>/<token>
```

### Tuning it

Notification behaviour is set instance-wide in `data/config.json`:

| Option | Default | What it does |
|--------|---------|--------------|
| `notif_enabled` | `true` | Master switch for the background poller |
| `notif_poll_interval` | `3600` | Seconds between inbox checks, per user |
| `notif_active_from` | `8` | Hour to start checking |
| `notif_active_to` | `22` | Hour to stop checking (so nobody is woken at 3 AM) |
| `notif_body_length` | `2000` | Max characters of message content to include - `0` sends the subject only |
| `notif_allowed_schemes` | `["tgram", "ntfy", "ntfys", "discord", "json", "jsons"]` | Which Apprise URL schemes users may save |
| `notif_min_tier` | `"free"` | Minimum tier required, if tiers are enabled |

The active hours use the **server's** local time. Under Docker that is UTC unless you set `TZ`, so `8`-`22` would silently mean 8-22 UTC - two hours off in Poland.

**A word on `notif_allowed_schemes`:** a destination URL makes your server send an outbound request wherever it points. On an instance with users you don't personally trust, keep this list tight - removing `json`/`jsons` in particular stops users from aiming Librusik at arbitrary HTTP endpoints on your network.

Librus doesn't offer any kind of push, so this is plain polling. Checking hourly is deliberate: log in too often and Librus may start rate-limiting or locking the account.

### If nothing arrives

*Settings → Notification destination* shows when the last check ran, or what went wrong. **Send a test** is the fastest way to tell a typo'd token from a working setup. For the full traceback, set `"debug": true` in `data/config.json` and watch the server output.

-----

## Installation (Docker) 🐳

### With Docker Compose (recommended)

A `docker-compose.yml` is included, so this is the whole setup:

```bash
docker compose up -d --build
```

It builds the image, publishes port 7777, mounts `./data` for your config and user database, restarts on boot, and sets the timezone.

Change `TZ` in the file if you are not in Poland, or override it for one run:

```bash
TZ=Europe/Berlin docker compose up -d
```

Follow the logs with:

```bash
docker compose logs -f
```

After changing any code, re-run `docker compose up -d --build`. The source is baked into the image, so restarting alone keeps running the old version.

### Without Compose

Build the image:

```bash
docker build -t librusik .
```

Then run it, mounting `/app/data` so your config and database survive a restart:

```bash
docker run -d -p 7777:7777 -e TZ=Europe/Warsaw -v $(pwd)/data:/app/data --name librusik librusik
```

Set `TZ` to your own timezone - without it the container runs on UTC, which shifts the notification quiet hours and every timestamp shown to users.

*On Windows PowerShell, quote the volume so it stays a single argument: `-v "${PWD}/data:/app/data"`. Unquoted, PowerShell splits it in two and Docker reports `invalid reference format`.*

Librusik is now running at [localhost:7777](http://localhost:7777).

-----

## Reporting a bug

**Feel free** to open new issues when something doesn't work or you want to ask for new features/improvements.

If you encounter a bug, remember to attach some logs (exception traceback or just a detailed description).

Also, **[ping me somewhere](https://dani3l0.dev/#contact)** so we can test whether fixes work as intended as I have no access to Librus anymore.

-----

## Some other words

Because this was my first app written in Python, code is a terrible mess. Don't expect it to be super readable and flexible.

_It just works_ (It actually worked since 2019 xD)
