FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements_dev.txt .
RUN pip install --no-cache-dir Cython setuptools wheel && \
    pip install --no-cache-dir -r requirements_dev.txt

COPY . .

RUN python setup.py install

RUN mkdir /test_run && \
    cp test.py *.html /test_run/

WORKDIR /test_run

CMD ["python", "test.py"]
