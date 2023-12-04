import disnake

from config.variables import constants, secrets
from datetime import datetime, timezone
from disnake import AllowedMentions, ApplicationCommandInteraction, Embed, Guild, MessageInteraction, Permissions, \
    TextInputStyle
from disnake.abc import GuildChannel
from disnake.ext import commands
from disnake.ui import Button, View
from services.dynamodb import DynamodbItem
from time import sleep
from tools.archivist.logger import Logger
from tools.directory_managers import create_directory
from tools.text_managers import read_yaml, write_yaml
import os


# Une classe pour les modals

class Poll(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__settings_directory = constants.DIRECTORY_POLLS
        create_directory(self.__settings_directory)
        self.__settings = self.__read_settings()

    def __read_settings(self) -> list:
        output = []
        for file in self.__get_file_list():
            file_content = read_yaml(self.__settings_directory + file)
            output.append(file_content)
        return output

    def __get_file_list(self) -> list:
        try:
            files = os.listdir(self.__settings_directory)
            return [file for file in files if file[-4:] == '.yml']
        except:
            return []

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_create(self, interaction: ApplicationCommandInteraction, name: str, channel: GuildChannel,
                                   public_message_id: str, private_message_id: str, newcomers: bool = False):
        """
        Crée une campagne de sondage à partir de deux messages de ce canal. Un salon peut être spécifié

        Parameters
        ----------
        name: :class: str
            Le nom de la campagne à créer. Il doit être unique, et ne pas contenir d'underscore _
        channel: :class: GuildChannel
            Le salon principal sur lequel se déroulera la campagne.
        public_message_id: class: str
            L'ID du message qui sert de modèle au message public qui sera affiché sur le salon principal.
        private_message_id: class: str
            L'ID du message qui sert de modèle au message privé à envoyer aux répondants.
        newcomers: class: bool
            Le message privé doit-il être envoyé d'office aux nouveaux membres du serveur ?
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé la création de la campagne de sondage "{name}".""",
            message_success=f"""La campagne de sondage "{name}" a été créée.""",
            message_failure=f"""La campagne de sondage "{name}" n'a pas été créée.""",
            task_info='command.poll.campaign create',
            interaction=interaction
        )
        await logger.log_start()

        if '_' in name:
            await logger.log_message(f"""Un nom de campagne de sondage ne doit pas contenir d'underscore.""")
            await logger.log_failure()
            return

        file_name = name + '.yml'
        if file_name in self.__get_file_list():
            await logger.log_message(f"""Une campagne de sondages "{name}" existe déjà.""")
            await logger.log_failure()
            return

        try:
            public_message = await interaction.channel.fetch_message(public_message_id)
            public_text = public_message.content
        except:
            await logger.log_message(
                f"""Le message (public) dont l'id est {message_id} n'a pas été trouvé dans {interaction.channel.mention}""")
            await logger.log_failure()
            return

        try:
            private_message = await interaction.channel.fetch_message(private_message_id)
            private_text = private_message.content
        except:
            await logger.log_message(
                f"""Le message (privé) dont l'id est {message_id} n'a pas été trouvé dans {interaction.channel.mention}""")
            await logger.log_failure()
            return

        channel_id = channel.id if channel else None
        if channel and hasattr(channel, 'parent'):
            await logger.log_message(f"""{channel.mention} n'est pas un salon.""")
            await logger.log_failure()
            return

        campaign_settings = {
            "name": name,
            "active": False,
            "newcomers": newcomers,
            "channel_id": channel_id if channel_id else '',
            "public_message": public_text,
            "private_message": private_text,
            "questions": []
        }
        file_path = self.__settings_directory + file_name
        write_yaml(campaign_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_edit(self, interaction: ApplicationCommandInteraction, name: str,
                                 channel: GuildChannel = None, public_message_id: str = None,
                                 private_message_id: str = None, newcomers: bool = None):
        """
        Modifie une campagne de sondage.

        Parameters
        ----------
        name: :class: str
            Le nom de la campagne à éditer.
        channel: :class: GuildChannel
            Le salon principal sur lequel se déroulera la campagne.
        public_message_id: class: str
            L'ID du message qui sert de modèle au message public qui sera affiché sur le salon principal.
        private_message_id: class: str
            L'ID du message qui sert de modèle au message privé à envoyer aux répondants.
        newcomers: class: bool
            Le message privé doit-il être envoyé d'office aux nouveaux membres du serveur ?
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé la modification de la campagne de sondage "{name}".""",
            message_success=f"""La campagne de sondage "{name}" a été modifié.""",
            message_failure=f"""La campagne de sondage "{name}" n'a pas été modifié.""",
            task_info='command.poll.campaign edit',
            interaction=interaction
        )
        await logger.log_start()

        file_name = name + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""Aucune campagne de sondage nommée "{name}" n'a été trouvée.""")
            await logger.log_failure()
            return

        if not channel and not public_message_id and not private_message_id and newcomers is None:
            await logger.log_message(f"""Aucun changement fourni pour la campagne de sondage nommée "{name}".""")
            await logger.log_failure()
            return

        poll_campaign_settings = [settings for settings in self.__settings if settings["name"] == name][0]

        if channel:
            channel_id = channel.id
            if hasattr(channel, 'parent'):
                await logger.log_message(f"""{channel.mention} n'est pas un salon.""")
                await logger.log_failure()
                return
            poll_campaign_settings["channel_id"] = channel_id

        if public_message_id:
            try:
                public_message = await interaction.channel.fetch_message(public_message_id)
                public_text = public_message.content
                poll_campaign_settings["public_message"] = public_text
            except:
                await logger.log_message(
                    f"""Le message (public) dont l'id est {message_id} n'a pas été trouvé dans {interaction.channel.mention}""")
                await logger.log_failure()
                return

        if private_message_id:
            try:
                private_message = await interaction.channel.fetch_message(private_message_id)
                private_text = private_message.content
                poll_campaign_settings["private_message"] = private_text
            except:
                await logger.log_message(
                    f"""Le message (privé) dont l'id est {message_id} n'a pas été trouvé dans {interaction.channel.mention}""")
                await logger.log_failure()
                return

        if newcomers is not None:
            poll_campaign_settings["newcomers"] = newcomers

        file_path = self.__settings_directory + file_name
        write_yaml(poll_campaign_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_list(self, interaction: ApplicationCommandInteraction):
        """
        Liste toutes les campagnes de sondage existantes et les salons associés.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé la liste des campagnes de sondage.""",
            message_success=f"""La liste des campagnes de sondage a été affichée sur {interaction.channel.mention}.""",
            message_failure=f"""La liste des campagnes de sondage n'a pas été affichée.""",
            task_info='command.poll.list',
            interaction=interaction
        )
        await logger.log_start()

        if not self.__settings:
            await logger.log_message("Il n'existe aucune campagne de sondage pour l'instant.")
            await logger.log_failure()
            return

        text = "__**Liste des campagnes de sondage**__"
        for settings in self.__settings:
            text += f"""\n{settings["name"]}"""
            try:
                channel = await self.__guild.fetch_channel(settings["channel_id"])
                text += f" {channel.mention}"
            except:
                pass
        await interaction.channel.send(text)

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_check(self, interaction: ApplicationCommandInteraction, name: str):
        """
        Affiche les informations d'une campagne de sondages.

        Parameters
        ----------
        name: :class: str
            Le nom de la campagne à afficher.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé l'affichage des informations de la campagne de sondage "{name}".""",
            message_success=f"""Les infos sur la campagne de sondage "{name}" ont été affichées sur {interaction.channel.mention}.""",
            message_failure=f"""Les infos sur la campagne de sondage "{name}" n'ont pas été affichées.""",
            task_info='command.poll.campaign check',
            interaction=interaction
        )
        await logger.log_start()

        file_name = name + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""Aucune campagne de sondage nommée "{name}" n'a été trouvée.""")
            await logger.log_failure()
            return

        settings = [settings for settings in self.__settings if settings["name"] == name][0]

        text = f"""__**Campagne de sondage "{name}"__**"""
        if settings["channel_id"]:
            text += f"\nParamétré pour s'afficher sur "
            try:
                channel = await self.__guild.fetch_channel(settings["channel_id"])
                text += f"{channel.mention}"
            except:
                pass

        embeds = []

        embed_public_message = Embed(
            title="Message public",
            description=settings["public_message"]
        )
        embeds.append(embed_public_message)

        embed_private_message = Embed(
            title="Message privé",
            description=settings["private_message"]
        )
        embeds.append(embed_private_message)

        for question in settings["questions"]:
            embed_title = f"""Question: {question["id"]}"""
            embed_description = ""
            for key, value in question.items():
                if key == "id":
                    pass
                elif key == "channel":
                    try:
                        question_channel = await self.__guild.fetch_channel(value)
                        embed_description += f"\n**{key}** : {question_channel.mention}"
                    except:
                        pass
                else:
                    embed_description += f"\n**{key}** : {value}"
            embed_question = Embed(
                title=embed_title,
                description=embed_description
            )
            embeds.append(embed_question)

        await interaction.channel.send(text, embeds=embeds[:10],
                                       allowed_mentions=AllowedMentions(everyone=False, users=False))
        embeds = embeds[10:]
        while embeds:
            await interaction.channel.send("...", embeds=embeds[:10],
                                           allowed_mentions=AllowedMentions(everyone=False, users=False))
            embeds = embeds[10:]
        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_delete(self, interaction: ApplicationCommandInteraction, name: str,
                                   confirmation: str = None):
        """
        ⚠️⚠️⚠️️ ACTION IRRÉVERSIBLE ⚠️⚠️⚠️ Supprime une campagne de sondage.

        Parameters
        ----------
        name: :class: str
            Le nom de la campagne à supprimer.
        confirmation: class: str
            Pour valider la suppression, taper "SUPPRIMER LA CAMPAGNE".
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé la suppresion de la campagne de sondage "{name}".""",
            message_success=f"""La campagne de sondage "{name}" a été supprimée.""",
            message_failure=f"""La campagne de sondage "{name}" n'a pas été supprimée.""",
            task_info='command.poll.campaign delete',
            interaction=interaction
        )
        await logger.log_start()

        if not confirmation == "SUPPRIMER LA CAMPAGNE":
            await logger.log_message(
                f"""La confirmation de la suppression de la campagne de sondage "{name}" n'a pas été correctement saisie.""")
            await logger.log_failure()
            return

        file_name = name + '.yml'
        file_path = self.__settings_directory + file_name
        try:
            os.remove(file_path)
        except:
            await logger.log_message(f"""Aucune campagne de sondage nommée "{name}" n'a été trouvée.""")
            await logger.log_failure()
            return

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_question_add(self, interaction: ApplicationCommandInteraction, campaign: str, id: str, title: str,
                                options: int, label: str,
                                channel: GuildChannel = None, description_message_id: str = '', emoji: str = None,
                                long_input: bool = False, max_characters: int = 100, placeholder: str = None,
                                ranking: bool = True):
        """
        Ajoute une question à une campagne de sondage

        Parameters
        ----------
        campaign: :class: str
            Le nom de la campagne à laquelle on veut ajouter la question.
        id: class: str
            Un nom court (en un mot) pour identifier la question.
        title: class: str
            La question à afficher, elle figurera sur le bouton, et en titre de la fenêtre de réponse.
        options: class: int
            Le nombre de réponses autorisées.
        label: class: str
            Le texte précédant chaque champ de réponse. Si l'option ranking est activée, il sera numéroté.
        channel: class: GuildChannel
            Le fil ou salon dédié à cette question.
        description_message_id: class: str
            L'ID du message qui sert de modèle à la description de la question.
        emoji: class: str
            Un emoji pour décorer le bouton.
        long_input: class: bool
            Faux : les champs de saisie sont sur une ligne. Vrai: les champs de saisie sont des boîtes.
        max_characters: class: int
            Le nombre maximum de caractères par réponse.
        placeholder: class: str
            Le texte affiché par défaut quand le champ réponse est vide. Ce n'est pas une réponse.
        ranking: class: bool
            Les réponses sont-elles hiérarchisées ? C'est purement esthétique, pour numéroter les labels.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé l'ajout de la question "{id}" à la campagne "{campaign}".""",
            message_success=f"""La question "{id}" a été ajoutée à la campagne "{campaign}".""",
            message_failure=f"""La question "{id}" n'a pas été ajoutée à la campagne "{campaign}".""",
            task_info='command.poll.question add',
            interaction=interaction
        )
        await logger.log_start()

        file_name = campaign + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""Aucune campagne de sondage nommée "{campaign}" n'a été trouvée.""")
            await logger.log_failure()
            return

        poll_campaign_settings = [x for x in self.__settings if x["name"] == campaign][0]
        if len([x for x in poll_campaign_settings["questions"] if x["id"] == id]) > 0:
            await logger.log_message(f"""Une question "{id}" existe déjà dans la campagne "{campaign}".""")
            await logger.log_failure()
            return

        try:
            description_message = await interaction.channel.fetch_message(description_message_id)
            description = description_message.content
        except:
            await logger.log_message(
                f"""Le message (public) dont l'id est {description_message_id} n'a pas été trouvé dans {interaction.channel.mention}.""")
            description = ''

        if channel:
            try:
                channel_item = await self.__guild.fetch_channel(channel)
                channel_id = channel_item.id
            except:
                pass
        else:
            channel_id = None

        question = {
            "id": id,
            "title": title,
            "channel": channel_id,
            "options": options,
            "label": label,
            "description": description,
            "emoji": emoji,
            "long_input": long_input,
            "max_characters": max_characters,
            "placeholder": placeholder,
            "ranking": ranking
        }
        poll_campaign_settings["questions"].append(question)

        file_path = self.__settings_directory + file_name
        write_yaml(poll_campaign_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_question_remove(self, interaction: ApplicationCommandInteraction, campaign: str, id: str):
        """
       Retire une question d'une campagne de sondage

       Parameters
       ----------
       campaign: :class: str
           Le nom de la campagne dont on veut retirer la question.
       id: class: str
           L'identifiant de la question à retirer.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé le retrait de la question "{id}" de la campagne "{campaign}".""",
            message_success=f"""La question "{id}" a été retirée de la campagne "{campaign}".""",
            message_failure=f"""La question "{id}" n'a pas été retirée de la campagne "{campaign}".""",
            task_info='command.poll.question remove',
            interaction=interaction
        )
        await logger.log_start()

        file_name = campaign + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""Aucune campagne de sondage nommée "{campaign}" n'a été trouvée.""")
            await logger.log_failure()
            return

        poll_campaign_settings = [x for x in self.__settings if x["name"] == campaign][0]

        if len([x for x in poll_campaign_settings["questions"] if x["id"] == id]) == 0:
            await logger.log_message(f"""La question "{id}" n'existe pas dans la campagne "{campaign}".""")
            await logger.log_failure()
            return

        question = [x for x in poll_campaign_settings["questions"] if x["id"] == id][0]
        poll_campaign_settings["questions"].pop(poll_campaign_settings["questions"].index(question))

        file_path = self.__settings_directory + file_name
        write_yaml(poll_campaign_settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_start(self, interaction: ApplicationCommandInteraction, name: str,
                                  confirmation: str = None, auto_setup: bool = False,
                                  send_private_message: bool = False):
        """
        Lance une campagne de sondage.

        Parameters
        ----------
        name: :class: str
            Le nom de la campagne à débuter.
        confirmation: class: str
            Pour valider, taper "LANCER LA CAMPAGNE".
        auto_setup: class: bool
            True : poster les messages sur les salons et fils. False : se limite à créer les fils manquants.
        send_private_message: class: bool
            Faut-il envoyer le message privé à tous les membres du serveur ? Non par défaut.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé le lancement de la campagne de sondage "{name}".""",
            message_success=f"""La campagne de sondage "{name}" a été lancée.""",
            message_failure=f"""La campagne de sondage "{name}" n'a pas été lancée.""",
            task_info='command.poll.campaign start',
            interaction=interaction
        )
        await logger.log_start()

        if not confirmation == "LANCER LA CAMPAGNE":
            await logger.log_message(
                f"""La confirmation du lancement de la campagne de sondage "{name}" n'a pas été correctement saisie.""")
            await logger.log_failure()
            return

        file_name = name + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""La campagne de sondages "{name}" n'existe pas.""")
            await logger.log_failure()
            return

        settings = [settings for settings in self.__settings if settings["name"] == name][0]
        if settings["active"]:
            await logger.log_message(f"""La campagne de sondage "{name}" est déja active.""")
            await logger.log_failure()
            return

        try:
            campaign_channel = await self.__guild.fetch_channel(settings["channel_id"])
        except:
            await logger.log_message(f"""Le salon indiqué pour la campagne de sondage "{name}" n'existe pas.""")
            await logger.log_failure()
            return

        view_private_message = View()
        button_private_message = Button(
            label="Participer au sondage",
            custom_id=f"""poll_{settings["name"]}_pm"""
        )
        view_private_message.add_item(button_private_message)
        await campaign_channel.send(settings["public_message"], view=view_private_message)

        for question in settings["questions"]:
            if question["channel"]:
                try:
                    question_thread = await self.__guild.fetch_channel(question["channel"])
                    if auto_setup:
                        await question_thread.send(question["description"])
                except:
                    pass
            else:
                question_thread = await campaign_channel.create_thread(name=question["title"],
                                                                       type=disnake.ChannelType.public_thread,
                                                                       auto_archive_duration=10080)
                if question["description"]:
                    await question_thread.send(question["description"])
                question["channel"] = question_thread.id

        if send_private_message:
            private_message = PrivateMessage(bot=self.__bot, campaign_settings=settings)
            await private_message.send_private_message_to_all_members(logger)

        settings["active"] = True
        file_path = self.__settings_directory + file_name
        write_yaml(settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def poll_campaign_stop(self, interaction: ApplicationCommandInteraction, name: str, confirmation: str = None):
        """
        Lance une campagne de sondage.

        Parameters
        ----------
        name: :class: str
            Le nom de la campagne à débuter.
        confirmation: class: str
            Pour valider, taper "INTERROMPRE LA CAMPAGNE".
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{interaction.author.mention} a demandé l'arrêt de la campagne de sondage "{name}".""",
            message_success=f"""La campagne de sondage "{name}" a été arrêtée.""",
            message_failure=f"""La campagne de sondage "{name}" n'a pas été arrêtée.""",
            task_info='command.poll.campaign stop',
            interaction=interaction
        )
        await logger.log_start()

        if not confirmation == "INTERROMPRE LA CAMPAGNE":
            await logger.log_message(
                f"""La confirmation de l'arrêt de la campagne de sondage "{name}" n'a pas été correctement saisie.""")
            await logger.log_failure()
            return

        file_name = name + '.yml'
        if file_name not in self.__get_file_list():
            await logger.log_message(f"""La campagne de sondages "{name}" n'existe pas.""")
            await logger.log_failure()
            return

        try:
            campaign_channel = await self.__guild.fetch_channel(settings["channel_id"])
            await campaign_channel.send(f"""Fin de la campagne de sondage "{name}".""")
        except:
            pass

        settings = [settings for settings in self.__settings if settings["name"] == name][0]
        settings["active"] = False
        file_path = self.__settings_directory + file_name
        write_yaml(settings, file_path)

        self.__settings = self.__read_settings()

        await logger.log_success()
        return

    @poll_campaign_edit.autocomplete("name")
    @poll_campaign_check.autocomplete("name")
    @poll_campaign_delete.autocomplete("name")
    @poll_question_add.autocomplete("campaign")
    @poll_question_remove.autocomplete("campaign")
    @poll_campaign_start.autocomplete("name")
    @poll_campaign_stop.autocomplete("name")
    async def autocomplete_poll_campaign_name(self, inter: ApplicationCommandInteraction, user_input: str):
        string = user_input.lower()
        return [x["name"] for x in self.__settings if string in x["name"]]

    @commands.Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        custom_id_split = interaction.component.custom_id.split("_")
        if custom_id_split[0] != "poll":
            return

        campaign_settings = [settings for settings in self.__settings if settings["name"] == custom_id_split[1]][0]
        private_message = PrivateMessage(self.__bot, campaign_settings=campaign_settings)

        if custom_id_split[2] == 'pm':
            await private_message.send_private_message_to_user_who_clicked_on_the_button(interaction)
        elif custom_id_split[2] == 'modal':
            await private_message.show_poll_modal(interaction, custom_id_split)
        elif custom_id_split[2] == 'share':
            await private_message.share_vote_with_community(interaction, custom_id_split)

        return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        for campaign in [x for x in self.__settings if x["newcomers"]]:
            sleep(2)
            private_message = PrivateMessage(self.__bot, campaign_settings=campaign)
            await private_message.send_private_message_to_newcomer(member)
        return


