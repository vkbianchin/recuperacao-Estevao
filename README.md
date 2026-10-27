# Almoxarifado simples — FastAPI + JWT

API REST em Python, sem Flask e sem interface gráfica. Por padrão usa SQLite para facilitar a execução local.

## 1. Preparar ambiente (Windows / PowerShell)

```powershell
cd caminho\para\almoxarifado_fastapi
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000/docs` para testar a API.

## 2. Administrador inicial

Na primeira inicialização, a API cria:

- E-mail: `admin@almox.local`
- Senha: `Admin123!`
- Papel: `administrador`

**Troque a senha e a chave secreta antes de usar fora do ambiente local.** A senha inicial serve apenas para a atividade.

## 3. Fluxo de teste

1. Em `POST /auth/login`, envie `{"email":"admin@almox.local","senha":"Admin123!"}`.
2. Copie `access_token`.
3. Clique em **Authorize** no `/docs` e informe o token (ou `Bearer <token>`, conforme a interface).
4. Como administrador, use `POST /usuarios` para criar usuários com papel `comum` e `gestor`.
5. Cadastre equipamento com `POST /equipamentos` usando o administrador.
6. Faça login como usuário comum e solicite empréstimo em `POST /emprestimos`, enviando `{"equipamento_id":1}`.
7. Faça login como gestor e use `POST /emprestimos/{id}/aprovar`.
8. Depois, o gestor registra a devolução com `POST /emprestimos/{id}/devolver`.

O login de outro usuário substitui o token atual no botão Authorize.

## 4. Permissões

| Operação | Comum | Gestor | Administrador |
|---|---:|---:|---:|
| Login e consultar próprio usuário | Sim | Sim | Sim |
| Listar equipamentos | Sim | Sim | Sim |
| Solicitar empréstimo | Sim | Não | Não |
| Aprovar empréstimo | Não | Sim | Não |
| Registrar devolução | Não | Sim | Não |
| Cadastrar usuário | Não | Não | Sim |
| Cadastrar equipamento | Não | Não | Sim |

Rotas protegidas retornam `401 Unauthorized` quando o token falta/é inválido e `403 Forbidden` quando o papel não tem permissão. Erros de recurso retornam, por exemplo, `404 Not Found`, `409 Conflict` e `422 Unprocessable Entity`.

## 5. Rotas principais

- `POST /auth/login`
- `GET /auth/me`
- `POST /usuarios` — administrador
- `GET /equipamentos` — usuário autenticado
- `POST /equipamentos` — administrador
- `POST /emprestimos` — usuário comum
- `GET /emprestimos` — autenticados; usuário comum vê apenas os próprios
- `POST /emprestimos/{emprestimo_id}/aprovar` — gestor
- `POST /emprestimos/{emprestimo_id}/devolver` — gestor

## Observações

- O token JWT contém o identificador do usuário e o papel; a API consulta o usuário no banco para autenticar a identidade.
- A proteção por papel é aplicada nas rotas do servidor, não apenas na documentação.
- O banco `almoxarifado.db` é criado automaticamente na pasta em que o comando `uvicorn` é executado.
- Para usar MySQL/MariaDB, configure `DATABASE_URL` com uma URL SQLAlchemy e instale o driver correspondente.
