document.addEventListener("DOMContentLoaded", () => {
    // Aplica o tema salvo no localStorage
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const applyTheme = () => {
            const theme = localStorage.getItem('theme') || 'light';
            document.documentElement.classList.toggle('dark-theme', theme === 'dark');
        };
        applyTheme();
        themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }

    // Alteração de idioma mantendo o tema atual
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', function () {
            const selectedLang = this.value;
            window.location.href = `/set_language/${selectedLang}`;
        });
    }

    // Modal de Pagamento
    const btnPagar = document.getElementById('btn-pagar');
    const modalPagamento = document.getElementById('modal-pagamento');
    const closeModalBtn = document.getElementById('close-modal');
    const decodeInvoiceBtn = document.getElementById('decode-invoice-btn');
    const confirmPaymentBtn = document.getElementById('confirm-payment-btn');
    const invoiceDetails = document.getElementById('invoice-details');
    const invoiceInput = document.getElementById('invoice-input');
    const scanQrButton = document.getElementById("scanQrButton");
    const readerDiv = document.getElementById("reader");

    if (btnPagar && modalPagamento) {
        btnPagar.addEventListener('click', () => modalPagamento.classList.remove('hidden'));
    }

    if (closeModalBtn && modalPagamento && invoiceInput) {
        closeModalBtn.addEventListener('click', () => {
            modalPagamento.classList.add('hidden');
            if (invoiceDetails) invoiceDetails.classList.add('hidden');
            invoiceInput.value = '';
        });
    }
    if (scanQrButton && readerDiv) {
        scanQrButton.addEventListener("click", function () {
            readerDiv.style.display = "block"; // Exibe o scanner
    
            const html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start(
                { facingMode: "environment" }, // Usa a câmera traseira
                {
                    fps: 10,
                    qrbox: function(viewfinderWidth, viewfinderHeight) {
                        const isMobile = window.innerWidth <= 768; // Define se é um dispositivo móvel
                        if (isMobile) {
                            // Para dispositivos móveis, aumenta a altura do delimitador
                            const width = viewfinderWidth * 0.8; // 80% da largura disponível
                            const height = viewfinderHeight * 0.9; // 90% da altura disponível
                            return { width: width, height: height };
                        } else {
                            // Para desktops, aumenta a largura do delimitador
                            const size = Math.min(viewfinderWidth * 1, viewfinderHeight * 0.9); // 100% da largura ou 90% da altura
                            return { width: size, height: size }; // Mantém o delimitador como um quadrado
                        }
                    }
                },
                qrCodeMessage => {
                    console.log("QR Code detectado:", qrCodeMessage);
    
                    // Remove o prefixo "lightning:" (case-insensitive), remove espaços e converte para minúsculas
                    const cleanedInvoice = qrCodeMessage.replace(/^lightning:/i, '').trim().toLowerCase();
    
                    // Insere o código escaneado no campo de pagamento
                    invoiceInput.value = cleanedInvoice;
    
                    // Para o scanner e esconde a área do QR Code
                    html5QrCode.stop().then(() => {
                        readerDiv.style.display = "none";
                    }).catch(err => {
                        console.error("Erro ao parar o scanner:", err);
                    });
                },
                errorMessage => {
                    console.warn("Erro no scan:", errorMessage);
                }
            ).catch(err => {
                console.error("Erro ao iniciar o scanner:", err);
            });
        });
    }
    if (decodeInvoiceBtn && invoiceInput) {
        decodeInvoiceBtn.addEventListener('click', () => {
            // Converte para minúsculas e remove "lightning:" se existir
            let invoice = invoiceInput.value.trim().toLowerCase();
            invoice = invoice.replace(/^lightning:/, '');
            fetch('/decode_invoice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invoice: invoice })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    document.getElementById('invoice-amount').innerText = data.amount_sats;
                    document.getElementById('invoice-desc').innerText = data.description;
                    document.getElementById('invoice-expiry').innerText = data.expiry;
                    if (invoiceDetails) invoiceDetails.classList.remove('hidden');
                }
            });
        });
    }

    if (confirmPaymentBtn && invoiceInput) {
        confirmPaymentBtn.addEventListener('click', () => {
            setLoadingCursor(true); // Ativa o cursor de espera
    
            // Força o navegador a renderizar o cursor antes de iniciar o fetch
            setTimeout(() => {
                let invoice = invoiceInput.value.trim().toLowerCase().replace(/^lightning:/, '');
                fetch('/pay_invoice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ invoice: invoice })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // Exibe a mensagem de sucesso
                        const flashMessagesContainer = document.getElementById('flash-messages-modal');
                        flashMessagesContainer.innerHTML = '';
                        const messageDiv = document.createElement('div');
                        messageDiv.classList.add('alert', 'alert-success');
                        const successMessage = document.getElementById('payment-success-msg').textContent;
                        messageDiv.textContent = successMessage;
                        flashMessagesContainer.appendChild(messageDiv);
    
                        atualizarSaldo();
                        // Após 3 segundos, redireciona para o dashboard
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 100);
                    } else {
                        // Exibe a mensagem de erro no modal
                        const flashMessagesContainer = document.getElementById('flash-messages-modal');
                        flashMessagesContainer.innerHTML = '';
                        const messageDiv = document.createElement('div');
                        messageDiv.classList.add('alert', 'alert-danger');
                        const errorMessage = document.getElementById('payment-error-msg').textContent;
                        messageDiv.textContent = `${errorMessage} ${data.error}`;
                        flashMessagesContainer.appendChild(messageDiv);
    
                        // Fecha o modal e redireciona para o dashboard
                        modalPagamento.classList.add('hidden');
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 100);
                    }
                })
                .catch(error => {
                    console.error("Erro no pagamento:", error);
                    // Exibe mensagem de erro genérica
                    const flashMessagesContainer = document.getElementById('flash-messages-modal');
                    flashMessagesContainer.innerHTML = '';
                    const messageDiv = document.createElement('div');
                    messageDiv.classList.add('alert', 'alert-danger');
                    messageDiv.textContent = "Erro inesperado ao processar o pagamento.";
                    flashMessagesContainer.appendChild(messageDiv);
    
                    // Fecha o modal e redireciona para o dashboard
                    modalPagamento.classList.add('hidden');
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 3000);
                })
                .finally(() => setLoadingCursor(false)); // Retorna o cursor ao normal
            }, 0); // Força o navegador a renderizar o cursor antes do fetch
        });
    }
    
    

    // Modal de Recebimento
