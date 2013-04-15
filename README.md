A little Python scraping and RabbitMQ test
==========================================

A task for Skyscanner's interview.

How to use
----------

`./flights_scraper.py --help` for details on how to use the scraper.

Notes on RabbitMQ
-----------------

The RabbitMQ functionality is only configured and tested for the 
default RabbitMQ server running on the same machine.

If using the `--rabbitmq` option the **pika** Python module needs to be 
available.

Here's the basics of a simple test with RabbitMQ:

1. Start a RabbitMQ server on locahost, probably `rabbitmq-server` 
   with the right user priveledges.
2. `./consumer.py` which will keep running.
3. Use `./flights_scraper.py` with the `--rabbitmq` argument.
4. Check the consumer.py console for messsages!

