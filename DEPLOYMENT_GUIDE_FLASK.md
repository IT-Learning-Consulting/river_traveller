# Deploying WFRP Traveling Bot to Render (Flask Method - 24/7 Free Tier!)

## Why This Method?

This approach uses **Flask web server** to keep your bot alive 24/7 on Render's **FREE tier**!

### How It Works:
1. Your Discord bot runs alongside a Flask web server
2. External monitoring services ping your Flask server every 5-10 minutes
3. This keeps Render from spinning down your service
4. Result: **Free 24/7 Discord bot hosting!**

## Prerequisites
- GitHub account
- Render account (free tier)
- Discord Bot Token
- UptimeRobot account (free, for keeping bot alive)

---

## Step-by-Step Deployment Guide

### Step 1: Push Your Code to GitHub

1. **Commit all changes:**
   ```bash
   cd "e:\foundry_development\bots\travelling-bot"
   git add .
   git commit -m "Add Flask server for Render deployment"
   ```

2. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Name: `wfrp-traveling-bot` (or your choice)
   - Visibility: Public or Private
   - Don't initialize with README
   - Click "Create repository"

3. **Push your code:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/wfrp-traveling-bot.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 2: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended for easy integration)
4. Verify your email

---

### Step 3: Deploy as Web Service

1. **From Render Dashboard:**
   - Click "New +" button (top right)
   - Select "Web Service"

2. **Connect Repository:**
   - Click "Build and deploy from a Git repository"
   - Click "Next"
   - Find and click "Connect" next to your `wfrp-traveling-bot` repository
   - (If first time: authorize Render to access GitHub)

3. **Configure Service:**

   Fill in these settings:

   | Field | Value |
   |-------|-------|
   | **Name** | `wfrp-traveling-bot` |
   | **Region** | Choose closest to you |
   | **Branch** | `main` |
   | **Root Directory** | Leave blank |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `python main.py` |

4. **Environment Variables:**

   Click "Advanced" then "Add Environment Variable":

   | Key | Value |
   |-----|-------|
   | `DISCORD_TOKEN` | Your Discord bot token |
   | `PORT` | `8080` |

   To get your Discord token:
   - Go to https://discord.com/developers/applications
   - Select your application
   - Go to "Bot" section
   - Copy the token (Reset if needed)

5. **Select Plan:**
   - Choose **"Free"** plan
   - Scroll down and click "Create Web Service"

6. **Wait for Deployment:**
   - Watch the logs as Render builds and deploys
   - Look for: "We are ready to go in [Bot Name]"
   - Copy your service URL (e.g., `https://wfrp-traveling-bot.onrender.com`)

---

### Step 4: Set Up UptimeRobot (Keep Bot Alive 24/7)

This is the KEY to keeping your bot running on free tier!

1. **Create Account:**
   - Go to https://uptimerobot.com
   - Sign up for free account
   - Verify email

2. **Add New Monitor:**
   - Click "Add New Monitor"
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `WFRP Bot Keepalive`
   - **URL**: Your Render service URL (e.g., `https://wfrp-traveling-bot.onrender.com`)
   - **Monitoring Interval**: 5 minutes (free tier allows this)
   - Click "Create Monitor"

3. **Verify:**
   - UptimeRobot will now ping your bot every 5 minutes
   - This prevents Render from spinning down your service
   - Your bot stays online 24/7 for FREE!

---

### Step 5: Test Your Bot

1. **Check Render Logs:**
   - In Render dashboard, view your service
   - Click "Logs" tab
   - You should see:
     ```
     * Running on http://0.0.0.0:8080
     Synced X command(s)
     We are ready to go in [Your Bot Name]
     ```

2. **Test in Discord:**
   - Go to your Discord server
   - Try: `/hello`
   - Try: `/roll 1d20`
   - Bot should respond immediately!

3. **Check Flask Server:**
   - Visit your Render URL in browser
   - You should see: "WFRP Traveling Bot is alive! 🚢"

---

## Files Created for This Deployment

- **[server.py](e:\foundry_development\bots\travelling-bot\server.py)** - Flask web server
- **[main.py](e:\foundry_development\bots\travelling-bot\main.py)** - Updated to start Flask server
- **[requirements.txt](e:\foundry_development\bots\travelling-bot\requirements.txt)** - Added Flask dependency
- **[render.yaml](e:\foundry_development\bots\travelling-bot\render.yaml)** - Render configuration (Web Service)

