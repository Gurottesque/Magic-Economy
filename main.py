import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import asqlite

extensiones = ['commands.perfil', 'commands.admin', 'commands.leaderboard', 'commands.tienda', 'commands.magia']

# Subclaseando 
class MyBot(commands.Bot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def setup_hook(self):
        for extension in extensiones:
            await client.load_extension(extension)
        check_tempbans.start()
        clear_sistema.start()
        
    async def on_ready(self):
        print(f"Logging in as: {self.user}")




#Creando el cliente/bot
client = MyBot(command_prefix=commands.when_mentioned_or("$$"),intents=discord.Intents.all(),
                      case_insensitive=True, activity=discord.Game(name="con el clítoris de la melónmadre"))
client.remove_command('help')

#Esto es para los comandos "/"
tree = client.tree




"""''' FUNCIONES DEL BOT '''
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"¡Espera {error.retry_after:.2f} segundos antes de usar este comando nuevamente!")"""


#Sincronizar los comandos "/", se tiene que hacer cada que haya un cambio en estos tipos de comandos
@client.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx):

    synced = await ctx.bot.tree.sync()

    await ctx.send(f"Sincronizados {len(synced)} comandos")

@client.command()
@commands.guild_only()
@commands.is_owner()
async def load(ctx, extension : str):
    """Carga una extensión"""
    try:
        await client.load_extension(f"commands.{extension}")
    except (AttributeError, ImportError) as e:
        await ctx.send(f"Error loading extension error: {e}")
        return
    await ctx.send(f"loaded {extension}")

@client.command()
@commands.guild_only()
@commands.is_owner()
async def unload(ctx, extension : str):
    """Descarga una extensión"""
    try:
        await client.unload_extension(f"commands.{extension}")
    except (AttributeError, ImportError) as e:
        await ctx.send(f"Error loading extension error: {e}")
        return
    await ctx.send(f"unloaded {extension}")

@client.command()
@commands.guild_only()
@commands.is_owner()
async def actualizacion(ctx):

    embed = discord.Embed(title="WHEZZECONOMY 3.22",
                        description="➠ Autocompletado en los comandos ``comprar, objeto, usar`` con ``/`` para los disléxicos del server\n\n➠Antilloros **NERFEADO**\n~~Protege contra un Ticket~~ -> `Reduce el tiempo del ticket a un 25%`\n\n➠ Reducido los wisis necesarios para los rangos 'Payaso' y 'Dueño del circo'\n~~2000~~ -> `1000`\n~~5000~~ -> `2000`",
                        colour=discord.Colour.dark_purple())
    embed.set_image(url="https://cdn.discordapp.com/attachments/1029613068788957206/1096983482657411163/SPOILER_916f7624e2135a93176ecb478ef873ec.png")
    await ctx.send(embed=embed)



''' FUNCIONES DE LA BASE DE DATOS '''


async def añadir_usuario_database(memberid):
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.execute("INSERT OR IGNORE INTO usuarios VALUES (?, ?, ?, ?, ?, ?, ?)", (memberid, 0, 0, 0, "Ninguno", 0, 0))
            await con.commit()

async def añadir_varios_usuarios_database(miembros_id):
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.executemany("INSERT OR IGNORE INTO usuarios VALUES (?, ?, ?, ?)", [(miembro_id, 0, 0, 0, "Ninguno", 0, 0) for miembro_id in miembros_id])
            await con.commit()

@client.command()
@commands.guild_only()
@commands.is_owner()
async def db(ctx):
    print("Iniciando")
    guild = ctx.guild
    id_miembros = [member.id for member in guild.members if not member.bot]
    await añadir_varios_usuarios_database(id_miembros)
    print("Base de datos actualizada")


@client.event
async def on_member_join(member):
    if not member.bot:
        await añadir_usuario_database(member.id)

@client.event
async def on_guild_join(guild):
    print("Iniciando")
    id_miembros = [member.id for member in guild.members if not member.bot]
    await añadir_varios_usuarios_database(id_miembros)
    print("Base de datos actualizada")
            


''' FUNCIONES DEL SISTEMA '''


async def agregar_wis(id_usuario):
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.execute("UPDATE usuarios SET wisis = wisis + 1 WHERE usuario_id = ?", (int(id_usuario),))
            await cur.execute("UPDATE usuarios SET wisis_totales = wisis_totales + 1 WHERE usuario_id = ?", (int(id_usuario),))
            await con.commit()

async def validar_wisis(miembro_id, wiseado_id):

    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.execute("INSERT OR IGNORE INTO sistemawis (usuario_id, wiseado_id, count) VALUES (?, ?, ?);",(miembro_id, wiseado_id, 0))
            await cur.execute("UPDATE sistemawis SET count = count + 1 WHERE usuario_id = ? AND wiseado_id = ?", (miembro_id, wiseado_id))

            await cur.execute("SELECT count FROM sistemawis WHERE usuario_id = ? AND wiseado_id = ?", (miembro_id, wiseado_id))
            resultado = await cur.fetchone()

            if resultado[0] > 1:
                return False

            else:
                return True

@client.event
async def on_reaction_add(reaction, member):
    if str(reaction.emoji) == "<:whezze:1029620490408574987>" and member != reaction.message.author:


        if reaction.count > 2:
            await agregar_wis(reaction.message.author.id)
            return

        else:
            
            validacion = await validar_wisis(member.id, reaction.message.author.id)

            if validacion:
                await agregar_wis(reaction.message.author.id)
                return


@client.event
async def on_reaction_remove(reaction, member):
    if str(reaction.emoji) == "<:whezze:1029620490408574987>" and member != reaction.message.author:
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("UPDATE usuarios SET wisis = wisis - 1 WHERE usuario_id = ?", (int(reaction.message.author.id),))
                await cur.execute("UPDATE usuarios SET wisis_totales = wisis_totales - 1 WHERE usuario_id = ?", (int(reaction.message.author.id),))
                await con.commit()




''' TASK LOOP FUNCTIONS '''


@tasks.loop(seconds=120)
async def check_tempbans():
    # Verificar los bans temporales almacenados en la base de datos
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            current_time = datetime.utcnow().timestamp()
            await cur.execute('SELECT user_id FROM tempbans WHERE unban_time <= ?', (current_time,))
            expired_bans = await cur.fetchall()

            if len(expired_bans) == 0:
                return

            for ban in expired_bans:
                guild = await client.fetch_guild(1029613068008828968)
                await guild.unban(discord.Object(id=ban[0]),reason="Tiempo de ban finalizado.")
                await cur.execute('DELETE FROM tempbans WHERE unban_time <= ?', (current_time,))

@tasks.loop(seconds=40)
async def clear_sistema():
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.execute("DELETE FROM sistemawis")






                    

if __name__ == "__main__":
    client.run(TOKEN)
