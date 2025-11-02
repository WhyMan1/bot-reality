# Domain Reality Checker Bot

⚡ **Domain Reality Checker Bot** — an advanced Telegram bot based on Python and Aiogram library for checking domains for suitability
- 🎯 **Contextual responses** — results appear in the relevant topic
- 📱 **Organization** — discussions don't mix between topics  
- 🔄 **Support for all commands** — prefix commands, mentions, and replies work

## 💬 Smart Group Operation

### 📋 Brief Reports with Reply
- In groups, the bot always responds **via reply** to the original message
- A **brief report** is sent to save space in chat
- A **"📄 Full Report in DM"** button is added to brief reports

### 📄 Full Reports in Direct Messages
- Full reports are **automatically sent to DM** of the user
- Command `!full domain.com` in group → full report comes to DM
- "📄 Full Report in DM" button → **smart bot link** with automatic query
- **Security**: deep link works for any user

💡 **How it works**: The button contains a link like `https://t.me/botname?start=full_domain.com`, which will automatically open the bot and request a full report. No prior setup is required!

### 🔄 Behavior by Chat Types
| Chat Type | Brief Report | Full Report | Button |
|----------|---------------|--------------|---------|
| **Direct Messages** | In the same chat | In the same chat | "Full Report" |
| **Groups/Supergroups** | Reply in group | Sending to DM | "📄 Full Report in DM" |
| **Topics in Supergroups** | Reply in topic | Sending to DM | "📄 Full Report in DM" |

## 🚀 Quick Start with Dockereality/VLESS Proxy. The bot works asynchronously, uses Redis for task queue management and result caching, and provides brief and full reports on domain checks.

## ✨ New Features

### 🚀 Retry Logic System
- **Exponential backoff** with configurable jitter
- **Automatic retries** for Redis, Telegram API, and domain checks
- **Flexible configuration** of timeout and number of attempts

### 📊 Batch Processing with Progress Bars
- **Automatic progress bar** for checking 3+ domains
- **Batch processing** of 3 domains at a time for optimization
- **Detailed execution statistics** (successful, from cache, errors)

### 📈 Analytics System
- **Collection of metrics** on bot usage and domain checks
- **Detailed reports** for the administrator (/analytics)
- **Tracking** of popular domains and user activity

### 🔒 Security for Group Chats
- **Group authorization** via environment variables
- **Automatic exit** from unauthorized groups
- **Flexible management** of the allowed groups list

### 🧵 Support for Topics in Supergroups
- **Smart replies** in the same topic where the bot was mentioned
- **Contextual work** with Telegram topics
- **Organized communication** in large groups

### 🎛️ Group Operation Mode
- **Prefix commands** (!check, !full, !help)
- **Bot mentions** (@botname domain.com)
- **Replies to bot messages** with new domains
- **Configurable command prefix**
- **Smart replies in groups**: brief reports with reply + "Full in DM" button
- **Full reports in DM**: automatic sending of full reports to direct messages

## 🔍 What it Checks

The bot performs a comprehensive domain check and returns a report including:

- 🌐 **DNS**: A-record (IPv4) resolution
- 📡 **Port scan**: Checking open TCP ports (80, 443, 8443)
- 🌍 **Geography and ASN**: IP geolocation, ASN, and provider
- 🚫 **Spamhaus**: IP check in Spamhaus blacklists
- 🟢 **Ping**: Latency to the server (in milliseconds)
- 🔒 **TLS**: TLS version (e.g., TLSv1.3), cipher, certificate validity
- 🌐 **HTTP**: HTTP/2 and HTTP/3 support, TTFB (time to first byte), redirects, server, presence of WAF and CDN
- 📄 **WHOIS**: Domain expiration date
- 🛰 **Suitability assessment**: Verdict on whether the domain is suitable for Reality (considers absence of CDN, HTTP/2 support, TLSv1.3, and ping < 50 ms)

### Example of a Brief Report
```
🔍 Check: 35photo.pro:443
✅ A: 185.232.233.233
🟢 Ping: ~25.0 ms
    🔒 TLS
✅ TLSv1.3 supported
    🌐 HTTP
❌ HTTP/2 not supported
❌ HTTP/3 not supported
🟢 WAF not detected
🟢 CDN not detected
    🛰 Suitability assessment
❌ Not suitable: HTTP/2 missing
[Full report]
```

