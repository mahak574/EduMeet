# Stage 1: Build React SPA
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve via Nginx as non-root user
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY ../docker/nginx.conf /etc/nginx/conf.d/default.conf

RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /etc/nginx/conf.d /usr/share/nginx/html

USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
