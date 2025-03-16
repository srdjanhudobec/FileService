FROM python:3-alpine3.15

# Instaliramo potrebne biblioteke i build alate za WeasyPrint
RUN apk add --no-cache \
    build-base \
    cairo \
    pango \
    gdk-pixbuf \
    libffi-dev \
    musl-dev \
    libxml2-dev \
    libxslt-dev \
    jpeg-dev \
    zlib-dev

WORKDIR /app

COPY . /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
