FROM python:3.11

COPY . /

RUN pip install --requirement /requirements.txt

CMD [ "python", "-u", "./main.py" ]
