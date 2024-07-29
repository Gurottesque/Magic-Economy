import random
import discord

TAZA_DEFENSA = 0.3


class GameState:

  def __init__(self, wisis, nombre, hechizo):
    self.jugador = Jugador(wisis, nombre, self, hechizo)
    self.fabrica = FabricaEnemigos(wisis, self)
    self.enemigo = None
    self.turno = 0
    self.decision_jugador = None
    self.decision_enemigo = None
    self.map_cooldown = None
    self.cooldown_hechizo = {}
    self.wealth_diccionario = {}
    self.touch_diccionario = {}
    self.thugfreeze_diccionario = {}
    self.parryados = {}
    self.defensa_diccionario = {}
    self.parry_cooldown = {}
    self.battle_logs = "╭── ⋅ ⋅ ── ✩**ACCIONES**✩ ── ⋅ ⋅ ──╮ \n\n"

  async def inicializar(self):
    self.enemigo = await self.fabrica.crearRandomMago()
    self.map_cooldown = await self.map_cooldown_func(self.enemigo.magia)

  async def sumar_turno(self):
    self.turno += 1

  async def map_cooldown_func(self, magia):

    dict_cooldown = {
      self.stellar_drip: 3,
      self.wealth_wraith: 4,
      self.gucci_invoker: 3,
      self.touch_of_gangsta: 4,
      self.keez_deez_nuts: 4,
      self.holy_sheesh: 3,
      self.thug_freeze: 4
    }

    return dict_cooldown[magia]

  async def wealth_timer(self):
    wealth_copy = self.wealth_diccionario.copy()
    for objetivo, turno_final in wealth_copy.items():
      if turno_final < self.turno:
        objetivo.isDamageBuff = False
        del self.wealth_diccionario[objetivo]

  async def defensa_timer(self):
    defensa_copy = self.defensa_diccionario.copy()
    for objetivo, turno_final in defensa_copy.items():
      if turno_final < self.turno:
        objetivo.isReducingDamage = False
        del self.defensa_diccionario[objetivo]

  async def touchgangsta_timer(self):
    touch_copy = self.touch_diccionario.copy()
    for objetivo, turno_final in touch_copy.items():
      if turno_final < self.turno:
        del self.touch_diccionario[objetivo]
        return
      bef_vida_jugador = self.jugador.hp
      daño = objetivo.hp_total * 0.1
      objetivo.hp -= round(daño)
      self.battle_logs += f"💀 ``Touch of gangsta`` ha inflingido ``{round(daño)}`` de daño\n❤️``{bef_vida_jugador}`` -> ❤️ ``{self.jugador.hp}``\n"

  async def thugfreeze_timer(self):
    thug_copy = self.thugfreeze_diccionario.copy()
    for objetivo, turno_final in thug_copy.items():
      if turno_final < self.turno:
        objetivo.isFreeze = False
        del self.thugfreeze_diccionario[objetivo]
        return

  async def parry_stun_timer(self):
    parry = self.parryados.copy()
    for objetivo, turno_final in parry.items():
      if turno_final < self.turno:
        objetivo.isStun = False
        del self.parryados[objetivo]
        return

  async def cooldown_hechizos_timer(self):
    cooldown_copy = self.cooldown_hechizo.copy()
    for objetivo, cooldown in cooldown_copy.items():
      if cooldown < self.turno:
        del self.cooldown_hechizo[objetivo]

  async def cooldown_parry_timer(self):
    cooldown_copy = self.parry_cooldown.copy()
    for objetivo, cooldown in cooldown_copy.items():
      if cooldown < self.turno:
        del self.parry_cooldown[objetivo]

  async def battle_logs_restart(self):
    self.battle_logs = "╭── ⋅ ⋅ ── ✩**ACCIONES**✩ ── ⋅ ⋅ ──╮ \n\n"

  async def poll_event(self):

    await self.battle_logs_restart()
    jugador_evento = None
    daño = None
    enemigo_evento = None
    jugador = self.jugador
    enemigo = self.enemigo

    bef_vida_enemiga = round(self.enemigo.hp)
    bef_vida_jugador = round(self.jugador.hp)

    if self.decision_jugador == "Atacar":

      daño = await self.evento_atacar(jugador, enemigo)

      await enemigo.recibir_daño(daño)
      af_vida_enemiga = round(self.enemigo.hp)

      if af_vida_enemiga < 0:
        af_vida_enemiga = 0

    elif self.decision_jugador == "Magia":

      if jugador.magia in [self.stellar_drip, self.holy_sheesh]:

        daño = await jugador.magia(jugador, enemigo)

        if daño == 0:
          self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` ha fallado!\n\n"

        else:
          self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` hará ``{daño}`` de daño!\n\n"

        await enemigo.recibir_daño(daño)
        af_vida_enemiga = enemigo.hp

        if af_vida_enemiga <= 0:
          af_vida_enemiga = 0

        self.cooldown_hechizo[jugador] = self.turno + await self.map_cooldown_func(jugador.magia)

      elif jugador.magia in [self.keez_deez_nuts]:

        bef_vida_jugador = round(self.jugador.hp)

        curacion = round(await jugador.magia(jugador, enemigo))
        self.cooldown_hechizo[jugador] = self.turno + await self.map_cooldown_func(jugador.magia)
        af_vida_jugador = round(jugador.hp)

        self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` ha recuperado ``{curacion}`` de vida!\n❤️``{bef_vida_jugador}`` -> ❤️ ``{af_vida_jugador}``\n\n"

      else:
        acertar = self.jugador.Acertar
        if acertar:
          self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` ha **acertado**!\n\n"
        else:
          self.battle_logs += f"¡💫 ``{await nombre_magia(jugador.magia)}`` ha **fallado**!\n\n"

    elif self.decision_jugador == "Defender":
      x = 1
    elif self.decision_jugador == "Parry":
      x = 1

    else:
      if jugador.isFreeze:
        self.battle_logs += f"🥶 Estás ``congelado``\n\n"
      elif jugador.isStun:
        self.battle_logs += f"😵 Estás ``stuneado``\n\n"

    decision = self.decision_enemigo
    bef_vida_jugador = round(self.jugador.hp)
    bef_vida_enemigo = round(self.enemigo.hp)

    if decision == "Atacar":

      daño = await self.evento_atacar(enemigo, jugador)

      await jugador.recibir_daño(daño)
      af_vida_jugador = round(self.jugador.hp)

      if af_vida_jugador < 0:
        af_vida_jugador = 0

    elif decision == "Magia":

      if enemigo.magia in [self.stellar_drip, self.holy_sheesh]:

        daño = await enemigo.magia(enemigo, jugador)

        if daño == 0:
          self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` ha fallado!\n\n"

        else:
          self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` hará ``{daño}`` de daño!\n\n"

        await jugador.recibir_daño(daño)
        af_vida_jugador = jugador.hp

        if af_vida_jugador < 0:
          af_vida_jugador = 0

        self.cooldown_hechizo[
          enemigo] = self.turno + await self.map_cooldown_func(enemigo.magia
                                                                  )

      elif enemigo.magia in [self.keez_deez_nuts]:

        bef_vida_enemigo = round(self.enemigo.hp)

        curacion = round(await enemigo.magia(enemigo, jugador))
        self.cooldown_hechizo[
          enemigo] = self.turno + await self.map_cooldown_func(enemigo.magia
                                                                  )

        af_vida_enemiga = round(self.enemigo.hp)

        self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` ha recuperado ``{curacion}`` de vida!\n❤️``{bef_vida_enemigo}`` -> ❤️ ``{af_vida_enemiga}``\n\n"

      else:

        acertar = self.enemigo.Acertar
        if acertar:
          self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` ha **acertado**!\n\n"
        else:
          self.battle_logs += f"¡💫 ``{await nombre_magia(enemigo.magia)}`` ha **fallado**!\n\n"

    elif decision == "Defender":
      pass

    else:
      if enemigo.isFreeze:
        self.battle_logs += f"🥶 **{enemigo.name}** está ``congelado``\n\n"
      elif enemigo.isStun:
        self.battle_logs += f"😵 **{enemigo.name}** está ``stuneado``\n\n"

    await self.reiniciar_estados()
    await self.sumar_turno()
    await self.wealth_timer()
    await self.touchgangsta_timer()
    await self.thugfreeze_timer()
    await self.cooldown_hechizos_timer()
    await self.defensa_timer()
    await self.cooldown_parry_timer()
    await self.parry_stun_timer()

    self.battle_logs += "╰── ⋅ ⋅ ── ✩**ACCIONES**✩ ── ⋅ ⋅ ──╯"
    return self.battle_logs

  async def reiniciar_estados(self):
    self.jugador.isDefendido = False
    self.jugador.isReflecting = False
    self.enemigo.isDefendido = False
    self.jugador.isEsquivando = False
    self.enemigo.isEsquivando = False
    self.enemigo.isReflecting = False
    self.enemigo.isNegating = False
    self.jugador.isNegating = False
    self.jugador.Acertar = False
    self.jugador.isParry = False
    self.enemigo.isParry = False
    self.enemigo.Acertar = False
    self.decision_jugador = None
    self.decision_enemigo = None

  async def evento_atacar(self, atacante, objetivo):

    daño = random.randint(int(atacante.daño - 10), int(atacante.daño + 10))

    if atacante.isDamageBuff:
      daño *= 1.8

    return round(daño)

  async def stellar_drip(self, atacante,
                         objetivo):  # Ejecutarse en el poll event, hace daño
    vida_faltante_objetivo = objetivo.hp_total - objetivo.hp
    daño = round(vida_faltante_objetivo * 0.3)

    if atacante.isDamageBuff:
      daño *= 1.8

    return daño

  async def wealth_wraith(
      self, atacante,
      objetivo):  # Ejecutarse antes del poll event, boosteo de daño
    atacante.isDamageBuff = True
    self.wealth_diccionario[atacante] = self.turno + 2
    return True

  async def gucci_invoker(
      self, atacante,
      objetivo):  # Ejecutarse antes del poll event, estado actualizado
    probabilidad = random.random()
    if probabilidad < 0.7:
      atacante.isReflecting = True
      return True
    return False

  async def touch_of_gangsta(
      self, atacante,
      objetivo):  # Ejecutarse antes del poll event, estado debuff

    self.touch_diccionario[objetivo] = self.turno + 2
    return True

  async def keez_deez_nuts(self, atacante,
                           objetivo):  # Ejecutarse en el poll event, curacion

    hp_curar = (atacante.hp_total - atacante.hp) * 0.3

    atacante.hp += hp_curar
    return hp_curar

  async def holy_sheesh(self, atacante,
                        objetivo):  # Ejecutarse en el poll event, hace daño
    daño = 0
    if random.random() < 0.5:
      daño = round(objetivo.hp * 0.5)

    return daño

  async def thug_freeze(self, atacante,
                        objetivo):  # Ejecutarse antes del poll event, stun
    if random.random() < 0.5:
      if objetivo.isParry:
        self.parryados[enemigo] = self.turno + 1
        enemigo.isStun = True
        self.battle_logs += f"💫**PARRY!**💫 {enemigo.name} ha sido stuneado 😵‍\n\n"
        self.parry_cooldown[self] = self.turno + 3
        return
      objetivo.isFreeze = True
      self.thugfreeze_diccionario[objetivo] = self.turno + 3
      return True
    return False

  async def is_gameover(self):

    hp_jugador = self.jugador.hp
    hp_enemigo = self.enemigo.hp

    if hp_jugador < 0 and hp_enemigo > 0:
      return "GameOverJugador"

    elif hp_jugador < 0 and hp_enemigo < 0:

      if hp_jugador > hp_enemigo:
        return "GameOverEnemigo"
      else:
        return "GameOverJugador"

    elif hp_enemigo < 0 and hp_jugador > 0:
      return "GameOverEnemigo"

    return None




