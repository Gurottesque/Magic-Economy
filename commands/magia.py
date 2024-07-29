import discord
from discord.ext import commands
from main import client
from datetime import datetime, timedelta
from typing import Literal
import random
import asyncio
import asqlite
from discord import app_commands
from magia.magia_clases import GameState

COOLDOWN_INVOCAR = 1
LOG_DURACION = 8
EPHEMERAL = True

class BotonesBatalla(
    discord.ui.View
):  #Esta clase define los botones del mensaje, solamente es usado para demostrar el flujo de los mensajes

    def __init__(self, client, game_state, user_id):
        super().__init__()
        self.client = client
        self.game_state = game_state
        self.jugador = game_state.jugador
        self.enemigo = game_state.enemigo
        self.user_id = user_id

    async def deshabilitar_botones(self):
        for item in self.children:
          if isinstance(item, discord.ui.Button):
            if item.disabled:
              item.disabled = False
            else:
              item.disabled = True
    async def realizar_accion(self, interaction: discord.Interaction, button: discord.Button, accion: str, accion_jugador: str, accion_enemigo: str, embedAtaque):

        # Decisión jugador
        freeze = self.jugador.isFreeze
        stun = self.jugador.isStun
        if freeze:
            if accion == "Atacar":
                embedAtaque.description += f"🥶 Has intentado **atacar** a ``{self.enemigo.name}`` pero estás **congelado**\n"
            elif accion == "Defender":
                embedAtaque.description += f"🥶 Has intentado **defenderte**, pero estás **congelado**\n"
            elif accion == "Magia":
                embedAtaque.description += f"🥶 Has intentado usar ``{self.jugador.hechizo}`` pero estás **congelado**\n"
        elif stun:
            if accion == "Atacar":
                embedAtaque.description += f"😵‍ Has intentado **atacar** a ``{self.enemigo.name}`` pero estás **stuneado**\n"
            elif accion == "Defender":
                embedAtaque.description += f"😵‍ Has intentado **defenderte** pero estás **stuneado**\n"
            elif accion == "Magia":
                embedAtaque.description += f"😵‍ Has intentado usar ``{self.jugador.hechizo}`` pero estás **stuneado**\n"
        else:
            await accion_jugador()
            if accion == "Atacar":
                embedAtaque.description += f"👊 Has atacado a ``{self.enemigo.name}``\n"
            elif accion == "Defender":
                embedAtaque.description += f"🛡️ Te has **defendido**\n"
            elif accion == "Magia":
                embedAtaque.description += f"🪄 Has usado ``{self.jugador.hechizo}``\n"
            elif accion == "Parry":
                embedAtaque.description += f"🤺 Has hecho un **Parry**\n"



        await interaction.edit_original_response(embed=embedAtaque)

        # Decision enemiga
        freeze = self.enemigo.isFreeze
        stun = self.enemigo.isStun
        if freeze:
            embedAtaque.description += f"🥶 ``{self.enemigo.name}`` está **congelado**\n"
        elif stun:
            embedAtaque.description += f"😵 ``{self.enemigo.name}`` está **stuneado**\n"
        else:
            await accion_enemigo(embedAtaque)

        await interaction.edit_original_response(embed=embedAtaque)

        # GameState
        battle_logs = await self.game_state.poll_event()
        await asyncio.sleep(1)
        embedAtaque.description += f"{battle_logs}"
        await interaction.edit_original_response(embed=embedAtaque)

        estado_combate = await self.game_state.is_gameover()

        if estado_combate == "GameOverJugador":
            await interaction.message.edit(embed=await gameOverEmbed(self.enemigo, interaction.user.id), view=None)
        elif estado_combate == "GameOverEnemigo":
            await interaction.message.edit(embed=await gameOverGanadorEmbed(self.enemigo, interaction.user.id), view=None)
        else:
            await interaction.message.edit(embed=await initialEmbed(self.jugador, self.enemigo), view=BotonesBatalla(self.client, self.game_state, interaction.user.id))


    @discord.ui.button(label="Atacar",style=discord.ButtonStyle.primary,emoji="⚔️")
    async def atacar(self, interaction: discord.Interaction, button: discord.Button):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "No puedes interactuar con esta batalla", ephemeral=True)
            return

        await self.deshabilitar_botones()
        await interaction.message.edit(view=self)

        embedAtaque = discord.Embed(title="■□■□ **DECISIONES** □■□■□",
                                    description="",
                                    colour=self.enemigo.colour)
        await interaction.response.send_message(embed=embedAtaque,
                                                delete_after=LOG_DURACION,
                                                ephemeral=EPHEMERAL)

        await self.realizar_accion(interaction, button, "Atacar", self.jugador.atacar, self.enemigo_decidir, embedAtaque)


    @discord.ui.button(label="Magia", style=discord.ButtonStyle.primary, emoji="✨")
    async def magia(self, interaction: discord.Interaction,button: discord.Button):

        if interaction.user.id != self.user_id:
          await interaction.response.send_message(
            "No puedes interactuar con esta batalla", ephemeral=True)
          return

        if self.jugador in self.game_state.cooldown_hechizo:
            turnos_faltantes = self.game_state.cooldown_hechizo[self.jugador] - self.game_state.turno
            await interaction.response.send_message(f"Este hechizo está en cooldown\nTurnos faltantes:``{turnos_faltantes + 1}``", ephemeral=True)
            return

        await self.deshabilitar_botones()
        await interaction.message.edit(view=self)

        embedAtaque = discord.Embed(title="■□■□ **DECISIONES** □■□■□",
                                    description="",
                                    colour=self.enemigo.colour)
        await interaction.response.send_message(embed=embedAtaque,
                                                delete_after=LOG_DURACION,
                                                ephemeral=EPHEMERAL)

        await self.realizar_accion(interaction, button, "Magia", self.jugador.usar_magia, self.enemigo_decidir, embedAtaque)

    @discord.ui.button(label="Defenderse",style=discord.ButtonStyle.primary,emoji="🛡️")
    async def defenderse(self, interaction: discord.Interaction, button: discord.Button):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "No puedes interactuar con esta batalla", ephemeral=True)
            return

        await self.deshabilitar_botones()
        await interaction.message.edit(view=self)

        embedAtaque = discord.Embed(title="■□■□ **DECISIONES** □■□■□",
                                    description="",
                                    colour=self.enemigo.colour)
        await interaction.response.send_message(embed=embedAtaque,
                                                delete_after=LOG_DURACION,
                                                ephemeral=EPHEMERAL)

        await self.realizar_accion(interaction, button, "Defender", self.jugador.defenderse, self.enemigo_decidir, embedAtaque)


    @discord.ui.button(label="Parry", style=discord.ButtonStyle.primary, emoji="🤺")
    async def parry(self, interaction: discord.Interaction, button: discord.Button):

        if interaction.user.id != self.user_id:
          await interaction.response.send_message(
            "No puedes interactuar con esta batalla", ephemeral=True)
          return

        if self.jugador in self.game_state.parry_cooldown:
            turnos_faltantes = self.game_state.parry_cooldown[self.jugador] - self.game_state.turno
            await interaction.response.send_message(f"El parry está en cooldown\nTurnos faltantes:``{turnos_faltantes + 1}``", ephemeral=True)
            return

        await self.deshabilitar_botones()
        await interaction.message.edit(view=self)

        embedAtaque = discord.Embed(title="■□■□ **DECISIONES** □■□■□",
                                    description="",
                                    colour=self.enemigo.colour)
        await interaction.response.send_message(embed=embedAtaque,
                                                delete_after=LOG_DURACION,
                                                ephemeral=EPHEMERAL)

        await self.realizar_accion(interaction, button, "Parry", self.jugador.parry, self.enemigo_decidir, embedAtaque)

        
    async def enemigo_decidir(self, embed):

        decision = await self.enemigo.decidir()
        decision = decision[0]
        await asyncio.sleep(1)

        if decision == "Atacar":
            embed.description += f"👊 {self.enemigo.name} te ha **atacado**\n\n"

        elif decision == "Magia":
            embed.description += f"🪄 ``{self.enemigo.name}`` ha usado ``{await nombre_magia(self.enemigo.magia)}``\n\n"

        elif decision == "Defender":
            embed.description += f"🛡️ ``{self.enemigo.name}`` se ha **defendido**\n\n"

        elif decision == "Parry":
            embed.description += f"🤺 ``{self.enemigo.name}`` ha hecho un **Parry**\n\n"



