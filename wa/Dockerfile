FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
VOLUME ["/app/auth_info_baileys"]   # persist WA session (no re-scan)
ENV PORT=3001
EXPOSE 3001
CMD ["node", "server.js"]