class FabricaEnemigos:

  def __init__(self, wisis, game_state):
    self.wisis = wisis
    self.game_state = game_state

  async def crearBlueMage(self):
    enemigo = Enemigo(name="Blue Mage",
                      daño=self.wisis * 0.13,
                      hp=self.wisis * 1.75,
                      hp_total=self.wisis * 1.75,
                      objeto="Zapatos Drip",
                      lostQuote="I... don't had... enough drip...",
                      winQuote="Your jordans are fake",
                      quotes=[
                            "Liches be actin' so tough, till you use holy magic",
                            "Die already, thou are losing precious magic time",
                            "Thou should cast a rope around your neck, NOW!"
                              ],
                      imagen="https://cdn.discordapp.com/attachments/1029620174015434772/1116476419598450848/background-remove.png",
                      magia=self.game_state.stellar_drip,
                      colour=discord.Colour.blue(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearGreenWizard(self):
    enemigo = Enemigo(name="Green Wizard",
                      daño=self.wisis * 0.17,
                      hp=self.wisis * 1.6,
                      hp_total=self.wisis * 1.6,
                      objeto="Luna Oscura",
                      lostQuote="Thou defeat me... This shalt be destiny",
                      winQuote="This rape was sponsored by the shadow government",
                      quotes=[
                          "Thou look like a virgin, i'll cast some bitches for thou",
                          "Look at those shiny jewelry, they bright more than your future",
                          "Shadow voices are whispering something..."
                            ],
                      imagen="https://cdn.discordapp.com/attachments/1029620174015434772/1116476666055753738/background-remove.png",
                      magia=self.game_state.wealth_wraith,
                      colour=discord.Colour.dark_green(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearRedFlame(self):
    enemigo = Enemigo(name="Red Flame",
                      daño=self.wisis * 0.32,
                      hp=self.wisis * 1.3,
                      hp_total=self.wisis * 1.3,
                      objeto="Anillo de Ruby",
                      lostQuote="I guess... This is the end...",
                      winQuote="Hueleme el dedo",
                      quotes=[
                            "Little nooby wizard doesn't know he is already lost",
                            "I wish i had some draconian zaza...",
                            "I can smell your fear, thou are worthless"
                            ],
                      imagen="https://cdn.discordapp.com/attachments/1029613068788957206/1116523129209102387/imagen.png",
                      magia=self.game_state.touch_of_gangsta,
                      colour=discord.Colour.brand_red(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearMagusOrange(self):
    enemigo = Enemigo(name="Magus Orange",
                      daño=self.wisis * 0.28,
                      hp=self.wisis * 1.5,
                      hp_total=self.wisis * 1.5,
                      objeto="Collar de la muerte",
                      lostQuote="I'll be tellin' da shadow government your achievements",
                      winQuote="Easy as fuck, come back when you can stand those spells",
                      quotes=[
                            "Don't waste my precious time with those nooby spells",
                            "What about casting some hoes", "Your momma goes harder than this"
                            ],
                      imagen="https://cdn.discordapp.com/attachments/1029613068788957206/1116125599497453629/20230607_034151.jpg",
                      magia=self.game_state.keez_deez_nuts,
                      colour=discord.Colour.orange(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearYellowSorcerer(self):
    enemigo = Enemigo(name="Yellow Sorcerer",
                      daño=self.wisis * 0.24,
                      hp=self.wisis * 1.5,
                      hp_total=self.wisis * 1.5,
                      objeto="Sphaera Ocularis",
                      lostQuote="It is what it is",
                      winQuote="My gay detector it's beeping",
                      quotes=[
                            "My magic ball already saw your power, this fight will be effortless",
                            "Apoco si muy verga", "Why are thou hurting yourself haha"
                            ],
                      imagen="https://cdn.discordapp.com/attachments/1029613068788957206/1116522060349444146/20230607_0342533.png",
                      magia=self.game_state.keez_deez_nuts,
                      colour=discord.Colour.gold(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearPurpleShadow(self):
    enemigo = Enemigo(name="Purple Shadow",
                      daño=self.wisis * 0.30,
                      hp=self.wisis * 1.4,
                      hp_total=self.wisis * 1.4,
                      objeto="Joyería Mágica",
                      lostQuote="You just had lucky",
                      winQuote="Don't worry, thou can try again, i enjoy beating your ass'",
                      quotes=[
                            "Let's finish this quickly, i have to bang some witches",
                            "Thou shalt summon the spirit lub, cuz this will hurt",
                            "Your soul will be mine, in this orb is where thou will live forever"
                          ],
                      imagen="https://cdn.discordapp.com/attachments/1029620174015434772/1116477569961832508/background-remove.png",
                      magia=self.game_state.thug_freeze,
                      colour=discord.Colour.dark_purple(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearPinkShot(self):
    enemigo = Enemigo(name="Pink Shot",
                      daño= self.wisis * 0.35,
                      hp=self.wisis * 1.25,
                      hp_total=self.wisis * 1.25,
                      objeto="Chumbo",
                      lostQuote="My bullets wasn't good enough? Next time i'll shoot you with some nasty spells",
                      winQuote="One shot, one kill",
                      quotes=[
                            "Prepare to die",
                            "I didn't believe in magic till i see your momma affording three niggas at the same time",
                            "I trust nothing but the strength of my spells and the edge of my gun"
                              ],
                      imagen="https://cdn.discordapp.com/attachments/1029620174015434772/1116478265033498694/background-remove.png",
                      magia=self.game_state.holy_sheesh,
                      colour=discord.Colour.fuchsia(),
                      game_state=self.game_state,
                      )
    await enemigo.inicializar()
    return enemigo

  async def crearRandomMago(self):

    magos_builder = [self.crearBlueMage, self.crearGreenWizard, self.crearRedFlame, self.crearMagusOrange, self.crearYellowSorcerer, self.crearPurpleShadow, self.crearPinkShot]

    builder = random.choices(magos_builder)[0]
    enemigo = await builder()
    return enemigo


class Enemigo:

  def __init__(self, name, daño, hp, hp_total, objeto, lostQuote, winQuote, quotes, imagen, magia, colour, game_state):
    self.name = name
    self.daño = daño
    self.hp = hp
    self.hp_total = hp_total
    self.imagen = imagen
    self.magia = magia
    self.colour = colour
    self.objeto = objeto
    self.winQuote = winQuote
    self.lostQuote = lostQuote
    self.quotes = quotes
    self.game_state = game_state
    self.decidir = None

    # Atributos booleanos
    self.isDefendido = False
    self.isFreeze = False
    self.isStun = False
    self.isReflecting = False
    self.Acertar = False
    self.isDamageBuff = False
    self.isParry = False
    self.isNegating = False
    self.isReducingDamage = False

  async def inicializar(self):
    self.decidir = await self.set_decision(self.name)

  """ FUNCIONES DE CONSTRUCCIÓN"""
  async def set_decision(self, name):

    diccionario_decisiones = {
      "Blue Mage": self.decidir_blue,
      "Green Wizard": self.decidir_green,
      "Yellow Sorcerer": self.decidir_yellow,
      "Magus Orange": self.decidir_orange,
      "Purple Shadow": self.decidir_purple,
      "Red Flame": self.decidir_red,
      "Pink Shot": self.decidir_pink
    }

    decidir = diccionario_decisiones[self.name]
    return decidir

  async def randomquote(self):
    return random.choices(self.quotes)[0]

  """ FUNCIONES DE FLUJO """

  async def recibir_daño(self, daño):

    if self.isReducingDamage:
      daño *= 0.85
    daño = round(daño)

    jugador = self.game_state.jugador
    gs = self.game_state
    bef_vida_enemigo = round(self.hp)
    bef_vida_jugador = round(jugador.hp)

    if self.isParry:
      daño = 0
      gs.parryados[jugador] = gs.turno + 1
      jugador.isStun = True
      gs.battle_logs += f"💫**PARRY!**💫 ``{jugador.name}`` ha sido stuneado 😵‍\n\n"

    elif self.isDefendido:
      daño *= TAZA_DEFENSA
      daño = round(daño)
      self.hp -= daño
      gs.battle_logs += f"🛡️ El daño ha sido **reducido** a ``{daño}``\n❤️ ``{bef_vida_enemigo}`` -> ❤️ ``{round(self.hp)}``\n\n"

    elif self.isReflecting:
      jugador.hp -= daño
      gs.battle_logs += f"🪞 El daño ha sido **reflejado** ``{daño}``\n❤️ ``{bef_vida_jugador}`` -> ❤️ ``{jugador.hp}``\n\n"

    else:
      self.hp -= daño
      gs.battle_logs += f"🗡️ ``{self.name}`` ha recibido ``{daño}`` de daño\n❤️ ``{bef_vida_enemigo}`` -> ❤️ ``{round(self.hp)}``\n\n"

  async def defenderse(self):
    self.isDefendido = True
    self.isReducingDamage = True
    self.game_state.defensa_diccionario[self] = self.game_state.turno + 2

  async def parry(self):
    self.isParry = True
    self.game_state.parry_cooldown[self] = self.game_state.turno + 2

  """ FUNCIONES DE INTELIGENCIA ARTIFICIAL"""

  async def decidir_red(self):
    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.7, 0.5]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.5
      probabilidades[1] = 0.4
      probabilidades.append(0.6)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 0.8
      probabilidades[0] = 0.1
      probabilidades[1] = 0.1
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      m = self.game_state

      acertar = await self.magia(m.enemigo, m.jugador)

      m.cooldown_hechizo[m.enemigo] = m.turno + await m.map_cooldown_func(self.magia)
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()

    self.game_state.decision_enemigo = decision[0]

    return decision

  async def decidir_blue(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.8, 0.2]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.7
      probabilidades[1] = 0.6
      probabilidades.append(0.5)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 1.0 - hp_jugador / hp_max_jugador
      probabilidades.append(probabilidad_magia)

    if hp_jugador < hp_max_jugador * 0.5:
      probabilidades[1] += 0.2
      probabilidades[0] -= 0.1

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Parry":
      await self.parry()

    gs.decision_enemigo = decision[0]
    return decision

  async def decidir_orange(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.55, 0.35]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.6
      probabilidades[1] = 0.3
      probabilidades.append(0.6)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      if gs.decision_jugador == "Atacar" or (
          gs.decision_jugador == "Magia"
          and gs.jugador.magia in [gs.holy_sheesh, gs.stellar_drip]):
        probabilidad_magia = 1.0
        probabilidades[0] = 0.0
        probabilidades[1] = 0.0

      elif self.hp < (self.hp_total / 3):
        probabilidad_magia = 1.0
      else:
        probabilidad_magia = 0.1
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      m = self.game_state

      acertar = await self.magia(m.enemigo, m.jugador)

      m.cooldown_hechizo[m.enemigo] = m.turno + await m.map_cooldown_func(
        self.magia)
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()
    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_green(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.5, 0.3]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.6
      probabilidades[1] = 0.3
      probabilidades.append(0.6)

    if not (self.game_state.enemigo in self.game_state.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 1.0
      probabilidades[0] = 0.0
      probabilidades[1] = 0.0
      probabilidades.append(probabilidad_magia)

    if hp_jugador < hp_max_jugador * 0.5:
      probabilidades[1] -= 0.1
      probabilidades[0] += 0.3

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)

    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      acertar = await self.magia(gs.enemigo, gs.jugador)

      gs.cooldown_hechizo[self] = gs.turno + await gs.map_cooldown_func(self.magia
                                                                     )
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()

    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_yellow(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.5, 0.3]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.55
      probabilidades[1] = 0.3
      probabilidades.append(0.65)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      if gs.decision_jugador == "Atacar" or (
          gs.decision_jugador == "Magia"
          and gs.jugador.magia in [gs.holy_sheesh, gs.stellar_drip]):
        probabilidad_magia = 0.8
        probabilidades[0] = 0.1
        probabilidades[1] = 0.1
      else:
        probabilidad_magia = 0.1
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    if hp_jugador < hp_max_jugador * 0.5:
      probabilidades[1] -= 0.1
      probabilidades[0] += 0.3

    decision = random.choices(decisiones, weights=probabilidades)

    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      acertar = await self.magia(gs.enemigo, gs.jugador)

      gs.cooldown_hechizo[self] = gs.turno + await gs.map_cooldown_func(self.magia
                                                                     )
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()
    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_pink(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.35, 0.65]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.45
      probabilidades[1] = 0.3
      probabilidades.append(0.65)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 1.0
      probabilidades[0] = 0.0
      probabilidades[1] = 0.0
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    if gs.enemigo.hp < hp_jugador:
      probabilidades[0] += 0.2
      probabilidades[1] -= 0.2

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Parry":
      await self.parry()

    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_purple(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.35, 0.65]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades.append(0.65)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 0.8
      probabilidades[0] = 0.2
      probabilidades[1] = 0.2
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    if gs.jugador.isFreeze:
      probabilidades[0] = 1.0
      probabilidades[1] = 0.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      acertar = await self.magia(gs.enemigo, gs.jugador)

      gs.cooldown_hechizo[self] = gs.turno + await gs.map_cooldown_func(self.magia
                                                                     )
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()
    gs.decision_enemigo = decision[0]
    return decision


class Jugador:

  def __init__(self, wisis, nombre, game_state, hechizo):
    self.wisis = wisis
    self.name = nombre
    self.hechizo = hechizo
    self.magia = None
    self.daño = wisis * 0.2
    self.hp = wisis
    self.hp_total = wisis
    self.isDefendido = False
    self.isParry = False
    self.isReducingDamage = False
    self.isStun = False
    self.isFreeze = False
    self.isDamageBuff = False
    self.isNegating = False
    self.Acertar = False
    self.isReflecting = False
    self.game_state = game_state

  async def atacar(self):
    self.game_state.decision_jugador = "Atacar"

  async def usar_magia(self):

    self.game_state.decision_jugador = "Magia"
    m = self.game_state

    if self.magia in [
        m.wealth_wraith, m.gucci_invoker, m.thug_freeze, m.touch_of_gangsta
    ]:

      acertar = await self.magia(m.jugador, m.enemigo)

      m.cooldown_hechizo[
        m.
        jugador] = self.game_state.turno + await self.game_state.map_cooldown_func(
          self.magia)
      if acertar:
        self.Acertar = True

  async def recibir_daño(self, daño):

    if self.isReducingDamage:
      daño *= 0.85
    daño = round(daño)
    enemigo = self.game_state.enemigo
    gs = self.game_state
    bef_vida_jugador = round(self.hp)
    bef_vida_enemigo = round(enemigo.hp)

    if self.isParry:
      daño = 0
      gs.parryados[enemigo] = gs.turno + 1
      enemigo.isStun = True
      gs.battle_logs += f" 💫**PARRY!**💫 ``{enemigo.name}`` ha sido stuneado 😵‍\n\n"
      gs.parry_cooldown[self] = gs.turno + 3
      return

    elif self.isDefendido:
      daño *= TAZA_DEFENSA
      daño = round(daño)
      self.hp -= daño
      gs.battle_logs += f"🛡️ El daño ha sido **reducido** a ``{daño}``\n❤️ ``{bef_vida_jugador}`` -> ❤️ ``{round(self.hp)}``\n\n"

    elif self.isReflecting:
      enemigo.hp -= daño
      gs.battle_logs += f"🪞 El daño ha sido **reflejado** ``{daño}``\n❤️ ``{bef_vida_enemigo}`` -> ❤️ ``{round(enemigo.hp)}``\n\n"

    else:
      self.hp -= daño
      gs.battle_logs += f"🗡️ Has recibido ``{daño}`` de daño\n❤️ ``{bef_vida_jugador}`` -> ❤️ ``{round(self.hp)}``\n\n"

  async def parry(self):
    self.isParry = True
    self.game_state.parry_cooldown[self] = self.game_state.turno + 2
    self.game_state.decision_jugador = "Parry"

  async def defenderse(self):
    self.game_state.decision_jugador = "Defender"
    self.isDefendido = True
    self.isReducingDamage = True
    self.game_state.defensa_diccionario[self] = self.game_state.turno + 2

  async def inicializar(self):
    m = self.game_state
    diccionario_hechizos = {
      "Stellar Drip": m.stellar_drip,
      "Wealth Wraith": m.wealth_wraith,
      "Gucci Invoker": m.gucci_invoker,
      "Keez Deez Nuts": m.keez_deez_nuts,
      "Thug Freeze": m.thug_freeze,
      "Touch of Gangsta": m.touch_of_gangsta,
      "Holy Sheesh": m.holy_sheesh
    }

    self.magia = diccionario_hechizos[self.hechizo]


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
