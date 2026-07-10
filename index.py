#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
from discord import app_commands
from discord.ext import commands
import re
import os
from datetime import datetime

# ==================== TOKEN DISCORD ====================
TOKEN = os.getenv('DISCORD_TOKEN')  # <-- Important pour Render / GitHub

# ==================== CHARGEMENT DU FICHIER ====================
def load_data():
    """Charge les données depuis message.txt dans le même dossier"""
    data = []
    
    # Chemin du fichier dans le même dossier que le script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "message.txt")
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        print(f"📁 Fichier trouvé : {file_path}")
        print(f"📄 {len(lines)} lignes lues")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Split par espaces multiples
            parts = re.split(r'\s{2,}', line)
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) < 6:
                continue
            
            # Extraction
            source = parts[0] if len(parts) > 0 else 'Coinbase'
            status = parts[1] if len(parts) > 1 else 'Verified'
            email = parts[2] if len(parts) > 2 else ''
            full_name = parts[3] if len(parts) > 3 else ''
            address = parts[4] if len(parts) > 4 else ''
            
            if len(parts) >= 9:
                city = parts[5] if len(parts) > 5 else ''
                state = parts[6] if len(parts) > 6 else ''
                zip_code = parts[7] if len(parts) > 7 else ''
                country = parts[8] if len(parts) > 8 else 'United States'
                phone = parts[9] if len(parts) > 9 else ''
            else:
                location = parts[5] if len(parts) > 5 else ''
                country = parts[6] if len(parts) > 6 else 'United States'
                phone = parts[7] if len(parts) > 7 else ''
                
                city = ''
                state = ''
                zip_code = ''
                
                match = re.search(r'(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', location)
                if match:
                    city = match.group(1).strip()
                    state = match.group(2)
                    zip_code = match.group(3)
                else:
                    city = location
            
            entry = {
                'Source': source,
                'Status': status,
                'Email': email,
                'Full_Name': full_name,
                'Address': address,
                'City': city,
                'State': state,
                'Zip': zip_code,
                'Country': country,
                'Phone': re.sub(r'[^\d+]', '', phone)
            }
            
            data.append(entry)
        
        print(f"✅ {len(data)} entrées chargées")
        return data
        
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé : {file_path}")
        return []
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return []

# ==================== CHARGEMENT ====================
DATA = load_data()
TOTAL = len(DATA)

# ==================== BOT DISCORD ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

current_page = 0

def get_domain(email):
    if '@' in email:
        return email.split('@')[1].lower()
    return 'inconnu'

def filter_by_domain(domain):
    if not domain:
        return DATA
    return [d for d in DATA if get_domain(d.get('Email', '')).startswith(domain.lower())]

def create_embed(index, filtered_data, total_filtered, filter_name):
    if not filtered_data:
        embed = discord.Embed(
            title="📭 Aucune donnée",
            description="Aucune entrée trouvée avec ce filtre.",
            color=0xe74c3c
        )
        return embed
    
    entry = filtered_data[index]
    
    embed = discord.Embed(
        title=f"👤 Entrée {index + 1} / {total_filtered}",
        color=0x00d4ff,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="📌 Source", value=entry.get('Source', 'N/A'), inline=True)
    embed.add_field(name="✅ Status", value=entry.get('Status', 'N/A'), inline=True)
    embed.add_field(name="👤 Nom", value=entry.get('Full_Name', 'N/A'), inline=True)
    embed.add_field(name="📧 Email", value=entry.get('Email', 'N/A'), inline=True)
    embed.add_field(name="📧 Domaine", value=get_domain(entry.get('Email', '')), inline=True)
    embed.add_field(name="🏠 Adresse", value=entry.get('Address', 'N/A')[:100], inline=False)
    embed.add_field(name="📍 Ville", value=entry.get('City', 'N/A'), inline=True)
    embed.add_field(name="🏛️ État", value=entry.get('State', 'N/A'), inline=True)
    embed.add_field(name="📮 Zip", value=entry.get('Zip', 'N/A'), inline=True)
    embed.add_field(name="🌍 Pays", value=entry.get('Country', 'N/A'), inline=True)
    embed.add_field(name="📞 Téléphone", value=entry.get('Phone', 'N/A'), inline=True)
    
    if filter_name:
        embed.set_footer(text=f"Filtre: {filter_name} | Total: {total_filtered}")
    else:
        embed.set_footer(text=f"Total: {total_filtered} entrées")
    
    return embed

