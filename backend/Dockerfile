# Use an official miniconda image as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the environment file to the container
COPY environment.yml .

# Create the conda environment from the environment.yml file
# and update the base environment with the new packages
# Also install the playwright browsers
RUN conda env update -n base -f environment.yml && \
    playwright install --with-deps

# Copy the rest of the application code into the container
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run the application
# It activates the conda environment and starts the uvicorn server
CMD ["conda", "run", "-n", "base", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]