### Example of a Full Report
```
🔍 Check: google.com:443
🌐 DNS
✅ A: 142.250.74.14
📡 Port scan
🟢 TCP 80 open
🟢 TCP 443 open
🔴 TCP 8443 closed
🌍 Geography and ASN
📍 IP: SE / Stockholm County / Stockholm
🏢 ASN: AS15169 Google LLC
✅ Not found in Spamhaus
🟢 Ping: ~7.7 ms
🔒 TLS
✅ TLSv1.3 supported
✅ TLS_AES_256_GCM_SHA384 used
⏳ TLS certificate expires in 65 days
🌐 HTTP
✅ HTTP/2 supported
✅ HTTP/3 (h3) supported
⏱️ TTFB: 0.13 sec
🔁 Redirect: https://www.google.com/
🧾 Server: Google Web Server
🟢 WAF not detected
⚠️ CDN detected: Google
📄 WHOIS
📆 Expiration date: 2028-09-14T04:00:00
🛰 Suitability assessment
❌ Not suitable: CDN detected (Google)
```

## � Bot Commands

### User Commands
- `/start` — Greeting and main menu
- `/check <domain>` — Brief domain check
- `/full <domain>` — Full domain check  
- `/mode` — Toggle output mode (brief/full)
- `/history` — Show last 10 checks

### Group Commands
- `!check <domain>` — Brief check in group
- `!full <domain>` — Full check in group
- `!help` — Help with commands in group
- `@botname <domain>` — Mention the bot for checking
- Reply to the bot's message with a new domain

### Administrative Commands
- `/adminhelp` — List of all admin commands
- `/reset_queue` — Reset the check queue
- `/clearcache` — Clear result cache
- `/analytics` — Show usage analytics
- `/groups` — Manage authorized groups
- `/groups_add <ID>` — Add group to authorized
- `/groups_remove <ID>` — Remove group from authorized
- `/groups_current` — Show current group ID

## 🤖 Bot Setup in @BotFather

### Quick Command Setup
A complete command template for setup in @BotFather is in the file [`BOTFATHER_COMMANDS.txt`](BOTFATHER_COMMANDS.txt).

#### Main commands for @BotFather:
```
/setcommands
start - 🚀 Launch the bot and show the menu
check - 🔍 Brief domain check
full - 📄 Full domain check
mode - ⚙️ Toggle output mode
history - 📜 Show recent checks
```

#### Setting the description:
```
/setdescription
Bot for checking domains for suitability for Reality/VLESS proxy. Checks DNS, TLS, HTTP/2, ping, WHOIS and issues brief/full reports. Supports group operation with smart replies.
```

#### Recommended settings:
- **Group mode**: Enable the ability to add to groups
- **Privacy**: `ENABLED` (the bot sees only commands and mentions)
- **Inline mode**: Optional for extended functionality

💡 **Full list of commands and settings** see in [`BOTFATHER_COMMANDS.txt`](BOTFATHER_COMMANDS.txt)

## ⚙️ Environment Variables

### Basic Settings
```env
BOT_TOKEN=your-telegram-bot-token          # Bot token from @BotFather
ADMIN_ID=123456789                         # Administrator ID
REDIS_HOST=redis                           # Redis host
REDIS_PORT=6379                            # Redis port
REDIS_PASSWORD=                            # Redis password (optional)
```

### Group Work Settings
```env
GROUP_MODE_ENABLED=true                    # Enable group operation
GROUP_COMMAND_PREFIX=!                     # Command prefix in groups
GROUP_OUTPUT_MODE=short                    # Output mode in groups: short (brief) or full (detailed)
AUTHORIZED_GROUPS=-1001234567890,-1009876543210  # IDs of authorized groups
AUTO_LEAVE_UNAUTHORIZED=false             # Automatically leave unauthorized groups
BOT_USERNAME=your_bot_username             # Bot username for deep links
```

### Additional Settings
```env
SAVE_APPROVED_DOMAINS=false               # Save the list of suitable domains
```

## 🔒 Security Setup for Groups

### 1. Get the Group ID
Add the bot to the group and use the command:
```
/groups_current
```

### 2. Authorize the group
Add the ID to the environment variable:
```env
AUTHORIZED_GROUPS=-1001234567890,-1009876543210
```

### 3. Automatic exit
To automatically exit from unauthorized groups:
```env
AUTO_LEAVE_UNAUTHORIZED=true
```