class DataView(discord.ui.View):
    def __init__(self, filter_domain=None):
        super().__init__(timeout=300)
        self.filter_domain = filter_domain
        self.update_data()
    
    def update_data(self):
        if self.filter_domain:
            self.filtered_data = filter_by_domain(self.filter_domain)
            self.total = len(self.filtered_data)
            self.filter_name = self.filter_domain.upper()
        else:
            self.filtered_data = DATA
            self.total = len(DATA)
            self.filter_name = None
        
        global current_page
        if current_page >= self.total and self.total > 0:
            current_page = self.total - 1
        elif self.total == 0:
            current_page = 0
    
    @discord.ui.button(label="◀ Précédent", style=discord.ButtonStyle.red, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.update_data()
        if self.total == 0:
            await interaction.response.send_message("❌ Aucune donnée.", ephemeral=True)
            return
        if current_page > 0:
            current_page -= 1
        embed = create_embed(current_page, self.filtered_data, self.total, self.filter_name)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Suivant ▶", style=discord.ButtonStyle.green, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.update_data()
        if self.total == 0:
            await interaction.response.send_message("❌ Aucune donnée.", ephemeral=True)
            return
        if current_page < self.total - 1:
            current_page += 1
        embed = create_embed(current_page, self.filtered_data, self.total, self.filter_name)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📧 Gmail", style=discord.ButtonStyle.blurple, custom_id="filter_gmail")
    async def filter_gmail(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.filter_domain = 'gmail'
        self.update_data()
        current_page = 0 if self.total > 0 else 0
        if self.total == 0:
            await interaction.response.send_message("❌ Aucun email Gmail.", ephemeral=True)
            return
        embed = create_embed(current_page, self.filtered_data, self.total, "GMAIL")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📧 Yahoo", style=discord.ButtonStyle.blurple, custom_id="filter_yahoo")
    async def filter_yahoo(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.filter_domain = 'yahoo'
        self.update_data()
        current_page = 0 if self.total > 0 else 0
        if self.total == 0:
            await interaction.response.send_message("❌ Aucun email Yahoo.", ephemeral=True)
            return
        embed = create_embed(current_page, self.filtered_data, self.total, "YAHOO")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📧 Outlook", style=discord.ButtonStyle.blurple, custom_id="filter_outlook")
    async def filter_outlook(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.filter_domain = 'outlook'
        self.update_data()
        current_page = 0 if self.total > 0 else 0
        if self.total == 0:
            await interaction.response.send_message("❌ Aucun email Outlook.", ephemeral=True)
            return
        embed = create_embed(current_page, self.filtered_data, self.total, "OUTLOOK")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📧 Proton", style=discord.ButtonStyle.blurple, custom_id="filter_proton")
    async def filter_proton(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.filter_domain = 'proton'
        self.update_data()
        current_page = 0 if self.total > 0 else 0
        if self.total == 0:
            await interaction.response.send_message("❌ Aucun email Proton.", ephemeral=True)
            return
        embed = create_embed(current_page, self.filtered_data, self.total, "PROTON")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.gray, custom_id="reset")
    async def reset_filter(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_page
        self.filter_domain = None
        self.update_data()
        current_page = 0 if self.total > 0 else 0
        embed = create_embed(current_page, self.filtered_data, self.total, None)
        await interaction.response.edit_message(embed=embed, view=self)

# ==================== COMMANDES ====================
@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    print(f"📁 {TOTAL} entrées chargées")
    await bot.tree.sync()

@bot.tree.command(name="view", description="Affiche les données Coinbase")
async def view(interaction: discord.Interaction):
    global current_page
    current_page = 0
    if TOTAL == 0:
        await interaction.response.send_message("❌ Aucune donnée trouvée.", ephemeral=True)
        return
    view = DataView()
    embed = create_embed(0, DATA, TOTAL, None)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="stats", description="Affiche les statistiques")
async def stats(interaction: discord.Interaction):
    domains = {}
    for entry in DATA:
        domain = get_domain(entry.get('Email', ''))
        domains[domain] = domains.get(domain, 0) + 1
    
    embed = discord.Embed(
        title="📊 Statistiques",
        color=0xffd93d,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="📁 Total", value=str(TOTAL), inline=True)
    embed.add_field(name="📧 Domaines", value=str(len(domains)), inline=True)
    
    top_domains = "\n".join([f"`{d}`: {c}" for d, c in list(domains.items())[:10]])
    embed.add_field(name="🏆 Top domaines", value=top_domains, inline=False)
    
    await interaction.response.send_message(embed=embed)

# ==================== LANCEMENT ====================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Token Discord manquant !")
        print("   Définir la variable d'environnement DISCORD_TOKEN")
    else:
        bot.run(TOKEN)