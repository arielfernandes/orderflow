# Orderflow Câmbio PoC

Prova de conceito de um sistema de orderflow para conversão de moedas. O objetivo técnico é demonstrar o desacoplamento entre a recepção de requisições web e o processamento de regras de negócio em background, garantindo resiliência e não-bloqueio da API principal.

## Stack Tecnológico

* **Ingestão:** FastAPI (Roteamento HTTP e validação via Pydantic)
* **Mensageria (Broker):** RabbitMQ
* **Processamento (Workers):** Celery
* **Persistência:** PostgreSQL (via SQLAlchemy/psycopg2)
* **Infraestrutura Base:** Docker Compose

## Fluxo Lógico

1. O cliente envia uma requisição `POST /orders/` com o valor em reais (BRL).
2. O FastAPI salva a intenção no banco de dados com status `PENDING`.
3. A tarefa de conversão é enfileirada no RabbitMQ. O FastAPI retorna `HTTP 202 Accepted` imediatamente ao cliente.
4. O worker do Celery consome a mensagem da fila.
5. O worker realiza o cálculo simulando o tempo de rede de uma API de câmbio externa e atualiza o banco de dados para `COMPLETED` com o valor em dólares (USD).

---

## Como Executar

### 1. Subir Banco de Dados e Broker
Certifique-se de ter o Docker instalado e inicie os containers em background:
```bash
docker-compose up -d
```

### 2. Configurar o Ambiente Python
Crie e ative um ambiente virtual, depois instale as dependências:
```bash
python -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Iniciar os Serviços
Para ver a arquitetura funcionando, você precisará de dois terminais abertos na raiz do projeto, ambos com o ambiente virtual ativado.

**Terminal 1 (A API FastAPI):**
```bash
uvicorn main:app --reload
```

**Terminal 2 (O Worker Celery):**
```bash
celery -A celery_app worker --loglevel=info
```

### 4. Testar o Fluxo
Com tudo rodando, acesse a documentação interativa do Swagger no navegador:
[http://localhost:8000/docs](http://localhost:8000/docs)

1. Encontre a rota `POST /orders/`.
2. Clique em **Try it out** e envie um payload como `{ "amount_brl": 1000 }`.
3. Observe que a API responde instantaneamente.
4. Olhe para o terminal do Celery e veja a tarefa sendo recebida e concluída alguns segundos depois.
