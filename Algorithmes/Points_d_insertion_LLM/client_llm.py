import os

import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()  # va chercher les clés API dans le .env à la racine du projet

# Les deux fonctions ci-dessous ont volontairement la MÊME signature
# (prompt, max_tokens) -> texte, pour être interchangeables : n'importe
# quel hook LLM du projet peut recevoir l'une ou l'autre en paramètre
# ("demander"), sans rien savoir de quel fournisseur c'est réellement.


def demander_a_claude(prompt, max_tokens=600, modele="claude-sonnet-5"):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    reponse = client.messages.create(
        model=modele,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    # reponse.content peut contenir un bloc de "réflexion" (ThinkingBlock)
    # avant le texte -- on cherche le premier bloc qui a vraiment du texte
    for bloc in reponse.content:
        if bloc.type == "text":
            return bloc.text
    return ""


def demander_a_deepseek(prompt, max_tokens=600, modele="deepseek-v4-pro"):
    client = openai.OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    reponse = client.chat.completions.create(
        model=modele,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return reponse.choices[0].message.content
