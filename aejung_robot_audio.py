from typing import Annotated, Literal, Annotated, List
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages.ai import AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

import os

from IPython.display import Image, display

api_cle_google  = os.environ['API_CLE_GOOGLE']

os.environ["GOOGLE_API_KEY"] = api_cle_google



from typing import TypedDict, List, Literal
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

class EtatCommande(TypedDict):
    messages: List[AIMessage]
    commande: List[str]
    fin: bool

class RobotAeJung:
    
    def __init__(self, aeJungInstructionsModele, messageBienvenue, menu):
        
        self.aeJungInstructionsModele = aeJungInstructionsModele
        self.messageBienvenue = messageBienvenue
        self.menu = menu
        self.nomModeleIAGenerative = 'gemini'
        self.etatCommande = EtatCommande(messages=[], commande=[], fin=False)
        self.modeleLangageMassif = ChatGoogleGenerativeAI(model='gemini-1.5-flash-latest')

    def boutonAeJung(self, state: EtatCommande) -> EtatCommande:
        
        if state["messages"]:
            messageSortie = self.modeleLangageMassif.invoke([self.aeJungInstructionsModele] + state["messages"])
        else:
            messageSortie = AIMessage(content=self.messageBienvenue)

        return state | {"messages": [messageSortie]}

    def initialisation(self, etatCommande: EtatCommande, messageUtilisateur: str) -> StateGraph:
        
        self.etatCommande = etatCommande
        self.messageUtilisateur = messageUtilisateur

        aeJungGraphe = StateGraph(EtatCommande)

        aeJungGraphe.add_node("aeJungRobot", self.boutonAeJung)
        aeJungGraphe.add_node("humain", self.noeudHumain)

        aeJungGraphe.add_edge(START, "aeJungRobot")
        aeJungGraphe.add_edge("aeJungRobot", "humain")
        aeJungGraphe.add_conditional_edges("humain", self.possiblementQuitterNoeudHumain)

        aeJungRobotAvecGraphe = aeJungGraphe.compile()

        user_msg = HumanMessage(content="Bonjour, que proposez-vous?")
        state = aeJungRobotAvecGraphe.invoke({"messages": [user_msg]})

        for msg in state["messages"]:
            print(f"{type(msg).__name__}: {msg.content}")

        return aeJungRobotAvecGraphe

    def possiblementQuitterNoeudHumain(self, state: EtatCommande) -> Literal["aeJungRobot", "__end__"]:
        if state.get("fin", False):
            return END
        else:
            return "aeJungRobot"

    def noeudHumain(self, state: EtatCommande) -> EtatCommande:
        
        dernierMessage = state["messages"][-1]
        print("Model:", dernierMessage.content)

        demandeUtilisateur = input("Client: ")

        if demandeUtilisateur.lower() in {"q", "quit", "exit", "goodbye"}:
            state["fin"] = True

        return state | {"messages": [HumanMessage(content=demandeUtilisateur)]}

# Exemple d'utilisation
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
robotAeJung = RobotAeJung(aeJungInstructionsModele=aeJungInstructionsModele, messageBienvenue=messageBienvenue, menu=menu)
robot = robotAeJung.initialisation(etatCommande=etatCommande, messageUtilisateur='Bonjour, comment allez-vous ?')
  