---

## How the Bot Works Now

```
┌─────────────────────────────────────┐
│         Render Free Tier            │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Flask Web Server :8080     │◄─┼─── UptimeRobot pings every 5 min
│  └──────────────────────────────┘  │
│              ▲                      │
│              │                      │
│  ┌──────────────────────────────┐  │
│  │    Discord Bot (main.py)     │◄─┼─── Discord events
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

---

## Updating Your Bot

Whenever you make changes:

```bash
git add .
git commit -m "Your update message"
git push
```

Render automatically detects the push and redeploys!

---

## Troubleshooting

### Bot Not Responding in Discord

1. **Check Render Logs:**
   - Look for errors in the logs
   - Verify "We are ready to go" message appears

2. **Check Discord Token:**
   - Ensure `DISCORD_TOKEN` env var is set correctly
   - Token hasn't been regenerated

3. **Check Discord Intents:**
   - Go to Discord Developer Portal
   - Your Application → Bot
   - Enable "MESSAGE CONTENT INTENT"
   - Enable "SERVER MEMBERS INTENT"

### Flask Server Not Responding

1. **Check PORT variable:**
   - Ensure `PORT=8080` is set in environment variables

2. **Check Render URL:**
   - Try visiting the URL in browser
   - Should see "WFRP Traveling Bot is alive! 🚢"

3. **Check Logs:**
   - Look for Flask startup message
   - Look for any Python errors

### Bot Goes Offline

1. **Check UptimeRobot:**
   - Is the monitor active?
   - Is it pinging every 5 minutes?
   - Check the monitor's status

2. **Check Render Service:**
   - Is it showing as "Live"?
   - Check for any build/deployment errors

### Commands Not Syncing

1. **Manual Sync:**
   - Bot automatically syncs on startup
   - Check logs for "Synced X command(s)"

2. **Discord Cache:**
   - Commands may take a few minutes to appear
   - Try restarting Discord
   - Try in a different server

---

## Cost Breakdown

| Service | Cost | Purpose |
|---------|------|---------|
| **Render** | FREE | Hosting the bot |
| **UptimeRobot** | FREE | Keeping bot alive |
| **GitHub** | FREE | Code repository |
| **Discord** | FREE | Bot platform |
| **Total** | **$0/month** | 🎉 |

---

## Alternative Method (Without Flask)

If you don't want to use the Flask method:
- Deploy as "Background Worker" instead of "Web Service"
- Bot will work but spin down after 15 minutes
- Upgrade to Render's Starter plan ($7/month) for 24/7 uptime
- See `DEPLOYMENT_GUIDE.md` for instructions

---

## Limits & Important Notes

### Render Free Tier Limits:
- **750 hours/month** of runtime (more than enough for 24/7)
- **Shared resources** (may be slower than paid plans)
- **Automatic deploys** included
- **Custom domains** not included (use .onrender.com subdomain)

### UptimeRobot Free Tier Limits:
- **50 monitors** (you only need 1)
- **5-minute intervals** (perfect for our needs)
- **Email alerts** included

### Important:
- Keep your `.env` file LOCAL (never commit it!)
- Set environment variables in Render dashboard
- Your bot token is sensitive - never share it!

---

## Need Help?

### Resources:
- **Render Docs**: https://render.com/docs
- **Discord.py Docs**: https://discordpy.readthedocs.io
- **Flask Docs**: https://flask.palletsprojects.com

### Common Issues:
- Bot offline? Check UptimeRobot monitor
- Commands not working? Check Discord intents
- Deployment failed? Check Render logs

---

## Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web Service deployed on Render
- [ ] `DISCORD_TOKEN` environment variable set
- [ ] `PORT` environment variable set to 8080
- [ ] UptimeRobot monitor created and active
- [ ] Bot shows "online" in Discord
- [ ] Flask server responds at Render URL
- [ ] Bot responds to `/hello` command
- [ ] Bot stays online for 24+ hours

---

**Congratulations! Your Discord bot is now running 24/7 on Render's free tier!** 🎉🚢
