FROM python:3.10-slim-bullseye

WORKDIR /usr/src/app

RUN groupadd -g 1000 app
RUN useradd -m -u 1000 -g 1000 app

COPY . .

RUN pip install --no-cache-dir .

RUN chown -R 1000:1000 /usr/src/app

RUN mkdir /app
RUN chown -R 1000:1000 /app
WORKDIR /app

USER 1000:1000

CMD [ "python", "-m", "sr.discord_bot" ]
