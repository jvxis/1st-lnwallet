from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ✅ Criando a instância do limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"  # Pode usar Redis em produção
)
