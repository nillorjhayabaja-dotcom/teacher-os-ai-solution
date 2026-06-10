# =============================================================================
# TeacherOS - Frontend Dockerfile (Multi-stage)
# =============================================================================
# Stage 1: Dependencies
# Stage 2: Build
# Stage 3: Production Runtime
# =============================================================================

# =============================================================================
# Stage 1: Base - Shared dependencies
# =============================================================================
FROM node:22-alpine AS base

# Add non-root user
RUN addgroup -S teacheros && adduser -S teacheros -G teacheros

# Install necessary build tools
RUN apk add --no-cache python3 make g++ curl

WORKDIR /app

# Copy package files
COPY package.json package-lock.json bun.lock bunfig.toml ./

# =============================================================================
# Stage 2: Dependencies - Install all dependencies (dev + prod)
# =============================================================================
FROM base AS deps

# Install dependencies
RUN npm ci --no-audit --no-fund 2>&1 || npm install --no-audit --no-fund

# =============================================================================
# Stage 3: Builder - Build the application
# =============================================================================
FROM deps AS builder

# Copy source code
COPY . .

# Copy environment file if available
ARG ENVIRONMENT=production
ENV NODE_ENV=$ENVIRONMENT

# Build the application
RUN npm run build

# =============================================================================
# Stage 4: Development Runtime - Hot reload
# =============================================================================
FROM base AS development

# Install dependencies
RUN npm ci --no-audit --no-fund 2>&1 || npm install --no-audit --no-fund

# Copy source code
COPY . .

# Set user
USER teacheros

# Expose port
EXPOSE 3000

# Start development server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# =============================================================================
# Stage 5: Production Runtime - Optimized and minimal
# =============================================================================
FROM node:22-alpine AS production

# Install security updates and curl for health checks
RUN apk add --no-cache curl tini

# Create non-root user
RUN addgroup -S teacheros && adduser -S teacheros -G teacheros

WORKDIR /app

# Copy built assets from builder stage
COPY --from=builder --chown=teacheros:teacheros /app/dist ./dist
COPY --from=builder --chown=teacheros:teacheros /app/node_modules ./node_modules
COPY --from=builder --chown=teacheros:teacheros /app/package.json ./package.json
COPY --from=builder --chown=teacheros:teacheros /app/public ./public

# Remove unnecessary files
RUN npm prune --production && \
    rm -rf /app/node_modules/.cache && \
    rm -rf /tmp/*

# Set to non-root user
USER teacheros

# Security: read-only root filesystem
RUN chmod 755 /app && \
    chmod 644 /app/package.json

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Use tini as init to handle signals properly
ENTRYPOINT ["/sbin/tini", "--"]

# Start production server
CMD ["node", "dist/server/index.js"]