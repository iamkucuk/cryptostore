FROM python:3.9-slim-bullseye

RUN apt update
RUN apt install gcc git -y

RUN pip install --no-cache-dir cython
RUN pip install --no-cache-dir git+https://github.com/iamkucuk/cryptofeed.git
RUN pip install --no-cache-dir aioredis
RUN pip install --no-cache-dir pymongo[srv]
RUN pip install --no-cache-dir motor
RUN pip install --no-cache-dir asyncpg
RUN pip install --no-cache-dir aiokafka
RUN pip install --no-cache-dir numpy

WORKDIR /cryptostore

CMD [ "python",  "cryptostore.py" ]
# COPY cryptostore.py /cryptostore.py

# CMD ["/cryptostore.py"]
# ENTRYPOINT ["python"]
