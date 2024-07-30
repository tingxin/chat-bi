# ---- Build ----
FROM public.ecr.aws/docker/library/node:18.16-alpine
COPY . .
RUN npm install && npm run build

# Expose the port the app will run on
EXPOSE 80

# Start the application
CMD ["npm", "start"]
