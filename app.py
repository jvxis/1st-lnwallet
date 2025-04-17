import logging
import os
import requests
from flask import Flask, render_template, request, session, redirect, url_for,jsonify, Response, flash
from auth import auth_blueprint
from lnbits import lnbits_blueprint, get_wallet_balance
from database import init_db, get_translation, register_satsback_transaction, get_db_connection
from config import Config
from auth import auth_blueprint, limiter  # Importando o limiter
from limiter import limiter  # Importando o limiter
import sys
from markupsafe import Markup


def nl2br(value):
    return Markup(value.replace("\n", "<br>"))

# Cria o diretório de logs se não existir
if not os.path.exists('logs'):
    os.makedirs('logs')


# Configura logging para usar UTF-8 (evita erros com emojis)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Saída no console
        logging.FileHandler("logs/app.log", encoding="utf-8")  # Log em arquivo UTF-8
    ]
)

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
app.config.from_object(Config)

app.jinja_env.filters['nl2br'] = nl2br

# Inicializar o Flask-Limiter no app
limiter.init_app(app)

# Registra os Blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(lnbits_blueprint)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))  # redireciona diretamente ao dashboard se logado

    if 'lang' not in session:
        lang = request.accept_languages.best_match(['pt', 'en']) or 'en'
        session['lang'] = 'pt' if lang == 'pt' else 'en'

    translations = get_translation(session.get('lang', 'pt'))
    # Decodifica caracteres escapados (caso o banco esteja armazenando "\\n")
    # Apenas substitui \n por <br> sem modificar outros caracteres
    translations["home_intro"] = str(translations["home_intro"]).replace("\\n", "<br>")

    # Log para verificar se a substituição aconteceu
    #logging.info(f"Texto depois do Markup: {translations['home_intro']}")
    return render_template('index.html', translations=translations)

@app.route('/terms')
def terms():
    translations = get_translation(session.get('lang', 'pt'))
    return render_template('terms.html', translations=translations)

@app.route('/proxy-image')
def proxy_image():
    image_url = request.args.get('url')  # Pega a URL passada na requisição
    headers = {'User-Agent': 'Mozilla/5.0'}  # Evita bloqueios de hotlinking
    
    try:
        response = requests.get(image_url, headers=headers)
        return Response(response.content, mimetype=response.headers['Content-Type'])
    except Exception as e:
        return Response("Imagem não encontrada", status=404)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['pt', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    translations = get_translation(session.get('lang', 'pt'))
    user = session['user']
    balance_data = get_wallet_balance(user['adminkey'])
    balance_msat = int(balance_data.get('balance', 0))
    balance = balance_msat // 1000  # convertendo milisats para sats

    ln_address = f"{user['lnurl'].split('/')[-1]}@{Config.LN_ADDRESS_DOMAIN}"
    return render_template('dashboard.html', translations=translations, user=user, balance=balance, ln_address=ln_address)

@app.route('/api/get_balance', methods=['GET'])
def get_balance():
    if 'user' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401

    user = session['user']
    balance_data = get_wallet_balance(user['adminkey'])
    balance_msat = int(balance_data.get('balance', 0))
    balance = balance_msat // 1000  # Convertendo mili-satoshis para satoshis

    return jsonify({'balance': balance})

@app.route('/decode_invoice', methods=['POST'])
def decode_invoice():
    data = request.get_json()
    invoice = data['invoice']

    headers = {'Content-Type': 'application/json'}
    payload = {'data': invoice}

    try:
        r = requests.post(f"{Config.LN_BITS_API_URL}/payments/decode", json=payload, headers=headers)
        r.raise_for_status()
        result = r.json()

        amount_sats = int(result.get('amount_msat', 0)) // 1000
        description = result.get('description', 'N/A')
        expiry = result.get('expiry', 0)

        return jsonify({
            'amount_sats': amount_sats,
            'description': description,
            'expiry': expiry
        })

    except requests.RequestException as e:
        return jsonify({'error': f'Erro ao decodificar invoice: {str(e)}'}), 400

@app.route('/pay_invoice', methods=['POST'])
def pay_invoice():
    if 'user' not in session:
        translations = get_translation(session.get('lang', 'pt'))
        flash(translations['payment_not_authenticated'], 'danger')
        return jsonify({'success': False, 'error': translations['payment_not_authenticated']}), 401

    translations = get_translation(session.get('lang', 'pt'))
    data = request.get_json()
    invoice = data['invoice']
    user = session['user']
    user_wallet_id = user['wallet_id']

    headers = {'X-Api-Key': user['adminkey'], 'Content-Type': 'application/json'}
    payload = {'out': True, 'bolt11': invoice}

    try:
        # 🔎 Decodificar a invoice antes do pagamento
        decode_headers = {'Content-Type': 'application/json'}
        decode_payload = {'data': invoice}
        r_decode = requests.post(f"{Config.LN_BITS_API_URL}/payments/decode", json=decode_payload, headers=decode_headers)
        r_decode.raise_for_status()
        decode_data = r_decode.json()

        amount_sats = int(decode_data.get("amount_msat", 0)) // 1000  # Convertendo mili-satoshis para satoshis
        if amount_sats == 0:
            logging.error(f"[{user}] {translations['payment_invalid_invoice']}")
            flash(translations['payment_invalid_invoice'], 'danger')
            return jsonify({'success': False, 'error': translations['payment_invalid_invoice']}), 400

        logging.info(f"Invoice decodificada. Valor real: {amount_sats} SATs")

        # 🔥 Processar o pagamento
        logging.info(f"[{user}] Enviando requisição de pagamento para LNbits: {payload}")
        r = requests.post(f"{Config.LN_BITS_API_URL}/payments", json=payload, headers=headers)
        r.raise_for_status()
        payment_data = r.json()

        if "payment_hash" in payment_data:
            transaction_id = payment_data["payment_hash"]
            logging.info(f"[{user}] {translations['payment_success']} - Transaction ID: {transaction_id}")
            flash(translations['payment_success'], 'success')
            # ✅ Registrar SATSBACK
            register_satsback_transaction(user_wallet_id, transaction_id, amount_sats)

            
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            logging.error(f"[{user}] {translations['payment_processing_error']}")
            flash(translations['payment_processing_error'], 'danger')
            return jsonify({'success': False, 'error': translations['payment_processing_error']}), 400

    except requests.RequestException as e:
        logging.error(f"[{user}] {translations['payment_error']} - {e}")
        flash(f"{translations['payment_error']} {str(e)}", 'danger')
        return jsonify({'success': False, 'error': translations['payment_error']}), 400

    
@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401

    data = request.get_json()
    amount = data['amount']
    memo = data['description']

    user_adminkey = session['user']['adminkey']

    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': user_adminkey
    }
    payload = {'out': False, 'amount': amount, 'memo': memo}

    try:
        r = requests.post(f"{Config.LN_BITS_API_URL}/payments", json=payload, headers=headers)
        r.raise_for_status()
        result = r.json()
        return jsonify({
            'success': True,
            'payment_request': result['payment_request'],
        })
    except requests.RequestException as e:
        error_message = e.response.json().get('detail', str(e)) if e.response else str(e)
        logging.error(f"Erro ao gerar invoice: {error_message}")
        return jsonify({'success': False, 'error': f'Erro ao gerar invoice: {error_message}'}), 400

