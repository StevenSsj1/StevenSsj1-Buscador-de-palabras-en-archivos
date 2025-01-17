# Build stage
FROM node:20-alpine as build
WORKDIR /app
COPY ../frontend/package*.json ./
RUN npm install
COPY ../frontend .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY ../frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80