## 🧵 Working with Topics in Supergroups

The bot automatically determines the topic in which it was mentioned and replies in it:

- 🎯 **Contextual responses** — results appear in the relevant topic
- 📱 **Organization** — discussions don't mix between topics  
- 🔄 **Support for all commands** — prefix commands, mentions, and replies work

## �🚀 Quick Start with Docker

1. Make sure [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) are installed.

2. Create a `.env` file with the Telegram bot token received from `@BotFather`:
   ```bash
   echo "BOT_TOKEN=your-telegram-bot-token" > .env
   ```

3. Create a `docker-compose.yml` file:
   ```yaml
   services:
     bot:
       container_name: domain-bot
       image: ghcr.io/dignezzz/bot-reality:latest
       command: python bot.py
       environment:
         - BOT_TOKEN=${BOT_TOKEN}
         - REDIS_HOST=redis
         - REDIS_PORT=6379
       depends_on:
         - redis
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
         interval: 30s
         timeout: 5s
         retries: 3
       logging:
         driver: json-file
         options:
           max-size: "10m"
           max-file: "3"
           compress: "true"
     worker:
       container_name: domain-worker
       image: ghcr.io/dignezzz/bot-reality:latest
       command: python worker.py
       environment:
         - BOT_TOKEN=${BOT_TOKEN}
         - REDIS_HOST=redis
         - REDIS_PORT=6379
       depends_on:
         - redis
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
         interval: 30s
         timeout: 5s
         retries: 3
       deploy:
         replicas: 3
       logging:
         driver: json-file
         options:
           max-size: "10m"
           max-file: "3"
           compress: "true"
     redis:
       container_name: domain-redis
       image: redis:7
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
         interval: 10s
         timeout: 3s
         retries: 5
       logging:
         driver: json-file
         options:
           max-size: "5m"
           max-file: "2"
           compress: "true"
   ```

4. Start the containers:
   ```bash
   docker compose up -d
   ```

5. Check the logs to confirm the start:
   ```bash
   docker compose logs -f
   ```

## � Limits and Restrictions

### User Limits
- **10 checks per minute** per user
- **100 checks per day** per user
- **Automatic blocking** when exceeding limits

### Penalty System
- **5+ violations** → temporary blocking
- **Progressive time-outs**: 1 min → 5 min → 15 min → 1 hour
- **Automatic lifting** of blocks after the time expires

### Performance
- **Asynchronous processing** for high throughput
- **Redis caching** of results for 1 hour
- **Batch processing** for multiple checks
- **Automatic retries** on failures

## 🏗️ Architecture

### System Components
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Telegram  │───▶│    Bot      │───▶│   Redis     │
│   Updates   │    │  (bot.py)   │    │   Queue     │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ Analytics   │    │   Worker    │
                   │ Collector   │    │ (worker.py) │
                   └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │   Metrics   │    │   Domain    │
                   │  Storage    │    │  Checker    │
                   └─────────────┘    └─────────────┘
```

### Modules
- **`bot.py`** — main bot logic and command handling
- **`worker.py`** — worker for performing domain checks
- **`checker.py`** — domain checking module (DNS, TLS, HTTP, etc.)
- **`redis_queue.py`** — managing task queue in Redis
- **`retry_logic.py`** — retry logic system with exponential backoff
- **`progress_tracker.py`** — progress bars and batch processing
- **`analytics.py`** — collection and analysis of usage metrics

## 🛠️ Local Development

### Requirements
- Python 3.9+
- Redis 6.0+
- Docker & Docker Compose

### Installation for Development
1. Clone the repository:
   ```bash
   git clone https://github.com/DigneZzZ/bot-reality.git
   cd bot-reality
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env`

5. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis:7
   ```

6. Run the bot and worker:
   ```bash
   python bot.py &
   python worker.py
   ```

## �🛠 Local Launch without Docker

