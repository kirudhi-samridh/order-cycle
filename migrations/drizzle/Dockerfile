FROM node:20-alpine
WORKDIR /usr/src/app
COPY package.json ./package.json
COPY tsconfig.json ./tsconfig.json
COPY drizzle.config.ts ./drizzle.config.ts
COPY schema.ts ./schema.ts
RUN npm install
CMD ["npm", "run", "migrate"]


