FROM python:3-alpine

WORKDIR /ChronosBot

RUN pip install python-dotenv discord.py psycopg2-binary

COPY *.py .env /ChronosBot/

ENTRYPOINT [ "python3", "main.py" ]