const btnReceber = document.getElementById('btn-receber');
const modalReceber = document.getElementById('modal-receber');
const closeModalReceber = document.getElementById('close-modal-receber');
const generateInvoiceBtn = document.getElementById('generate-invoice-btn');
const invoiceResult = document.getElementById('invoice-result');
const paymentRequestText = document.getElementById('payment-request-text');
const copyInvoiceBtn = document.getElementById('copy-invoice-btn');
const qrcodeDiv = document.getElementById('qrcode');

let saldoAtual = 0;
let checkBalanceInterval;

if (btnReceber && modalReceber) {
    btnReceber.addEventListener('click', () => {
        modalReceber.classList.remove('hidden');
        invoiceResult.classList.add('hidden');
        document.getElementById('receive-amount').value = '';
        document.getElementById('receive-description').value = '';
        qrcodeDiv.innerHTML = '';
        
        // Obtém o saldo antes de gerar uma invoice
        obterSaldoAtual();
    });
}

if (closeModalReceber && modalReceber) {
    closeModalReceber.addEventListener('click', () => {
        verificarRecebimento(); // Atualiza o saldo imediatamente antes de fechar
        modalReceber.classList.add('hidden');
        clearInterval(checkBalanceInterval); // Para a verificação se o modal for fechado
    });
}


