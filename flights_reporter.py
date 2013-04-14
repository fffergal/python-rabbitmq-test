import json

class Reporter:
    def __init__(self, details, carriers, stations):
        self.details = details
        self.carriers = carriers
        self.stations = stations
    
    def report(self, outbound, inbound, price):
        # Floating points being annoying as ever, Python 2.7 is good at
        # rounding.
        price = round(price, 2)
        if (not self.details):
            print outbound['Id'],
            if (inbound):
                print ' %s' % inbound['Id'],
            print ' %s' % price
        else:
            output = dict(outbound=self.leg_detail_dict(outbound), 
                          price=price)
            if (inbound):
                output['inbound'] = self.leg_detail_dict(inbound)
            print json.dumps(output)
    
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

