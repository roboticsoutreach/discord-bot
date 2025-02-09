FROM python:3.9-slim-bullseye

WORKDIR /usr/src/app

RUN groupadd -g 1000 app
RUN useradd -m -u 1000 -g 1000 app

COPY . .

RUN pip install --no-cache-dir .

RUN chown -R 1000:1000 /usr/src/app
USER 1000:1000

CMD [ "python", "-m", "sr.discord_bot" ]
