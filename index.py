#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
from discord import app_commands
from discord.ext import commands
import os
import re
from datetime import datetime

# ==================== CONFIGURATION ====================
TOKEN = os.getenv('DISCORD_TOKEN')

# ==================== CHARGEMENT ====================
def load_data():
    data = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "message.txt")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        print(f"📁 Fichier trouvé : {file_path}")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            parts = [p.strip() for p in parts if p.strip()]

            if len(parts) < 6:
                continue

            email = parts[2] if len(parts) > 2 else ''
            full_name = parts[3] if len(parts) > 3 else ''
            address = parts[4] if len(parts) > 4 else ''
            location = parts[5] if len(parts) > 5 else ''
            country = parts[6] if len(parts) > 6 else 'United States'
            phone = parts[7] if len(parts) > 7 else ''

            # extraction ville/état/zip
            city = state = zip_code = ''
            if location:
                m = re.search(r'(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', location)
                if m:
                    city, state, zip_code = m.group(1).strip(), m.group(2), m.group(3)
                else:
                    city = location

            data.append({
                'email': email,
                'nom': full_name,
                'adresse': address,
                'ville': city,
                'etat': state,
                'zip': zip_code,
                'pays': country,
                'telephone': re.sub(r'[^\d+]', '', phone)
            })

        print(f"✅ {len(data)} entrées chargées")
        return data

    except Exception as e:
        print(f"❌ Erreur de chargement : {e}")
        return []

DATA = load_data()
TOTAL = len(DATA)

# ==================== BOT ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

current_page = 0

def domain(email):
    return email.split('@')[1].lower() if '@' in email else 'inconnu'

def filtered_by(domain_name):
    return [e for e in DATA if domain_name in domain(e.get('email', ''))]

def embed_for(index, liste, total, label):
    if not liste:
        return discord.Embed(title="📭 Aucune donnée", color=0xe74c3c)

    e = liste[index]
    embed = discord.Embed(
        title=f"👤 {index+1} / {total}",
        color=0x00d4ff,
        timestamp=datetime.now()
    )
    embed.add_field(name="📧 Email", value=e.get('email', 'N/A'), inline=False)
    embed.add_field(name="👤 Nom", value=e.get('nom', 'N/A'), inline=True)
    embed.add_field(name="📍 Ville", value=e.get('ville', 'N/A'), inline=True)
    embed.add_field(name="🏛️ État", value=e.get('etat', 'N/A'), inline=True)
    embed.add_field(name="📮 Zip", value=e.get('zip', 'N/A'), inline=True)
    embed.add_field(name="🌍 Pays", value=e.get('pays', 'N/A'), inline=True)
    embed.add_field(name="📞 Téléphone", value=e.get('telephone', 'N/A'), inline=True)
    embed.add_field(name="🏠 Adresse", value=e.get('adresse', 'N/A'), inline=False)
    embed.set_footer(text=f"{label or 'Total'} : {total} entrées")

    return embed

class NavView(discord.ui.View):
    def __init__(self, filtre=None):
        super().__init__(timeout=300)
        self.filtre = filtre
        self.update()

    def update(self):
        self.liste = filtered_by(self.filtre) if self.filtre else DATA
        self.total = len(self.liste)
        global current_page
        if current_page >= self.total and self.total > 0:
            current_page = self.total - 1
        elif self.total == 0:
            current_page = 0

    @discord.ui.button(label="◀", style=discord.ButtonStyle.red)
    async def prev(self, interaction, btn):
        global current_page
        self.update()
        if self.total == 0:
            return await interaction.response.send_message("❌ Aucune donnée", ephemeral=True)
        if current_page > 0:
            current_page -= 1
        embed = embed_for(current_page, self.liste, self.total, self.filtre)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
    async def next(self, interaction, btn):
        global current_page
        self.update()
        if self.total == 0:
            return await interaction.response.send_message("❌ Aucune donnée", ephemeral=True)
        if current_page < self.total - 1:
            current_page += 1
        embed = embed_for(current_page, self.liste, self.total, self.filtre)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Gmail", style=discord.ButtonStyle.blurple)
    async def gmail(self, interaction, btn):
        global current_page
        self.filtre = 'gmail'
        self.update()
        current_page = 0 if self.total > 0 else 0
        embed = embed_for(0, self.liste, self.total, 'GMAIL')
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Yahoo", style=discord.ButtonStyle.blurple)
    async def yahoo(self, interaction, btn):
        global current_page
        self.filtre = 'yahoo'
        self.update()
        current_page = 0 if self.total > 0 else 0
        embed = embed_for(0, self.liste, self.total, 'YAHOO')
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Outlook", style=discord.ButtonStyle.blurple)
    async def outlook(self, interaction, btn):
        global current_page
        self.filtre = 'outlook'
        self.update()
        current_page = 0 if self.total > 0 else 0
        embed = embed_for(0, self.liste, self.total, 'OUTLOOK')
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Proton", style=discord.ButtonStyle.blurple)
    async def proton(self, interaction, btn):
        global current_page
        self.filtre = 'proton'
        self.update()
        current_page = 0 if self.total > 0 else 0
        embed = embed_for(0, self.liste, self.total, 'PROTON')
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.gray)
    async def reset(self, interaction, btn):
        global current_page
        self.filtre = None
        self.update()
        current_page = 0 if self.total > 0 else 0
        embed = embed_for(0, self.liste, self.total, None)
        await interaction.response.edit_message(embed=embed, view=self)

# ==================== COMMANDES ====================
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} connecté")
    print(f"📁 {TOTAL} entrées chargées")
    await bot.tree.sync()

@bot.tree.command(name="view", description="Affiche les données")
async def view(interaction: discord.Interaction):
    global current_page
    current_page = 0
    if TOTAL == 0:
        return await interaction.response.send_message("❌ Aucune donnée", ephemeral=True)
    view = NavView()
    embed = embed_for(0, DATA, TOTAL, None)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="stats", description="Statistiques")
async def stats(interaction: discord.Interaction):
    domaines = {}
    for e in DATA:
        d = domain(e.get('email', ''))
        domaines[d] = domaines.get(d, 0) + 1

    embed = discord.Embed(title="📊 Statistiques", color=0xffd93d)
    embed.add_field(name="📁 Total", value=str(TOTAL), inline=True)
    embed.add_field(name="📧 Domaines", value=str(len(domaines)), inline=True)
    top = "\n".join([f"`{d}`: {c}" for d, c in list(domaines.items())[:10]])
    if top:
        embed.add_field(name="🏆 Top", value=top, inline=False)

    await interaction.response.send_message(embed=embed)

# ==================== LANCEMENT ====================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token manquant")
    else:
        bot.run(TOKEN)