import logging
import sqlite3
import pyotp
import qrcode
import io
from flask import Blueprint, request, redirect, url_for, session, flash, render_template, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from lnbits import create_wallet, create_lnurl_pay_link
from database import get_db_connection, get_translation
import base64
from PIL import Image
from limiter import limiter
import requests
import re
import io
import time
from urllib.parse import urlparse

FAILED_ATTEMPTS_KEY = "failed_login_attempts"  # Nome da chave para armazenar falhas
auth_blueprint = Blueprint('auth', __name__)


def validate_image_url(url):
    ALLOWED_DOMAINS = ["imgur.com", "cdn.example.com"]
    ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/gif"]
    MAX_IMAGE_KB = 500  # Tamanho máximo da imagem final permitida
    MAX_DOWNLOAD_KB = 600  # Tamanho máximo de download permitido
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        logging.info(f"Validando URL da imagem: {url}")

        # 🚫 Bloquear acessos a IPs internos
        parsed_url = urlparse(url)
        if parsed_url.hostname and (parsed_url.hostname.startswith("localhost") or parsed_url.hostname.startswith("127.") or parsed_url.hostname.startswith("10.") or parsed_url.hostname.startswith("192.168.")):
            logging.warning(f"Acesso bloqueado para endereço interno: {url}")
            return False

        # 🔎 Verifica se a URL pertence a domínios confiáveis
        if not any(domain in url for domain in ALLOWED_DOMAINS):
            logging.warning(f"URL não pertence a domínios permitidos: {url}")
            return False

        # 🔒 Tenta fazer a requisição GET com um User-Agent
        try:
            response = requests.get(url, stream=True, timeout=5, headers=HEADERS)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:
                logging.warning(f"Rate Limit excedido. Aguardando 3 segundos e tentando novamente...")
                time.sleep(3)
                response = requests.get(url, stream=True, timeout=5, headers=HEADERS)
                response.raise_for_status()
            else:
                logging.error(f"Erro HTTP ao acessar imagem: {err}")
                return False

        # 🚫 Limitar tamanho da imagem (para evitar DoS)
        content_length = int(response.headers.get("Content-Length", 0))
        if content_length > MAX_DOWNLOAD_KB * 1024:
            logging.warning(f"Imagem excede o tamanho máximo permitido ({content_length / 1024:.2f} KB)")
            return False

        # 🔎 Baixa no máximo 600KB
        image_data = io.BytesIO()
        total_size = 0
        for chunk in response.iter_content(1024):
            image_data.write(chunk)
            total_size += len(chunk)
            if total_size > MAX_DOWNLOAD_KB * 1024:
                logging.warning(f"Download interrompido, imagem muito grande ({total_size / 1024:.2f} KB)")
                return False

        # 🔍 Detectar tipo de conteúdo real via PIL
        try:
            image_data.seek(0)  # Reseta ponteiro
            image = Image.open(image_data)
            detected_format = image.format.lower()
            content_type = f"image/{detected_format}"
            logging.info(f"Formato detectado pela PIL: {content_type}")
        except Exception as e:
            logging.warning(f"Falha ao detectar formato da imagem com PIL: {e}")
            return False

        # 🔒 Verifica se o formato é permitido
        if content_type not in ALLOWED_TYPES:
            logging.warning(f"Formato de imagem não permitido: {content_type}")
            return False

        # 🚫 Valida tamanho real da imagem após o download
        image_size_kb = total_size / 1024
        logging.info(f"Tamanho final da imagem: {image_size_kb:.2f} KB")

        if image_size_kb > MAX_IMAGE_KB:
            logging.warning(f"Imagem muito grande: {image_size_kb:.2f} KB")
            return False

        logging.info("Imagem validada com sucesso.")
        return True

    except Exception as e:
        logging.error(f"Erro ao validar imagem: {e}")
        return False

@auth_blueprint.route('/register', methods=['GET'])
def show_register():
    translations = get_translation(session.get('lang', 'pt'))
    return render_template('register.html', translations=translations)


@auth_blueprint.route('/register', methods=['POST'])
def register():
    try:
        lang = session.get('lang', 'pt')
        translations = get_translation(lang)

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        logo_url = request.form.get('logo_url', '')

        if logo_url and not validate_image_url(logo_url):
            flash(translations['error_logo_url'], "warning")
            logging.warning(f"URL da imagem inválida: {logo_url}")
            return redirect(url_for('auth.show_register'))
        
        # Verificar se o e-mail já está registrado
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            flash(translations['email_exists'], "warning")
            return redirect(url_for('auth.show_register'))

        # Regras de validação
        if not re.match(r"^[a-zA-Z0-9]{4,}$", name):
            flash(translations['error_wallet_name'], "warning")
            return redirect(url_for('auth.show_register'))

        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            flash(translations['error_email'], "warning")
            return redirect(url_for('auth.show_register'))

        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$", password):
            flash(translations['error_password'], "warning")
            return redirect(url_for('auth.show_register'))

        # Hash da senha
        hashed_password = generate_password_hash(password)

        # Criar chave secreta do 2FA
        totp_secret = pyotp.random_base32()

        session['pending_registration'] = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'logo_url': logo_url,
            'totp_secret': totp_secret  # ✅ Adicionando a chave secreta
        }

        #flash(translations['register_success'], "success")
        return redirect(url_for('auth.setup_2fa'))

    except Exception as e:
        logging.error(f"Erro no registro: {e}")
        flash(translations['register_error'], "danger")
        return redirect(url_for('index'))


