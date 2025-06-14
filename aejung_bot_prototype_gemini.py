import os

from typing import Annotated, Literal, Annotated, List
from typing_extensions import TypedDict

from google import genai

from langgraph.graph.message import add_messages
from langchain_core.messages.ai import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages.tool import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, InjectedState
from langchain_core.messages import AIMessage, HumanMessage

from langchain.chat_models import init_chat_model

from IPython.display import Image, display

from collections.abc import Iterable
from random import randint

import pydub
import requests
import csv
import subprocess
import ast

from pydub import AudioSegment
from pydub.playback import play

from datetime import datetime, timedelta


from langchain.chat_models import init_chat_model

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas as genererSignatureAccesPartageBlob, BlobSasPermissions as permissionsSignatureAccesPartageBlob

with open('identifiants_api_informatique_nuage.json','r') as identifiants_informatique_nuage:
    identifiants_informatique_nuage = str(identifiants_informatique_nuage.read())
    identifiants_informatique_nuage = ast.literal_eval(identifiants_informatique_nuage)


nomCompte = 'azureclementmsika'
cleCompte = identifiants_informatique_nuage['CLE_COMPTE_AZURE'] 
nomConteneur = 'aejung-1748699492400'

texteConnecte = 'DefaultEndpointsProtocol=https;AccountName=' + nomCompte + ';AccountKey=' + cleCompte + ';EndpointSuffix=core.windows.net'

blobServiceClient = BlobServiceClient.from_connection_string(texteConnecte)

conteneurClient = blobServiceClient.get_container_client('aejung-1748699492400')

signatureAccesPartageLienUniqueRessourceListe = [] 

for blob in conteneurClient.list_blobs():
    
    nomBlob = blob.name
    
    signatureAccesPartage = genererSignatureAccesPartageBlob(account_name = nomCompte,
                                                             container_name = nomConteneur,
                                                             blob_name = nomBlob,
                                                             account_key = cleCompte,
                                                             permission = permissionsSignatureAccesPartageBlob(read=True),
                                                             expiry = datetime.utcnow() + timedelta(hours=1))
    
    
    signatureAccesPartageLienUniqueRessource = 'https://' + nomCompte + '.blob.core.windows.net/'  + nomConteneur + '/' + nomBlob +  '?' + signatureAccesPartage
    
    signatureAccesPartageLienUniqueRessourceListe.append(signatureAccesPartageLienUniqueRessource)


reponseFichierBlobAccesPartage = requests.get(signatureAccesPartageLienUniqueRessourceListe[0])

with open('commande_restaurant.blob', 'wb') as fichier:
    
    fichier.write(reponseFichierBlobAccesPartage.content)


subprocess.run(['ffmpeg', '-y', '-i', 'commande_restaurant.blob', 'commande_restaurant.wav'], check=True)

clientGenAI = genai.Client(api_key = identifiants_informatique_nuage["GOOGLE_API_KEY"])


model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

menu = """

Les plats et boissons sont référencés par des ids (1,2,3,4...). 

    MENU (en incluant le riz et les légumes). 
    
    1: Poulet épicé (Yangneom): 11,5 euros
    2: Poulet sucré (Ganjang): 11,5 euros
    3: Poulet fromage: 11,5 euros

    4: Tteokbokki: 15 euros
    5: Tteokbokki fromage: 17 euros

    Morceaux de poulet coréen à l'unité sans le MENU:
    Soit épicé (Yangneom), sucré (Ganjang), ou fromage
    => Petit (5 pièces): 8 euros
    => Moyen (12 pièces): 16 euros
    => Grand (22 pièces): 30 euros
    
    6: Poulet coréen épicé 5 pièces
    7: Poulet coréen épicé 12 pièces
    8: Poulet coréen épicé 22 pièces
    
    9: Poulet coréen sucré 5 pièces
    10: Poulet coréen sucré 12 pièces
    11: Poulet coréen sucré 22 pièces
    
    12: Poulet coréen fromage 5 pièces
    13: Poulet coréen fromage 12 pièces
    14: Poulet coréen fromage 22 pièces
    

    Bento coréen: 14 euros
    Trois options: 
    15: bento sauce épicée, 
    16: bento parmesan
    17: bento sauce sucrée (ganjang) 

    18: Mandu: (5 pièces)
    7 euros

    Corn dogs (Hallal)
    4 options:
    19: corn dog fromage, saucisse, pommes de terre: 6,5 euros
    20: corn dog fromage, saucisse: 5,5 euros
    21: corn dog fromage, pommes de terre: 6,5 euros
    22: corn dog fromage: 5,5 euros

    Boissons

    Boissons non-alcoolisées en excluant le thé: 2 euros

    23: Volvic
    24: Lipton Ice Tea
    25: San Pellegrino
    26: Coca-Cola Zero 
    27: Coca-Cola aromatisé à la cerise 
    28: Coca-Cola normal

    b) Thé

    3 options de thé qui peut être glacé (5,5 euros) ou chaud (5 euros)
    29: thé gingembre glacé
    30: thé gingembre chaud
    31: thé yuzu (citron coréen) glacé 
    32: thé yuzu (citron coréen) chaud 
    33: thé prune verte glacé
    34: thé prune verte chaud


    Trois options de bubble tea (6 euros): 
    35: lait aromatisé au sucre de canne et aux perles de tapiocca
    36: lait aromatisé au matcha et aux perles de tapioca
    37: lait aromatisé au taro et aux perles de tapioca

  """



aeJungInstructionsModele =  'vous êtes un robot de commande pour un restaurant coréen de cuisine de rue. Vous devez identifier les plats et boissons commandés en fonction de la commande sous forme de liste. '
aeJungInstructionsModele += 'Vous ne pouvez pas poser de question au client. Si le client ne précise pas, vous devez choisir au hasard les plats et boissons commandés. Vous ne pouvez pas poser de question au client.'
aeJungInstructionsModele += 'vous devez fournir comme message de sortie une structure Python liste obligatoirement qui contient deux dictionnaires, le premier contenant les plats et le second décrivant les boissons commandées avec en clé le numéro du plat ou de la boisson et en valeur un dictionnaire contenant le nom des plats, le numéro des plats, la quantité  et le prix par unité .'

reponse_agent_conversationnel = model.invoke(
    [
        HumanMessage(content=menu),
        HumanMessage(content=aeJungInstructionsModele),
        AIMessage(content="Bonjour que souhaitez-vous aujourd'hui"),
        HumanMessage(content=reponse.text),
    ]
)


commande_aejung = reponse_agent_conversationnel.content.replace('\n','').replace('`','').replace('python','').replace("'","")

commande_aejung = ast.literal_eval(commande_aejung)

print(commande_aejung)
