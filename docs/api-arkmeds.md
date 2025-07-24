# Arkmeds API – Documentação REST

Documentação adaptada do SwaggerHub para uso rápido e prático.

> **Original:** [SwaggerHub Arkmeds API v1.0.0](https://app.swaggerhub.com/apis-docs/Arkmeds/Arkmeds-APIs/1.0.0#/)

---

## Autenticação

### Gerar Token de Autenticação

```http
POST /rest-auth/token-auth/
```

**Request Body:**
```json
{
  "username": "usuario",
  "password": "senha"
}
```

**Response:**
```json
{
  "token": "string"
}
```

Utilize o token retornado em todas as requisições autenticadas no header:
```
Authorization: JWT <token>
```

---

## Tipos de Peça

### Listar tipos de peça
```http
GET /api/v2/part_type/
```
**Response:**
```json
{
  "count": 1029,
  "next": "...",
  "previous": null,
  "results": [
    { "id": 1458, "descricao": "Teclado com Mouse" }
  ]
}
```

### Criar tipo de peça
```http
POST /api/v2/part_type/
```
**Request Body:**
```json
{ "descricao": "Regulador de Pressão de Retorno 100 PSI" }
```
**Response:** `201 Created`

### Obter detalhes do tipo de peça
```http
GET /api/v2/part_type/{id}/
```
**Response:**
```json
{ "id": 195, "descricao": "Cabo VGA" }
```

### Atualizar tipo de peça
```http
PUT /api/v2/part_type/{id}/
```
**Request Body:**
```json
{ "descricao": "Cabo HDMI" }
```
**Response:** `200 OK`

---

## Peças

### Listar peças
```http
GET /api/v2/part/
```
**Response (exemplo):**
```json
{
  "id": 203,
  "tipo": 7,
  "categoria": 13,
  "fabricante": "",
  "codigo_fabricante": "",
  "modelo": "",
  "estoque_minimo": 1,
  "quantidade": 8,
  "observacoes": "",
  "itens_peca": [
    {
      "id": 193,
      "peca": 203,
      "quantidade": 8,
      "fornecedor": 46,
      "numero_nota_fiscal": "testenumero",
      "lote_peca": "testelote",
      "valor_aquisicao": "10.00",
      "valor_venda": "20.00"
    }
  ]
}
```

### Criar peça
```http
POST /api/v2/part/
```
**Request Body:**
```json
{
  "tipo": 7,
  "categoria": 13,
  "fabricante": "Fabricante ABC",
  "codigo_fabricante": "ABC123",
  "modelo": "Modelo XYZ",
  "estoque_minimo": 10,
  "observacoes": "Observações sobre a peça"
}
```
**Response:** `201 Created`

### Obter detalhes da peça
```http
GET /api/v2/part/{id}/
```
**Response:**
```json
{
  "id": 195,
  "tipo": 192,
  "categoria": 1,
  "fabricante": "",
  "codigo_fabricante": "",
  "modelo": "",
  "estoque_minimo": 3,
  "quantidade": 19,
  "observacoes": "TESTE TESTE",
  "itens_peca": [
    {
      "id": 189,
      "peca": 195,
      "quantidade": 9,
      "fornecedor": 46,
      "numero_nota_fiscal": "TESTE",
      "lote_peca": "TESTE 1",
      "valor_aquisicao": "10.00",
      "valor_venda": "20.00"
    }
  ]
}
```

### Atualizar peça
```http
PUT /api/v2/part/{id}/
```
**Request Body:**
```json
{
  "tipo": 7,
  "categoria": 15,
  "fabricante": "Fabricante XYZ",
  "codigo_fabricante": "XYZ123",
  "modelo": "Novo Modelo",
  "estoque_minimo": 15,
  "observacoes": "Novas Observações sobre a peça"
}
```
**Response:** `200 OK`

---

## Itens de Peça

### Listar itens de peça
```http
GET /api/v2/part_item/
```
**Response:**
```json
{
  "count": 1115,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "peca": 1,
      "quantidade": 0,
      "fornecedor": 13,
      "numero_nota_fiscal": "1",
      "lote_peca": "",
      "valor_aquisicao": "",
      "valor_venda": ""
    }
  ]
}
```

### Criar item de peça
```http
POST /api/v2/part_item/
```
**Request Body:**
```json
{
  "peca": 0,
  "quantidade": 0,
  "fornecedor": 0,
  "numero_nota_fiscal": "string",
  "lote_peca": "string",
  "valor_aquisicao": 0,
  "valor_venda": 0
}
```
**Response:** `201 Created`

### Obter detalhes do item de peça
```http
GET /api/v2/part_item/{id}/
```
**Response:**
```json
{
  "id": 74,
  "peca": 75,
  "quantidade": 1,
  "fornecedor": 190,
  "numero_nota_fiscal": "",
  "lote_peca": "",
  "valor_aquisicao": "315.00",
  "valor_venda": "315.00"
}
```

### Atualizar item de peça
```http
PUT /api/v2/part_item/{id}/
```
**Request Body:**
```json
{
  "peca": 123,
  "quantidade": 5,
  "fornecedor": 456,
  "numero_nota_fiscal": "1234567890",
  "lote_peca": "Lote123",
  "valor_aquisicao": "150.75",
  "valor_venda": "199.99"
}
```
**Response:** `200 OK`

---

## Campos Gerenciais

### Listar estados de ordem de serviço
```http
GET /api/v3/estado_ordem_servico/
```
**Response:**
```json
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    { "id": 0, "descricao": "string", "pode_visualizar": true }
  ]
}
```

### Listar origens de problema
```http
GET /api/v3/origem_problema/
```
**Response:**
```json
[
  { "id": 1, "descricao": "Origem 1" },
  { "id": 2, "descricao": "Origem 2" },
  { "id": 3, "descricao": "Origem 3" }
]
```

### Listar problemas relatados
```http
GET /api/v3/problema_relatado/?empresa_id={id}&tipo={tipo}
```
**Response:**
```json
[
  { "id": 15, "descricao": "Cheiro de queimado", "tipo": 1 }
]
```

### Listar tipos de serviço
```http
GET /api/v3/tipo_servico/
```
**Response:**
```json
{
  "count": 29,
  "next": null,
  "previous": null,
  "results": [
    { "id": 54, "descricao": "626265 - Manutenção preventiva" }
  ]
}
```

### Listar oficinas
```http
GET /api/v5/oficina/
```
**Response:**
```json
{
  "data": [
    { "id": 2, "descricao": "Engenharia Clínica" }
  ]
}
```

---

## Serviço de Orçamento

### Enviar serviço para orçamento
```http
POST /api/v4/servico_orcamento/
```
**Request Body:**
```json
{
  "tipo_servico_id": 0,
  "precificacao_servico": 0,
  "descricao": "string",
  "referencia_interna": "string",
  "garantia": 0,
  "valor": 0
}
```
**Response:** `201 Created`

---

## Chamado

### Criar chamado
```http
POST /api/v5/chamado/
```
**Request Body:**
```json
{
  "equipamento_id": 0,
  "solicitante": 0,
  "tipo_servico": 0,
  "problema": 0,
  "observacoes": "string",
  "id_tipo_ordem_servico": 0,
  "localizacao": 0,
  "data_criacao": 0
}
```
**Response:**
```json
{ "chamado_id": 0, "ordem_servico_id": 0 }
```

### Listar chamados
```http
GET /api/v5/chamado/?arquivadas=true
```
**Response:** `200 OK`

---

## Empresas

### Listar empresas
```http
GET /api/v5/company/
```
**Response:**
```json
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "tipo": 0,
      "nome": "string"
    }
  ]
}
```

### Obter detalhes da empresa
```http
GET /api/v5/company/{id}
```
**Response:** (mesma estrutura acima)

### Criar empresa
```http
POST /api/v2/company/
```
**Request Body:**
```json
{
  "tipo": 0,
  "nome": "string",
  "nome_fantasia": "string",
  "superior": 0,
  "cnpj": "string",
  "observacoes": "string",
  "contato": "string",
  "email": "string",
  "telefone": "string",
  "ramal": "string",
  "telefone1": "string",
  "ramal1": "string",
  "fax": "string",
  "cep": "string",
  "rua": "string",
  "numero": 0,
  "complemento": "string",
  "bairro": "string",
  "cidade": "string",
  "estado": "string"
}
```
**Response:** `201 Created`

---

## Equipamentos

### Listar equipamentos por empresa
```http
GET /api/v5/company/equipaments/
```
**Response:**
```json
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "nome": "string",
      "equipamentos": [
        { "id": 0, "nome": "string", "tipo": "string" }
      ]
    }
  ]
}
```

### Obter detalhes do equipamento
```http
GET /api/v5/equipament/{id}
```
**Response:**
```json
{
  "id": 207,
  "proprietario": 113,
  "fabricante": "",
  "modelo": "",
  "patrimonio": "",
  "numero_serie": "202677",
  "identificacao": "",
  "tipo": 149,
  "qr_code": -1,
  "tipo_contrato": null
}
```

---

## Ordem de Serviço

### Listar OS do usuário conectado
```http
GET /api/v5/ordem_servico/?page=1&page_size=10
```
**Response:**
```json
{
  "count": 1000,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 31656,
      "tipo_ordem_servico": 1,
      "numero": 1234,
      "estado": { "id": 1, "descricao": "Aberta", "pode_visualizar": true },
      "is_active": true,
      "equipamento": {
        "id": 54050,
        "fabricante": "FABRICANTE",
        "modelo": "",
        "patrimonio": "ABC123",
        "numero_serie": "ABC123",
        "identificacao": "ABC123"
      }
    }
  ]
}
```

### Criar ordem de serviço
```http
POST /api/v5/ordem_servico/
```
**Request Body:**
```json
{
  "equipamento": 0,
  "solicitante": 0,
  "tipo_servico": 0,
  "problema": 0,
  "observacoes": "string",
  "data_criacao": "string",
  "id_tipo_ordem_servico": 0,
  "tipo_criticidade": 0,
  "prioridade": 0
}
```
**Response:** `201 Created`

### Obter detalhes da OS
```http
GET /api/v5/ordem_servico/{id}
```
**Response:** (estrutura semelhante ao de listagem, mas com mais detalhes)

### Atualizar ordem de serviço
```http
PUT /api/v5/ordem_servico/{id}
```
**Request Body:**
```json
{
  "solicitante_id": 0,
  "responsavel_id": 0,
  "tipo_servico_id": 0,
  "origem": 0,
  "problema": 0,
  "descricao_servico": "string",
  "imprimir_utilizacao_pecas": true,
  "oficina": 0,
  "campo_extra": "string",
  "inicio_agendamento": "string",
  "fim_agendamento": "string",
  "observacoes": "string",
  "origem_problema": 0,
  "terceiros": 0,
  "tipo_criticidade": 0,
  "prioridade": 0,
  "tecnicos_executores": [0],
  "estado": 0
}
```
**Response:** `200 OK`

---

## Referências rápidas

- [SwaggerHub da Arkmeds API](https://app.swaggerhub.com/apis-docs/Arkmeds/Arkmeds-APIs/1.0.0#/)

---