if (generateInvoiceBtn) {
    generateInvoiceBtn.addEventListener('click', () => {
        const amount = parseInt(document.getElementById('receive-amount').value);
        const description = document.getElementById('receive-description').value;

        if (isNaN(amount) || amount < 1) {
            alert("Valor Mínimo de 1 Sat / Minimum Value 1 sat!");
            return;
        }

        fetch('/generate_invoice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, description })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                paymentRequestText.textContent = data.payment_request;
                invoiceResult.classList.remove('hidden');
                qrcodeDiv.innerHTML = '';
                new QRCode(qrcodeDiv, { text: data.payment_request, width: 300, height: 300 });

                // Inicia a verificação do saldo a cada 1 segundos
                checkBalanceInterval = setInterval(verificarRecebimento, 1000);
            } else {
                alert(data.error);
            }
        });
    });
}

if (copyInvoiceBtn) {
    copyInvoiceBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(paymentRequestText.textContent).then(() => {
            alert('Invoice copiada!');
        });
    });
}

// 🔹 Função para obter o saldo antes de gerar a invoice
function obterSaldoAtual() {
    fetch('/api/get_balance')
        .then(res => res.json())
        .then(data => {
            saldoAtual = data.balance;
        })
        .catch(err => console.error("Erro ao buscar saldo inicial:", err));
}

