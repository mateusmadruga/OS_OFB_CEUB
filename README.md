# OS/OFB Lab

Aplicação didática completa para demonstrar arquitetura em camadas, autenticação, autorização por papéis, CRUD, persistência SQLite, workflow OS/OFB, trilha de auditoria, pesquisa e relatórios.

## Execução no Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Acesse `http://127.0.0.1:5000`.

## Execução no Linux/WSL2

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Ver o banco com o DB Browser for SQLite

Baixe em https://sqlitebrowser.org/dl/ , abra `os_ofb.db`, aba *Browse Data*, tabela `user`.

## Roteiro da demonstração

1. Entre como `gestor`, cadastre um contrato e emita uma OS.
2. Entre como `contratada`, registre a entrega.
3. Entre como `fiscaltec`, faça o recebimento provisório e avalie a qualidade.
4. Use `fiscaladm` para aderência, regularidades e liquidação.
5. Simule não conformidade e o ciclo de correção.
6. Abra Relatórios e exporte CSV.
7. Entre como `admin` para inspecionar a trilha de auditoria.

## Segurança demonstrada

- Senhas com hash Werkzeug, sessões HttpOnly/SameSite, CSRF em formulários, autorização RBAC no servidor, limite simples de tentativas de login, validação de entrada, ORM contra injeção SQL e cabeçalhos CSP/X-Frame-Options.
- Em produção: defina `SECRET_KEY`, TLS, `COOKIE_SECURE=1`, banco gerenciado, logs centralizados, cofre de segredos, backup e monitoramento.

Assinatura acadêmica: CEUB · Professor Uender Amaral
