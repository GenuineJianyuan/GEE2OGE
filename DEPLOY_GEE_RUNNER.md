# 集群部署

推荐使用 Docker。镜像包含 Flask、Gunicorn、Python Earth Engine API 和 GEE JavaScript SDK；服务账号私钥、OpenAI 密钥和运行记录不写入镜像。

## Docker Compose

1. 准备目录和配置：

```bash
mkdir -p secrets
cp /path/to/service-account.json secrets/gee-service-account.json
export OPENAI_API_KEY=your-key
export GEE_PROJECT=your-project
```

2. 修改 `docker-compose.yml` 中的 `GEE_PROJECT`，构建并启动：

```bash
docker compose build
docker compose up -d
```

访问 `http://集群地址:5000/`，GEE Runner 在 `/gee-runner`。

## 上传镜像到集群

```bash
docker build -t registry.example.com/gee-to-oge:1.0.0 .
docker push registry.example.com/gee-to-oge:1.0.0
kubectl create secret generic gee-to-oge-secrets \
  --from-file=service-account.json=secrets/gee-service-account.json \
  --from-literal=openai-api-key=your-key \
  --from-literal=openai-base-url=https://api.openai.com/v1
kubectl apply -f k8s/gee-to-oge.yaml
```

将清单中的镜像地址、项目 ID 和 Ingress/Service 配置替换成集群实际值。

## 重要说明

- GEE Runner 当前批处理状态保存在进程内存，部署必须保持 `replicas: 1`；`runs` 目录用于历史结果持久化。
- Kubernetes 的 `PersistentVolume` 需要同时承载 `/app/web/gee_runner/runs` 和 `/app/resource`，生产环境建议拆成两个 PVC。
- 如果集群通过代理访问 Google/OpenAI，注入 `HTTPS_PROXY`、`HTTP_PROXY`。
- 服务账号必须已在 Earth Engine 项目中注册，并具备需要的资产/导出权限。
- 不要把 `service-account.json`、`.env`、API Key 提交到 Git 或打进镜像。
