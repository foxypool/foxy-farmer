FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential git curl ocl-icd-libopencl1

WORKDIR /app

ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY . .
RUN pip install --upgrade pip
RUN pip install wheel
RUN pip install -e . --extra-index-url https://pypi.chia.net/simple/

VOLUME /root/.foxy-farmer
VOLUME /root/.chia_keys

CMD ["foxy-farmer"]
