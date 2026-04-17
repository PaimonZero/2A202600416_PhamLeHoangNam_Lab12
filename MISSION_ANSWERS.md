# Day 12 Lab - Mission Answers

> **Student Name:** Phạm Lê Hoàng Nam
> **Student ID:** 2A202600416
> **Date:** 17/04/2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found (develop)

1. Hardcoded secret trong code:

- OPENAI_API_KEY va DATABASE_URL duoc hardcode.
- Rui ro lo secret neu push repo.

2. Khong dung config management theo env vars:

- DEBUG va MAX_TOKENS dat cung trong code.
- Kho thay doi theo moi truong dev/staging/prod.

3. Logging khong an toan:

- Dung print va log truc tiep key.
- Vua kho quan sat tap trung, vua lo thong tin nhay cam.

4. Thieu health check/readiness endpoint:

- Khong co /health, /ready.
- Platform kho phat hien app chet hoac chua san sang.

5. Cau hinh host/port khong production-ready:

- host=localhost (chi local truy cap duoc).
- port=8000 co dinh (khong doc PORT tu env).

6. Reload mode trong runtime:

- reload=True khong phu hop production.
- Lam tang overhead va rui ro van hanh.

### Exercise 1.2: Chay basic version

- Da chay app develop thanh cong.
- Da goi duoc endpoint /ask theo contract query parameter va nhan 200.

### Exercise 1.3: Comparison table

| Feature        | Develop                           | Production                                  | Why Important?                            |
| -------------- | --------------------------------- | ------------------------------------------- | ----------------------------------------- |
| Config         | Hardcode trong code               | Doc tu env vars qua settings                | Tach config khoi code, dung 12-factor     |
| Secrets        | De trong source code              | Lay tu env, co validate                     | Giam nguy co lo secret                    |
| Logging        | print thu cong, co log secret     | Structured logging JSON                     | De monitor va khong lo thong tin nhay cam |
| Health check   | Khong co                          | Co /health                                  | Nen tang cloud dung de liveness check     |
| Readiness      | Khong co                          | Co /ready voi flag is_ready                 | LB chi route traffic khi app da san sang  |
| Shutdown       | Dot ngot, khong lifecycle ro rang | Lifespan startup/shutdown + SIGTERM handler | Giam mat request dang xu ly               |
| Host/Port      | localhost + port co dinh          | 0.0.0.0 + port tu env                       | Chay duoc trong container/cloud           |
| CORS           | Khong cau hinh                    | Co CORSMiddleware                           | Kiem soat truy cap tu frontend/domain     |
| Input handling | Contract don gian                 | Parse JSON body, validate question          | Giam loi payload va tang do on dinh API   |

### Test evidence (production)

- GET /health -> 200 OK
- GET /ready -> 200 OK
- POST /ask voi JSON hop le -> 200 OK

Ghi chu:

- Co 1 lan 500 do payload JSON malformed khi quote command, sau do gui lai payload hop le thi /ask tra 200.

### Checkpoint 1

- [x] Hieu tai sao hardcode secrets nguy hiem
- [x] Biet cach dung environment variables
- [x] Hieu vai tro cua health check endpoint
- [x] Hieu readiness va graceful shutdown trong production context

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions (develop)

1. **Base image là gì?**
   - `python:3.11` — Full Python distribution (~1 GB), có sẵn tất cả build tools.

2. **Working directory là gì?**
   - `/app` — Đây là thư mục làm việc trong container, tất cả commands chạy ở đây.

3. **Tại sao COPY requirements.txt trước code?**
   - Docker layer cache — Nếu app code thay đổi nhưng requirements không đổi, Docker dùng lại cached layer thay vì cài lại packages (tiết kiệm thời gian build).

4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - CMD: Lệnh mặc định, có thể override khi chạy container (`docker run ... python other_script.py`).
   - ENTRYPOINT: Luôn chạy, CMD là argument cho nó (cách khác là hardcode lệnh).
   - Dockerfile này dùng CMD vì đơn giản cho development.

### Exercise 2.2: Build và run

**Build thành công:**

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
```

**Chạy container:**

```bash
docker run -p 8000:8000 my-agent:develop
```

**Test endpoint:**

```bash
curl "http://localhost:8000/ask?question=What%20is%20Docker?" -X POST
# Hoặc dùng GET (vì develop dùng query param)
curl "http://localhost:8000/ask?question=Hello"
```

### Exercise 2.3: Multi-stage build comparison

**Production Dockerfile analysis:**

**Stage 1 (builder):**

- Base image: `python:3.11-slim` (~150 MB, không có build tools)
- Cài gcc, libpq-dev (build dependencies)
- Cài pip packages vào `/root/.local` (dùng `--user` để dễ copy)
- Image này KHÔNG được deploy, chỉ dùng để build

**Stage 2 (runtime):**

- Base image: `python:3.11-slim` (lại một lần nữa, image mới)
- Copy `/root/.local` từ stage 1 sang `/home/appuser/.local`
- Copy source code (`main.py`)
- Tạo non-root user `appuser` (security best practice)
- Chỉ ~150 MB vì không có build tools, gcc, etc.

**Tại sao image nhỏ hơn:**

- Develop: ~1 GB (full python:3.11 + all build stuff)
- Production: ~250-300 MB (slim + chỉ runtime packages, không có gcc, build tools)
- Savings: ~70% nhỏ hơn

### Exercise 2.4: Docker Compose stack

**Services trong docker-compose.yml:**

1. **agent** — FastAPI app (2 workers) từ production Dockerfile
2. **redis** — Cache & session storage (port 6379)
3. **qdrant** — Vector database cho RAG (port 6333)
4. **nginx** — Reverse proxy & load balancer (port 80, 443)

**Architecture:**

```
Client → Nginx (Load balancer) → Agent (2 instances) ← Redis, Qdrant
```

**Communication:**

- Nginx: Route requests tới agent (port 8000)
- Agent: Call Redis & Qdrant cho internal state
- Health checks: Tự động restart nếu fail

**Test stack:**

```bash
docker compose up

# Health check
curl http://localhost/health

# Ask endpoint qua Nginx
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain Docker"}'
```

### Checkpoint 2

- [x] Hieu cau truc Dockerfile (single-stage vs multi-stage)
- [x] Biet loi ich cua multi-stage builds (giam image size ~70%)
- [x] Hieu Docker Compose orchestration (services, networking, health checks)
- [x] Biet cach debug container (docker logs, docker exec, docker inspect)

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results

[Paste your test outputs]

### Exercise 4.4: Cost guard implementation

[Explain your approach]

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

[Your explanations and test results]
