# Mecip_IFSP

Este repositório contém o projeto Desenvolvido em Python utilizando Django. 

Esse projeto de estudo é um processo de automoção de relatórios internos de uma instituição para avaliação de curso do MEC. 

## Requisitos

- Python 3.8+ (use virtualenv ou venv)
- pip

## Setup local (Windows)

1. Crie e ative um ambiente virtual:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
pip install -r requirements.txt
```

3. Crie um arquivo `.env` a partir de `.env.example`:

```powershell
copy .env.example .env
```

4. Gere uma `SECRET_KEY` segura e adicione ao `.env`:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie a saída e substitua o valor em `SECRET_KEY` no arquivo `.env`.

5. Aplique migrations e crie um superusuário (se necessário):

```powershell
python manage.py migrate
python manage.py createsuperuser
```

6. Rode o servidor de desenvolvimento:

```powershell
python manage.py runserver
```

## Arquivos importantes

- `db.sqlite3` — banco de dados local (não comitado).
- `media/` — uploads de arquivos (não comitado).
- `.env` — variáveis de ambiente locais (não comitado).

## Como empurrar para o GitHub

1. Inicialize o repositório (se ainda não):

```powershell
git init
git remote add origin <URL_DO_REPO>
```

2. Se houver erro de históricos não relacionados ao puxar, veja instruções no README ou usar:

```powershell
git pull origin main --allow-unrelated-histories
```

## Arquivo `.env.example`

Criei um exemplo de `.env.example` com variáveis comuns. Ajuste conforme seu ambiente.

---
Última atualização: 2026-02-18