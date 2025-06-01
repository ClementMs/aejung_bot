# Adaptation du notebook du cours d'IA générative sur Kaggle par Clément Msika en utilisant Mistral et ChatGPT
# https://www.kaggle.com/learn-guide/5-day-genai
# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import Annotated, Literal, Annotated, List
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages.ai import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages.tool import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, InjectedState

from collections.abc import Iterable
from random import randint


import os

api_cle_google  = os.environ['API_CLE_GOOGLE'] 

os.environ["GOOGLE_API_KEY"] = api_cle_google

class EtatCommande(TypedDict):
    '''
    Statut représentant la conversation de commande du client.
    '''
    # La conversation de commande. Cela préserve l'historique de conversation entre les noeuds.
    # l'annotation `add_messages` indique à LangGraph que le statut est mis à jour en ajoutant les messages retournés et en ne les remplaçant pas.
    messages: Annotated[list, add_messages]
    # La commande en cours de traitement du client.
    # chaque commande est une liste de texte
    commande: List[str]
    #order: list[tuple]

    # Note indiquant que la prise de commande est confirmée et terminée.
    fin: bool

    
class RobotAeJung():

    def __init__(self, aeJungInstructionsModele, messageBienvenue, menu):

        self.aeJungInstructionsModele = None
        self.messageBienvenue = None
        self.etatCommande = EtatCommande(messages=[], commande=[], fin=False)
        self.nomModeleIAGenerative = 'gemini'
        self.menu = None
        self.modeleLangageMassif = None
    

    def boutonAeJung(self, etatCommande):      
        '''
        Un agent conversationnel. Le wrapper autour de l'interface du modèle. 
        '''
        defaults = {"commande": [], "fin": False}

            

        if etatCommande:

            messageSortie = self.modeleLangageMassif.invoke([self.aeJungInstructionsModele] + etatCommande["messages"])

        else:

            messageSortie = AIMessage(output = messageBienvenue)

        return etatCommande | {"messages": [messageSortie]}

    def noeudCommande(etatCommande: EtatCommande) -> EtatCommande:
        '''
        Le noeud de commande. C'est ici que l'état de la commande est modifié.
        6 appels possible: afficherMenu, ajouterCommande, confirmerCommande, prendreCommande, reinitialiserCommande, executerCommande 
        '''
        messageOutil = etatCommande.get("messages", [])[-1]
        commande = etatCommande.get("commande", [])
        messagesEnvoi = []
        elementsSupprimer = []
        commandePrise = False

        for appelOutil in messageOutil.appelOutils:

            if appelOutil["name"] == "ajouterCommande":

                #print('current order: ' + str(commande))

                # Chaque élément de la commande est défini par du texte. C'est ici que que ces éléments sont transformés en boissons (modificateurs,...).
                modificateurs = appelOutil["args"]["modificateurs"]
                texteModificateur = ", ".join(modificateurs) if modifiers else "pas de modificateurs"



                commande.append(f'{appelOutil["args"]["elementsPlatBoisson"]} ({texteModificateur})')
                reponse = "\n".join(commande)

            if appelOutil["name"] == "afficherMenu":
                return self.menu

            elif appelOutil["name"] == "confirmerCommande":

                # We could entrust the LLM to do order confirmation, but it is a good practice to
                # show the user the exact data that comprises their order so that what they confirm
                # precisely matches the order that goes to the kitchen - avoiding hallucination
                # or reality skew.

                # In a real scenario, this is where you would connect your POS screen to show the
                # order to the user.

                print("Votre commande:")
                if not commande:
                    print("  (pas d'éléments)")

                for elementsPlatBoisson in commande:
                    print(f"  {elementsPlatBoisson}")

                reponse = input("Est-ce correct? ")

            elif appelOutil["name"] == "prendreCommande":

                reponse = "\n".join(commande) if order else "(pas de commande)"


            #elif appelOutil["name"] == "enleverElementsCommande":

            #    print(commande)

            # Each order item is just a string. This is where it assembled as "drink (modifiers, ...)".
            #    modifiers = tool_call["args"]["modifiers"]
            #    modifier_str = ", ".join(modifiers) if modifiers else "no modifiers"

            #    print('modifier_str: '  + str(modifier_str))

            #    items_to_remove.append(tool_call["args"]["food_drink_item"])

            #    print('tool_call["args"]["food_drink_item"]: ' + str(tool_call["args"]["food_drink_item"]))

            #    print('items to remove: ' + str(items_to_remove))

                #order.pop(f'{tool_call["args"]["food_drink_item"]} ({modifier_str})')

                #response = "\n".join(commande)

            elif appelOutil["name"] == "reinitialiserCommande":

                commande.clear()
                reponse = None

            elif appelOutil["name"] == "executerCommande":

                commandeTexte = "\n".join(commande)
                print("Envoi de la commande en cuisine!")
                print(commandeTexte)

            # Préparer les plats et boissons!.
                commandePrise = True
                delaiPreparationLivraisonCommande = str(randint(1, 5))  # delai de préparation et de livraison de la commande en  minutes
                reponseExecutionCommande = 'Votre commande sera prête dans {delaiPreparationLivraisonCommande} minutes'

                print(reponseExecutionCommande)

                # préparer les paramètres d'entrée
                self.generateurVoix(reponseExecutionCommande)

            else:
                raise NotImplementedError(f'Appel outil inconnu: {appelOutil["name"]}')

            # Enregistre les résultats de l'outil comme message d'outil.
            messagesEnvoi.append(
                ToolMessage(
                    content=reponse,
                    name=appelOutil["name"],
                    tool_call_id=appelOutil["id"],
                )
            )

        return {"messages": messagesEnvoi, "commande": commande, "fin": commandePrise}

    def generateurVoix(self, texte):
        '''
        Utilisé notamment dans la fonction prendreCommande de noeudCommande.
        '''
        #prompteur_texte = "Votre commande sera prête dans 5 minutes."
        parametresEntree = processor(texte)
        # generate speech
        sortieVoix = model.generate(**parametresEntree.to(appareil))

        tauxEchantillonnage = model.generation_config.sample_rate
        return Audio(speech_output[0].cpu().numpy(), rate=tauxEchantillonnage)

    def initialisation(self, etatCommande: EtatCommande, messageUtilisateur, aeJungInstructionsModele)  -> StateGraph:
        
        self.aeJungInstructionsModele = aeJungInstructionsModele

        self.etatCommande = etatCommande
        
        self.messageUtilisateur = messageUtilisateur

        outilsAutomatisation = [self.afficherMenu]
        noeudOutil = ToolNode(outilsAutomatisation)

        outilsCommande = [self.ajouterCommande, self.enleverElementsCommande, self.confirmerCommande, self.prendreCommande, self.supprimerCommande, self.executerCommande]

        self.modeleLangageMassif = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")        

        self.modeleLangageMassif = self.modeleLangageMassif.bind_tools(outilsAutomatisation + outilsCommande)        

        # besoin d'initaliser le modèle de langage massif avant car on ne peut pas utiliser de variables dans les fonctions appelées avec add_node? 
        #outilsAutomatisation = [self.afficherMenu(self.menu)]
        #noeudOutil = ToolNode([])
        #noeudOutil = ToolNode(outilsAutomatisation)
       

        aeJungGraphe = StateGraph(EtatCommande)
         
        aeJungGraphe.add_node('robotAeJung', self.boutonAeJung)
        aeJungGraphe.add_node('humain', self.noeudHumain)
        aeJungGraphe.add_node('outils', noeudOutil)
        aeJungGraphe.add_node('priseCommande', self.noeudCommande)

        aeJungGraphe.add_conditional_edges('robotAeJung', self.possiblementVoieVersOutils)
        aeJungGraphe.add_conditional_edges('humain', self.possiblementQuitterNoeudHumain)
        
        aeJungGraphe.add_edge('outils', 'robotAeJung')
        aeJungGraphe.add_edge('priseCommande', 'robotAeJung')
        aeJungGraphe.add_edge(START, 'robotAeJung')
        
        aeJungGraphe = aeJungGraphe.compile()
        

        return aeJungGraphe

    def executerRobotAeJung(self, aeJungGraphe: StateGraph):
    
        self.aeJungGraphe = aeJungGraphe
        config = {'recursion_limit': 100}
        self.aeJungGraphe.invoke({'messages': []}, config)
    

    def possiblementQuitterNoeudHumain(self, etatCommande: EtatCommande) -> Literal["robotAeJung", "__end__"]:
        '''
        Voie vers l'agent conversationnel à moins que l'utilisateur est en train de partir.
        '''
        if etatCommande.get('fin', False):
            return END
        else:
            return "robotAeJung"


    def possiblementVoieVersOutils(self, etatCommande: EtatCommande) -> Literal["outils", "humain"]:
        '''
        Voie vers les noeuds humain et outil en fonction de l'appel outil effectué. 
        '''
        if not (messages:=  etatCommande.get("messages", [])):
            raiseValueError(f"pas de message trouvé en parsant : {etatCommande}")

        # seulement pointer vers le dernier message
        message = messages[-1]
        if hasattr(message, "appelOutils") and len(message.appelOutils) > 0:
            return "outils"
        else:
            return "humain" 
    

    def noeudHumain(self, etatCommande: EtatCommande) -> EtatCommande:
        '''
        Affiche le dernier message du modèle à l'utilisateur, et reçoit l'input de l'utilisateur.
        '''
        self.etatCommande = etatCommande
        dernierMessage = self.etatCommande["messages"][-1]

        demandeUtilisateur = input("Utilisateur: ")

        # Si l'utilisateur essaie de quitter, considérer la conversation comme terminée.
        if demandeUtilisateur in {"q", "quit", "exit", "goodbye"}:
            self.etatCommande["fin"] = True
        
        return self.etatCommande | {"messages": [("user", demandeUtilisateur)]}

    def noeudRobot(self, etatCommande: EtatCommande, aeJungInstructionsModele, nomModeleIAGenerative) -> EtatCommande:
        
        self.nomModeleIAGenerative = nomModeleIAGenerative

        if self.nomModeleIAGenerative == 'gemini':
            llm = ChatGoogleGenerativeAI(model = 'gemini-1.5-flash-latest')        

        self.etatCommande = etatCommande

        self.aeJungInstructionsModele = aeJungInstructionsModele

        if self.etatCommande:

            messageSortie = modeleLangageMassif.invoke([self.aeJungInstructionsModele] + self.etatCommande["messages"])

        else:

            messageSortie = AIMessage(output = self.messageBienvenue)

        return self.etatCommande | {"messages": [messageSortie]}


    @tool
    def afficherMenu(self) -> str:
        '''
        Présente la dernière version à jour du menu.
        '''
        
        return self.menu


    @tool
    def ajouterCommande(self, elementsPlatBoisson: str, modificateurs: Iterable[str]) -> str:
        '''
        Ajoute l'élément de plat ou boisson spécifié à la commande du client en incluant les modificateurs.
        Retourne:
            La commande mise à jour en cours de traitement.
        '''


    @tool
    def confirmerCommande(self) -> str:
        '''
        Demande au client si la commande est correcte.
        Retourne:
            La réponse du client.
        '''

    @tool
    def enleverElementsCommande(self, elementsPlatBoisson: str, modificateurs: Iterable[str]) -> str:
         '''
         Enlève les éléments de la commande si le client veut enlever ces éléments.

         Retourne:
             La commande mise à jour par le client.
         '''


    @tool
    def prendreCommande(self) -> str:
        '''
        Retourne la commande du client en cours de traitement. Un élément par ligne. Chaque élément est suivi de la quantité (nombre entier)
        '''


    @tool
    def supprimerCommande(self):
        '''
        Supprime tous les éléments de la commande du client
        '''

    @tool
    def executerCommande(self) -> int:
        '''
        Envoie la commande à la propriétaire du restaurant  pour délivrer la commande.
        Besoin de connecter avec système de comptabilité. 
        Retourne:
            Le nombre de minutes moyen nécessaire pour que la commande soit prête.
        '''

