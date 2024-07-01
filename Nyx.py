from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sched import scheduler
import discord
from discord.ext.commands import Bot
from discord.ui import View, Button
from discord.ext import commands
import io
import html
from collections import defaultdict
from datetime import datetime, timedelta
from constante import server, rules_1, rules_2, invite, donate, embed_botton

TOKEN = 'SEU_TOKEN_AQUI'

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
scheduler = AsyncIOScheduler()

bot = commands.Bot(command_prefix='n!', intents=intents)

#sistema de ticket
@bot.event
async def on_ready():
    bot.add_view(TicketView())  # Adiciona a view persistent ao iniciar
    print(f'Bot conectado como {bot.user.name}')

@bot.command()
async def ticket(ctx):
    guild = ctx.guild

    channel = discord.utils.get(guild.text_channels, name=f'ticket-{ctx.author.name}')
    if not channel:
        admin_role_id = 1241104535905243177  # Replace with the actual ID
        admin_role = guild.get_role(admin_role_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        # Criação do canal de texto diretamente na guild
        channel = await guild.create_text_channel(f'ticket-{ctx.author.name}', overwrites=overwrites)
        embed = discord.Embed(title="Ticket Aberto", description=f"Olá {ctx.author.mention}, 📩 Seu ticket foi aberto!", color=0xDC143C)
        
        await channel.send(embed=embed, view=CloseButtonView(ctx.author))

@bot.command()
async def ticket_button(ctx):
    emoji = "<:t_handshake:1254036881360949429>"
    description = (
        "Utilize este canal para fazer denúncias ou relatar questões que estejam afetando gravemente "
        "sua gameplay ou sua conta.\n\n"
        "**Tudo é anônimo, apenas os ADMs têm acesso.** "
        f"{emoji}"
    )
    embed = discord.Embed(title="Atendimento Terminus", description=description, color=0xDC143C)
    embed.set_footer(text="O prazo para o atendimento é de até 12 horas. Por favor, tenha paciência.")

    if ctx.author.guild_permissions.administrator:  # Verifica se o autor do comando é um administrador
        view = TicketView()
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send(embed=embed)
    
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Disable timeout for the view

    @discord.ui.button(label="Abrir Ticket 📩", style=discord.ButtonStyle.primary)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        await interaction.response.send_message("Criando seu ticket...", ephemeral=True, delete_after=-1)
        channel = discord.utils.get(guild.text_channels, name=f'ticket-{interaction.user.global_name}')
        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            # Criação do canal de texto diretamente na guild
            channel = await guild.create_text_channel(f'ticket-{interaction.user.global_name}', overwrites=overwrites)
            
            embed = discord.Embed(title="Ticket Aberto", description=f"Olá {interaction.user.mention}, como podemos ajudar?", color=0xDC143C)
            await channel.send(embed=embed, view=CloseButtonView(interaction.user, channel))
        else:
            await interaction.followup.send(f'Você já possui um ticket aberto: {channel.mention}', ephemeral=True)

    @discord.ui.button(label="Fazer denúncia 🗯️", style=discord.ButtonStyle.red)
    async def make_complaint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Criando sua denúncia...", ephemeral=True, delete_after=-1)
        guild = interaction.guild

        channel = discord.utils.get(guild.text_channels, name=f'denúncia-{interaction.user.global_name}')
        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            # Criação do canal de texto diretamente na guild
            channel = await guild.create_text_channel(f'denúncia-{interaction.user.global_name}', overwrites=overwrites)

            embed = discord.Embed(title="Denúncia Aberta", description=f"Olá {interaction.user.mention}, nos informe o que aconteceu com o maior número de detalhes possíveis.", color=0xDC143C)
            await channel.send(embed=embed, view=CloseButtonView(interaction.user, channel))
            return  # Retorna aqui para evitar qualquer mensagem adicional
        else:

            await interaction.followup.send(f'Você já possui uma denúncia aberta: {channel.mention}', ephemeral=True)

async def save_transcript(channel):
    # Substitua 'ID_DO_CANAL' pela ID do canal onde deseja enviar os transcripts
    transcript_channel_id = 1256331123454120078  # Coloque aqui a ID do canal
    transcript_channel = channel.guild.get_channel(transcript_channel_id)

    if not transcript_channel:
        transcript_channel = await channel.guild.create_text_channel('transcripts')

    transcript = "<html><body><h2>Transcrição do ticket:</h2>"
    async for message in channel.history(limit=None):
        content = html.escape(message.clean_content)        
        author = html.escape(message.author.display_name)
        transcript += f"<p><b>{author}</b>: {content}</p>"
        if message.attachments:
            for attachment in message.attachments:
                transcript += f'<p><a href="{attachment.url}">[Attachment]</a></p>'
    transcript += "</body></html>"

    with io.BytesIO(transcript.encode()) as file:
        discord_file = discord.File(file, f"transcript-{channel.name}.html")
        await transcript_channel.send(file=discord_file)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def close(ctx):
    if "ticket" in ctx.channel.name or "denúncia" in ctx.channel.name:
        await ctx.channel.set_permissions(ctx.author, send_messages=False)
        await ctx.send("O ticket foi fechado.")
    else:
        await ctx.send("Este comando só pode ser usado em canais de tickets ou denúncias.")

@bot.command()
async def salvar_ticket(ctx, ticket_channel: discord.TextChannel):
    save_channel_id = 1253853222385487945  # Substitua pelo ID do canal de salvamento
       
    if "ticket" in ticket_channel.name:
        save_channel = bot.get_channel(save_channel_id)
        if save_channel:                      
            transcript = "<html><body><h2>Transcrição do ticket:</h2>"
            async for message in ticket_channel.history(limit=None):
                content = html.escape(message.clean_content)
                author = html.escape(message.author.display_name)
                transcript += f"<p><b>{author}</b>: {content}</p>"
                if message.attachments:
                    for attachment in message.attachments:
                        transcript += f'<p><a href="{attachment.url}">[Attachment]</a></p>'
            transcript += "</body></html>"

            with io.BytesIO(transcript.encode()) as file:
                discord_file = discord.File(file, f"transcript-{ticket_channel.name}.html")
            await save_channel.send(file=discord_file)
        else:
                await ctx.send("Canal de salvamento não encontrado. Por favor, configure um canal de salvamento válido.")
    else:
        await ctx.send("Este comando só pode ser usado em canais de tickets.")
#*------------------------------------------------------------------------------------------------------------------------------*
#embeds
@bot.command()
async def info_server(ctx):

    embed = discord.Embed(title="", description=server, color=0xDC143C)  
    
    embed.set_footer(text=f"")

    await ctx.send(embed=embed)

@bot.command()
async def regras_1(ctx):

    embed = discord.Embed(title="", description=rules_1, color=0xDC143C)  
    
    embed.set_footer(text=f"")

    await ctx.send(embed=embed)

@bot.command()
async def regras_2(ctx):

    embed = discord.Embed(title="", description=rules_2, color=0xDC143C)  
 
    embed.set_footer(text=f"")

    await ctx.send(embed=embed)

@bot.command()
async def convite(ctx):

    embed = discord.Embed(title="", description=invite, color=0xDC143C)  
 
    embed.set_footer(text=f"")

    await ctx.send(embed=embed)
#*------------------------------------------------------------------------------------------------------------------------------*
#doações
@bot.command()
async def embed_donate(ctx):

    embed = discord.Embed(title="", description=donate, color=0xDC143C)  
 
    embed.set_footer(text=f"")

    await ctx.send(embed=embed)

@bot.command()
async def doacao(ctx):

    embed = discord.Embed(title="", description=embed_botton, color=0xDC143C)
    embed.set_footer(text="O prazo para o atendimento é de até 12 horas. Por favor, tenha paciência.")
    
    if ctx.author.guild_permissions.administrator:  # Verifica se o autor do comando é um administrador
        view = DonateView()
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send(embed=embed)
    
class DonateView(View):
    heart_green = "<:heart_green:1251918163310936136>"

    def __init__(self):
            super().__init__()    
            self.timeout = None  # Garante que não há timeout para a view

    @discord.ui.button(label="Fazer doação 💵", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        await interaction.response.send_message("Criando seu ticket...", ephemeral=True, delete_after=-1)
        channel = discord.utils.get(guild.text_channels, name=f'ticket-{interaction.user.global_name}')
        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            # Criação do canal de texto diretamente na guild
            channel = await guild.create_text_channel(f'donate-{interaction.user.global_name}', overwrites=overwrites)
            
            embed = discord.Embed(title="Ticket Aberto", description=f"Olá {interaction.user.mention}, seu ticket de doação está aberto, logo iremos te atender.", color=0xDC143C)
            await channel.send(embed=embed, view=CloseButtonView(interaction.user, channel))
        else:
            await interaction.followup.send(f'Você já possui um ticket aberto: {channel.mention}', ephemeral=True)
class CloseButtonView(View):
    def __init__(self, ticket_owner, ticket_channel):
        super().__init__(timeout=None)  # Disable timeout for the view
        self.ticket_owner = ticket_owner
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="Fechar 🔒", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Tem certeza de que gostaria de fechar?",
            view=ConfirmCloseView(self.ticket_owner, self.ticket_channel)
        )

class ConfirmCloseView(View):
    def __init__(self, ticket_owner, ticket_channel):
        super().__init__(timeout=None)  # Disable timeout for the view
        self.ticket_owner = ticket_owner
        self.ticket_channel = ticket_channel

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        await channel.set_permissions(self.ticket_owner, send_messages=False)
        await channel.send("O ticket foi fechado.")
        await save_transcript(channel)
        await interaction.channel.delete()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("O fechamento do ticket foi cancelado.")
#*------------------------------------------------------------------------------------------------------------------------------*
@bot.event
async def on_member_join(member):
    # Boas-vindas
    regras = "<#1241173127552303104>"
    spike = "<:spike_cute:1245772152590958693>"
    channel_id = 1241059756647514222  # ID do canal de boas-vindas

    join_channel = bot.get_channel(channel_id)
    if not join_channel:
        print(f"Erro: Canal de boas-vindas com ID {channel_id} não encontrado.")
    else:
	
        embed = discord.Embed(
            title="",
            description=f"### **Olá {member.mention}, boas vindas ao Terminus!** ###\n\n"
                        f"### Não se esqueça de olhar o canal {regras} {spike} ###",
            color=0xDC143C
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Esperamos que você se divirta no servidor!")
        await join_channel.send(embed=embed)

    # Autorole
    role_id = 1241093915008962573  # Substitua pelo ID do cargo desejado
    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)
        print(f"Atribuído o cargo {role.name} ao membro {member.name}")
    else:
        print(f"Cargo com ID {role_id} não encontrado.")

@bot.event
async def on_member_remove(member):
    channel_exit_id = 1241087223651106888  # ID do canal de saída
    
    exit_channel = bot.get_channel(channel_exit_id)
    if not exit_channel:
        return
    
    embed = discord.Embed(
        description=f"{member.mention} Até mais! 👋"
    )
    
    await exit_channel.send(embed=embed)
#*------------------------------------------------------------------------------------------------------------------------------*
@bot.event
async def on_ready():
    scheduler.start()
    schedule_all_messages()
    print(f'{bot.user.name} está online e pronto!')

# Função para enviar mensagem com embed de restart
async def restart(channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="Aviso de restart automático",
            description="O servidor é configurado para reiniciar automaticamente a cada seis horas todos os dias."
                        " Fazemos isso para garantir a fluidez do jogo e realizar backups do progresso do mundo.\n\n"
                        "O restart é feito nos seguintes horários:\n" 
                        "06h10 ; 12h10 ; 18h10 ; 00h10",
            color=0xDC143C
        )
        await channel.send(embed=embed)

# Função para enviar mensagem com embed de claim carros
async def claim_carros(channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="Lembrem-se sempre de reivindicar seus veículos!",
            description="Reivindicar a posse do seu carro oferece maior segurança, protegendo-o contra roubo."
                        " Carros sem reivindicação são de total responsabilidade do jogador.\n\n"
                        "Para reivindicar um carro, clique com o direito no mouse nele e em **reivindicar**.",
            color=0xDC143C
        )
        await channel.send(embed=embed)

# Função para enviar mensagem com embed de PVP
async def pvp(channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="",
            description="Este servidor é PVP. Existe o risco constante de combate entre jogadores. Esteja preparado para confrontos a qualquer momento."
                        " Lembre-se: **Posso matar ou posso morrer**. Divirta-se e jogue com estratégia!\n\n"
                        "**E lembre-se A LUTA COMEÇA E ACABA DENTRO DO JOGO.**",
            color=0xDC143C
        )
        await channel.send(embed=embed)

# Função para agendar todas as mensagens
def schedule_all_messages():
    now = datetime.now()

    # Horários para mensagens de restart
    restart_times = [
        (6, 10),    # 06h10
        (12, 10),   # 12h10
        (18, 10),   # 18h10
        (0, 10)     # 00h10
    ]
    for hour, minute in restart_times:
        run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if run_time < now:
            run_time += timedelta(days=1)
        scheduler.add_job(restart, 'date', run_date=run_time, args=[1253194851709882438])

    # Horários para mensagens de claim carros
    claim_carros_times = [
        (10, 0),   # 10h00
        (22, 0)    # 22h00
    ]
    for hour, minute in claim_carros_times:
        run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if run_time < now:
            run_time += timedelta(days=1)
        scheduler.add_job(claim_carros, 'date', run_date=run_time, args=[1253194851709882438])

    # Horário para mensagem de PVP
    pvp_times = [
        (20, 30)    # 20h30
    ]
    for hour, minute in pvp_times:
        run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if run_time < now:
            run_time += timedelta(days=1)
        scheduler.add_job(pvp, 'date', run_date=run_time, args=[1253194851709882438])
        
bot.run(TOKEN)