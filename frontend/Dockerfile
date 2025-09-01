# Use the official Node.js 20 image.
FROM node:20-slim AS base

# Set the working directory in the container.
WORKDIR /usr/src/app

# Install dependencies.
COPY package*.json ./
RUN npm install

# Copy the rest of the application code.
COPY . .

# Build the Next.js application.
RUN npm run build

# Expose the port the app runs on.
EXPOSE 3000

# Define the command to run the app.
CMD ["npm", "start"]