// 🔹 Função para verificar se o saldo aumentou (indicando recebimento)
function verificarRecebimento() {
    fetch('/api/get_balance')
        .then(res => res.json())
        .then(data => {
            if (data.balance > saldoAtual) {
                document.getElementById('balance-amount').textContent = data.balance;
                saldoAtual = data.balance;
                clearInterval(checkBalanceInterval); // Para a verificação após atualizar o saldo
            }
        })
        .catch(err => console.error("Erro ao verificar recebimento:", err));
}


    // Modal de Extrato
    const btnExtrato = document.getElementById('btn-extrato');
    const modalExtrato = document.getElementById('modal-extrato');
    const closeModalExtrato = document.getElementById('close-modal-extrato');
    const extratoList = document.getElementById('extrato-list');

    if (btnExtrato && modalExtrato) {
        btnExtrato.addEventListener('click', () => {
            modalExtrato.classList.remove('hidden');
            fetch('/get_statement')
            .then(res => res.json())
            .then(data => {
                extratoList.innerHTML = ''; // Limpa lista anterior
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.classList.add('extrato-item');

                    let emoji = item.status === 'success' 
                                ? (item.amount >= 0 ? '🟢' : '💸') 
                                : '⚠️';

                    let date = new Date(item.time * 1000).toLocaleString();
                    let amount = (item.amount / 1000).toFixed(0);
                    let fee = (item.fee / 1000).toFixed(0);

                    li.innerHTML = `
                        <span class="extrato-status">${emoji}</span>
                        <div class="extrato-info">
                            <span class="extrato-text">${date}</span>
                            <span>📝 ${item.memo || 'Sem descrição'}</span>
                        </div>
                        <div>
                            <span class="valor">💲 ${amount} SATs</span>
                            <span class="taxa">💰 ${fee} SATs</span>
                        </div>
                    `;
                    extratoList.appendChild(li);
                });
            });
        });
    }

    if (closeModalExtrato) {
        closeModalExtrato.addEventListener('click', () => modalExtrato.classList.add('hidden'));
    }

    // Esconde todos os modais ao iniciar a página
    document.querySelectorAll('.modal').forEach(modal => modal.classList.add('hidden'));

    // Fecha modais ao clicar no fundo escuro
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });

    // Botões de fechar modal
    document.querySelectorAll("[id^=close-modal]").forEach(btn => {
        btn.addEventListener("click", function () {
            this.closest('.modal').classList.add('hidden');
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    // Redirecionar para a página de alteração de senha ao clicar no botão
    const changePasswordBtn = document.getElementById("change-password-btn");
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener("click", () => {
            window.location.href = "/change_password";
        });
    }
});
document.addEventListener("DOMContentLoaded", () => {
    const toggleBalance = document.getElementById("toggle-balance");
    const balanceAmount = document.getElementById("balance-amount");
    const balanceConverted = document.getElementById("balance-converted"); // Adicionando a conversão

    if (toggleBalance && balanceAmount && balanceConverted) {
        toggleBalance.addEventListener("click", () => {
            if (balanceAmount.textContent === "---") {
                balanceAmount.textContent = balanceAmount.getAttribute("data-real-balance");
                balanceConverted.style.display = "block"; // Exibe a conversão
                toggleBalance.textContent = "👁️"; // Olho aberto
            } else {
                balanceAmount.setAttribute("data-real-balance", balanceAmount.textContent);
                balanceAmount.textContent = "---";
                balanceConverted.style.display = "none"; // Esconde a conversão
                toggleBalance.textContent = "🙈"; // Olho fechado
            }
        });
    }
});
document.addEventListener("DOMContentLoaded", () => {
    const btnSatsback = document.getElementById("btn-satsback");
    const modalSatsback = document.getElementById("modal-satsback");
    const closeModalSatsback = document.getElementById("close-modal-satsback");
    const satsbackList = document.getElementById("satsback-list");
    const claimButton = document.getElementById("btn-claim-satsback");
    const satsbackTotal = document.getElementById("satsback-total");
    const satsbackClaimed = document.getElementById("satsback-claimed");

    if (btnSatsback && modalSatsback) {
        btnSatsback.addEventListener("click", () => {
            modalSatsback.classList.remove("hidden");

            fetch('/get_satsback')
                .then(res => res.json())
                .then(data => {
                    satsbackList.innerHTML = "";
                    let totalSatsback = parseFloat(data.total_available) / 1000; // 🔹 Converte msats → sats
                    let totalClaimed = parseFloat(data.total_claimed); 

                    // Atualizar saldo total disponível e total já resgatado
                    satsbackTotal.innerHTML = `💰 ${totalSatsback.toFixed(2)} SATs`;
                    satsbackClaimed.innerHTML = `🏆 ${totalClaimed.toFixed(2)} SATs`;

                    data.transactions.forEach(item => {
                        const li = document.createElement("li");
                        li.innerHTML = `
                            📅 ${item.date} | 🔗 ${item.payment_hash} <br>
                            💳 ${item.original_amount} SATs ➡️ 🎁 ${item.satsback_amount} SATs | ${item.status}
                        `;
                        satsbackList.appendChild(li);
                    });

                    // 🚀 Agora garantimos que a lógica funcione corretamente!
                    if (totalSatsback >= 10) {
                        claimButton.style.display = "block";  // Exibe o botão
                    } else {
                        claimButton.style.display = "none";  // Esconde o botão
                    }
                })
                .catch(error => console.error("Erro ao buscar Satsback:", error));
        });
    }

    if (closeModalSatsback) {
        closeModalSatsback.addEventListener("click", () => modalSatsback.classList.add("hidden"));
    }
});


document.addEventListener("DOMContentLoaded", () => {
    const claimButton = document.getElementById("btn-claim-satsback");

    if (claimButton) {
        claimButton.addEventListener("click", () => {
            setLoadingCursor(true);  // Ativa cursor de espera
            fetch('/claim_satsback', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert("✅ Resgate realizado com sucesso!");
                        // 🔄 Atualiza o modal de SatsBack para refletir o novo saldo
                        atualizarSatsBack();

                        // 🔄 Atualiza o saldo da carteira
                        atualizarSaldo();

                        claimButton.style.display = "none"; // Esconde o botão após o resgate
                    } else {
                        alert("❌ Erro ao resgatar: " + data.error);
                    }
                })
                .catch(error => console.error("Erro ao resgatar SATSBACK:", error))
                .finally(() => setLoadingCursor(false));  // Retorna cursor ao normal
        });
    }
});


