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

__2. Say hi to your bot.__ Open the chat with your new bot and send it any message (`/start` is fine). A Telegram bot cannot message you first, so this step is required.

__3. Paste the URL into Librusik.__ Go to *Settings → Notification destination* and enter:

```
tgram://123456789:AAHfaKeToKeNfAkEtOkEnFaKeToKeN123
```

That's it - with no chat ID, Librusik notifies whoever talked to the bot. Hit **Send a test** to confirm it works, then flip on **Message notifications** in *Settings*.

__To notify several people instead:__ create a Telegram group, add your bot to it, send one message in the group, then find the group's chat ID (it starts with `-`) at:

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

and use it as the target:

```
tgram://123456789:AAHfaKeToKeNfAkEtOkEnFaKeToKeN123/-1001234567890
```

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

**A word on `notif_allowed_schemes`:** a destination URL makes your server send an outbound request wherever it points. On an instance with users you don't personally trust, keep this list tight - removing `json`/`jsons` in particular stops users from aiming Librusik at arbitrary HTTP endpoints on your network.

Librus doesn't offer any kind of push, so this is plain polling. Checking hourly is deliberate: log in too often and Librus may start rate-limiting or locking the account.

### If nothing arrives

*Settings → Notification destination* shows when the last check ran, or what went wrong. **Send a test** is the fastest way to tell a typo'd token from a working setup. For the full traceback, set `"debug": true` in `data/config.json` and watch the server output.

-----

## Installation (Docker) 🐳

If you prefer using Docker to keep your system clean, you can build and run Librusik using the included Dockerfile.

__1. Build the image:__
```bash
docker build -t librusik .

```

**2. Run the container:**
The default port is **7777**. You need to map it to your host machine.

```bash
docker run -d -p 7777:7777 --name librusik librusik

```

*Note: If you want to persist your data (config & database) so it survives container restarts, mount the `/app/data` volume:*

```bash
docker run -d -p 7777:7777 -v $(pwd)/data:/app/data --name librusik librusik

```

### Docker Compose

Alternatively, you can use `docker-compose`. Create a `docker-compose.yml` file in the project directory:

```yaml
services:
  librusik:
    image: librusik:latest
    container_name: librusik
    ports:
      - "7777:7777"
    volumes:
        - ./data:/app/data
    #   - librusik-data:/app/data
    restart: unless-stopped

# volumes:
#   librusik-data:
```

Then simply run:

```bash
docker compose up -d

```

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
