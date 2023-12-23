FROM python:3.11-alpine
WORKDIR /app
COPY app.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "app.py" ]