function setLoadingCursor(loading) {
    document.body.style.cursor = loading ? "wait" : "default";  // Altera para "espera" ou "normal"
}

// Função para atualizar o saldo no frontend
function atualizarSaldo() {
    fetch('/api/get_balance')
        .then(res => res.json())
        .then(data => {
            if (data.balance !== undefined) {
                document.getElementById('balance-amount').textContent = data.balance;
            }
        })
        .catch(err => console.error("Erro ao atualizar saldo:", err));
}
function atualizarSatsBack() {
    fetch('/get_satsback')
        .then(res => res.json())
        .then(data => {
            const satsbackTotal = document.getElementById("satsback-total");
            const satsbackClaimed = document.getElementById("satsback-claimed");
            const satsbackList = document.getElementById("satsback-list");
            const claimButton = document.getElementById("btn-claim-satsback");

            if (satsbackTotal && satsbackClaimed && satsbackList) {
                // Atualiza os valores no modal
                let totalSatsback = parseFloat(data.total_available) / 1000; // Converte msats → sats
                let totalClaimed = parseFloat(data.total_claimed);

                satsbackTotal.innerHTML = `💰 ${totalSatsback.toFixed(2)} SATs`;
                satsbackClaimed.innerHTML = `🏆 ${totalClaimed.toFixed(2)} SATs`;

                // Limpa e preenche a lista de transações de SatsBack
                satsbackList.innerHTML = "";
                data.transactions.forEach(item => {
                    const li = document.createElement("li");
                    li.innerHTML = `
                        📅 ${item.date} | 🔗 ${item.payment_hash} <br>
                        💳 ${item.original_amount} SATs ➡️ 🎁 ${item.satsback_amount} SATs | ${item.status}
                    `;
                    satsbackList.appendChild(li);
                });

                // 🚀 Esconde o botão de resgate se o saldo disponível for menor que 10 SATs
                if (totalSatsback >= 10) {
                    claimButton.style.display = "block";  
                } else {
                    claimButton.style.display = "none";  
                }
            }
        })
        .catch(error => console.error("Erro ao atualizar SatsBack:", error));
}

document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll(".flash-messages .alert");

    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.transition = "opacity 0.5s";
                message.style.opacity = "0"; // Faz a mensagem desaparecer suavemente

                setTimeout(() => {
                    message.style.display = "none"; // Esconde completamente após a animação
                }, 500);
            });
        }, 4000); // Tempo até sumir (4 segundos)
    }
});
document.addEventListener("DOMContentLoaded", () => {
    async function fetchBitcoinPrice() {
        try {
            const response = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,brl");
            const data = await response.json();
            return { usd: data.bitcoin.usd, brl: data.bitcoin.brl };
        } catch (error) {
            console.error("Erro ao buscar taxa de conversão:", error);
            return null;
        }
    }

    async function updateConvertedBalance() {
        const balanceElement = document.getElementById("balance-amount");
        const convertedElement = document.getElementById("balance-converted");

        if (!balanceElement || !convertedElement) return;

        const balanceInSats = parseInt(balanceElement.textContent.replace(/[^0-9]/g, ""), 10);
        if (isNaN(balanceInSats)) return;

        const prices = await fetchBitcoinPrice();
        if (!prices) return;

        const lang = document.documentElement.lang || "pt"; // Detecta o idioma da página
        const btcPrice = lang === "pt" ? prices.brl : prices.usd;
        const currencySymbol = lang === "pt" ? "R$" : "$";

        const balanceInBtc = balanceInSats / 100_000_000; // Converte SATs para BTC
        const balanceInFiat = balanceInBtc * btcPrice; // Converte BTC para moeda local

        convertedElement.textContent = `${currencySymbol} ${balanceInFiat.toFixed(2)}`; // Exibe o valor
    }

    updateConvertedBalance();
    setInterval(updateConvertedBalance, 30000); // Atualiza a cada 30 segundos
});