aeJungInstructionsModele = (
    "system",  # 'system' indique que le message est une instruction système.
    "Vous êtes un robot de commande pour un restaurant de street food coréen, un système interactif de commande de restaurant coréen. Un humain va vous parler des "
    "produits disponibles et vous répondrez à toutes les questions concernant les articles du menu (et uniquement sur "
    "les articles du menu - pas de discussion hors sujet, mais vous pouvez discuter des produits et de leur histoire). "
    "Le client passera une commande pour un ou plusieurs articles du menu, que vous structurerez "
    "et enverrez au système de commande après avoir confirmé la commande avec l'humain. Veuillez demander aux clients s'ils souhaitent manger au restaurant ou à emporter."
    "\n\n"
    "Ajoutez des articles à la commande du client avec ajouterCommande, et réinitialisez la commande avec reinitialiserCommande."
    # Retirez des articles de la commande avec retirer_articles_de_la_commande"
    "Pour voir le contenu de la commande jusqu'à présent, appelez prendreCommande (cela vous est montré, pas à l'utilisateur). "
    "Confirmez toujours la commande avec l'utilisateur (double vérification) avant d'appeler prendrecommande. L'appel à confirmerCommande affichera "
    "les articles de la commande à l'utilisateur et retournera leur réponse à la vue de la liste. Leur réponse peut contenir des modifications. "
    "Vérifiez toujours et répondez avec les noms des boissons, des plats et des modificateurs du MENU avant de les ajouter à la commande. "
    "Si vous n'êtes pas sûr qu'une boisson, un plat ou un modificateur corresponde à ceux du MENU, posez une question pour clarifier ou rediriger. "
    "Vous n'avez que les modificateurs listés dans le menu. "
    "Une fois que le client a terminé de commander des articles, appelez confirmerCommande pour vous assurer qu'elle est correcte, puis faites "
    "les mises à jour nécessaires et appelez ensuite prendreCommande. Une fois que prendreCommande a été appelée, remerciez l'utilisateur et "
    "dites au revoir!",
)

