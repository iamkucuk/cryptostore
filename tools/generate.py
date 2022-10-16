import yaml
import os
from cryptofeed.exchanges import EXCHANGE_MAP


def main():
    with open("tools/config.yaml", 'r') as fp:
        config = yaml.safe_load(fp)

    kwargs = config.copy()
    [kwargs.pop(key) for key in ('backend', 'channels', 'exchanges', 'symbols', 'symbols_per_channel')]
    kwargs_str = '-e ' + ' -e '.join([f"{key.upper()}='{value}'" for key, value in kwargs.items()])

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
            - CHANNELS='{','.join(config['channels'])}'
            - SYMBOLS={','.join(symbols[i:i+config['symbols_per_channel']])}
            - BACKEND={config['backend']}{kwargs_str.replace('-e ', os.linesep + '            - ')}"""

    # compose_string += """
        
    # redpanda:
    #     command:
    #         - redpanda
    #         - start
    #         - --smp 1
    #         - --overprovisioned
    #         - --node-id 0
    #         - --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092
    #         - --advertise-kafka-addr PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092
    #     image: docker.vectorized.io/vectorized/redpanda:v21.11.15
    #     container_name: redpanda
    #     hostname: redpanda
    #     ports:
    #         - "9092:9092"
    #         - "29092:29092"
    #     """

    with open("docker-compose.yml", "w") as f:
        f.write(compose_string)

if __name__ == '__main__':
    main()