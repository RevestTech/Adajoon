FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json ./
RUN npm install

ARG CACHEBUST=20260406
ENV BUILD_ID=20260406
COPY frontend/ .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/index.html || exit 1

CMD ["/start.sh"]
