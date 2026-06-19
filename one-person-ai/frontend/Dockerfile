FROM node:22-alpine AS builder

WORKDIR /app

# npm 用国内源加速
ENV npm_config_registry=https://registry.npmmirror.com

# 复制依赖文件
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./

# 用 npm 安装(pnpm 在 alpine/overlay2 下写 store 会触发 EPERM,
# npm 无此问题;lockfile 仍由 pnpm-lock 维护,这里用 npm install 按 package.json 装)
RUN npm install --no-audit --no-fund

# 复制源代码并构建
COPY . .
RUN npm run build

# 生产阶段 - 使用 standalone 输出
FROM node:22-alpine
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

ENV PORT=3000
CMD ["node", "server.js"]