# API REST MECiP

Base URL:

`/api/v1/`

Autenticacao:

`POST /api/v1/auth/login/`

Payload:

```json
{
  "username": "usuario",
  "password": "senha"
}
```

Resposta:

```json
{
  "token": "token_de_acesso"
}
```

Use nas proximas requisicoes:

`Authorization: Token token_de_acesso`

Endpoints:

- `GET /api/v1/cursos/`
- `GET /api/v1/cursos/{id}/`
- `POST /api/v1/cursos/`
- `PUT/PATCH /api/v1/cursos/{id}/`
- `GET /api/v1/campus/`
- `GET /api/v1/campus/{id}/`
- `POST /api/v1/campus/`
- `PUT/PATCH /api/v1/campus/{id}/`
- `GET /api/v1/relatorios/`
- `GET /api/v1/relatorios/{id}/`
- `POST /api/v1/relatorios/`
- `PUT/PATCH /api/v1/relatorios/{id}/`
- `GET /api/v1/questionarios/`
- `GET /api/v1/questionarios/{id}/`
- `POST /api/v1/questionarios/`
- `PUT/PATCH /api/v1/questionarios/{id}/`
- `POST /api/v1/questionarios/importar/`
- `POST /api/v1/questionarios/{id}/responder/`

Payload para importar questionario, secao, questao e alternativas:

```json
{
  "questionario": "Instrumento de Avaliacao de cursos de graduacao Presencial e a distancia",
  "dimensao": "DIMENSAO 1 - Organizacao Didatico-Pedagogica",
  "indicador": "Indicador 1.1",
  "questao": "politicas institucionais no ambito do curso",
  "tipo": "Multipla escolha",
  "obrigatoria": "Sim",
  "condicao_especial": null,
  "conceitos": [
    {
      "conceito": "1",
      "criterio_de_aceite": "Criterio de aceitacao"
    }
  ]
}
```

Payload para responder:

```json
{
  "report": 1,
  "question": 1,
  "answer": "Resposta textual",
  "free_text": "Observacao complementar"
}
```

Permissoes:

- Equipe: pode autenticar, listar/visualizar registros permitidos e responder questionarios atribuidos por relatorio/equipe.
- Coordenador: pode listar, criar e atualizar Curso, Campus, Relatorio e Questionario.
- SuperAdmin: possui permissoes de Coordenador e permissoes administrativas existentes no Django.

Listagens usam paginacao padrao com `PAGE_SIZE = 10`.
