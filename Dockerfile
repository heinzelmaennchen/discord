FROM python:3.10

COPY . /

RUN pip install --requirement /requirements.txt

CMD [ "python", "-u", "./main.py" ]
