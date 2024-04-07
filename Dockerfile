FROM python:3.10-slim-bullseye

RUN apt update
RUN apt install gcc git -y

RUN pip install --no-cache-dir cython
RUN pip install --no-cache-dir redis
RUN pip install --no-cache-dir pymongo[srv]
RUN pip install --no-cache-dir motor
RUN pip install --no-cache-dir asyncpg
RUN pip install --no-cache-dir aiokafka
RUN pip install --no-cache-dir numpy
RUN pip install --no-cache-dir confluent-kafka
RUN pip install --no-cache-dir fastavro

ADD https://www.random.org/strings/?num=1&len=8&digits=on&unique=on&format=plain&rnd=new /tmp/dummy

RUN pip install --no-cache-dir git+https://github.com/iamkucuk/cryptofeed.git

WORKDIR /cryptostore

CMD [ "python",  "cryptostore.py" ]
# COPY cryptostore.py /cryptostore.py

# CMD ["/cryptostore.py"]
# ENTRYPOINT ["python"]