1. Install [Python 3.11+](https://www.python.org/downloads/) and [Redis](https://redis.io/docs/install/install-redis/).
2. Clone the repository:
   ```bash
   git clone https://github.com/dignezzz/bot-reality.git
   cd bot-reality
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   export BOT_TOKEN=your-telegram-bot-token
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   ```
5. Run the bot:
   ```bash
   python bot.py
   ```
6. In a separate terminal, run the worker:
   ```bash
   python worker.py
   redis-cli --version
   ```

## 🔧 Configuration and Monitoring

### Checking the Health
```bash
# Status of containers
docker-compose ps

# Logs of all services
docker-compose logs -f

# Logs of a specific service
docker-compose logs -f bot
docker-compose logs -f worker

# Monitoring Redis
docker exec -it domain-redis redis-cli monitor
```

### Usage Statistics
- Command `/analytics` — detailed analytics for the administrator
- Automatic collection of metrics by users and domains
- Performance and error tracking

## 🤝 Contributing to the Project

We welcome contributions to the development of the project! 

### How to Contribute:
1. Fork the repository
2. Create a branch for the new feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Reporting Issues:
- Use GitHub Issues to report bugs
- Provide a detailed description of the problem
- Include logs and steps to reproduce

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **[Aiogram](https://github.com/aiogram/aiogram)** — modern asynchronous library for Telegram Bot API
- **[Redis](https://redis.io/)** — fast in-memory data store
- **[Docker](https://docker.com/)** — containerization and orchestration
- **[OpenAI](https://openai.com/)** — AI assistant in development
- **[OpeNode.xyz](https://openode.xyz/)** — project support

## 🚀 What's Next?

### Planned Improvements:
- 🌐 **Web interface** for bot management
- 📊 **Advanced analytics** with graphs
- 🔄 **API for integration** with external services
- 🎯 **Machine learning** for improved domain assessment
- 🔒 **Additional security checks**

---

<div align="center">

**🌟 If the project was helpful, please give it a star!**

Made with ❤️ by [DigneZzZ](https://github.com/DigneZzZ) and AI

</div>

### Dependencies
- `aiogram`: Asynchronous framework for Telegram bots.
- `redis`: Client for interacting with Redis.
- `httpx`, `h2`: Checking HTTP/2 and HTTP/3.
- `requests`, `python-whois`: Requests to external APIs and WHOIS.
- `ping3`, `dnspython`: Ping and DNS requests.
- `aiohttp`: Asynchronous HTTP requests.

Full list in `requirements.txt`.

## 🤖 Using the Bot

Find the bot on Telegram and start interacting:

### Commands
- `/start`: Welcome message with inline buttons.
- `/check <domain>`: Brief report (e.g., `/check example.com`).
- `/full <domain>`: Full report (e.g., `/full example.com`).
- `/ping`: Check bot availability.
- `/history`: Last 10 user checks.

### Other Methods
- Send the domain directly: `example.com` (brief report).
- Send multiple domains separated by comma or newline:
  ```
  example.com, google.com
  ```
- Click the inline button "Full Report" to get a detailed result.

### Restrictions
- **Speed**: 10 checks per 30 seconds.
- **Daily limit**: 100 checks per user.
- **Penalties**: Incorrect requests may lead to temporary blocking (from 1 minute to 1 hour).

## 🔧 Configuration and Optimization

### Redis
To prevent Redis crashes, configure the Linux kernel parameter:
```bash
sudo sysctl vm.overcommit_memory=1
echo "vm.overcommit_memory=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Logging
Logs are stored in files:
- `bot.log`: Bot logs.
- `worker.log`: Worker logs.
- `checker.log`: Checking logs.
- `redis_queue.log`: Queue logs.

Docker logs are limited to 10 MB (3 files with compression).

### Healthcheck
- Bot and workers: Check `/health` on port 8080 (every 30 seconds).
- Redis: Check `redis-cli ping` (every 10 seconds).

## 🛠 CI/CD

Docker images are automatically built and published to [GitHub Container Registry](https://ghcr.io/dignezzz/bot-reality) via GitHub Actions. Configuration in `.github/workflows/docker.yml`.

## 🔒 Security

- Keep `BOT_TOKEN` in `.env` and don't publish it.
- Use environment variables instead of hard-coded values.
- Regularly update dependencies (`pip install -r requirements.txt --upgrade`).

## 👨‍💻 Development

1. Clone the repository:
   ```bash
   git clone https://github.com/dignezzz/bot-reality.git
   cd bot-reality
   ```
2. Copy `.env.sample` to `.env` and configure:
   ```bash
   cp .env.sample .env
   nano .env
   ```
3. Build and start:
   ```bash
   docker compose up --build -d
   ```

## 📜 License

Developed by [neonode.cc](https://neonode.cc). License: MIT. Contact for feedback or suggestions!
