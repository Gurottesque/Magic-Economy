import discord
from discord.ext import commands
from main import client
import asqlite


"""Modulo de admin
TO-DO:
"""

def errorEmbed(razon_error):
    embed = discord.Embed(title="¡Oops! Sucedió un error al ejecutar el comando",
                        description=f"**Razon**: {razon_error}",
                        colour=discord.Colour.blue())
    embed.set_image(url="https://img1.picmix.com/output/stamp/normal/6/9/9/1/1921996_759c3.gif")

    return embed



class Admin(commands.Cog): #Clase de cog para los comandos
    
    def __init__(self, client: commands.Bot):
        self.client = client
        
    @commands.hybrid_command(name="additem", description="Añade un objeto")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def additem(self, ctx, nombre: str, valor: int, descripcion: str):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM objetos WHERE nombre = ?", (nombre,))
                result = await cur.fetchone()

                if result[0] == 0:
                    await cur.execute("INSERT INTO objetos (nombre, valor, descripcion) VALUES (?, ?, ?)", (nombre, valor, descripcion))
                    await con.commit()

                    embed = discord.Embed(title="Objeto agregado",
                                         description=f"**Nombre:** {nombre}\n**Valor:** {valor}\n**Descripcion:** {descripcion}",
                                         colour=discord.Colour.blue())

                    await ctx.send(embed=embed)

                else:
                    embed = errorEmbed("Ya existe un objeto con nombre similar en la base de datos")
                    await ctx.send(embed=embed)


    @commands.hybrid_command(name="delitem", description="Remueve un objeto")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def delitem(self, ctx, objeto: str):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT objeto_id FROM objetos WHERE nombre = ?", (objeto,))
                result = await cur.fetchone()
                
                if result == None:
                    embed = errorEmbed("No se ha encontrado el objeto en la base de datos")
                    await ctx.send(embed=embed)

                else:
                    await cur.execute("DELETE FROM objetos WHERE nombre = ?", (objeto,))
                    embed = discord.Embed(title="Objeto Eliminado",
                                         description=f"**Nombre:** {objeto}",
                                         colour=discord.Colour.blue())

                    await ctx.send(embed=embed)

                await con.commit()

    @commands.hybrid_command(name="edititem", description="Edita un objeto")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def edititem(self, ctx, objeto: str, tipo_de_cambio: str, cambio: str):

        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:

                await cur.execute("SELECT COUNT(*) FROM objetos WHERE nombre = ?", (objeto,))
                result = await cur.fetchone()

                if result[0] == 0:
                    embed = errorEmbed(f"No se ha encontrado el objeto **{objeto}** en la base de datos")
                    await ctx.send(embed=embed)
                    return

                if tipo_de_cambio == "nombre":
                    await cur.execute("UPDATE objetos SET nombre = ? WHERE nombre = ?", (cambio,objeto))

                elif tipo_de_cambio == "valor":
                    try:
                        cambio = int(cambio)
                    except:
                        embed = errorEmbed("El valor para el cambio no es válido, debe ser un entero mayor que 0")
                        await ctx.send(embed=embed)
                        return

                    if not cambio > 0:
                        embed = errorEmbed("El valor para el cambio no es válido, debe ser un entero mayor que 0")
                        await ctx.send(embed=embed)
                        return

                    await cur.execute("UPDATE objetos SET valor = ? WHERE nombre = ?", (int(cambio),objeto))

                elif tipo_de_cambio == "descripcion":
                    await cur.execute("UPDATE objetos SET descripcion = ? WHERE nombre = ?", (cambio,objeto))

                else:
                    embed = errorEmbed("No se ha especificado un tipo de cambio válido\nTipos de cambio validos: 'nombre', 'valor', 'descripcion'")
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(title=f"Objeto: {objeto} cambiado exitosamente!",
                                    description=f"Se ha cambiado el **{tipo_de_cambio}** a **{cambio}**",
                                    colour=discord.Colour.green())
                await ctx.send(embed=embed)

                await con.commit()

        

    @commands.hybrid_command(name="addwis", description="Añade wisis a un usuario")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def addwis(self, ctx, usuario: discord.Member, wisis: int):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("UPDATE usuarios SET wisis = wisis + ?, wisis_totales = wisis + ? WHERE usuario_id = ?",(wisis, wisis, usuario.id))
                await con.commit()

                embed = discord.Embed(title=f"Wisis añadidos!",
                                    description=f"Se han añadido **{wisis}** a **{usuario.mention}**",
                                    colour=discord.Colour.green())
                await ctx.send(embed=embed)



    	
    @commands.hybrid_command(name="delwis", description="Remueve wisis a un usuario")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def delwis(self, ctx, usuario: discord.Member, wisis: int):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("UPDATE usuarios SET wisis = wisis - ?, wisis_totales = wisis - ? WHERE usuario_id = ?",(wisis, wisis, usuario.id))
                await con.commit()

                embed = discord.Embed(title=f"Wisis borrados!",
                                    description=f"Se han borrado **{wisis}** a **{usuario.mention}**",
                                    colour=discord.Colour.green())
                await ctx.send(embed=embed)


    @commands.hybrid_command(name="giveitem", description="Añade un item a un usuario")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def giveitem(self, ctx, usuario: discord.Member, objeto: str, cantidad: int):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT objeto_id FROM objetos WHERE nombre = ?", (objeto,))
                resultado = await cur.fetchone()
                objeto_id = resultado[0]
                if resultado == None:
                    await ctx.send(f"No existe el objeto {objeto}")
                    return

                await cur.execute("SELECT usuario_id FROM inventario WHERE usuario_id = ? AND objeto_id = ?",(usuario.id, objeto_id))
                resultado = await cur.fetchone()

                if resultado == None:
                    await cur.execute("INSERT INTO inventario (usuario_id, objeto_id, cantidad) VALUES (?, ?, ?)", (usuario.id, objeto_id, cantidad))

                else:
                    await cur.execute("UPDATE inventario SET cantidad = cantidad + ? WHERE usuario_id = ? AND objeto_id = ?", (cantidad, usuario.id, objeto_id))

                embed = discord.Embed(title=f"Objeto añadido!",
                                    description=f"Se han añadido el objeto**{objeto}** a **{usuario.mention}**",
                                    colour=discord.Colour.green())
                await ctx.send(embed=embed)


    @commands.hybrid_command(name="removeitem", description="Remueve un objeto del inventario de alguien")
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.is_owner()
    async def removeitem(self, ctx, usuario: discord.Member, wisis: int):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT objeto_id FROM objetos WHERE nombre = ?", (objeto,))
                resultado = await cur.fetchone()
                objeto_id = resultado[0]
                if resultado == None:
                    await ctx.send(f"No existe el objeto {objeto}")
                    return

                await cur.execute("SELECT usuario_id FROM inventario WHERE usuario_id = ? AND objeto_id = ?",(usuario.id, objeto_id))
                resultado = await cur.fetchone()

                await cur.execute("UPDATE inventario SET cantidad = cantidad - ? WHERE usuario_id = ? AND objeto_id = ?", (cantidad, usuario.id, objeto_id))

                embed = discord.Embed(title=f"Objeto removido!",
                                    description=f"Se han removido el objeto**{objeto}** a **{usuario.mention}**",
                                    colour=discord.Colour.green())
                await ctx.send(embed=embed)

    @commands.hybrid_command(name="help", description="Muestra la lista de comandos disponibles")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def help(self, ctx, seccion: str="a"):

        if seccion.lower() == "perfil":
            embed = discord.Embed(title="Comandos de perfil 👤", description="```wisis, inventario```",
                                colour=discord.Colour.green())
            embed.add_field(name="wisis <usuario>", value="Muestra los wisis del usuario, si no se especifica un usuario, muestra los wisis del usuario que ejecutó el comando")
            embed.add_field(name="inventario", value="Muestra el inventario del usuario")

            await ctx.send(embed=embed)
            return

        elif seccion.lower() == "tienda":
            embed = discord.Embed(title="Comandos de tienda 🛒", description="```tienda, comprar```",
                                colour=discord.Colour.red())
            embed.add_field(name="tienda", value="Muestra la tienda")
            embed.add_field(name="comprar <objeto> <cantidad>", value="Compra un objeto de la tienda")

            await ctx.send(embed=embed)
            return

        elif seccion.lower() == "objetos":
            embed = discord.Embed(title="Comandos de objetos 🛠️", description="```objeto, usar, usar_rol```",
                                colour=discord.Colour.purple())
            embed.add_field(name="objeto <objeto>", value="Muestra información sobre el objeto")
            embed.add_field(name="usar <usuario>", value="Usa el objeto, si no se especifica un usuario, se usa en si mismo")
            embed.add_field(name="usar_rol <nombre_rol> <color>", value="Usa el objeto 'Rol', el parametro 'color' debe ser un color hexadecimal")

            await ctx.send(embed=embed)
            return

        elif seccion.lower() == "admin":
            embed = discord.Embed(title="Comandos de admin 💻", description="```additem, delitem, edititem, addwis, delwis```",
                                colour=discord.Colour.dark_magenta())
            embed.add_field(name="additem <objeto> <valor> <descripcion>", value="Añade un objeto")
            embed.add_field(name="delitem <objeto>", value="Elimina un objeto")
            embed.add_field(name="edititem <objeto> <tipo de cambio> <cambio>", value="Edita un objeto")
            embed.add_field(name="addwis <usuario>", value="Añade wisis al usuario")
            embed.add_field(name="delwis <usuario>", value="Quita wisis del usuario")

            await ctx.send(embed=embed)
            return

        elif seccion.lower() == "leaderboard":
            embed = discord.Embed(title="Comandos de admin 💻", description="```top, topwisis```",
                                colour=discord.Colour.dark_magenta())
            embed.add_field(name="top", value="Muestra el top de las personas mas ricas del server")
            embed.add_field(name="topwisis", value="Muestra el top de las personas que más wisis han obtenido")

            await ctx.send(embed=embed)
            return

        else:
            embedAyuda = discord.Embed(title="Secciones de comandos",
                                        description="Para ver mas información sobre una sección usa help <seccion>",
                                        colour=discord.Colour.gold())

            embedAyuda.add_field(name="👤 Perfil",value="Muestra los comandos relacionados con el usuario")
            embedAyuda.add_field(name="🛒 Tienda",value="Muestra los comandos relacionados con la tienda")
            embedAyuda.add_field(name="🛠️ Objetos",value="Muestra los comandos relacionados con los objetos")
            embedAyuda.add_field(name="💻 Admin",value="Muestra los comandos admins disponibles")
            embedAyuda.add_field(name="🏆 Leaderboard",value="Muestra los comandos leaderboard disponibles")

            await ctx.send(embed=embedAyuda)
            return






async def setup(client):
    await client.add_cog(Admin(client))