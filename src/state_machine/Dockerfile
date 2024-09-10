FROM python:3.9.20
WORKDIR /app
COPY ./requirements.txt ./requiments.txt
RUN pip install -r requiments.txt
COPY ./* ./
CMD ["python", "state_machine.py"]