class PrivateMessage(commands.Cog):
    def __init__(self, bot, campaign_settings: dict):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__campaign = campaign_settings
        self.__view = None
        self.__current_poll = {}
        self.__members_contacted = 0

    async def send_private_message_to_all_members(self, logger: Logger) -> int:
        await self.__populate_view()
        for member in self.__bot.get_all_members():
            try:
                await self.__send_vote_options_to_member(member)
            except:
                pass
        await logger.log_message(f"""Le message privé pour la campagne de sondage "{self.__campaign["name"]} a été envoyé à {self.__members_contacted} membres.""")
        return

    async def __populate_view(self):
        self.__view = View()
        await self.__build_event_link_button()
        for question in self.__campaign["questions"]:
            self.__current_poll = question
            self.__add_buttons_to_view()

    async def __build_event_link_button(self):
        campaign_channel = await self.__guild.fetch_channel(self.__campaign["channel_id"])
        button = Button(label="Salon du sondage", url=campaign_channel.jump_url)
        self.__view.add_item(button)

    def __add_buttons_to_view(self):
        if self.__current_poll["options"] <= 5:
            self.__build_and_add_single_button()
        else:
            self.__build_and_add_multiple_buttons()

    def __build_and_add_single_button(self):
        poll_settings = self.__current_poll
        button = Button(label=poll_settings["title"],
                        style=disnake.ButtonStyle.blurple,
                        emoji=poll_settings["emoji"],
                        custom_id=f'poll_{self.__campaign["name"]}_modal_{poll_settings["id"]}_1_{poll_settings["options"]}'
                        )
        self.__view.add_item(button)

    def __build_and_add_multiple_buttons(self):
        poll_settings = self.__current_poll
        poll_options = poll_settings["options"]
        nb_buttons = -(-poll_options // 5)
        for i in range(1, nb_buttons + 1):
            range_start = 5 * (i - 1) + 1
            range_end = 5 * i if i < nb_buttons else poll_options
            button = Button(
                label=f'{poll_settings["title"]} ({range_start} à {range_end})',
                style=disnake.ButtonStyle.blurple,
                emoji=poll_settings["emoji"],
                custom_id=f'poll_{self.__campaign["name"]}_modal_{poll_settings["id"]}_{range_start}_{range_end}'
            )
            self.__view.add_item(button)

    async def __send_vote_options_to_member(self, member):
        if not member.bot:
            self.__members_contacted += 1
            embed = Embed(
                title=self.__campaign["name"],
                description=self.__campaign["private_message"].replace("${user}", member.mention),
                colour=0xF0C43F,
                timestamp=datetime.now(timezone.utc)
            )
            await member.send(embed=embed, view=self.__view)
            return
        else:
            return

    async def send_private_message_to_user_who_clicked_on_the_button(self, interaction: MessageInteraction):
        user = interaction.author
        logger = Logger(
            self.__bot,
            log_group='Bouton',
            message_start=f"""{user.mention} a demandé l'envoi du MP pour la campagne de sondage {self.__campaign["name"]}.""",
            message_success=f"""Le MP pour la campagne de sondage {self.__campaign["name"]} a été envoyé à {user.mention}.""",
            message_failure=f"""Le MP pour la campagne de sondage {self.__campaign["name"]} n'a pas été envoyé à {user.mention}.""",
            task_info='button.poll.pm',
            interaction=interaction
        )
        await logger.log_start()
        await self.__populate_view()
        if user.bot:
            await logger.log_message(f"""{user.mention} est identifié comme un bot.""")
            await logger.log_failure()
            return

        await self.__send_vote_options_to_member(user)
        await logger.log_success()
        return

    async def send_private_message_to_newcomer(self, user):
        logger = Logger(
            self.__bot,
            log_group='Tâche',
            message_success=f"""Le MP pour la campagne de sondage {self.__campaign["name"]} a été envoyé à {user.mention}.""",
            task_info='task.poll.welcome',
            interaction=None
        )
        await self.__populate_view()
        if user.bot:
            return
        await self.__send_vote_options_to_member(user)
        await logger.log_success()
        return

    async def show_poll_modal(self, interaction: MessageInteraction, custom_id_split):
        logger = Logger(
            self.__bot,
            log_group='Bouton',
            task_info='button.poll.modal',
            interaction=interaction
        )
        poll_id = custom_id_split[3]
        poll_range = [int(i) for i in custom_id_split[4:]]
        user_id = interaction.author.id
        poll = [top for top in self.__campaign["questions"] if top["id"] == poll_id][0]
        await logger.log_message(f"**Campagne de sondage {self.__campaign['name']}** : un membre affiche le formulaire *{poll['title']}*.")
        await interaction.response.send_modal(
            modal=ModalBuilder(bot=self.__bot, campaign_name=self.__campaign["name"], question=poll,
                               poll_range=poll_range, user_id=user_id))

    async def share_vote_with_community(self, interaction: MessageInteraction, custom_id_split):
        poll_id = custom_id_split[3]
        poll_info = [top for top in self.__campaign["questions"] if top["id"] == poll_id][0]
        question_thread = await self.__guild.fetch_channel(poll_info["channel"])
        logger = Logger(
            self.__bot,
            log_group='Bouton',
            message_start=f"""**Campagne de sondage {self.__campaign["name"]}** : {interaction.author.mention} souhaite partager son vote sur *{question_thread.mention}*.""",
            message_success=f"**Campagne de sondage {self.__campaign['name']}** : {interaction.user.mention} a publié son vote sur *{question_thread.mention}*",
            task_info='button.poll.share'
        )
        await logger.log_start()
        await interaction.response.defer()

        embed = interaction.message.embeds[0]

        top_item = VoteHandler('poll_' + self.__campaign["name"], interaction.user.id)
        user_vote = top_item.get_vote(poll_id)

        channel_id = poll_info["channel"]
        channel = self.__bot.get_channel(channel_id)

        if "public_message_id" in user_vote.keys():
            public_message = self.__bot.get_message(user_vote["public_message_id"])
        else:
            public_message = None

        if public_message:
            await public_message.edit(content=f"{interaction.author.mention} a voté!", embed=embed,
                                      allowed_mentions=disnake.AllowedMentions(everyone=False, users=False))
        else:
            public_message = await channel.send(content=f"{interaction.author.mention} a voté!", embed=embed,
                                                allowed_mentions=disnake.AllowedMentions(everyone=False, users=True))
        public_message_id = public_message.id

        view_private = View()
        button = Button(label="Voir mon vote dans le fil dédié",
                        url=f"https://discord.com/channels/{secrets.discord_guild}/{channel_id}/{public_message_id}"
                        )
        view_private.add_item(button)
        await interaction.message.edit(view=view_private)
        await logger.log_success()

        top_item.save_vote(poll_id, user_vote["vote"], user_vote["private_message_id"], public_message_id)


class VoteHandler(DynamodbItem):
    def __init__(self, poll: str, user_id: int):
        super().__init__(poll, user_id)

    def get_vote(self, poll_id: str) -> dict:
        output = self._item[poll_id] if poll_id in self._item.keys() else {}
        return output

    def save_vote(self, poll_id: str, vote: list, private_message_id: int, public_message_id: int = None) -> None:
        self._item[poll_id] = self._item[poll_id] if poll_id in self._item.keys() else {}
        self._item[poll_id]["vote"] = vote
        self._item[poll_id]["private_message_id"] = private_message_id

        if public_message_id:
            self._item[poll_id]["public_message_id"] = public_message_id

        self._update_item()


class ModalBuilder(disnake.ui.Modal):
    def __init__(self, bot, campaign_name: str, question: dict, poll_range: list, user_id: int):
        self.__bot = bot
        self.__poll_title = question["title"][:45]
        self.__poll_id = question["id"]
        self.__poll_range_start = poll_range[0]
        self.__poll_range_end = poll_range[1] + 1
        self.__poll_range = range(self.__poll_range_start, self.__poll_range_end)
        self.__label = question["label"]
        self.__display_label_rank = question["ranking"]
        self.__placeholder = question["placeholder"]
        self.__long_input = question["long_input"]
        self.__max_characters = question["max_characters"]
        self.__user_id = user_id
        self.__campaign = campaign_name
        self.__top_item = VoteHandler('poll_' + self.__campaign, self.__user_id)
        self.__vote_info = self.__top_item.get_vote(self.__poll_id)
        self.__vote_list = self.__get_vote_list()
        self.__private_message = self.__get_private_message()
        self.__interaction = None

        self.__components = []
        for i in self.__poll_range:
            value = self.__get_vote(i)
            label = self.__label + (' ' + str(i) if self.__display_label_rank else '')
            self.__components.append(disnake.ui.TextInput(
                label=label,
                value=value,
                placeholder=self.__placeholder,
                custom_id=self.__poll_id + '_' + str(i),
                style=TextInputStyle.paragraph if self.__long_input else TextInputStyle.short,
                max_length=self.__max_characters,
                required=False,
            ))
        super().__init__(
            title=self.__poll_title,
            custom_id=f"{self.__poll_id}_{str(poll_range[0])}_{str(poll_range[1])}",
            components=self.__components,
        )

    def __get_vote_list(self):
        output = self.__vote_info["vote"] if "vote" in self.__vote_info.keys() else []
        return output

    def __get_private_message(self):
        output = self.__bot.get_message(
            self.__vote_info["private_message_id"]) if "private_message_id" in self.__vote_info.keys() else None
        return output

    def __get_vote(self, i):
        try:
            vote = self.__vote_info["vote"][i - 1]
        except IndexError:
            vote = ''
        except KeyError:
            vote = ''
        return vote

    async def callback(self, interaction: disnake.ModalInteraction):
        logger = Logger(
            self.__bot,
            log_group='Modal',
            message_start=f"""**Campagne de sondage {self.__campaign}** : un membre a voté sur {self.__poll_title}.""",
            message_success=f"""**Campagne de sondage {self.__campaign}** : le vote d'un utilisateur sur {self.__poll_title} a été enregistré""",
            task_info='button.poll.share'
        )
        await logger.log_start()
        self.__interaction = interaction
        self.__update_vote_list()
        await self.__interaction.response.defer(with_message=True)
        await self.__send_vote_confirmation()
        self.__push_vote_to_dynamodb()
        await self.__update_poll_buttons()
        await logger.log_success()
        return

    def __update_vote_list(self):
        vote_raw = list(self.__interaction.text_values.values())
        vote_clean = [vote.lstrip().rstrip() for vote in vote_raw if vote.lstrip() != ""]
        vote_updated = self.__vote_list.copy()
        vote_updated[self.__poll_range_start - 1: self.__poll_range_end - 1] = vote_clean
        vote_deduplicated = []
        for vote in vote_updated:
            if vote not in vote_deduplicated:
                vote_deduplicated.append(vote)
        self.__vote_list = vote_deduplicated

    async def __send_vote_confirmation(self):
        view = View()
        button = Button(label="Partager mon vote avec la communauté.",
                        style=disnake.ButtonStyle.green,
                        custom_id=f"poll_{self.__campaign}_share_{self.__poll_id}"
                        )
        view.add_item(button)
        embed = Embed(
            title=self.__poll_title,
            description='\n'.join(self.__vote_list)
        )

        if self.__private_message:
            await self.__private_message.delete()

        text = f"""Merci pour ta réponse ! Nous t'invitons à en vérifier l'exactitude ci-dessous.
        Tu peux la modifier en cliquant à nouveau sur le bouton du vote correspondant."""

        self.__private_message = await self.__interaction.edit_original_response(content=text,
                                                                                 embed=embed,
                                                                                 view=view)

    def __push_vote_to_dynamodb(self):
        self.__top_item.save_vote(self.__poll_id, self.__vote_list, self.__private_message.id)

    async def __update_poll_buttons(self):
        view_edit = View()
        buttons = []
        for action_row in self.__interaction.message.components:
            buttons.extend(action_row.children)
        for button in buttons:
            if button.style == disnake.components.ButtonStyle.link:
                button_new = Button(label=button.label,
                                    url=button.url)
            else:
                button_new = Button(label=button.label,
                                    style=disnake.ButtonStyle.green if self.__poll_id == button.custom_id.split('_')[
                                        3] else button.style,
                                    emoji=button.emoji,
                                    custom_id=button.custom_id)
            view_edit.add_item(button_new)
        await self.__interaction.message.edit(view=view_edit)


def setup(bot):
    bot.add_cog(Poll(bot))
