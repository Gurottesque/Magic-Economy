import discord
from discord.ext import commands
from main import client
import asqlite


""" Modulo de leaderboard
TO-DO:"""

class Leaderboard(commands.Cog): #Clase de cog para los comandos
    
    def __init__(self, client: commands.Bot):
        self.client = client
        
    @commands.hybrid_command(name="top", description="Muestra los usuarios con mas whezzes actuales")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def top(self, ctx):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT usuario_id, wisis FROM usuarios ORDER BY wisis DESC LIMIT 5")
                resultado = await cur.fetchall()

                embed = discord.Embed(title="💰 Top 5 más ricos del server",colour=discord.Colour.random())
                for ids in resultado:
                    usuario = await self.client.fetch_user(ids[0])
                    embed.add_field(name=f"{usuario.display_name}", value=f"<:whezze:1029620490408574987> **{ids[1]}**", inline=False)

                await ctx.send(embed=embed)


    @commands.hybrid_command(name="topwisis", description="Muestra los usuarios con mas whezzes totales")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def topwisis(self, ctx):
        
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT usuario_id, wisis_totales FROM usuarios ORDER BY wisis_totales DESC LIMIT 5")
                resultado = await cur.fetchall()

                embed = discord.Embed(title="🎪 Top 5 payasos del server",colour=discord.Colour.random())
                for ids in resultado:
                    usuario = await self.client.fetch_user(ids[0])
                    embed.add_field(name=f"{usuario.display_name}", value=f"<:whezze:1029620490408574987> **{ids[1]}**", inline=False)

                await ctx.send(embed=embed)

    	




async def setup(client):
    await client.add_cog(Leaderboard(client))