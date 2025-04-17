import sqlite3
import logging
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = sqlite3.connect(Config.DB_NAME)
        cursor = conn.cursor()

        # Criar tabela de usuários
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            wallet_id TEXT,
            logo_url TEXT,
            adminkey TEXT,
            inkey TEXT,
            lnurl TEXT DEFAULT 'N/A',
            totp_secret TEXT
        )
        ''')

        # Criar tabela de traduções
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            key TEXT PRIMARY KEY,
            pt TEXT NOT NULL,
            en TEXT NOT NULL
        )
        ''')

        # Criar tabelas do SATSBACK
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS satsback_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id TEXT UNIQUE NOT NULL,
            total_satsback INTEGER DEFAULT 0,
            last_claim_date TEXT DEFAULT NULL,
            last_claim_amount INTEGER DEFAULT 0
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS satsback_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id TEXT NOT NULL,
            transaction_id TEXT NOT NULL,
            amount_sats INTEGER NOT NULL,
            satsback_amount INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            claimed INTEGER DEFAULT 0,
            FOREIGN KEY (wallet_id) REFERENCES satsback_users(wallet_id)
        )
        ''')
        
        translations = [
    ('title', '⚡ Carteira Lightning', '⚡ Lightning Wallet'),
    ('welcome', '👋 Bem-vindo à Carteira Lightning', '👋 Welcome to Lightning Wallet'),
    ('description', '💼 Uma carteira rápida e segura para pequenos negócios.', '💼 A fast and secure wallet for small businesses.'),
    ('register', '📝 Registrar', '📝 Register'),
    ('wallet_name', '🏦 Nome da Carteira', '🏦 Wallet Name'),
    ('email', '📧 E-mail', '📧 Email'),
    ('password', '🔑 Senha', '🔑 Password'),
    ('logo_url', '🖼️ URL do Logotipo (Opcional)', '🖼️ Logo URL (Optional)'),
    ('register_button', '✅ Criar Conta', '✅ Create Account'),
    ('login', '🔓 Entrar', '🔓 Login'),
    ('login_button', '🔑 Entrar', '🔑 Sign In'),
    ('dashboard', '📊 Painel de Controle', '📊 Dashboard'),
    ('welcome_user', '👋 Bem-vindo,', '👋 Welcome,'),
    ('wallet_id', '🆔 ID da Carteira', '🆔 Wallet ID'),
    ('balance', '💰 Saldo', '💰 Balance'),
    ('logout', '🚪 Sair', '🚪 Logout'),
    ('register_success', '✅ Conta criada com sucesso! Faça login.', '✅ Account successfully created! Please log in.'),
    ('register_error', '⚠️ Erro ao criar conta. Tente novamente.', '⚠️ Error creating account. Please try again.'),
    ('login_success', '✅ Login realizado com sucesso.', '✅ Login successful.'),
    ('login_invalid', '❌ Credenciais inválidas. Tente novamente.', '❌ Invalid credentials. Please try again.'),
    ('login_error', '⚠️ Erro ao fazer login.', '⚠️ Error logging in.'),
    ('logout_success', '👋 Você saiu com sucesso.', '👋 You have successfully logged out.'),
    ('welcome_back', '🔄 Bem-vindo de volta', '🔄 Welcome back'),
    ('register_here', '🆕 Ainda não tem uma conta? Registre-se aqui', '🆕 Do not have an account? Register here'),
    ('have_account', '👤 Já tem uma conta?', '👤 Already have an account?'),
    ('login_here', '🔑 Faça login aqui', '🔑 Login here'),
    ('lightning_address', '⚡ Endereço Lightning', '⚡ Lightning Address'),
    ('pay_invoice', '💳 Pagar Invoice', '💳 Pay Invoice'),
    ('receive', '📥 Receber', '📥 Receive'),
    ('paste_invoice', '📋 Cole a invoice aqui', '📋 Paste invoice here'),
    ('scan_qr', '📷 Escanear QR Code', '📷 Scan QR Code'),
    ('check_invoice', '🔍 Checar Invoice', '🔍 Check Invoice'),
    ('amount', '💲 Valor', '💲 Amount'),
    ('description_invoice', '📝 Descrição', '📝 Description'),
    ('expiry', '⏳ Expira em', '⏳ Expires in'),
    ('confirm_payment', '✅ Confirmar Pagamento', '✅ Confirm Payment'),
    ('close', '❌ Fechar', '❌ Close'),
    ('receive_payment', '📥 Receber Pagamento', '📥 Receive Payment'),
    ('amount_sats', '💰 Valor em Satoshis', '💰 Amount in Satoshis'),
    ('generate_invoice', '⚡ Gerar Invoice', '⚡ Generate Invoice'),
    ('payment_request', '📜 Pedido de Pagamento', '📜 Payment Request'),
    ('copy_invoice', '📋 Copiar Invoice', '📋 Copy Invoice'),
    ('back_dashboard', '⬅️ Voltar ao Dashboard', '⬅️ Back to Dashboard'),
    ('statement', '📜 Extrato', '📜 Statement'),
    ('fee', '💸 Taxa', '💸 Fee'),
    ('go_to_dashboard', '📊 Ir para o Painel', '📊 Go to Dashboard'),
    
    # **Mensagens de 2FA**
    ('setup_2fa', '🔐 Configurar autenticação em duas etapas (2FA)', '🔐 Setup two-factor authentication (2FA)'),
    ('verify_2fa', '🔍 Verificação em duas etapas', '🔍 Two-factor verification'),
    ('enter_2fa_code', '🔢 Digite o código gerado pelo seu aplicativo 2FA', '🔢 Enter the code from your 2FA app'),
    ('invalid_2fa_code', '❌ Código 2FA inválido.', '❌ Invalid 2FA code.'),
    ('2fa_enabled', '✅ Autenticação em duas etapas ativada com sucesso.', '✅ Two-factor authentication successfully enabled.'),
    ('2fa_error', '⚠️ Erro ao ativar autenticação em duas etapas.', '⚠️ Error enabling two-factor authentication.'),
    ('2fa_ok', '✅ Autenticação em duas etapas verificada com sucesso.', '✅ Two-factor authentication successfully verified.'),
    ('verify', '✅ Verificar', '✅ Verify'),
    ('2fa_setup_instruction', '📷 Escaneie este QR Code com seu aplicativo autenticador.', '📷 Scan this QR Code with your authenticator app.'),
    ('change_password', '🔑 Alterar Senha', '🔑 Change Password'),
    ('current_password', '🔒 Senha Atual', '🔒 Current Password'),
    ('new_password', '🆕 Nova Senha', '🆕 New Password'),
    ('confirm_new_password', '✅ Confirmar Nova Senha', '✅ Confirm New Password'),
    ('update_password', '💾 Atualizar Senha', '💾 Update Password'),
    ('password_updated', '✅ Senha alterada com sucesso!', '✅ Password successfully updated!'),
    ('error_current_password', '❌ Senha atual incorreta.', '❌ Incorrect current password.'),
    ('error_password_mismatch', '⚠️ As senhas não coincidem.', '⚠️ Passwords do not match.'),
    # Mensagens de Pagamento Invoice
     ('payment_success', '✅ Pagamento realizado com sucesso!', '✅ Payment successful!'),
    ('payment_failed', '❌ Falha no pagamento.', '❌ Payment failed.'),
    ('payment_error', '⚠️ Erro no pagamento.', '⚠️ Payment error.'),
    ('payment_not_authenticated', '⚠️ Usuário não autenticado.', '⚠️ User not authenticated.'),
    ('payment_invalid_invoice', '⚠️ Erro ao obter valor da invoice.', '⚠️ Error retrieving invoice value.'),
    ('payment_processing_error', '❌ Erro ao processar pagamento.', '❌ Error processing payment.'),
    # **Mensagens de erro de validação**
    ('error_wallet_name', '⚠️ O nome da carteira deve ter pelo menos 4 caracteres e conter apenas letras e números.', '⚠️ The wallet name must be at least 4 characters long and contain only letters and numbers.'),
    ('error_email', '⚠️ Por favor, insira um e-mail válido.', '⚠️ Please enter a valid email address.'),
    ('error_password', '⚠️ A senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula, uma minúscula, um número e um caractere especial.', '⚠️ The password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character.'),
    ('error_logo_url', '⚠️ A URL da imagem é inválida. Use uma imagem menor que 500KB e de fontes confiáveis', '⚠️ The image URL is invalid or too large. Use an image smaller than 500KB and from trusted sources.'),
    ('email_exists', '⚠️ Já existe uma conta para esse email, faça Login', '⚠️ There is an account for this email, please Login instead'),
    ('home_intro', 'O My First Lightning Wallet nasceu para tornar o Bitcoin mais acessível! 🚀\nCom ele, qualquer pessoa pode enviar e receber pagamentos instantâneos.\n\n🔗 Educação e Adoção: Esse projeto é um movimento!\nCriado pela BR⚡LN, ele incentiva e patrocina a adoção do Bitcoin.\n\n🌎 Leve essa inovação para sua comunidade!\nDivulgue o projeto e ajude mais pessoas a darem seu primeiro passo no Bitcoin.\n\n🏢 Quer integrar essa tecnologia no seu negócio ou comunidade?\nAssocie-se à BR⚡LN e traga essa inovação agora!\n<a href="https://br-ln.com" target="_blank">Saiba mais</a> 🚀',
'The My First Lightning Wallet was created to make Bitcoin more accessible! 🚀\nWith it, anyone can send and receive instant payments easily.\n\n🔗 Education and Adoption: This project is a movement!\nDeveloped by BR⚡LN, it promotes and sponsors Bitcoin adoption.\n\n🌎 Bring this innovation to your community!\nSpread the project and help more people take their first step into Bitcoin.\n\n🏢 Want to integrate this technology into your business or community?\nJoin BR⚡LN and bring this innovation today!\n<a href="https://br-ln.com" target="_blank">Learn more</a> 🚀'),
    ('home_intro_title', '🔥 A Revolução do Bitcoin Lightning Começa Aqui!', '🔥 The Bitcoin Lightning Revolution Starts Here!'),
    ('terms_conditions', 'Ao se registrar, você concorda automaticamente com os Termos e Condições.', 'By registering, you automatically agree to the Terms and Conditions.'),
    ('terms_link', 'Termos e Condições', 'Terms and Conditions'),
    ('terms_title', 'Termos e Condições', 'Terms and Conditions'),
    ('terms_intro', 'Ao utilizar nossos serviços, você concorda com os seguintes termos.', 'By using our services, you agree to the following terms.'),
    ('balance_limit', 'Limite de Saldo', 'Balance Limit'),
    ('balance_text', 'Cada carteira possui um limite máximo de saldo de 500.000 satoshis. Valores acima desse limite podem ser recusados pelo sistema.', 'Each wallet has a maximum balance limit of 500,000 satoshis. Any amount exceeding this limit may be rejected by the system.'),
    ('transaction_fees', 'Taxas de Transação', 'Transaction Fees'),
    ('fees_text', 'É cobrada uma taxa de 0,1% sobre retiradas, além das taxas usuais da Rede Lightning.', 'A fee of 0.1% is charged on withdrawals, in addition to the usual Lightning Network fees.'),
    ('liability', 'Responsabilidade Limitada', 'Limited Liability'),
    ('liability_text', "O serviço é oferecido 'como está', sem garantias. Não somos responsáveis por perdas devido a falhas técnicas, comprometimento de credenciais ou ataques à rede.", "The service is provided 'as is', without guarantees. We are not responsible for losses due to technical failures, compromised credentials, or network attacks."),
    ('2fa_disclaimer', 'Autenticação de Dois Fatores (2FA)', 'Two-Factor Authentication (2FA)'),
    ('2fa_disclaimer_text', "Para garantir a segurança de sua conta, a autenticação de dois fatores (2FA) é obrigatória e não pode ser desativada ou alterada após a ativação. Por questões de segurança, não armazenamos nem fornecemos a chave secreta de 2FA após a configuração inicial. É responsabilidade do usuário manter um backup seguro do seu dispositivo autenticador. Caso perca o acesso ao seu dispositivo, não será possível recuperar o 2FA e sua conta poderá se tornar inacessível.", "To ensure the security of your account, two-factor authentication (2FA) is mandatory and cannot be disabled or changed once activated. For security reasons, we do not store or provide the 2FA secret key after the initial setup. It is the user's responsibility to keep a secure backup of their authenticator device. If you lose access to your device, it will not be possible to recover 2FA, and your account may become inaccessible." ),
    ('terms_changes', 'Alterações nos Termos', 'Changes to Terms'),
    ('changes_text', 'Nos reservamos o direito de modificar estes termos a qualquer momento, notificando os usuários previamente.', 'We reserve the right to modify these terms at any time, notifying users in advance.'),
    ('contact', 'Contato', 'Contact'),
    ('contact_text', 'Em caso de dúvidas ou suporte, entre em contato pelo nosso canal oficial.', 'If you have any questions or need support, please contact us through our official channel.'),
    ('enable', '✅ Ativar', '✅ Enable'),
    ('satsback', '🎁 Satsback', '🎁 Satsback'),
    ('satsback_history', '📜 Histórico de Satsback', '📜 Satsback History'),
    ('claim_satsback', '💰 Resgatar Satsback', '💰 Claim Satsback'),
    ('satsback_success', '✅ Satsback resgatado com sucesso!', '✅ Satsback successfully claimed!'),
    ('satsback_insufficient', '⚠️ Saldo insuficiente para resgate.', '⚠️ Insufficient balance for claiming.'),
    ('satsback_transactions', '🔄 Transações elegíveis para Satsback', '🔄 Eligible transactions for Satsback'),
    ('satsback_tooltip', 
    '🛈 <strong>Funcionamento:</strong><br><br>✅ São elegíveis ao SatsBack pagamentos iguais ou acima de 1000 satoshis.<br><br>📊 A cada pagamento elegível, o sistema calcula o % de sats back e disponibiliza no histórico com um código de cor azul.<br><br>💰 <strong>3 SATs</strong> | 🏆 <strong>14 SATs</strong> - Representam o total resgatável e o total já resgatado, respectivamente.<br><br>🔓 Você precisa acumular <strong>10 ou mais satoshis</strong> para ter o resgate habilitado.<br><br>✅ Após o resgate, as transações mudam para o código de cor <strong>verde</strong>, indicando que já foram resgatadas.','🛈 <strong>How it works:</strong><br><br>✅ Eligible payments for SatsBack must be equal to or greater than 1000 satoshis.<br><br>📊 For each eligible payment, the system calculates the % of sats back and displays it in history with a blue status.<br><br>💰 <strong>3 SATs</strong> | 🏆 <strong>14 SATs</strong> - Represent the total claimable and total already claimed, respectively.<br><br>🔓 You need to accumulate <strong>10 or more satoshis</strong> to enable withdrawal.<br><br>✅ After claiming, transactions turn <strong>green</strong> to indicate they have been redeemed.')
]

        
        cursor.executemany("INSERT OR IGNORE INTO translations (key, pt, en) VALUES (?, ?, ?)", translations)
        
        conn.commit()
        conn.close()
        logging.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao inicializar o banco de dados: {e}")

def get_translation(lang):
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key, {} FROM translations".format(lang))
    translations = dict(cursor.fetchall())
    conn.close()
    return translations

def register_satsback_transaction(wallet_id, transaction_id, amount_sats):
    elegible_tx = 1000
    if amount_sats < elegible_tx:
        logging.info(f"Transação {transaction_id} ignorada para Satsback. Valor abaixo do limite: {elegible_tx} SATs.")
        return  # Apenas transações ≥ 1000 SATs

    satsback_amount = int(amount_sats * 0.0005 * 1000)  # convertendo para milisats
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logging.info(f"Registrando SATSBACK para {wallet_id} - Transação: {transaction_id} - Valor: {amount_sats} SATs - Satsback: {satsback_amount} mSATs")

        # Registrar transação
        cursor.execute('''
        INSERT INTO satsback_transactions (wallet_id, transaction_id, amount_sats, satsback_amount, timestamp, claimed)
        VALUES (?, ?, ?, ?, datetime('now'), 0)
        ''', (wallet_id, transaction_id, amount_sats, satsback_amount))

        # Atualizar saldo acumulado do usuário
        cursor.execute('''
        INSERT INTO satsback_users (wallet_id, total_satsback)
        VALUES (?, ?)
        ON CONFLICT(wallet_id) DO UPDATE SET total_satsback = total_satsback + excluded.total_satsback
        ''', (wallet_id, satsback_amount))

        conn.commit()
        conn.close()

        logging.info(f"SATSBACK registrado com sucesso para {wallet_id} - {satsback_amount} mSATs.")
    except Exception as e:
        logging.error(f"Erro ao registrar SATSBACK: {e}")


