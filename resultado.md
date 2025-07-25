# Resultado da API /api/v5/chamado/

**Data da consulta:** 24/07/2025 às 22:03:25  
**Endpoint:** `/api/v5/chamado/`  
**Status HTTP:** 200  
**Content-Type:** application/json

## Estrutura da Resposta

```json
{
  "count": 5049,
  "next": "https://comg.arkmeds.com/api/v5/chamado/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "chamados": 1,
      "chamado_arquivado": false,
      "responsavel_id": 1,
      "tempo": [
        "vazio",
        0,
        1,
        null
      ],
      "tempo_fechamento": [
        "vazio",
        0,
        1,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Usuario de consulta",
        "email": "_consulta@dsh.com",
        "has_resp_tecnico": true,
        "id": "1",
        "avatar": "Uc"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "1",
        "data_criacao": "19/04/23 - 15:58",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 1,
        "problema": 22,
        "estado": 2,
        "oficina": 5,
        "solicitante": 50
      }
    },
    {
      "id": 19,
      "chamados": 2,
      "chamado_arquivado": true,
      "responsavel_id": 1,
      "tempo": [
        "finalizado sem atraso",
        1,
        2,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        2,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Usuario de consulta",
        "email": "_consulta@dsh.com",
        "has_resp_tecnico": true,
        "id": "1",
        "avatar": "Uc"
      },
      "ordem_servico": {
        "usuario_solicitante": 1,
        "numero": "19",
        "data_criacao": "18/05/23 - 10:15",
        "prioridade": 1,
        "equipamento": 827,
        "tipo_servico": 3,
        "id": 19,
        "problema": 7,
        "estado": 2,
        "oficina": 2,
        "solicitante": 474
      }
    },
    {
      "id": 20,
      "chamados": 3,
      "chamado_arquivado": true,
      "responsavel_id": 1,
      "tempo": [
        "vazio",
        0,
        3,
        null
      ],
      "tempo_fechamento": [
        "vazio",
        0,
        3,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Usuario de consulta",
        "email": "_consulta@dsh.com",
        "has_resp_tecnico": true,
        "id": "1",
        "avatar": "Uc"
      },
      "ordem_servico": {
        "usuario_solicitante": 3,
        "numero": "20",
        "data_criacao": "18/05/23 - 10:15",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 20,
        "problema": 20,
        "estado": 2,
        "oficina": 5,
        "solicitante": 173
      }
    },
    {
      "id": 21,
      "chamados": 4,
      "chamado_arquivado": true,
      "responsavel_id": 1,
      "tempo": [
        "vazio",
        0,
        4,
        null
      ],
      "tempo_fechamento": [
        "vazio",
        0,
        4,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Usuario de consulta",
        "email": "_consulta@dsh.com",
        "has_resp_tecnico": true,
        "id": "1",
        "avatar": "Uc"
      },
      "ordem_servico": {
        "usuario_solicitante": 3,
        "numero": "21",
        "data_criacao": "18/05/23 - 10:15",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 21,
        "problema": 10,
        "estado": 2,
        "oficina": 5,
        "solicitante": 173
      }
    },
    {
      "id": 101,
      "chamados": 7,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado sem atraso",
        1,
        7,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        7,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": 3,
        "numero": "101",
        "data_criacao": "18/05/23 - 16:08",
        "prioridade": 1,
        "equipamento": 827,
        "tipo_servico": 3,
        "id": 101,
        "problema": 5,
        "estado": 2,
        "oficina": 2,
        "solicitante": 474
      }
    },
    {
      "id": 105,
      "chamados": 8,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado com atraso",
        1,
        8,
        null
      ],
      "tempo_fechamento": [
        "finalizado com atraso",
        1,
        8,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": 1,
        "numero": "105",
        "data_criacao": "19/05/23 - 13:30",
        "prioridade": 5,
        "equipamento": 467,
        "tipo_servico": 3,
        "id": 105,
        "problema": 2,
        "estado": 2,
        "oficina": 2,
        "solicitante": 246
      }
    },
    {
      "id": 106,
      "chamados": 9,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado com atraso",
        1,
        9,
        null
      ],
      "tempo_fechamento": [
        "finalizado com atraso",
        1,
        9,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "106",
        "data_criacao": "19/05/23 - 13:32",
        "prioridade": 1,
        "equipamento": 463,
        "tipo_servico": 3,
        "id": 106,
        "problema": 3,
        "estado": 2,
        "oficina": 2,
        "solicitante": 245
      }
    },
    {
      "id": 107,
      "chamados": 10,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado com atraso",
        1,
        10,
        null
      ],
      "tempo_fechamento": [
        "finalizado com atraso",
        1,
        10,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "107",
        "data_criacao": "19/05/23 - 13:35",
        "prioridade": 1,
        "equipamento": 445,
        "tipo_servico": 3,
        "id": 107,
        "problema": 3,
        "estado": 2,
        "oficina": 2,
        "solicitante": 224
      }
    },
    {
      "id": 150,
      "chamados": 12,
      "chamado_arquivado": true,
      "responsavel_id": 7,
      "tempo": [
        "finalizado com atraso",
        1,
        12,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        12,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Hudson Poletti",
        "email": "_hudson@dsh.com",
        "has_resp_tecnico": true,
        "id": "7",
        "avatar": "HP"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "150",
        "data_criacao": "23/05/23 - 14:33",
        "prioridade": 1,
        "equipamento": 270,
        "tipo_servico": 3,
        "id": 150,
        "problema": 6,
        "estado": 2,
        "oficina": 2,
        "solicitante": 252
      }
    },
    {
      "id": 155,
      "chamados": 13,
      "chamado_arquivado": true,
      "responsavel_id": 3,
      "tempo": [
        "vazio",
        0,
        13,
        null
      ],
      "tempo_fechamento": [
        "vazio",
        0,
        13,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Ulisses Arthur Ribeiro Nascimento",
        "email": "_ulisses@dsh.com",
        "has_resp_tecnico": true,
        "id": "3",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/3/avatar_small.png?Signature=SKCgjDe26BkkxzcRuBYgJI1rycw%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": 3,
        "numero": "155",
        "data_criacao": "23/05/23 - 15:26",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 155,
        "problema": 8,
        "estado": 2,
        "oficina": 5,
        "solicitante": 163
      }
    },
    {
      "id": 156,
      "chamados": 14,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado sem atraso",
        1,
        14,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        14,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": 3,
        "numero": "156",
        "data_criacao": "23/05/23 - 15:31",
        "prioridade": 1,
        "equipamento": 828,
        "tipo_servico": 3,
        "id": 156,
        "problema": 7,
        "estado": 2,
        "oficina": 2,
        "solicitante": 225
      }
    },
    {
      "id": 157,
      "chamados": 15,
      "chamado_arquivado": true,
      "responsavel_id": 4,
      "tempo": [
        "vazio",
        0,
        15,
        null
      ],
      "tempo_fechamento": [
        "vazio",
        0,
        15,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Alvaro Luiz",
        "email": "_alvaro@dsh.com",
        "has_resp_tecnico": true,
        "id": "4",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/4/avatar_small.png?Signature=wZ6F7gp7kid4%2BUWYukozkRgqB0E%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "157",
        "data_criacao": "23/05/23 - 16:27",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 157,
        "problema": 11,
        "estado": 2,
        "oficina": 5,
        "solicitante": 357
      }
    },
    {
      "id": 161,
      "chamados": 16,
      "chamado_arquivado": true,
      "responsavel_id": 7,
      "tempo": [
        "finalizado com atraso",
        1,
        16,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        16,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Hudson Poletti",
        "email": "_hudson@dsh.com",
        "has_resp_tecnico": true,
        "id": "7",
        "avatar": "HP"
      },
      "ordem_servico": {
        "usuario_solicitante": 3,
        "numero": "161",
        "data_criacao": "24/05/23 - 08:41",
        "prioridade": 1,
        "equipamento": 269,
        "tipo_servico": 3,
        "id": 161,
        "problema": 5,
        "estado": 2,
        "oficina": 2,
        "solicitante": 252
      }
    },
    {
      "id": 164,
      "chamados": 17,
      "chamado_arquivado": true,
      "responsavel_id": 4,
      "tempo": [
        "vazio",
        0,
        17,
        null
      ],
      "tempo_fechamento": [
        "vazio",
        0,
        17,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Alvaro Luiz",
        "email": "_alvaro@dsh.com",
        "has_resp_tecnico": true,
        "id": "4",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/4/avatar_small.png?Signature=wZ6F7gp7kid4%2BUWYukozkRgqB0E%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "164",
        "data_criacao": "24/05/23 - 10:15",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 164,
        "problema": 25,
        "estado": 2,
        "oficina": 5,
        "solicitante": 22
      }
    },
    {
      "id": 170,
      "chamados": 21,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado sem atraso",
        1,
        21,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        21,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "170",
        "data_criacao": "24/05/23 - 10:37",
        "prioridade": 3,
        "equipamento": 829,
        "tipo_servico": 3,
        "id": 170,
        "problema": 7,
        "estado": 2,
        "oficina": 2,
        "solicitante": 146
      }
    },
    {
      "id": 171,
      "chamados": 22,
      "chamado_arquivado": true,
      "responsavel_id": 6,
      "tempo": [
        "finalizado sem atraso",
        1,
        22,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        22,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Raylla Silva Martins de Souza",
        "email": "_raylla@dsh.com",
        "has_resp_tecnico": true,
        "id": "6",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/6/avatar_small.png?Signature=G8T%2FB76XfDjy0EoM1Wj7x8M%2BjqI%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "171",
        "data_criacao": "24/05/23 - 10:53",
        "prioridade": 1,
        "equipamento": 155,
        "tipo_servico": 3,
        "id": 171,
        "problema": 4,
        "estado": 2,
        "oficina": 2,
        "solicitante": 22
      }
    },
    {
      "id": 175,
      "chamados": 26,
      "chamado_arquivado": true,
      "responsavel_id": 7,
      "tempo": [
        "finalizado sem atraso",
        1,
        26,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        26,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Hudson Poletti",
        "email": "_hudson@dsh.com",
        "has_resp_tecnico": true,
        "id": "7",
        "avatar": "HP"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "175",
        "data_criacao": "24/05/23 - 11:05",
        "prioridade": 5,
        "equipamento": 467,
        "tipo_servico": 3,
        "id": 175,
        "problema": 3,
        "estado": 2,
        "oficina": 2,
        "solicitante": 246
      }
    },
    {
      "id": 180,
      "chamados": 27,
      "chamado_arquivado": true,
      "responsavel_id": 7,
      "tempo": [
        "finalizado sem atraso",
        1,
        27,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        27,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Hudson Poletti",
        "email": "_hudson@dsh.com",
        "has_resp_tecnico": true,
        "id": "7",
        "avatar": "HP"
      },
      "ordem_servico": {
        "usuario_solicitante": 1,
        "numero": "180",
        "data_criacao": "25/05/23 - 08:02",
        "prioridade": 1,
        "equipamento": 147,
        "tipo_servico": 3,
        "id": 180,
        "problema": 7,
        "estado": 2,
        "oficina": 2,
        "solicitante": 22
      }
    },
    {
      "id": 192,
      "chamados": 29,
      "chamado_arquivado": true,
      "responsavel_id": 7,
      "tempo": [
        "finalizado sem atraso",
        1,
        29,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        29,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Hudson Poletti",
        "email": "_hudson@dsh.com",
        "has_resp_tecnico": true,
        "id": "7",
        "avatar": "HP"
      },
      "ordem_servico": {
        "usuario_solicitante": 1,
        "numero": "192",
        "data_criacao": "25/05/23 - 14:28",
        "prioridade": 1,
        "equipamento": 317,
        "tipo_servico": 3,
        "id": 192,
        "problema": 5,
        "estado": 2,
        "oficina": 2,
        "solicitante": 324
      }
    },
    {
      "id": 195,
      "chamados": 32,
      "chamado_arquivado": true,
      "responsavel_id": 1,
      "tempo": [
        "finalizado sem atraso",
        1,
        32,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        32,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": false,
        "nome": "Usuario de consulta",
        "email": "_consulta@dsh.com",
        "has_resp_tecnico": true,
        "id": "1",
        "avatar": "Uc"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "195",
        "data_criacao": "25/05/23 - 15:22",
        "prioridade": 1,
        "equipamento": 386,
        "tipo_servico": 3,
        "id": 195,
        "problema": 3,
        "estado": 2,
        "oficina": 2,
        "solicitante": 67
      }
    },
    {
      "id": 212,
      "chamados": 37,
      "chamado_arquivado": true,
      "responsavel_id": 4,
      "tempo": [
        "finalizado sem atraso",
        1,
        37,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        37,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Alvaro Luiz",
        "email": "_alvaro@dsh.com",
        "has_resp_tecnico": true,
        "id": "4",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/4/avatar_small.png?Signature=wZ6F7gp7kid4%2BUWYukozkRgqB0E%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "212",
        "data_criacao": "26/05/23 - 14:34",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 212,
        "problema": 36,
        "estado": 2,
        "oficina": 5,
        "solicitante": 22
      }
    },
    {
      "id": 216,
      "chamados": 38,
      "chamado_arquivado": true,
      "responsavel_id": 4,
      "tempo": [
        "finalizado com atraso",
        1,
        38,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        38,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Alvaro Luiz",
        "email": "_alvaro@dsh.com",
        "has_resp_tecnico": true,
        "id": "4",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/4/avatar_small.png?Signature=wZ6F7gp7kid4%2BUWYukozkRgqB0E%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "216",
        "data_criacao": "26/05/23 - 16:00",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 216,
        "problema": 11,
        "estado": 2,
        "oficina": 5,
        "solicitante": 305
      }
    },
    {
      "id": 219,
      "chamados": 39,
      "chamado_arquivado": false,
      "responsavel_id": 3,
      "tempo": [
        "finalizado sem atraso",
        1,
        39,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        39,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Ulisses Arthur Ribeiro Nascimento",
        "email": "_ulisses@dsh.com",
        "has_resp_tecnico": true,
        "id": "3",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/3/avatar_small.png?Signature=SKCgjDe26BkkxzcRuBYgJI1rycw%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "219",
        "data_criacao": "27/05/23 - 09:16",
        "prioridade": 3,
        "equipamento": 170,
        "tipo_servico": 3,
        "id": 219,
        "problema": 7,
        "estado": 2,
        "oficina": 2,
        "solicitante": 453
      }
    },
    {
      "id": 220,
      "chamados": 40,
      "chamado_arquivado": true,
      "responsavel_id": 4,
      "tempo": [
        "finalizado sem atraso",
        1,
        40,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        40,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Alvaro Luiz",
        "email": "_alvaro@dsh.com",
        "has_resp_tecnico": true,
        "id": "4",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/4/avatar_small.png?Signature=wZ6F7gp7kid4%2BUWYukozkRgqB0E%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "220",
        "data_criacao": "27/05/23 - 09:42",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 220,
        "problema": 34,
        "estado": 2,
        "oficina": 5,
        "solicitante": 122
      }
    },
    {
      "id": 228,
      "chamados": 41,
      "chamado_arquivado": true,
      "responsavel_id": 4,
      "tempo": [
        "finalizado sem atraso",
        1,
        41,
        null
      ],
      "tempo_fechamento": [
        "finalizado sem atraso",
        1,
        41,
        null
      ],
      "get_resp_tecnico": {
        "has_avatar": true,
        "nome": "Alvaro Luiz",
        "email": "_alvaro@dsh.com",
        "has_resp_tecnico": true,
        "id": "4",
        "avatar": "https://arkmeds-files.s3.amazonaws.com/comg/avatar/4/avatar_small.png?Signature=wZ6F7gp7kid4%2BUWYukozkRgqB0E%3D&Expires=1753409005&AWSAccessKeyId=AKIAJXZYAOEXFLV5IRNQ"
      },
      "ordem_servico": {
        "usuario_solicitante": null,
        "numero": "228",
        "data_criacao": "29/05/23 - 09:24",
        "prioridade": 1,
        "equipamento": null,
        "tipo_servico": 3,
        "id": 228,
        "problema": 14,
        "estado": 2,
        "oficina": 5,
        "solicitante": 12
      }
    }
  ]
}
```

## Análise dos Dados

- **Total de registros:** 5049
- **Registros retornados:** 25
- **Estrutura do primeiro registro:**
  - `id`: int
  - `chamados`: int
  - `chamado_arquivado`: bool
  - `responsavel_id`: int
  - `tempo`: list
  - `tempo_fechamento`: list
  - `get_resp_tecnico`: dict
  - `ordem_servico`: dict
- **Próxima página:** Sim
- **Página anterior:** Não

## Raw Response Headers

- **allow:** GET, POST, HEAD, OPTIONS
- **content-type:** application/json
- **date:** Fri, 25 Jul 2025 01:03:25 GMT
- **server:** Apache/2.4.27 (Amazon) mod_wsgi/3.5 Python/2.7.13
- **vary:** Accept,Cookie
- **x-frame-options:** SAMEORIGIN
- **x-remote-schema:** comg
- **x-remote-user-email:** rafael.ribeiro@drumondsolucoeshospitalares.com
- **x-remote-user-memory:** 0.49609375
- **x-remote-user-name:** Rafael Ribeiro
- **content-length:** 15287
- **connection:** keep-alive
