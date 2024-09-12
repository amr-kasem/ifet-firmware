FROM python:3.9.20
WORKDIR /app
COPY ./requirements.txt ./requiments.txt
RUN pip install -r requiments.txt
ADD ./ ./
CMD ["python", "valves_node.py"]