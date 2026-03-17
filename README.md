# SuinoGest Pro

Aplicativo web completo para gestão de suinocultura com:

- Cadastro de suínos
- Controle sanitário (vacinas/tratamentos)
- Lançamento de ração
- Registro de vendas
- Dashboard com visão financeira e operacional

## Como executar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Acesse: `http://localhost:5000`

## Gerar link público temporário (para testar no celular)

Este comando sobe o app e cria um link público temporário usando LocalTunnel:

```bash
./scripts/public_link.sh
```

Quando aparecer `your url is: https://...loca.lt`, abra esse link no celular.

> Observação: o link funciona enquanto o comando estiver em execução no terminal.
