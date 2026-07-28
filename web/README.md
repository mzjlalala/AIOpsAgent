# OpsAgent Web Console

Vue 3 + Vite 演示控制台：Incident SSE + 人工审批。

## 启动

先启动后端（仓库根目录）：

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

再启动前端：

```bash
cd web
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（默认 http://127.0.0.1:5173）。  
`/incident`、`/workflows`、`/health` 已 proxy 到 `http://127.0.0.1:8000`。