# C'est le message avec lequel le système ouvre la conversation.
messageBienvenue = "Bienvenue chez Ae Jung, un restaurant authentique de street food coréenne situé au cœur de Paris. Tapez `q` pour quitter. Comment puis-je vous servir aujourd'hui ?"



menu = '''

        1) MENU (en incluant le riz et les légumes):
        Poulet épicé (Yangneom): 11,5 euros
        Poulet sucré (Ganjang): 11,5 euros
        Poulet fromage: 11,5 euros

        2) Tteokbokki: 15 euros
        Tteokbokki fromage: 17 euros

        3) Morceaux de poulet coréen à l'unité sans le MENU:
        Soit épicé (Yangneom), sucré (Ganjang), ou fromage
        => Petit (5 pièces): 8 euros
        => Moyen (12 pièces): 16 euros
        => Grand (22 pièces): 30 euros

        4) Bento coréen: 14 euros
        3 options: sauce épicée, parmesan, ou sucrée (ganjang)

        5) Mandu: (5 pièces)
        7 euros

        6) Corn dogs (Hallal)
        4 options:
        a) fromage, saucisse, pommes de terre: 6,5 euros
        b) fromage, saucisse: 5,5 euros
        c) fromage, pommes de terre: 6,5 euros
        d) fromage: 5,5 euros

        7) Boissons

        a) Boissons non-alcoolisées en excluant le thé: 2 euros

        - Volvic
        - Lipton Ice Tea
        - San Pellegrino
        - Coca-Cola: Coca-Cola Zero, aromatisé à la cerise ou normal

        b) Thé

       3 options de thé options: gingembre, yuzu (citron coréen), prune verte

       - glacé: 5,5 euros
       - chaud: 5 euros


       3 options de bubble tea (6 euros):
       - lait aromatisé au sucre de canne et aux perles de tapiocca
       - lait aromatisé au matcha et aux perles de tapioca
       - lait aromatisé au taro et aux perles de tapioca      

'''


etatCommande = EtatCommande(messages=[], commande=[], fin=False)
robotAeJung = RobotAeJung(aeJungInstructionsModele = aeJungInstructionsModele, messageBienvenue = messageBienvenue, menu = menu)
robot = robotAeJung.initialisation(etatCommande = etatCommande, messageUtilisateur = 'bonjour, comment allez-vous ?', aeJungInstructionsModele = aeJungInstructionsModele)
robotAeJung.executerRobotAeJung(robot)