@auth_blueprint.route('/setup_2fa', methods=['GET'])
def setup_2fa():
    if 'pending_registration' not in session:
        return redirect(url_for('index'))

    translations = get_translation(session.get('lang', 'pt'))

    if 'totp_secret' not in session['pending_registration']:
        logging.error("Erro: TOTP_SECRET não encontrado na sessão.")
        flash(translations['2fa_error'], "danger")
        return redirect(url_for('index'))

    totp_secret = session['pending_registration']['totp_secret']

    name = session['pending_registration']['name']
    email = session['pending_registration']['email']
    logo_url = session['pending_registration']['logo_url']

    totp = pyotp.TOTP(totp_secret)
    otp_auth_url = totp.provisioning_uri(
        f"{name} - {email}", issuer_name="My First Lightning Wallet"
    )

    # 🖼️ **Gerar QR Code como Base64 para exibição direta na página**
    qr = qrcode.make(otp_auth_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template('setup_2fa.html', otp_auth_url=otp_auth_url, qr_base64=qr_base64, translations=translations)

@auth_blueprint.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    
    translations = get_translation(session.get('lang', 'pt'))
    if 'pending_registration' not in session:
        logging.error("Erro: Sessão de registro não encontrada. Redirecionando para a página inicial.")
        flash(translations['2fa_error'], "danger")
        return redirect(url_for('index'))

    code = request.form['code']
    email = session['pending_registration'].get('email', 'Email desconhecido')

    logging.info(f"Tentativa de verificação 2FA para {email}")

    totp_secret = session['pending_registration']['totp_secret']
    totp = pyotp.TOTP(totp_secret)

    if totp.verify(code, valid_window=1):
        logging.info("2FA verificado com sucesso. Criando carteira no LNbits...")

        # Recuperando os dados da sessão
        name = session['pending_registration']['name']
        email = session['pending_registration']['email']
        password = session['pending_registration']['password']
        logo_url = session['pending_registration']['logo_url']

        # Criar a carteira no LNbits
        wallet_data = create_wallet(name)

        logging.info(f"Resposta da API do LNbits: {wallet_data}")  # 💡 Verifica resposta da API

        if not wallet_data or "error" in wallet_data or not wallet_data.get('id'):
            logging.error(f"Erro ao criar carteira para {name}. Resposta da API: {wallet_data}")
            flash(translations['register_error'], "danger")
            return redirect(url_for('index'))

        wallet_id = wallet_data.get('id')
        adminkey = wallet_data.get('adminkey')
        inkey = wallet_data.get('inkey')

        logging.info(f"✅ Carteira criada com sucesso! ID: {wallet_id}")

        # Criar LNURL
        try:
            lnurl = f"{name}{wallet_id[:4]}".lower()
            lnurl_data = create_lnurl_pay_link(adminkey, lnurl, wallet_id)
            logging.info(f"Resposta da API do LNURL: {lnurl_data}")  # 💡 Log do LNURL
            if lnurl_data and "error" in lnurl_data:
                logging.error(f"Erro ao criar LNURL Pay: {lnurl_data['error']}")
                lnurl = "N/A"
            else:
                logging.info(f"✅ LNURL criado com sucesso: {lnurl}")

        except Exception as e:
            logging.error(f"⚠️ Exceção ao criar link LNURL Pay: {e}")
            lnurl = 'N/A'

        # **Salvar no banco de dados**
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (name, email, password, wallet_id, logo_url, adminkey, inkey, lnurl, totp_secret)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, password, wallet_id, logo_url, adminkey, inkey, lnurl, totp_secret))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()

            logging.info(f"✅ Usuário {name} salvo no banco de dados com ID {user_id}.")

        except Exception as e:
            logging.error(f"❌ Erro ao salvar usuário no banco de dados: {e}")
            flash(translations['register_error'], "warning")
            return redirect(url_for('index'))

        # Criar a sessão definitiva do usuário
        session['user'] = {
            'id': user_id,
            'name': name,
            'email': email,
            'wallet_id': wallet_id,
            'adminkey': adminkey,
            'inkey': inkey,
            'lnurl': lnurl,
            'logo_url': logo_url
        }

        # Remover os dados temporários
        session.pop('pending_registration', None)

        logging.info(f"✅ Autenticação 2FA concluída com sucesso para {email}. Redirecionando para o dashboard.")

        flash(translations['2fa_enabled'], "success")
        return redirect(url_for('dashboard'))
    else:
        logging.warning(f"⚠️ 2FA falhou para {email} - Código: {code}")
        flash(translations['2fa_error'], "danger")
        return redirect(url_for('auth.setup_2fa'))