@app.route('/get_statement')
def get_statement():
    if 'user' not in session:
        return jsonify([]), 401

    user_adminkey = session['user']['adminkey']
    headers = {
        'accept': 'application/json',
        'X-Api-Key': user_adminkey
    }

    try:
        r = requests.get(f"{Config.LN_BITS_API_URL}/payments?direction=desc", headers=headers)
        r.raise_for_status()
        payments = r.json()
        return jsonify(payments)

    except requests.RequestException as e:
        logging.error(f"Erro ao buscar extrato: {e}")
        return jsonify([]), 500
@app.route('/get_satsback')
def get_satsback():
    if 'user' not in session:
        return jsonify([]), 401

    user_wallet_id = session['user']['wallet_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obter saldo total disponível e total já resgatado
        cursor.execute('''
        SELECT total_satsback, last_claim_amount FROM satsback_users
        WHERE wallet_id = ?
        ''', (user_wallet_id,))
        user_data = cursor.fetchone()
        total_available = (user_data[0]) if user_data else 0  # Converter msats → sats
        total_claimed = (user_data[1]) if user_data and user_data[1] else 0  # Converter msats → sats

        # Obter histórico das transações
        cursor.execute('''
        SELECT timestamp, transaction_id, amount_sats, satsback_amount, claimed
        FROM satsback_transactions
        WHERE wallet_id = ?
        ORDER BY timestamp DESC
        ''', (user_wallet_id,))
        
        transactions = cursor.fetchall()
        conn.close()

        # Construir resposta com dados formatados
        transactions_list = [
            {
                "date": row[0],
                "payment_hash": row[1][:10] + "..." + row[1][-6:],  # Mascarar hash
                "original_amount": row[2],  # Valor original da transação em SATs
                "satsback_amount": "{:.4f}".format(row[3] / 1000),  # Converter msats → sats com 4 casas
                "status": "🟢" if row[4] else "🔵"  # Resgatado ou não
            }
            for row in transactions
        ]

        return jsonify({
            "total_available": int(total_available),  # Saldo disponível em SATs
            "total_claimed": int(total_claimed),  # Total já resgatado
            "transactions": transactions_list
        })

    except Exception as e:
        logging.error(f"Erro ao buscar SATSBACK: {e}")
        return jsonify([]), 500

@app.route('/claim_satsback', methods=['POST'])
def claim_satsback():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401

    user_wallet_id = session['user']['wallet_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obter o saldo disponível para resgate
        cursor.execute('SELECT total_satsback FROM satsback_users WHERE wallet_id = ?', (user_wallet_id,))
        user_data = cursor.fetchone()
        if not user_data or user_data['total_satsback'] < 10:  # Checando em sats 
            return jsonify({'success': False, 'error': 'Saldo insuficiente para resgate'}), 400
        
        total_satsback = int(user_data['total_satsback'] / 1000)  # Convertendo msats → sats
        
        # Obter o LNURL do usuário
        cursor.execute('SELECT lnurl FROM users WHERE wallet_id = ?', (user_wallet_id,))
        lnurl_data = cursor.fetchone()
        if not lnurl_data or not lnurl_data['lnurl']:
            return jsonify({'success': False, 'error': 'LNURL não encontrado para o usuário'}), 400
        
        ln_address = f"{lnurl_data['lnurl']}@{Config.LN_ADDRESS_DOMAIN}"

        logging.info(f"[{user_wallet_id}] Iniciando resgate de {total_satsback} SATs para {ln_address}")

        # Resolver o LN Address para obter uma invoice
        resolved = resolve_lnaddress(ln_address, "Resgate de Satsback", amount=total_satsback)
        if "error" in resolved:
            logging.error(f"[{user_wallet_id}] Erro ao resolver LN Address: {ln_address}: {resolved['error']}")
            return jsonify({'success': False, 'error': resolved['error']}), 400
        
        payment_request = resolved.get("payment_request")
        if not payment_request:
            logging.error(f"[{user_wallet_id}] Erro ao obter invoice para pagamento para {ln_address}")
            return jsonify({'success': False, 'error': 'Erro ao obter invoice para pagamento'}), 400

        # Enviar o pagamento via LNbits
        if not send_to_lightning_address(payment_request, total_satsback):
            logging.error(f"[{user_wallet_id}] Erro ao enviar pagamento de {total_satsback} SATs para {ln_address}")
            return jsonify({'success': False, 'error': 'Erro ao processar pagamento'}), 400

        # Atualizar as transações como resgatadas
        cursor.execute('''
            UPDATE satsback_transactions 
            SET claimed = 1 
            WHERE wallet_id = ?
        ''', (user_wallet_id,))

        # Atualizar o registro do usuário acumulando o last_claim_amount
        cursor.execute('''
            UPDATE satsback_users
            SET last_claim_date = datetime('now'), 
                last_claim_amount = last_claim_amount + ?,  -- Acumula o valor ao invés de sobrescrever
                total_satsback = 0
            WHERE wallet_id = ?
        ''', (total_satsback, user_wallet_id))


        conn.commit()
        conn.close()

        logging.info(f"[{user_wallet_id}] Resgate de {total_satsback} SATs concluído para {ln_address}")

        return jsonify({'success': True, 'message': 'Resgate concluído com sucesso'})

    except Exception as e:
        logging.error(f"Erro ao processar resgate: {e}")
        return jsonify({'success': False, 'error': 'Erro interno'}), 500

def resolve_lnaddress(ln_address, description, amount=None):
    try:
        if "@" not in ln_address:
            logging.error(f"Formato de Lightning Address inválido: {ln_address}")
            return {"error": "Formato de Lightning Address inválido"}
        
        user, domain = ln_address.split("@", 1)
        url = f"https://{domain}/.well-known/lnurlp/{user}"
        r1 = requests.get(url, timeout=15)

        if r1.status_code != 200:
            logging.error(f"Erro ao buscar LNURLP: {r1.status_code}")
            return {"error": f"Erro ao buscar LNURLP: {r1.status_code}"}

        lnurl_data = r1.json()
        if "callback" not in lnurl_data:
            logging.error(f"LNURLP callback ausente: {lnurl_data}")
            return {"error": "LNURLP callback ausente"}

        callback_url = lnurl_data["callback"]
        params = {}
        if amount:
            params["amount"] = amount * 1000  # Converte SATs para msats
        if description:
            params["comment"] = description

        final_url = requests.Request("GET", callback_url, params=params).prepare().url
        r2 = requests.get(final_url, timeout=15)

        if r2.status_code == 200:
            final_data = r2.json()
            if "pr" in final_data:
                logging.info(f"payment_request: {final_data['pr']}")
                return {"payment_request": final_data["pr"]}
            logging.error(f"payment_request não encontrado na resposta")
            return {"error": "Payment request (pr) não encontrado na resposta"}
        logging.error(f"Erro ao resolver callback: {r2.status_code}")
        return {"error": f"Erro ao resolver callback: {r2.status_code}"}

    except Exception as e:
        logging.error(f"Exceção ao resolver LN Address: {e}")
        return {"error": str(e)}

def send_to_lightning_address(payment_request, amount_sats):
    url = f"{Config.LN_BITS_API_URL}/payments"
    headers = {"X-Api-Key": Config.SATSBACK_WALLET_ADMIN_KEY, "Content-Type": "application/json"}
    payload = {"out": True, "bolt11": payment_request}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 201:
            logging.info(f"Pagamento de {amount_sats} SATs enviado com sucesso.")
            return True
        else:
            logging.error(f"Erro ao realizar pagamento LN: {resp.text}")
            return False
    except Exception as e:
        logging.error(f"Exceção no pagamento LN: {e}")
        return False


if __name__ == '__main__':
    init_db()  # Inicializar banco apenas aqui, para evitar duplicidade
    logging.info("Iniciando a aplicação Flask...")
    app.run(debug=Config.DEBUG, port=Config.PORT)

