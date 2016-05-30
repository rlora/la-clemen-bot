# LaClemenBot
Source code used to build **LaClemenBot**. A
Telegram bot assistant for **Clementina** (http://www.clementina.com.bo/).

The Bot was built using **telebot** as a starting point. For further instructions, please visit:
https://github.com/yukuku/telebot

**LaClemenBot** is available at: https://telegram.me/LaClemenBot

In addition to **telebot**'s approach, **LaClemenBot** uses **Wit** to extract customer `intent` and `dates`. This is used to determine if customer wants to know about the bakery schedule, needs a recommendation or wants additional info like `address`, `phone`, etc. 

![Entity extraction using Wit](http://www.clementina.com.bo/assets/images/bot.jpg)

Instructions
============

1. Follow **telebot** instructions to get started: https://github.com/yukuku/telebot

2. Open a **Wit** account at: https://wit.ai, create an app and get your `server access token` at the settings panel.

3. Update your `WIT_TOKEN` at `main.py`

4. Design and train your Wit conversation engine

5. Modify responses based on menu actions or customer intent

Usage recommendations
=====================

If you find this code **useful** and use it as a starting point for your **own** projects we kindly ask you to remove **photos** and **references** that are directly related to **Clementina**.