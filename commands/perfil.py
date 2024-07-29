import discord
from discord.ext import commands
from main import client
import asqlite

"""Modulo de perfil
TO-DO:
"""

async def seleccionar_rango(wisis_totales):
	if wisis_totales < 100:
		return "Ninguno"

	elif wisis_totales >= 100 and wisis_totales < 500:
		return "Comediante de calle"

	elif wisis_totales >= 500 and wisis_totales < 1000:
		return "Comediante Stand-Up"

	elif wisis_totales >= 1000 and wisis_totales < 2000:
		return "Payaso"

	elif wisis_totales >= 2000:
		return "Dueño del circo"



class Perfil(commands.Cog): #Clase de cog para los comandos
    
    def __init__(self, client: commands.Bot):
        self.client = client
        
    @commands.hybrid_command(name="wisis", description="Muestra los wisis del usuario")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def wisis(self, ctx, usuario: discord.Member = None):
    	async with asqlite.connect('wisis.db') as con:
    		async with con.cursor() as cur:
		    	if usuario == None:
		    		usuario = ctx.author

		    	await cur.execute("SELECT wisis, wisis_totales FROM usuarios WHERE usuario_id = ?", (int(usuario.id),))
		    	whezzes = await cur.fetchone()
		    	embed = discord.Embed(title=f"{usuario.display_name} Whezzes",
			    					colour=discord.Colour.dark_gold())
		    	embed.add_field(name=f"<:whezze:1029620490408574987>", value=f"{whezzes[0]}")

		    	embed.add_field(name="\n<:whezze:1029620490408574987> **TOTALES**", value=f"{whezzes[1]}")
		    	embed.add_field(name="``Rango:``", value=f"**{await seleccionar_rango(whezzes[1])}**", inline=False)


		    	embed.set_thumbnail(url=usuario.display_avatar)


		    	await ctx.send(embed=embed)


    @commands.hybrid_command(name="inventario", description="Muestra el inventario")
    async def inventario(self, ctx):
    	async with asqlite.connect('wisis.db') as con:
    		async with con.cursor() as cur:
		    	await cur.execute("SELECT objeto_id, cantidad FROM inventario WHERE usuario_id = ? AND cantidad > 0", (int(ctx.author.id),))
		    	objetos = await cur.fetchall()

		    	embed = discord.Embed(title=f"🎒 Inventario de {ctx.author.name}",
		    						colour=discord.Colour.random())

		    	for objeto in objetos:
		    		cantidad = objeto[1]
		    		await cur.execute("SELECT nombre FROM objetos WHERE objeto_id = ?", (objeto[0],))
		    		nombre = await cur.fetchone()

		    		embed.add_field(name=f"{nombre[0]}", value=f"Tienes: **{cantidad}**")

		    	await ctx.send(embed=embed)

    	




async def setup(client):
    await client.add_cog(Perfil(client))