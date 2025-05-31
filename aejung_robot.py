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
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

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
    commande: list[str]
    #order: list[tuple]

    # Note indiquant que la prise de commande est confirmée et terminée.
    fin: bool

    
class RobotAeJung():

    def __init__(self, aeJungSystint, messageBienvenue):

        self.aeJungSystint = None
        self.messageBienvenue = None
        self.etatCommande = EtatCommande(messages=[], commande=[], fin=False)
        self.nomModeleIAGenerative = 'gemini'
        self.menu = None
    

    def boutonAeJung(self, etatCommande):      
        '''
        Un chatbot. Le wrapper autour de l'interface chat du modèle. 
        '''

        if self.nomModeleIAGenerative == 'gemini':
            llm = ChatGoogleGenerativeAI(model = 'gemini-1.5-flash-latest')


        if etatCommande:

            messageSortie = llm.invoke([self.aeJungSystint] + etatCommande["messages"])

        else:

            messageSortie = AIMessage(output = messageBienvenue)

        return etatCommande | {"messages": [messageSortie]}



    def initialisation(self, etatCommande: EtatCommande, messageUtilisateur, aeJungSystint):

        self.etatCommande = etatCommande

        self.aeJungSystint = aeJungSystint

        self.messageUtilisateur = messageUtilisateur

        aeJungGraphe = StateGraph(EtatCommande)
         
        aeJungGraphe.add_node('robotAeJung', self.boutonAeJung)
        aeJungGraphe.add_node('humain', self.noeudHumain)
        
        aeJungGraphe.add_edge(START, 'robotAeJung')
        aeJungGraphe.add_edge('robotAeJung', 'humain')
        aeJungGraphe.add_conditional_edges('humain', self.possiblementQuitterNoeudHumain)
        aeJungGraphe.compile()
        
        return aeJungGraphe

    def possiblementQuitterNoeudHumain(etatCommande: EtatCommande) -> Literal["robotAeJung", "__end__"]:
        '''
        Voie vers le chatbot à moins que l'utilisateur est en train de partir
        '''
        if etatCommande.get('fin', False):
            return END
        else:
            return "robotAeJung"


    def noeudHumain(self,etatCommande: EtatCommande) -> EtatCommande:
        '''
    Affiche le dernier message du modèle à l'utilisateur, et reçoit l'input de l'utilisateur.
        '''
        self.etatCommande = etatCommande
        dernierMessage = self.etatCommande["messages"][-1]

        inputUtilisateur = input("Utilisateur: ")

        # Si l'utilisateur essaie de quitter, considérer la conversation comme terminée.
        if inputUtilisateur in {"q", "quit", "exit", "goodbye"}:
            self.etatCommande["fin"] = True
        
        return self.etatCommande | {"messages": [("user", inputUtilisateur)]}

    def noeudRobot(self, etatCommande: EtatCommande, aeJungSystint, nomModeleIAGenerative) -> EtatCommande:
        
        self.nomModeleIAGenerative = nomModeleIAGenerative

        if self.nomModeleIAGenerative == 'gemini':
            llm = ChatGoogleGenerativeAI(model = 'gemini-1.5-flash-latest')        

        self.etatCommande = etatCommande

        self.aeJungSystint = aeJungSystint

        if self.etatCommande:

            messageSortie = llm.invoke([self.aeJungSystint] + self.etatCommande["messages"])

        else:

            messageSortie = AIMessage(output = self.messageBienvenue)

        return self.etatCommande | {"messages": [messageSortie]}


    @tool
    def afficher_menu(self, menu) -> str:
        '''
        Présente la dernière version à jour du menu.
        '''
        # Note that this is just hard-coded text, but you could connect this to a live stock
        # database, or you could use Gemini's multi-modal capabilities and take live photos of
        # your cafe's chalk menu or the products on the counter and assemble them into an input.
        self.menu = menu
        return self.menu

aeJungSystint = (
    "system",  # 'system' indique que le message est une instruction système.
    "Vous êtes un robot de commande pour un restaurant de street food coréen, un système interactif de commande de restaurant coréen. Un humain va vous parler des "
    "produits disponibles et vous répondrez à toutes les questions concernant les articles du menu (et uniquement sur "
    "les articles du menu - pas de discussion hors sujet, mais vous pouvez discuter des produits et de leur histoire). "
    "Le client passera une commande pour un ou plusieurs articles du menu, que vous structurerez "
    "et enverrez au système de commande après avoir confirmé la commande avec l'humain. Veuillez demander aux clients s'ils souhaitent manger au restaurant ou à emporter."
    "\n\n"
    "Ajoutez des articles à la commande du client avec ajouter_a_la_commande, et réinitialisez la commande avec reinitialiser_commande."
    # Retirez des articles de la commande avec retirer_articles_de_la_commande"
    "Pour voir le contenu de la commande jusqu'à présent, appelez prendre_commande (cela vous est montré, pas à l'utilisateur). "
    "Confirmez toujours la commande avec l'utilisateur (double vérification) avant d'appeler prendre_commande. L'appel à confirmer_commande affichera "
    "les articles de la commande à l'utilisateur et retournera leur réponse à la vue de la liste. Leur réponse peut contenir des modifications. "
    "Vérifiez toujours et répondez avec les noms des boissons, des plats et des modificateurs du MENU avant de les ajouter à la commande. "
    "Si vous n'êtes pas sûr qu'une boisson, un plat ou un modificateur corresponde à ceux du MENU, posez une question pour clarifier ou rediriger. "
    "Vous n'avez que les modificateurs listés dans le menu. "
    "Une fois que le client a terminé de commander des articles, appelez confirmer_commande pour vous assurer qu'elle est correcte, puis faites "
    "les mises à jour nécessaires et appelez ensuite prendre_commande. Une fois que prendre_commande a été appelée, remerciez l'utilisateur et "
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


etatCommande = etatCommande = EtatCommande(messages=[], commande=[], fin=False)
robotAeJung = RobotAeJung(aeJungSystint = aeJungSystint, messageBienvenue = messageBienvenue)
chat = robotAeJung.initialisation(etatCommande = etatCommande, messageUtilisateur = 'bonjour, comment allez-vous ?', aeJungSystint = aeJungSystint)

