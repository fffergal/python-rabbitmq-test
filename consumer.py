#!/usr/bin/env python

import pika

connection_params = pika.ConnectionParameters(host='localhost')
connection = pika.BlockingConnection(connection_params);
channel = connection.channel()
channel.queue_declare(queue='blogs')

def consume_callback(ch, method, properties, body):
	print body
channel.basic_consume(consume_callback, queue='blogs', no_ack=True)
channel.start_consuming()

