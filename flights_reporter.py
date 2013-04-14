import json

class Reporter:
    rabbitmq_queue = 'flights'
    
    def __init__(self, carriers, stations, details=False, 
            rabbitmq=False):
        self.carriers = carriers
        self.stations = stations
        self.details = details
        self.rabbitmq = rabbitmq
        if (self.rabbitmq):
            # Apparent Python caches modules so this isn't so bad
            import pika
            connection_params = pika.ConnectionParameters(
                host='localhost')
            connection = pika.BlockingConnection(connection_params)
            self.channel = connection.channel()
            self.channel.queue_declare(queue=self.rabbitmq_queue)
    
    def report(self, outbound, inbound, price):
        # Floating points being annoying as ever, Python 2.7 is good at
        # rounding.
        price = round(price, 2)
        output = ''
        if (not self.details):
            output += outbound['Id']
            if (inbound):
                output += ' %s' % inbound['Id']
            output += ' %s' % price
        else:
            output_dict = dict(outbound=self.leg_detail_dict(outbound), 
                               price=price)
            if (inbound):
                output_dict['inbound'] = self.leg_detail_dict(inbound)
            output += json.dumps(output_dict)
        self.send(output)
    
    def send(self, output):
        if (not self.rabbitmq):
            print output
        else:
            output = output.encode('utf8')
            self.channel.basic_publish(
                exchange='', routing_key=self.rabbitmq_queue, 
                body=output)
    
    def leg_detail_dict(self, leg):
        output = {}
        output['depart'] = leg['DepartureDateTime']
        output['arrive'] = leg['ArrivalDateTime']
        output['carriers'] = []
        for carrier in leg['MarketingCarrierIds']:
            output['carriers'].append(self.carriers[carrier]['Name'])
        # Some results have StopsCount > 0 but still no StopIds, weird
        if (leg['StopsCount'] and 'StopIds' in leg):
            output['stops'] = []
            for stop in leg['StopIds']:
                output['stops'].append(self.stations[stop]['Name'])
        return output

