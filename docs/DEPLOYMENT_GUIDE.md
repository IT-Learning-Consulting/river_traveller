# Deploying WFRP Traveling Bot to Render

## Prerequisites
- GitHub account
- Render account (free tier works!)
- Discord Bot Token

## Step-by-Step Deployment Guide

### Step 1: Push Your Code to GitHub

1. Make sure all your changes are committed:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   ```

2. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name it something like `wfrp-traveling-bot`
   - Don't initialize with README (you already have code)
   - Click "Create repository"

3. Push your code to GitHub:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/wfrp-traveling-bot.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Set Up Render Account

1. Go to https://render.com
2. Sign up for a free account (you can sign up with GitHub)
3. Verify your email if required

### Step 3: Create a New Web Service on Render

1. From your Render dashboard, click **"New +"** button
2. Select **"Background Worker"** (NOT Web Service - important!)
3. Choose **"Build and deploy from a Git repository"**
4. Click **"Connect" next to your GitHub repository**
   - If this is your first time, you'll need to authorize Render to access your GitHub
   - You can grant access to all repositories or just the bot repository

### Step 4: Configure Your Service

Fill in the following settings:

- **Name**: `wfrp-traveling-bot` (or any name you prefer)
- **Region**: Choose the closest region to you
- **Branch**: `main` (or `master` if that's your default branch)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`

### Step 5: Add Environment Variables

In the "Environment Variables" section, click **"Add Environment Variable"**:

- **Key**: `DISCORD_TOKEN`
- **Value**: Your Discord bot token (from Discord Developer Portal)

### Step 6: Select Your Plan

- Choose **"Free"** plan
- Note: Free tier will spin down after 15 minutes of inactivity
- For 24/7 uptime, upgrade to the $7/month Starter plan later

### Step 7: Deploy!

1. Click **"Create Background Worker"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies from requirements.txt
   - Start your bot with `python main.py`

3. Watch the deployment logs to ensure everything works correctly

### Step 8: Verify Your Bot is Running

1. Check the logs in Render dashboard for "We are ready to go in [Bot Name]"
2. Test your bot in Discord with `/hello` or other commands
3. If you see errors, check the logs in Render

## Important Notes

### Free Tier Limitations
- **Spin down after 15 minutes of inactivity**: Your bot will go offline
- This means your Discord bot won't be available 24/7 on the free tier
- For production use, consider upgrading to the paid tier ($7/month)

### Updating Your Bot
Whenever you push changes to your GitHub repository:
1. Commit and push changes: `git push`
2. Render will automatically detect changes and redeploy
3. You can also manually deploy from the Render dashboard

### Troubleshooting

**Bot doesn't start:**
- Check logs in Render dashboard
- Verify DISCORD_TOKEN is set correctly
- Make sure requirements.txt includes all dependencies

**Commands don't work:**
- Ensure your bot has proper intents enabled in Discord Developer Portal
- Check that MESSAGE CONTENT INTENT is enabled

**Bot goes offline:**
- Free tier limitation - upgrade to paid plan for 24/7 uptime

## Alternative: Keep Free Tier Alive

If you want to stay on free tier but keep your bot online longer, you can:
1. Use a service like UptimeRobot to ping a health endpoint (requires adding a small web server to your bot)
2. This is more complex and not recommended for Discord bots

## Recommended: Upgrade for Production

For a Discord bot that needs to be online 24/7:
- Upgrade to Render's **Starter plan** ($7/month)
- Your bot will run continuously without interruption
- Much more reliable for server members

## Files Created for Deployment

- `render.yaml`: Render configuration (optional, but helps with deployment)
- `.gitignore`: Ensures sensitive files aren't committed
- `requirements.txt`: Already existed, contains Python dependencies

## Questions?

If you encounter issues during deployment, check:
1. Render dashboard logs
2. Discord Developer Portal bot settings
3. GitHub repository connection in Render
