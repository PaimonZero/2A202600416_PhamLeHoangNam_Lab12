## Plan: Hoan Thanh Lab12 End-to-End

Muc tieu la di qua toan bo 6 phan theo dung trinh tu hoc tap, vua hieu concept vua tao ra artifact nop bai (MISSION_ANSWERS.md, DEPLOYMENT.md, code production-ready). Cach lam toi uu: dung cac thu muc develop de nhan dien anti-pattern va thu muc production/06-lab-complete de doi chieu implementation dung, sau do tu build hoac clone pattern vao bai cuoi.

**Steps**

1. Phase 0 - Baseline va run nhanh (_bat buoc truoc cac phase khac_): doc README tong quan, chon chuoi thuc hien 1->6, cai dependencies local/Docker, chay quick smoke endpoint de xac nhan moi truong.
2. Phase 1 - Part 1 Localhost vs Production (_block cho phan con lai_): so sanh `01-localhost-vs-production/develop/app.py` va `01-localhost-vs-production/production/app.py` + `config.py`; ghi ro 5 anti-pattern; test `/health` va `/ready`; dien bang so sanh vao MISSION_ANSWERS.
3. Phase 2 - Part 2 Dockerization (_depends on 2_): build image develop va production, so sanh kich thuoc image, doc multi-stage Dockerfile va docker-compose stack; test qua Nginx endpoint; ghi lai architecture diagram va ket qua logs.
4. Phase 3 - Part 3 Cloud Deployment (_depends on 3_): uu tien Railway hoac Render de co URL public nhanh; set env vars dung; test public `/health` va `/ask`; ghi URL + screenshot/log trich yeu vao DEPLOYMENT.
5. Phase 4 - Part 4 API Security (_depends on 4_): verify API key/JWT flow, rate limiting (429), cost guard (402) trong `04-api-gateway/production`; bo sung implement neu thieu; chot quy trinh token + bao mat secret.
6. Phase 5 - Part 5 Scaling & Reliability (_depends on 5_): verify stateless session qua Redis, load balancing Nginx, graceful shutdown, health/readiness; chay test stateless de chung minh session khong mat khi qua instance khac.
7. Phase 6 - Part 6 Final Project Assembly (_depends on 2-6_): dung `06-lab-complete` lam reference implementation, build project nop bai dap ung full non-functional checklist (auth, rate limit, cost guard, health/ready, graceful shutdown, stateless, JSON logs, Docker multi-stage).
8. Phase 7 - Artifact hoan thien va nộp bai (_final gate_): hoan tat `MISSION_ANSWERS.md`, `DEPLOYMENT.md`, run `06-lab-complete/check_production_ready.py`, fix tat ca muc fail den khi dat pass cao nhat; chot link deploy.
9. Workstream song song de tiet kiem thoi gian: trong khi cloud deploy dang build, co the song song hoan thien MISSION_ANSWERS va tu test rate limit/cost guard local; khong song song cac buoc phu thuoc state (part 1 truoc part 6).

**Relevant files**

- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/README.md` - order hoc va dieu huong tong quan
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/CODE_LAB.md` - checklist bai tap tung part
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/DAY12_DELIVERY_CHECKLIST.md` - tieu chi cham diem va artifact nop
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/01-localhost-vs-production/develop/app.py` - anti-pattern baseline
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/01-localhost-vs-production/production/app.py` - health/ready, graceful shutdown, logging
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/01-localhost-vs-production/production/config.py` - env-based config/validation
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/02-docker/develop/Dockerfile` - single-stage baseline
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/02-docker/production/Dockerfile` - multi-stage + non-root pattern
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/02-docker/production/docker-compose.yml` - stack orchestration
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/02-docker/production/nginx/nginx.conf` - reverse proxy/load balancing basics
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/03-cloud-deployment/railway/railway.toml` - deploy Railway
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/03-cloud-deployment/render/render.yaml` - deploy Render
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/03-cloud-deployment/production-cloud-run/cloudbuild.yaml` - CI/CD Cloud Run
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/03-cloud-deployment/production-cloud-run/service.yaml` - Cloud Run runtime spec
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/04-api-gateway/develop/app.py` - API key auth baseline
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/04-api-gateway/production/app.py` - secure gateway integration
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/04-api-gateway/production/auth.py` - JWT flow
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/04-api-gateway/production/rate_limiter.py` - rate limit logic
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/04-api-gateway/production/cost_guard.py` - budget protection
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/05-scaling-reliability/production/app.py` - stateless session with Redis
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/05-scaling-reliability/production/docker-compose.yml` - scaling to multiple replicas
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/05-scaling-reliability/production/nginx.conf` - LB config for reliability
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/05-scaling-reliability/production/test_stateless.py` - resilience verification
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/06-lab-complete/app/main.py` - integrated production behavior
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/06-lab-complete/app/config.py` - final config safety checks
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/06-lab-complete/Dockerfile` - final optimized container
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/06-lab-complete/docker-compose.yml` - local prod-like stack
- `i:/VinUni/codeSample/Lab12/day12_ha-tang-cloud_va_deployment/06-lab-complete/check_production_ready.py` - objective validator truoc nop bai

**Verification**

1. Local sanity: run ung dung o moi part va xac nhan endpoint can ban tra ve dung status code (200/401/429/402/503 theo tung case).
2. Docker sanity: build image develop + production, so sanh image size va xac nhan healthcheck trong compose.
3. Security tests: goi endpoint khong key/invalid token/over-limit/over-budget de xac nhan bao ve hoat dong dung.
4. Reliability tests: scale nhieu instance va chay `05-scaling-reliability/production/test_stateless.py`, xac nhan session van dung qua replica khac.
5. Cloud tests: ping public `/health` va goi public `/ask` voi auth hop le.
6. Final gate: chay `06-lab-complete/check_production_ready.py`; muc tieu pass tat ca hoac ghi ro ly do neu khong the pass 100%.

**Decisions**

- Included scope: hoc va thuc thi full 6 part, uu tien dat artifact nop bai + deploy public URL.
- Excluded scope: toi uu chi phi hạ tầng nang cao (Kubernetes, observability nâng cao) vi nam ngoai rubric bat buoc.
- Approach decision: reference-first, reuse patterns tu thu muc production/06-lab-complete thay vi tu code lai tat ca tu dau de tiet kiem thoi gian va giam loi.

**Further Considerations**

1. Nen chon Railway lam deploy chinh neu uu tien toc do; chon Render neu muon IaC qua blueprint va giao dien dashboard de quan sat.
2. Neu khong co Redis cloud trong bai nop, can ghi ro mode fallback local va gioi han (khong phu hop scale thuc su) trong DEPLOYMENT.md.
3. Truoc khi nop, doi tat ca key mac dinh dev trong env production de tranh truot tieu chi security.
