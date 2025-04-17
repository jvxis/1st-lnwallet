import requests
import logging
from flask import Blueprint
from config import Config

lnbits_blueprint = Blueprint('lnbits', __name__)

# Criação da carteira no LNbits

def create_wallet(name):
    try:
        headers = {"X-Api-Key": Config.LN_BITS_API_KEY, "Content-Type": "application/json"}
        data = {"name": name}
        response = requests.post(f"{Config.LN_BITS_API_URL}/wallet", json=data, headers=headers)
        response.raise_for_status()
        logging.info(f"Carteira {name} criada com sucesso.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao criar carteira: {e}")
        return {"error": "Erro ao criar carteira"}


def get_wallet_balance(adminkey):
    try:
        headers = {"X-Api-Key": adminkey}
        response = requests.get(f"{Config.LN_BITS_API_URL}/wallet", headers=headers)
        response.raise_for_status()
        logging.info("Saldo da carteira obtido com sucesso.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao obter saldo da carteira: {e}")
        return {"error": "Erro ao obter saldo"}


def create_lnurl_pay_link(adminkey, username, wallet_id):
    try:
        headers = {
            "X-Api-Key": adminkey,
            "Content-Type": "application/json"
        }
        data = {
            "description": f"LNURL Pay para {username}",
            "max": 1000000,
            "min": 1,
            "comment_chars": 200,
            "username": username,
            "wallet": wallet_id  # Campo adicionado corretamente
        }
        response = requests.post(f"{Config.LN_BITS_BASE_URL}/lnurlp/api/v1/links", json=data, headers=headers)
        response.raise_for_status()
        logging.info(f"LNURL Pay link criado com sucesso para {username}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao criar link LNURL Pay: {e}")
        return {"error": "Erro ao criar LNURL Pay link"}