@auth_blueprint.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    translations = get_translation(session.get('lang', 'pt'))
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        code = request.form['code']
        user_id = session['user']['id']

        # Verificar se a nova senha atende aos critérios
        import re
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_pattern, new_password):
            flash(translations['error_password'], "warning")
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_new_password:
            flash(translations['error_password_mismatch'], "warning")
            return redirect(url_for('auth.change_password'))

        # Conectar ao banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password, totp_secret FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], current_password):
            flash(translations['error_current_password'], "danger")
            conn.close()
            return redirect(url_for('auth.change_password'))

        # Verificar código 2FA
        totp = pyotp.TOTP(user['totp_secret'])
        if not totp.verify(code):
            flash(translations['invalid_2fa_code'], "danger")
            conn.close()
            return redirect(url_for('auth.change_password'))

        # Atualizar senha
        hashed_password = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        conn.close()

        flash(translations['password_updated'], "success")
        logging.info(f"Usuário {session['user']['email']} alterou a senha com sucesso.")
        return redirect(url_for('dashboard'))

    return render_template('change_password.html', translations=translations)

@auth_blueprint.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Mantém o limite de 5 tentativas por minuto
def login():
    try:
        lang = session.get('lang', 'pt')
        translations = get_translation(lang)

        email = request.form['email']
        password = request.form['password']

        # Inicializa contagem de tentativas falhas na sessão
        if FAILED_ATTEMPTS_KEY not in session:
            session[FAILED_ATTEMPTS_KEY] = 0

        # **Verifica se o CAPTCHA é necessário**
        requires_captcha = session[FAILED_ATTEMPTS_KEY] >= 3

        if requires_captcha:
            recaptcha_response = request.form.get('g-recaptcha-response')
            recaptcha_secret = Config.RECAPTCHA_SECRET_KEY
            recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"
            recaptcha_payload = {'secret': recaptcha_secret, 'response': recaptcha_response}
            recaptcha_result = requests.post(recaptcha_verify_url, data=recaptcha_payload).json()

            if not recaptcha_result.get("success"):
                logging.warning("⚠️ CAPTCHA falhou! Tentativa de login bloqueada.")
                flash(translations['login_error'], "warning")  # Adiciona emoji para chamar atenção
                return redirect(url_for('index'))


        # **Verifica credenciais no banco**
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not check_password_hash(user['password'], password):
            session[FAILED_ATTEMPTS_KEY] += 1  # Incrementa tentativas falhas
            logging.warning(f"⚠️ Tentativas falhas de login: {session[FAILED_ATTEMPTS_KEY]}")
    
            flash(translations['login_invalid'], "danger")
            return redirect(url_for('index'))


        # **Login bem-sucedido → Reseta tentativas falhas**
        session.pop(FAILED_ATTEMPTS_KEY, None)

        # Armazena informações temporárias na sessão antes de validar o 2FA
        session['pending_2fa'] = {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'wallet_id': user['wallet_id'],
            'adminkey': user['adminkey'],
            'inkey': user['inkey'],
            'lnurl': user['lnurl'],
            'logo_url': user['logo_url']
        }
        return redirect(url_for('auth.verify_2fa_login'))

    except Exception as e:
        logging.error(f"Erro no login: {e}")
        flash(translations['login_error'], "danger")
        return redirect(url_for('index'))




@auth_blueprint.route('/verify_2fa_login', methods=['GET', 'POST'])
def verify_2fa_login():
    if 'pending_2fa' not in session:
        return redirect(url_for('index'))

    translations = get_translation(session.get('lang', 'pt'))

    if request.method == 'POST':
        code = request.form['code']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT totp_secret FROM users WHERE id = ?', (session['pending_2fa']['id'],))
        user = cursor.fetchone()
        conn.close()

        if user is None or not user['totp_secret']:
            flash(translations['2fa_error'], "warning")
            return redirect(url_for('index'))

        totp = pyotp.TOTP(user['totp_secret'])

        if totp.verify(code):
            # Transferimos os dados da sessão temporária para a sessão principal do usuário
            session['user'] = session.pop('pending_2fa')
            flash(translations['2fa_ok'], "success")
            return redirect(url_for('dashboard'))
        else:
            flash(translations['invalid_2fa_code'], "danger")

    return render_template('verify_2fa.html', translations=translations)

@auth_blueprint.route('/logout')
def logout():
    lang = session.get('lang', 'pt')
    translations = get_translation(lang)
    session.clear()
    flash(translations['logout_success'], "success")
    return redirect(url_for('index'))