FROM cypress/included:14.0.0

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ENTRYPOINT ["npx", "cypress", "run"]
