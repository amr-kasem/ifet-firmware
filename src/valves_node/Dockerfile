FROM python:3.9.20

# Install system dependencies for gpiod
RUN apt-get update && apt-get install -y \
    libgpiod2 \
    gpiod \
    python3-libgpiod \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY ./requirements.txt ./requiments.txt
RUN pip install -r requiments.txt
ADD ./ ./
STOPSIGNAL SIGINT
CMD ["python", "valves_node.py"]