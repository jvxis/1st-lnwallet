# ⚡ My First Lightning Wallet

My First Lightning Wallet é uma aplicação Flask que permite criar e gerenciar carteiras Lightning Network, realizar pagamentos, receber fundos e muito mais. Este projeto foi desenvolvido para facilitar a adoção do Bitcoin Lightning Network.

![image](https://github.com/user-attachments/assets/dc6c05eb-8cf1-4875-bbb8-9cbaf1108472)

## ✨ Funcionalidades

- Registro e login de usuários com autenticação 2FA.
- Criação e gerenciamento de carteiras Lightning Network.
- Pagamento e recebimento de invoices Lightning.
- Sistema de Satsback para recompensas em transações.
- Suporte a temas claro e escuro.
- Interface multilíngue (Português e Inglês).

## 🏗️ Estrutura do Projeto

```plaintext
.
├── app.py                 # Arquivo principal da aplicação Flask
├── auth.py                # Gerenciamento de autenticação e registro
├── config_example.py      # Exemplo de configuração
├── database.py            # Configuração e manipulação do banco de dados
├── limiter.py             # Configuração de limites de requisição
├── lnbits.py              # Integração com a API do LNbits
├── requirements.txt       # Dependências do projeto
├── static/                # Arquivos estáticos (CSS, JS, imagens)
├── templates/             # Templates HTML
└── logs/                  # Logs da aplicação
```

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter os seguintes itens instalados:

- Python 3.8 ou superior
- Virtualenv (opcional, mas recomendado)
- SQLite (para o banco de dados)
- Um servidor LNbits configurado (ou acesso a um servidor existente)
- Habilitar a extensão PAYLINKS no seu LNBITS

## ⚙️ Configuração do Projeto

Siga os passos abaixo para configurar e executar o projeto:

### 🔄 1. Clone o Repositório

```bash
git clone https://github.com/jvxis/1st-lnwallet.git
cd 1st-lnwallet
```

### 🛡️ 2. Crie e Ative um Ambiente Virtual

Recomendamos o uso de um ambiente virtual para isolar as dependências do projeto.

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 📦 3. Instale as Dependências

Instale as bibliotecas necessárias listadas no arquivo `requirements.txt`.

```bash
pip3 install -r requirements.txt
```

### 🔧 4. Configure as Variáveis de Ambiente

Renomeie o arquivo `config_example.py` para `config.py` e preencha os valores necessários:

```bash
mv config_example.py config.py
```

Edite o arquivo `config.py` e substitua os valores de exemplo pelos valores reais:

- `SECRET_KEY`: Uma chave secreta para a aplicação Flask.
- `LN_BITS_API_URL`: URL da API do LNbits.
- `LN_BITS_BASE_URL`: URL base do LNbits.
- `LN_ADDRESS_DOMAIN`: Domínio usado para endereços Lightning.
- `LN_BITS_API_KEY`: Chave de API do LNbits.
- `RECAPTCHA_SITE_KEY` e `RECAPTCHA_SECRET_KEY`: Chaves do Google reCAPTCHA.
- `SATSBACK_WALLET_ADMIN_KEY`: Chave de administrador para o sistema de Satsback.

### 🚀 5. Execute o Servidor

Inicie o servidor Flask:

```bash
python3 app.py
```

O servidor estará disponível em `http://127.0.0.1:37421` por padrão

### 🌐 7. Acesse a Aplicação

Abra o navegador e acesse `http://127.0.0.1:37421` para usar a aplicação, isso para a mesma máquina. Caso o navegador esteja em máquina diferente da aplicação, usar o IP da máquina que está a aplicação.

## 🛡️🚀 Implementação para PRODUÇÃO

Se você deseja fazer uma implementação para produção siga os passos abaixo:

### 📝 Passo 1 - Altere o host na última linha do script `app.py` para 127.0.0.1, isso irá permitir somente acesso local.

Altere:

```bash
app.run(debug=Config.DEBUG, port=Config.PORT, host='0.0.0.0')
```

Para:
```bash
app.run(debug=Config.DEBUG, port=Config.PORT, host='127.0.0.1')
```

### 🌐 Passo 2 - Implemente um proxy reverso do Nginx ou usando Cloudflare para a porta da aplicação

### 🧭 Passo 3 - Aponte o Domínio para a aplicação

### ⚙️ Passo 4 - Mude a variável de ambiente para Produção. Na linha de comando execute:
```bash
export FLASK_ENV=production
```
### 🔒 Passo 5 - No caso de usar o Nginx, utilize o `CERTBOT` para criar um certificado e acesso ao site via HTTPS.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

Melhorias Sugeridas:
- Pagamento via Lightning Address ⚡
- Chave Backup ao cadastrar o 2FA 🔑 e permitir a alteração

## 📜 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).


