import yaml
import os
from cryptofeed.exchanges import EXCHANGE_MAP


def main():
    with open("./config.yaml", 'r') as fp:
        config = yaml.safe_load(fp)

    kwargs = config.copy()
    [kwargs.pop(key) for key in ('backend', 'channels', 'exchanges', 'symbols', 'symbols_per_channel')]
    kwargs_str = '-e ' + ' -e '.join([f"{key.upper()}={value}" for key, value in kwargs.items()])

    compose_string = """version: "3.9"
services:"""

    for exchange in config['exchanges']:
        eobj = EXCHANGE_MAP[exchange.upper()]()
        symbols = eobj.symbols()

        parity1_specified = False
        if ('-' not in config['symbols'][exchange]) and config['symbols'][exchange] != 'ALL':
            parity1_specified = True

        if parity1_specified:
            to_be_deleted_list = []
            for i in range(len(symbols) - 1):
                parity1_curr = symbols[i].split('-')[0]
                parity2_curr = symbols[i].split('-')[1]
                if (not any (parity1_query == parity1_curr for parity1_query in config['symbols'][exchange])) or (not any (x == parity2_curr for x in ["BTC", "USD", "USDT", "BUSD", "USDC"])):
                    to_be_deleted_list.append(i)
                elif "PINDEX" in symbols[i]:
                    to_be_deleted_list.append(i)
            for to_be_deleted in reversed(to_be_deleted_list):
                del symbols[to_be_deleted]

        elif config['symbols'][exchange] != 'ALL':
            if any([s not in symbols for s in config['symbols'][exchange]]):
                print("Invalid symbol specified")
                return
            symbols = config['symbols'][exchange]

        for i in range(0, len(symbols), config['symbols_per_channel']):
            print(f"docker run --name {exchange.upper()} -d --rm -e EXCHANGE={exchange.upper()} -e CHANNELS='{','.join(config['channels'])}' -e SYMBOLS='{','.join(symbols[i:i+config['symbols_per_channel']])}' -e BACKEND={config['backend']} {kwargs_str} cryptostore_new")
            # for chan in config["channels"]:
            compose_string += f"""
    {exchange.lower()}:
        image: cryptostore
        restart: always
        container_name: {exchange.upper()}
        volumes:
            - /home/furkan/cryptostore:/cryptostore
        environment:
            - EXCHANGE={exchange.upper()}
            - CHANNELS={','.join(config['channels'])}
            - SYMBOLS={','.join(symbols[i:i+config['symbols_per_channel']])}
            - BACKEND={config['backend']}{kwargs_str.replace('-e ', os.linesep + '            - ')}"""

    compose_string += """
        
    redpanda-0:
        command:
        - redpanda
        - start
        - --kafka-addr internal://0.0.0.0:9092,external://0.0.0.0:19092
        # Address the broker advertises to clients that connect to the Kafka API.
        # Use the internal addresses to connect to the Redpanda brokers'
        # from inside the same Docker network.
        # Use the external addresses to connect to the Redpanda brokers'
        # from outside the Docker network.
        - --advertise-kafka-addr internal://redpanda-0:9092,external://localhost:19092
        - --pandaproxy-addr internal://0.0.0.0:8082,external://0.0.0.0:18082
        # Address the broker advertises to clients that connect to the HTTP Proxy.
        - --advertise-pandaproxy-addr internal://redpanda-0:8082,external://localhost:18082
        - --schema-registry-addr internal://0.0.0.0:8081,external://0.0.0.0:18081
        # Redpanda brokers use the RPC API to communicate with each other internally.
        - --rpc-addr redpanda-0:33145
        - --advertise-rpc-addr redpanda-0:33145
        # Mode dev-container uses well-known configuration properties for development in containers.
        - --mode dev-container
        # Tells Seastar (the framework Redpanda uses under the hood) to use 1 core on the system.
        - --smp 1
        - --default-log-level=info
        image: docker.redpanda.com/redpandadata/redpanda:v23.3.11
        container_name: redpanda-0
        volumes:
        - redpanda-0:/var/lib/redpanda/data
        ports:
        - 18081:18081
        - 18082:18082
        - 19092:19092
        - 19644:9644
    console:
        container_name: redpanda-console
        image: docker.redpanda.com/redpandadata/console:v2.4.5
        entrypoint: /bin/sh
        command: -c 'echo "$$CONSOLE_CONFIG_FILE" > /tmp/config.yml; /app/console'
        environment:
        CONFIG_FILEPATH: /tmp/config.yml
        CONSOLE_CONFIG_FILE: |
            kafka:
            brokers: ["redpanda-0:9092"]
            schemaRegistry:
                enabled: true
                urls: ["http://redpanda-0:8081"]
            redpanda:
            adminApi:
                enabled: true
                urls: ["http://redpanda-0:9644"]
        ports:
        - 8080:8080
        depends_on:
        - redpanda-0
        """

    with open("docker-compose.yml", "w") as f:
        f.write(compose_string)

if __name__ == '__main__':
    main()
