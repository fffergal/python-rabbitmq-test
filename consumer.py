#!/usr/bin/env python

import argparse
import pika

arg_parser = argparse.ArgumentParser(description='Consume messages.')
arg_parser.add_argument('--queue', default='flights')
args = arg_parser.parse_args()

connection_params = pika.ConnectionParameters(host='localhost')
connection = pika.BlockingConnection(connection_params);
channel = connection.channel()
channel.queue_declare(queue=args.queue)

def consume_callback(ch, method, properties, body):
    print body
channel.basic_consume(consume_callback, queue=args.queue, no_ack=True)
channel.start_consuming()