class BotonesCartas(discord.ui.View):

  def __init__(self, client, user_id, hechizos):
    super().__init__()
    self.client = client
    self.user_id = user_id
    self.hechizos = hechizos

  async def deshabilitar_botones(self):
    for item in self.children:
      if isinstance(item, discord.ui.Button):
        if item.disabled:
          item.disabled = False
        else:
          item.disabled = True

  @discord.ui.button(label="🌙", style=discord.ButtonStyle.primary)
  async def uno(self, interaction: discord.Interaction,
                button: discord.Button):

    if interaction.user.id != self.user_id:
      await interaction.response.send_message("No puedes interactuar con esta batalla", ephemeral=True)
      return

    await self.deshabilitar_botones()
    await interaction.message.edit(view=self)
    seleccionado, estado = await self.random_seleccionar()  # Selecciona un objeto/ hechizo random

    if estado == "Objeto":

      await self.insertar_objeto(interaction.user.id, seleccionado)

    elif estado == "Hechizo":

      await self.insertar_hechizo(interaction.user.id, seleccionado)

    embed = discord.Embed(title="🌙 Revelando Carta 🌙",
                          colour=discord.Colour.random())
    await interaction.response.send_message(embed=embed, delete_after=3.0)
    await asyncio.sleep(1)

    embed = discord.Embed(title="Carta revelada",
                          description=f"``{seleccionado}`` x1",
                          colour=discord.Colour.dark_purple())
    embed.set_image(
      url=
      "https://us.123rf.com/450wm/antusenoktanya/antusenoktanya2108/antusenoktanya210800026/173821970-tarjeta-magic-tarot-fondo-de-cielo-nocturno-con-estrellas-y-luna-creciente-sobre-fondo-negro-marco.jpg?ver=6"
    )
    await interaction.message.edit(embed=embed, view=None)

    await self.remover_mazo(interaction.user.id)

  @discord.ui.button(label="🔮", style=discord.ButtonStyle.primary)
  async def dos(self, interaction: discord.Interaction,
                button: discord.Button):

    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
        "No puedes interactuar con esta batalla", ephemeral=True)
      return

    await self.deshabilitar_botones()
    await interaction.message.edit(view=self)
    seleccionado, estado = await self.random_seleccionar(
    )  # Selecciona un objeto/ hechizo random

    if estado == "Objeto":

      await self.insertar_objeto(interaction.user.id, seleccionado)

    elif estado == "Hechizo":

      await self.insertar_hechizo(interaction.user.id, seleccionado)

    embed = discord.Embed(title="🔮 Revelando Carta 🔮",
                          colour=discord.Colour.random())
    await interaction.response.send_message(embed=embed, delete_after=3.0)
    await asyncio.sleep(1)

    embed = discord.Embed(title="Carta revelada",
                          description=f"``{seleccionado}`` x1",
                          colour=discord.Colour.dark_purple())
    embed.set_image(
      url=
      "https://media.istockphoto.com/id/1285236767/es/vector/carta-de-tarot-con-mano-y-planeta-tarjeta-m%C3%A1gica-dise%C3%B1o-boho-tatuaje-grabado-cubierta-para.jpg?s=170667a&w=0&k=20&c=NoGUo2jvIFprYpfHTV1835yG2WlvJgID_ZIe9eIM2Xc="
    )
    await interaction.message.edit(embed=embed, view=None)

    await self.remover_mazo(interaction.user.id)

  @discord.ui.button(label="🔺", style=discord.ButtonStyle.primary)
  async def tres(self, interaction: discord.Interaction,
                 button: discord.Button):

    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
        "No puedes interactuar con esta batalla", ephemeral=True)
      return

    await self.deshabilitar_botones()
    await interaction.message.edit(view=self)
    seleccionado, estado = await self.random_seleccionar(
    )  # Selecciona un objeto/ hechizo random

    if estado == "Objeto":

      await self.insertar_objeto(interaction.user.id, seleccionado)

    elif estado == "Hechizo":

      await self.insertar_hechizo(interaction.user.id, seleccionado)

    embed = discord.Embed(title="🔺 Revelando Carta 🔺",
                          colour=discord.Colour.random())
    await interaction.response.send_message(embed=embed, delete_after=3.0)
    await asyncio.sleep(1)

    embed = discord.Embed(title="Carta revelada",
                          description=f"``{seleccionado}`` x1",
                          colour=discord.Colour.dark_purple())
    embed.set_image(
      url=
      "https://media.discordapp.net/attachments/1029620174015434772/1116875721621643324/background-remove.png?width=424&height=424"
    )
    await interaction.message.edit(embed=embed, view=None)

    await self.remover_mazo(interaction.user.id)

  async def insertar_hechizo(self, usuario_id, hechizo):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute(
          "INSERT INTO magia (usuario_id, hechizo) VALUES (?, ?)",
          (usuario_id, hechizo))

  async def insertar_objeto(self, usuario_id, objeto):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        objeto_id = await get_objetoid(objeto)
        # Verificar si el objeto ya existe en el inventario
        await cur.execute(
          "SELECT usuario_id FROM inventario WHERE objeto_id = ? AND usuario_id = ?",
          (objeto_id, usuario_id))
        resultado = await cur.fetchone()

        # Si no existe, crea una row en la db, si existe, actualiza el valor de la cantidad
        if resultado == None:
          await cur.execute(
            "INSERT INTO inventario (usuario_id, objeto_id, cantidad) VALUES (?, ?, ?)",
            (usuario_id, objeto_id, 1))
        else:
          await cur.execute(
            "UPDATE inventario SET cantidad = cantidad + ? WHERE usuario_id = ? AND objeto_id = ?",
            (1, usuario_id, objeto_id))

  async def random_seleccionar(self):

    lista_objetos = ["BanTicket", "TimeoutTicket", "Antilloros", "Rol", "MazoMagico"]
    lista_hechizos = ["Stellar Drip", "Wealth Wraith", "Gucci Invoker", "Touch of Gangsta",
      "Keez Deez Nuts", "Holy Sheesh", "Thug Freeze"]

    for hechizo in self.hechizos:
        lista_hechizos.remove(hechizo)

    lista = lista_objetos + lista_hechizos
    probabilidades = [0.01, 0.08, 0.09, 0.11, 0.15]
    for i in range(0,len(lista_hechizos)):
        probabilidades.append(0.5)

    seleccionado = random.choices(lista, probabilidades)[0]

    if seleccionado in lista[0:4]:
      estado = "Objeto"
    elif seleccionado in lista[5:len(lista)]:
      estado = "Hechizo"

    return seleccionado, estado

  async def remover_mazo(self, usuario_id):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute(
          "UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?",
          (usuario_id, await get_objetoid("MazoMagico")))




