FROM python:3.10

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir -r /src/requirements.txt

COPY ./app /src/app

EXPOSE 8000 443

CMD ["fastapi", "run",  "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
