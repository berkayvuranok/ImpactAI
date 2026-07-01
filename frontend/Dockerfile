# Build stage
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_BASE=/api/v1
ARG VITE_AUTH_REQUIRED=false
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_AUTH_REQUIRED=$VITE_AUTH_REQUIRED
RUN npm run build

# Serve stage
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