class Magia(commands.Cog):  #Clase de cog para los comandos

  def __init__(self, client: commands.Bot):
    self.client = client

  async def random_arcana(self):

    arcanas = [
      "El Loco", "El Mago", "El Hierofante", "La Justicia", "El Ahorcado",
      "El Diablo", "El Eon"
    ]

    prob = [0.6, 0.55, 0.5, 0.45, 0.4, 0.3, 0.22]

    combinados = list(zip(arcanas, prob))
    seleccionado = random.choices(combinados, weights=prob)
    arcana = seleccionado[0][0]
    probabilidad = seleccionado[0][1]

    if probabilidad in [0.55, 0.6]:
      rareza = "Comun"
      color = 0x808080
    elif probabilidad == 0.5:
      rareza = "Poco comun"
      color = 0x008F39
    elif probabilidad == 0.45:
      rareza = "Raro"
      color = 0x0000FF
    elif probabilidad in [0.4, 0.3]:
      rareza = "Legendario"
      color = 0xFFD300
    elif probabilidad == 0.22:
      rareza = "Astral"
      color = 0x7D2181

    if arcana == "El Loco":
      descripcion = "El Loco es un joven que combina sabiduría e insensatez, hace las cosas desordenadamente pero, curiosamente, están bien hechas y es normal que sean así. Este aspecto alocado y juvenil es un símbolo de la extraña naturaleza cuántica de la realidad."
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/5/53/Fool-0.png/revision/latest?cb=20200102070155&path-prefix=es"
      hechizo = "Stellar Drip"
    elif arcana == "El Mago":
      descripcion = "El mago es sinónimo del viejo sabio, que se remonta en línea directa a la figura del hechicero de la sociedad primitiva. Es, como el Ánima, un demonio inmortal, que ilumina con la luz del sentido las caóticas oscuridades de la vida pura y simple. Es el iluminador, el preceptor y maestro"
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/a/ac/66360212-10A7-41D7-B559-E95193F54218.png/revision/latest/scale-to-width-down/248?cb=20190517144102&path-prefix=es"
      hechizo = "Wealth Wraith"
    elif arcana == "El Hierofante":
      descripcion = "El Hierofante es el mediador entre lo mundano y lo divino. Es un puente entre la iluminación interna y la vida externa. Representa todas las estructuras que defienden sistemas de creencias."
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/f/f6/Hierophant-0.png/revision/latest?cb=20200416120350&path-prefix=es"
      hechizo = "Gucci Invoker"
    elif arcana == "La Justicia":
      descripcion = "La justicia encarna la Verdad y la ley. La balanza representa el equilibrio entre la intuición y la lógica, entre la severidad y la compasión. Su espada de doble filo es su imparcialidad, y su capacidad de ejecutar cualquier sentencia que dicte."
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/d/d4/5EA74E62-F55C-4813-9BC2-94881A7C0D31.png/revision/latest?cb=20200610142736&path-prefix=es"
      hechizo = "Touch of Gangsta"
    elif arcana == "El Ahorcado":
      descripcion = "El Ahorcado está ahí por voluntad propia, representa el sacrificio positivo y la aceptación, expresa la capacidad de renuncia para crear algo nuevo en aras de un bien mayor. Es la voluntad del sacrificio propio para una recompensa universal."
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/4/4b/B0667AE1-B07A-4AF2-AE82-96E8F0F9AB46.png/revision/latest?cb=20200926123420&path-prefix=es"
      hechizo = "Keez Deez Nuts"
    elif arcana == "El Diablo":
      descripcion = "Retratado como un demonio con forma de cabra frente a dos figuras desnudas y encadenadas, el Arcana del Diablo representa la necesidad de hacer cosas egoístas, impulsivas y violentas, ser esclavo de los propios impulsos y sentimientos. Ocasionalmente, también se representa como un símbolo de tentación."
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/3/35/E3BD5787-81B2-4FB5-820C-65B2E9705D4D.png/revision/latest?cb=20200620055837&path-prefix=es"
      hechizo = "Holy Sheesh"
    elif arcana == "El Eon":
      descripcion = "El Eón simboliza y condensaría precisamente la perpetuidad del tiempo. Lo eterno del universo, del tiempo y el destino, lo enigmático de la existencia y lo interminable de la historia. Es la carta más poderosa que existe, a quien obtenga este arcana su futuro estará lleno de gloria y miseria, sólo tú podrás saber cómo controlarlo."
      imagen = "https://static.wikia.nocookie.net/megamitensei/images/2/26/D9C3C2D4-8A06-452D-AD2E-0F3AD73B3520.png/revision/latest?cb=20200722115040&path-prefix=es"
      hechizo = "Thug Freeze"

    return arcana, rareza, color, descripcion, imagen, hechizo

  @commands.hybrid_command(name="invocar",
                           description="Invoca un shadow wizard")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def invocar(self, ctx):


    #await cur.execute("SELECT user_id FROM sistema_magia WHERE user_id = ?",(ctx.author.id, ))
    #resultado = await cur.fetchone()
    #if not (resultado is None):
    #    await ctx.send(f"Puedes volver a invocar un mago cada {COOLDOWN_INVOCAR} minutos, intenta de nuevo más tarde")
    #    return

    wisis = 0
    hechizo = None
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.execute(
              "SELECT wisis_totales FROM usuarios WHERE usuario_id = ?",
              (ctx.author.id, ))
            resultado = await cur.fetchone()
            wisis = resultado[0]
            if wisis < 50:
              await ctx.send(
                f"Necesitas tener mas de 50 wisis totales para invocar a un mago")
              return
            await cur.execute(
              "SELECT hechizo_activo FROM usuarios WHERE usuario_id = ?",
              (ctx.author.id, ))
            resultado = await cur.fetchone()
            hechizo = resultado[0]

            if hechizo == "Ninguno":
              embed = discord.Embed(
                title="¡No puedes entrar a una batalla sin un hechizo activo!",
                description=
                f"Puedes obtener un hechizo usando /arcana o en un mazo mágico")
              await ctx.send(embed=embed)
              return

            des_cooldown = datetime.utcnow() + timedelta(minutes=COOLDOWN_INVOCAR)
            await cur.execute(
              'INSERT OR REPLACE INTO sistema_magia (user_id, des_cooldown) VALUES (?, ?)',
              (int(ctx.author.id), des_cooldown.timestamp()))

    game_state = GameState(wisis, ctx.author.name, hechizo)
    await game_state.inicializar()

    jugador = game_state.jugador
    enemigo = game_state.enemigo
    await enemigo.inicializar()
    await jugador.inicializar()

    await ctx.send(embed=await initialEmbed(jugador, enemigo),
                   view=BotonesBatalla(client, game_state, ctx.author.id))

  @commands.hybrid_command(name="arcana",
                           description="Selecciona tu primer hechizo")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def arcana(self, ctx):

    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute("SELECT arcana FROM usuarios WHERE usuario_id = ?",
                          (ctx.author.id, ))
        resultado = await cur.fetchone()
        arcana = resultado[0]

        if not (arcana == 0):
          embed = discord.Embed(title="Ya Has seleccionado un arcana!",
                                colour=discord.Colour.random())
          await ctx.send(embed=embed)
          return

    embedArcana = discord.Embed(
      title="**Asignando arcana**",
      description=
      "*El Arcana es el medio por el cual todo se revela ...*\n*Solo el coraje ante la duda puede llevar a uno a la respuesta...*"
    )
    embedArcana.set_image(
      url="https://i.makeagif.com/media/5-07-2016/q9alNY.gif")
    embedArcana.set_thumbnail(url=ctx.author.avatar.url)

    msg = await ctx.send(embed=embedArcana)

    await asyncio.sleep(3)
    arcana, rareza, color, descripcion, imagen, hechizo = await self.random_arcana(
    )

    embedArcana.title = f"**{arcana}**\n{rareza}"
    embedArcana.description = f"*{descripcion}*\n\n**Hechizo**: `{hechizo}`"
    embedArcana.colour = color
    embedArcana.set_image(url=imagen)
    embedArcana.set_footer(text=f"Usa /grimorio para ver tu lista de hechizos")
    await msg.edit(embed=embedArcana)

    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute(
          "UPDATE usuarios SET arcana = 1 WHERE usuario_id = ?",
          (ctx.author.id, ))
        await cur.execute(
          "INSERT INTO magia (usuario_id, hechizo) VALUES (?, ?)",
          (ctx.author.id, hechizo))

  @commands.hybrid_command(
    name="grimorio", description="Muestra la lista de hechizos disponibles")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def grimorio(self, ctx):

    embed = discord.Embed(title=f"\t{ctx.author.display_name}'s 𝔊𝔯𝔦𝔪𝔬𝔯𝔦𝔬",
                          colour=discord.Colour.dark_purple())
    embed.set_thumbnail(
      url=
      "https://static.wikia.nocookie.net/yugiohenespanol/images/a/a0/Foto_grimorio_del_mundo_oscuro.jpg/revision/latest?cb=20120613002102&path-prefix=es"
    )
    embed.set_footer(
      text=
      f"Para equiparte un hechizo usa /hechizo <hechizo> (solo puedes tener 1 equipado)"
    )
    hechizos = None
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute(
          "SELECT DISTINCT hechizo FROM magia WHERE usuario_id = ?",
          (ctx.author.id, ))
        hechizos = await cur.fetchall()

        for hechizo in hechizos:
          embed.add_field(name=f"{hechizo[0]}",
                          value=f"`{await descripcion_magia(hechizo[0])}`")

    await ctx.send(embed=embed)

  async def hechizo_autocomplete(self, interaction: discord.Interaction,
                                 current: str):
    hechizos = [
      'Stellar Drip', 'Wealth Wraith', 'Gucci Invoker', 'Touch of Gangsta',
      'Keez Deez Nuts', 'Holy Sheesh', 'Thug Freeze'
    ]
    return [
      app_commands.Choice(name=hechizo, value=hechizo) for hechizo in hechizos
      if current.lower() in hechizo.lower()
    ]

  @app_commands.command(name="hechizo", description="Equipa un hechizo")
  @app_commands.autocomplete(hechizo=hechizo_autocomplete)
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def hechizo(self, interaction: discord.Interaction, hechizo: str):

    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute(
          "SELECT hechizo FROM magia WHERE usuario_id = ? AND hechizo = ?",
          (interaction.user.id, hechizo))
        hechizo_resultado = await cur.fetchone()

        if hechizo_resultado is None:
          await interaction.response.send_message(
            f"No tienes el hechizo `{hechizo}` en tu grimorio")
          return

        await cur.execute(
          "UPDATE usuarios SET hechizo_activo = ? WHERE usuario_id = ?",
          (hechizo, interaction.user.id))
        embed = discord.Embed(
          title="¡Hechizo equipado!",
          description=f"El hechizo `{hechizo}` ha sido equipado",
          colour=discord.Colour.random())
        await interaction.response.send_message(embed=embed)

  @commands.hybrid_command(name="additem_magico",
                           description="Añade un objeto mágico")
  @commands.cooldown(1, 10, commands.BucketType.member)
  @commands.is_owner()
  async def additem_magico(self, ctx, nombre: str, orbes: int,
                           descripcion: str):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM objetos WHERE nombre = ?",
                          (nombre, ))
        result = await cur.fetchone()

        if result[0] == 0:
          await cur.execute(
            "INSERT INTO objetos (nombre, orbes, descripcion) VALUES (?, ?, ?)",
            (nombre, orbes, descripcion))
          await con.commit()

          embed = discord.Embed(
            title="Objeto agregado",
            description=
            f"**Nombre:** {nombre}\n**Orbes:** {orbes}\n**Descripcion:** {descripcion}",
            colour=discord.Colour.blue())

          await ctx.send(embed=embed)

        else:
          embed = errorEmbed(
            "Ya existe un objeto con nombre similar en la base de datos")
          await ctx.send(embed=embed)

  @commands.hybrid_command(name="usar_mazo", description="Usa un mazo mágico")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def usar_mazo(self, ctx):
    # Obtener la ID del objeto
    objeto_id = await get_objetoid("MazoMagico")

    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        #Buscar por la cantidad de ese objeto en el inventario
        await cur.execute(
          "SELECT cantidad FROM inventario WHERE usuario_id = ? AND objeto_id = ?",
          (int(ctx.author.id), objeto_id))
        cantidad = await cur.fetchone()

        if cantidad == None or cantidad[0] == 0:
          await ctx.send(f"No tienes ningun **MazoMágico** en tu inventario")
          return

        await cur.execute("SELECT DISTINCT hechizo FROM magia WHERE usuario_id = ?", (ctx.author.id,))
        resultado = await cur.fetchall()

        hechizos = [fila[0] for fila in resultado]
        embed = discord.Embed(
          title="Selecciona una carta",
          description="*Detrás de cada carta hay un hechizo/objeto aleatorio*",
          colour=discord.Colour.random())
        embed.set_image(
          url=
          "https://cdn.discordapp.com/attachments/1029613068788957206/1116860342258114671/background-remove.png"
        )
        await ctx.send(embed=embed, view=BotonesCartas(client, ctx.author.id, hechizos))

  async def vender_autocomplete(self, interaction: discord.Interaction,
                                current: str):
    objetos = [
      'Zapatos Drip', 'Luna Oscura', 'Anillo de Ruby', 'Sphaera Ocularis',
      'Collar de la muerte', 'Joyería Mágica', 'Chumbo'
    ]
    return [
      app_commands.Choice(name=objeto, value=objeto) for objeto in objetos
      if current.lower() in objeto.lower()
    ]

  @app_commands.command(name="vender", description="Vende un objeto mágico")
  @app_commands.autocomplete(objeto=vender_autocomplete)
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def vender(self, interaction: discord.Interaction, objeto: str):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        objeto_id = await get_objetoid(objeto)

        await cur.execute(
          "SELECT comprable, valor FROM objetos WHERE objeto_id = ?",
          (objeto_id, ))
        resultado = await cur.fetchone()

        if resultado is None:
          await interaction.response.send_message("No existe este objeto")
          return
        if resultado[0] == 0:
          await interaction.response.send_message(
            "Este objeto no puede ser vendido")
          return

        orbes = resultado[1]

        await cur.execute(
          "SELECT cantidad FROM inventario WHERE usuario_id = ? AND objeto_id = ?",
          (interaction.user.id, objeto_id))
        resultado = await cur.fetchone()

        if resultado is None or resultado[0] == 0:
          await interaction.response.send_message(
            "No tienes este objeto en tu inventario")
          return

        await cur.execute(
          "UPDATE usuarios SET orbes = orbes + ? WHERE usuario_id = ?",
          (orbes, interaction.user.id))

        await cur.execute(
          "UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?",
          (interaction.user.id, objeto_id))

        embed = discord.Embed(
          title="¡Objeto vendido!",
          description=f"Has vendido el objeto {objeto} por 🔮 ``{orbes}``",
          colour=discord.Colour.dark_purple())
        await interaction.response.send_message(embed=embed)

  @commands.hybrid_command(name="logros", description="Mira tus logros")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def logros(self, ctx):

    embed = discord.Embed(title="Logros", colour=discord.Colour.random())

    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:

        await cur.execute("SELECT * FROM logros WHERE usuario_id = ?",
                          (ctx.author.id, ))
        usuario = await cur.fetchone()

        usuario_id, blue, green, yellow, orange, red, pink, purple = usuario[
          0], usuario[1], usuario[2], usuario[3], usuario[4], usuario[
            5], usuario[6], usuario[7]

        if blue > 0:
          embed.add_field(name="Derrota a Blue Mage",
                          value=f"Veces derrotado: {blue}")

        if green > 0:
          embed.add_field(name="Derrota a Green Wizard",
                          value=f"Veces derrotado: {green}")

        if yellow > 0:
          embed.add_field(name="Derrota a Yellow Sorcerer",
                          value=f"Veces derrotado: {yellow}")

        if orange > 0:
          embed.add_field(name="Derrota a Magus Orange",
                          value=f"Veces derrotado: {orange}")

        if red > 0:
          embed.add_field(name="Derrota a Red Magus",
                          value=f"Veces derrotado: {red}")

        if pink > 0:
          embed.add_field(name="Derrota a Pink Shot",
                          value=f"Veces derrotado: {pink}")

        if purple > 0:
          embed.add_field(name="Derrota a Purple Shadow",
                          value=f"Veces derrotado: {purple}")

    await ctx.send(embed=embed)

  @commands.hybrid_command(name="setorb",
                           description="Actualiza los orbes de un objeto")
  @commands.cooldown(1, 10, commands.BucketType.member)
  @commands.is_owner()
  async def setorb(self, ctx, objeto: str, cambio: int):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:

        await cur.execute("SELECT COUNT(*) FROM objetos WHERE nombre = ?",
                          (objeto, ))
        result = await cur.fetchone()

        if result[0] == 0:
          embed = errorEmbed(
            f"No se ha encontrado el objeto **{objeto}** en la base de datos")
          await ctx.send(embed=embed)
          return

        try:
          cambio = int(cambio)
        except:
          embed = errorEmbed(
            "El valor para el cambio no es válido, debe ser un entero mayor que 0"
          )
          await ctx.send(embed=embed)
          return

        if not cambio > 0:
          embed = errorEmbed(
            "El valor para el cambio no es válido, debe ser un entero mayor que 0"
          )
          await ctx.send(embed=embed)
          return

        await cur.execute("UPDATE objetos SET orbes = ? WHERE nombre = ?",
                          (int(cambio), objeto))

        embed = discord.Embed(title=f"¡Se han actualizado las orbes!",
                              colour=discord.Colour.green())
        await ctx.send(embed=embed)

        await con.commit()

  @commands.hybrid_command(name="giveorb", description="Da orbes a un usuario")
  @commands.cooldown(1, 10, commands.BucketType.member)
  @commands.is_owner()
  async def giveorb(self, ctx, usuario: discord.Member, orbes: int):
    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:
        await cur.execute(
          "UPDATE usuarios SET orbes = orbes + ? WHERE usuario_id = ?",
          (orbes, usuario.id))
        await con.commit()

        embed = discord.Embed(
          title=f"Orbes añadidos!",
          description=f"Se han añadido **{orbes}** a **{usuario.mention}**",
          colour=discord.Colour.green())
        await ctx.send(embed=embed)

  @commands.hybrid_command(name="idea", description="Envia una idea o sugerencia")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def idea(self, ctx, idea:str):
    yo = self.client.get_user(299658276638031873)
    dm = await self.client.create_dm(yo)
    embed = discord.Embed(title="Idea", description=f"{idea}\n\nEnviado por: {ctx.author.name}")
    await dm.send(embed=embed)
    await ctx.send("Idea enviada")

  @commands.hybrid_command(name="magiadb",
                           description="Actualiza base de datos")
  @commands.cooldown(1, 10, commands.BucketType.member)
  @commands.is_owner()
  async def magiadb(self, ctx):

    async with asqlite.connect('wisis.db') as con:
      async with con.cursor() as cur:

        await cur.execute(
          "CREATE TABLE magia (usuario_id INT, hechizo TEXT, FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id))"
        )
        await cur.execute(
          "CREATE TABLE logros (usuario_id INT,Blue_Mage INT,Green_Wizard INT,Yellow_Sorcerer INT,Magus_Orange INT,Red_Magus INT,Pink_Shot INT,Purple_Shadow INT, PRIMARY KEY (usuario_id))"
        )
        await cur.execute(
          "CREATE TABLE sistema_magia (user_id INTEGER PRIMARY KEY, des_cooldown INTEGER)"
        )

        await cur.execute("ALTER TABLE objetos ADD COLUMN orbes INT")
        await cur.execute("ALTER TABLE objetos ADD COLUMN comprable INT")

        await cur.execute("ALTER TABLE usuarios ADD COLUMN hechizo_activo TEXT"
                          )
        await cur.execute("ALTER TABLE usuarios ADD COLUMN arcana INT")
        await cur.execute("ALTER TABLE usuarios ADD COLUMN orbes INT")

        await cur.execute(
          "UPDATE usuarios SET hechizo_activo = ?, arcana = 0, orbes = 0",
          ("Ninguno", ))
        await cur.execute("UPDATE objetos SET orbes = 0")

        await cur.execute("UPDATE objetos SET comprable = 0")

        for member_id in [x.id for x in ctx.guild.members if not x.bot]:
          await cur.execute(
            "INSERT OR IGNORE INTO logros VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (member_id, 0, 0, 0, 0, 0, 0, 0))

        objetos = [
          "MazoMagico", "Chumbo", "Zapatos Drip", "Luna Oscura",
          "Anillo de Ruby", "Sphaera Ocularis", "Collar de la muerte",
          "Joyería Mágica"
        ]
        valores = [0, 200, 50, 75, 90, 100, 120, 150]
        descripciones = [
          "Mazo de tres cartas  con hechizos u objetos aleatorios",
          "Arma de Pink Shot, puede venderse a un buen precio en la tienda",
          "Zapatos de Blue Mage, puede venderse a buen precio en la tienda",
          "Luna que suelta Green Wizard al ser vencido, puede venderse en el mercado",
          "Anillo que suelta Red Flame al ser derrotado, puede venderse a buen precio",
          "Orbe mágico que suelta Yellow Sorcerer al ser derrotado, puede venderse a buen precio en la tienda",
          "Collar que suelta Magus Orange al ser derrotado, puede venderse a buen precio en la tienda",
          "Montón de joyas y accesorios que suelta Purple Shadow al ser derrotado, puede venderse a buen precio en la tienda"
        ]
        comprables = [0, 1, 1, 1, 1, 1, 1, 1]
        orbes = [300, 0, 0, 0, 0, 0, 0, 0]

        for nombre, valor, descripcion, comprable, orbe in zip(
            objetos, valores, descripciones, comprables, orbes):
          await cur.execute(
            "INSERT INTO objetos (nombre, valor, descripcion, comprable, orbes) VALUES (?, ?, ?, ?, ?)",
            (nombre, valor, descripcion, comprable, orbe))

        print("Opéración completada")

  @commands.hybrid_command(name="tutorial",
                           description="Tutorial sobre el evento de magia")
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def tutorial(self, ctx):

    embedTutorial = discord.Embed(
      title="Tutorial",
      description=
      "Los magos de las sombras han venido desde tierras prohibidas, para detenerlos debes enviarme una foto de tu tarjeta de crédito, los 3 números de atras y su fecha de vencimiento\n\n",
      colour=discord.Colour.dark_purple())

    embedTutorial.description += f"**[1]** Empieza asignando tu arcana, tu arcana es el poder principal y te dará un hechizo para iniciar, usa ``/arcana``\n\n"
    embedTutorial.description += f"**[2]** Para ver tu lista de hechizos usa ``/grimorio``, puedes conseguir hechizos con un mazo de cartas mágicas\n\n"
    embedTutorial.description += f"**[3]** Un mazo de cartas mágicas te puede dar un objeto (BanTicket, Antilloros,etc) o un hechizo aleatorio, puedes encontrarlo en la ``/tienda`` y cuesta **orbes**\n\n"
    embedTutorial.description += f"**[4]** Las **orbes** son las fichas del evento, ganaras orbes invocando magos, si los vences, te daran muchas más orbes\n\n"
    embedTutorial.description += f"**[5]** ¡Ya estás preparado para empezar! recuerda equiparte un hechizo con ``/hechizo`` y lanzate al combate con ``/invocar``\n\n"
    embedTutorial.description += f"**[6]** Una vez hayas derrotado un mago, desloquearas un logro ``/logros``\n\n"
    embedTutorial.set_image(
      url=
      "https://m.media-amazon.com/images/I/51XKHSpffkL._UXNaN_FMjpg_QL85_.jpg")

    await ctx.send(embed=embedTutorial)

  async def mago_autocomplete(self, interaction: discord.Interaction,
                              current: str):
    objetos = [
      'Blue Mage', 'Green Wizard', 'Yellow Sorcerer', 'Magus Orange',
      'Purple Shadow', 'Red Flame', 'Pink Shot'
    ]
    return [
      app_commands.Choice(name=objeto, value=objeto) for objeto in objetos
      if current.lower() in objeto.lower()
    ]

  @app_commands.command(name="magos",
                        description="Muestra información sobre un mago")
  @app_commands.autocomplete(mago=mago_autocomplete)
  @commands.cooldown(1, 10, commands.BucketType.member)
  async def mago(self, interaction: discord.Interaction, mago: str):

    diccionario_color = {
      "Blue Mage": discord.Colour.blue(),
      "Green Wizard": discord.Colour.dark_green(),
      "Yellow Sorcerer": discord.Colour.gold(),
      "Magus Orange": discord.Colour.orange(),
      "Purple Shadow": discord.Colour.dark_purple(),
      "Red Flame": discord.Colour.brand_red(),
      "Pink Shot": discord.Colour.fuchsia()
    }

    diccionario_imagen = {
      "Blue Mage":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116476419598450848/background-remove.png",
      "Green Wizard":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116476666055753738/background-remove.png",
      "Yellow Sorcerer":
      "https://cdn.discordapp.com/attachments/1029613068788957206/1116522060349444146/20230607_0342533.png",
      "Magus Orange":
      "https://cdn.discordapp.com/attachments/1029613068788957206/1116125599497453629/20230607_034151.jpg",
      "Purple Shadow":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116477569961832508/background-remove.png",
      "Red Flame":
      "https://cdn.discordapp.com/attachments/1029613068788957206/1116523129209102387/imagen.png",
      "Pink Shot":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116478265033498694/background-remove.png"
    }

    diccionario_descripcion = {
      "Blue Mage":
      "-Poco daño\n-Mucha vida\n\n✨**Hechizo** ``Stellar Drip`` (3 turnos CD): Inflinge ``30 %`` de la vida faltante enemiga como daño",
      "Green Wizard":
      "-Daño medio\n-Vida media\n✨**Hechizo** ``Wealth Wraith`` (4 turnos CD): Aumenta el daño de ataque durante 2 turnos",
      "Yellow Sorcerer":
      "-Mucho daño\n-Vida media\n✨**Hechizo** ``Gucci Invoker`` (3 turnos CD): ``70 %`` de probabilidad de reflejar el daño",
      "Magus Orange":
      "-Mucho daño\n-Vida media\n✨**Hechizo** ``Keez Deez Nuts`` (4 turnos CD): Cura un ``40%`` de la vida faltante",
      "Purple Shadow":
      "-Mucho daño\n-Poca vida\n✨**Hechizo** ``Thug Freeze`` (4 turnos CD): ``50 %`` de probabilidad de congelar por 3 turnos",
      "Red Flame":
      "-Mucho daño\n-Poca vida\n✨**Hechizo** ``Touch of Gangsta`` (4 turnos CD): Inflinge ``10 %`` de la vida máxima enemiga como daño durante 2 turnos",
      "Pink Shot":
      "-Mucho daño\n-Poca vida\n✨**Hechizo** ``Holy Sheesh`` (3 turnos CD): ``50 %`` probabilidades de inflingir la mitad de la vida enemiga como daño"
    }

    if mago not in diccionario_color:
      await interaction.response.send_message("El nombre del mago no es válido"
                                              )
      return

    embed = discord.Embed(title=f"{mago}",
                          description=f"{diccionario_descripcion[mago]}",
                          colour=diccionario_color[mago])
    embed.set_thumbnail(url=f"{diccionario_imagen[mago]}")

    await interaction.response.send_message(embed=embed)


async def initialEmbed(
    jugador, enemigo):  #Embed que muestra la información de la batalla
  embed = discord.Embed(title="", colour=enemigo.colour)
  embed.add_field(name=f"{jugador.name}",
                  value=f"**:heart: HP:** {int(jugador.hp)}")

  embed.add_field(
    name=f"{enemigo.name}",
    value=
    f'**:heart: HP:** {int(enemigo.hp)}\n\n*"{await enemigo.randomquote()}"*',
    inline=False)

  embed.set_image(url=enemigo.imagen)

  return embed


async def nombre_magia(funcion):

  nombre = funcion.__name__

  if nombre == "wealth_wraith":
    return "Wealth Wraith"

  elif nombre == "gucci_invoker":
    return "Gucci Invoker"

  elif nombre == "touch_of_gangsta":
    return "Touch of Gangsta"

  elif nombre == "keez_deez_nuts":
    return "Keez Deez Nuts"

  elif nombre == "holy_sheesh":
    return "Holy Sheesh"

  elif nombre == "thug_freeze":
    return "Thug Freeze"

  elif nombre == "stellar_drip":
    return "Stellar Drip"


async def descripcion_magia(nombre):

  dict_descripcion = {
    "Stellar Drip":
    "Inflinge 30% de la vida enemiga faltante como daño\nCooldown: 3 turnos",
    "Wealth Wraith":
    "Aumenta el daño *1.8 durante 2 turnos\nCooldown: 4 turnos",
    "Gucci Invoker":
    "60% de probabilidades de reflejar el daño enemigo\nCooldown: 3 turnos",
    "Touch of Gangsta":
    "Inflinge 10% de la vida enemiga máxima como daño cada 2 turnos\nCooldown: 4 turnos",
    "Keez Deez Nuts":
    "Cura un 30% de la vida faltante\nCooldown: 4 turnos",
    "Holy Sheesh":
    "30% de probabilidad de inflingir la mitad de la vida enemiga como daño\nCooldown: 3 turnos",
    "Thug Freeze":
    "40% de probabilidades de aturdir por 3 turnos\nCooldown: 3 turnos"
  }

  return dict_descripcion[nombre]


async def get_objetoid(nombre_objeto):
  async with asqlite.connect('wisis.db') as con:
    async with con.cursor() as cur:
      await cur.execute("SELECT objeto_id FROM objetos WHERE nombre = ?",
                        (nombre_objeto, ))
      resultado = await cur.fetchone()

      if resultado is None:
        return None
      return resultado[0]


async def gameOverEmbed(enemigo, usuario_id):  # Perdió el jugador
  embed = discord.Embed(title="", colour=enemigo.colour)

  embed.add_field(name=f"{enemigo.name}",
                  value=f'*"{enemigo.winQuote}"*',
                  inline=False)

  drop, cantidad = await drop_perder(enemigo, usuario_id)

  embed.add_field(name=f"Drop", value=f'``{drop} x{cantidad} ``', inline=False)

  embed.set_image(url=enemigo.imagen)

  return embed


async def gameOverGanadorEmbed(enemigo, usuario_id):  # Ganó el jugador
  embed = discord.Embed(title="", colour=enemigo.colour)

  embed.add_field(name=f"{enemigo.name}",
                  value=f'*"{enemigo.lostQuote}"*',
                  inline=False)

  diccionario_drops = await drop_ganar(enemigo, usuario_id)

  for item, cantidad in diccionario_drops.items():
    embed.add_field(name=f"Drop",
                    value=f'``{item} x{cantidad} ``',
                    inline=False)

  embed.set_image(url=enemigo.imagen)

  await añadir_logro(enemigo.name, usuario_id)

  return embed


async def añadir_logro(enemigo, usuario_id):
  enemigo = enemigo.replace(" ", "_")
  async with asqlite.connect('wisis.db') as con:
    async with con.cursor() as cur:
      await cur.execute(
        f"UPDATE logros SET {enemigo} = {enemigo} + 1 WHERE usuario_id = ?",
        (usuario_id, ))


async def drop_ganar(enemigo, usuario_id):
  diccionario_drops = {}
  objeto = None
  objeto_bool = False
  cantidad = random.randint(20, 50)
  diccionario_drops["Orbes"] = cantidad
  diccionario_drops[enemigo.objeto] = 1

  if random.random() < 0.2:
    objeto = await objeto_random()
    diccionario_drops[objeto] = 1
    objeto_bool = True

  async with asqlite.connect('wisis.db') as con:
    async with con.cursor() as cur:
      await cur.execute(
        "UPDATE usuarios SET orbes = orbes + ? WHERE usuario_id = ?",
        (cantidad, usuario_id))

      #Si ha salido un objeto random
      if objeto_bool:
        objeto_id = await get_objetoid(objeto)
        await añadir_objeto(usuario_id, objeto_id)

      objeto_id = await get_objetoid(enemigo.objeto)
      await añadir_objeto(usuario_id, objeto_id)

  return diccionario_drops


async def añadir_objeto(usuario_id, objeto_id):

  async with asqlite.connect('wisis.db') as con:
    async with con.cursor() as cur:
      # Verificar si el objeto ya existe en el inventario
      await cur.execute(
        "SELECT usuario_id FROM inventario WHERE objeto_id = ? AND usuario_id = ?",
        (objeto_id, usuario_id))
      resultado = await cur.fetchone()

      # Si no existe, crea una row en la db, si existe, actualiza el valor de la cantidad
      if resultado == None:
        await cur.execute(
          "INSERT INTO inventario (usuario_id, objeto_id, cantidad) VALUES (?, ?, ?)",
          (usuario_id, objeto_id, 1))
      else:
        await cur.execute(
          "UPDATE inventario SET cantidad = cantidad + ? WHERE usuario_id = ? AND objeto_id = ?",
          (1, usuario_id, objeto_id))


async def objeto_random():
  objetos = ["BanTicket", "TimeoutTicket", "Antilloros", "Rol", "MazoMagico"]
  probabilidad = [0.02, 0.09, 0.1, 0.2, 0.6]

  objeto = random.choices(objetos, probabilidad)

  return objeto[0]


async def drop_perder(enemigo, usuario_id):

  cantidad = random.randint(1, 11)
  drop = "Orbes"

  async with asqlite.connect('wisis.db') as con:
    async with con.cursor() as cur:
      await cur.execute(
        "UPDATE usuarios SET orbes = orbes + ? WHERE usuario_id = ?",
        (cantidad, usuario_id))
      await con.commit()

  return drop, cantidad


async def setup(client):
  await client.add_cog(Magia(client))
