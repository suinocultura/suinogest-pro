# SuinoGest Pro

Aplicativo web para gestão de suinocultura com:

- Cadastro de suínos
- Controle sanitário (vacinas/tratamentos)
- Lançamento de ração
- Registro de vendas
- Dashboard financeiro e operacional

## Rodar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Acesse: `http://localhost:5000`

## Deploy estável (Render)

Este repositório já inclui `render.yaml` com configuração pronta para deploy estável.

### 1) Criar o serviço
1. Acesse [https://render.com](https://render.com).
2. Clique em **New +** → **Blueprint**.
3. Selecione este repositório `suinocultura/suinogest-pro`.
4. Confirme o deploy.

### 2) Resultado
- O Render vai publicar uma URL estável no formato:
  `https://suinogest-pro.onrender.com`
- O banco SQLite ficará persistido em disco (`/var/data/suinogest.db`).

## Link público temporário (alternativo, sem password)

Para teste rápido no celular, sem deploy:

```bash
./scripts/public_link.sh
```

Esse script usa **localhost.run** e mostra uma URL no formato:
`https://suinogest-XXXXXX.localhost.run`

Para encerrar depois:

```bash
./scripts/stop_public_link.sh
```
