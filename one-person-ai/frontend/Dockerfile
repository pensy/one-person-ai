FROM node:22-alpine AS builder

WORKDIR /app

# npm/pnpm 用国内源加速
ENV npm_config_registry=https://registry.npmmirror.com

# pnpm 配置:alpine + overlay2 下默认的硬链接 store 会触发 EPERM,
# 改用 copy 导入 + hoisted 布局规避(容器内单次构建,不在乎磁盘占用)
ENV PNPM_HOME=/pnpm
RUN corepack enable && corepack prepare pnpm@9 --activate

# 复制依赖文件
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
RUN pnpm install --frozen-lockfile --config.package-import-method=copy --node-linker=hoisted

# 复制源代码并构建
COPY . .
RUN pnpm run build

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