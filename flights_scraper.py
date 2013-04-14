#!/usr/bin/env python

import argparse
import urllib
import re
import json

arg_parser = argparse.ArgumentParser(description='Get flight info.')
arg_parser.add_argument('from_airport', help='From airport')
arg_parser.add_argument('to_airport', help='To airport')
arg_parser.add_argument('depart_date', 
                        help='Date of departure as YYMMDD')
arg_parser.add_argument('return_date', help='Return date as YYMMDD', 
                        nargs='?')
arg_parser.add_argument('--details', action='store_true', 
                        help='Show flight details as JSON')
arg_parser.add_argument('--lowest', action='store_true', 
                        help='Show lowest price at end of output. '
                        'Useful for validation by cross referencing '
                        'with Skyscanner website.')
args = arg_parser.parse_args()

session_key_url = 'http://www.skyscanner.net/flights/{}/{}/{}/'.format(
    args.from_airport, args.to_airport, args.depart_date)
if (args.return_date):
    session_key_url += '{}/'.format(args.return_date)
session_file = urllib.urlopen(session_key_url)
session_page_string = session_file.read()
m = re.search(r'"SessionKey":"([a-z0-9-]+)"', session_page_string)
session_key = m.group(1)

data_url = 'http://www.skyscanner.net/dataservices/routedate/v2.0/{}'
data_url = data_url.format(session_key)
data_file = urllib.urlopen(data_url)
data = json.load(data_file)

# A dict of incoming and outgoing legs and quotes by their ids will be 
# easiest to work with.
def dictify(things):
    output = {}
    for thing in things:
        output[thing['Id']] = thing
    return output

inbounds = dictify(data['InboundItineraryLegs'])
outbounds = dictify(data['OutboundItineraryLegs'])
quotes = dictify(data['Quotes'])
stations = dictify(data['Stations'])
carriers = dictify(data['Carriers'])

# Calculating prices will need to be done a few times
def get_price(pricing_option):
    price = 0
    # Multiple quotes means multipart booking, sum up
    for quote_id in pricing_option['QuoteIds']:
        quote = quotes[quote_id]
        price += float(quote['Price'])
    return price

def leg_detail_dict(leg):
    output = {}
    output['depart'] = leg['DepartureDateTime']
    output['arrive'] = leg['ArrivalDateTime']
    output['carriers'] = []
    global carriers
    for carrier in leg['MarketingCarrierIds']:
        output['carriers'].append(carriers[carrier]['Name'])
    # Some results have StopsCount > 0 but still no StopIds, weird
    if (leg['StopsCount'] and 'StopIds' in leg):
        output['stops'] = []
        global stations
        for stop in leg['StopIds']:
            output['stops'].append(stations[stop]['Name'])
    return output

# Figuring if it's the min price can be done a lot
min_price = None
def test_min_price(candidate):
    global min_price
    if (not min_price or candidate < min_price):
        min_price = candidate

inbound_singles = []
if (args.return_date):
    # Collect inbound singles for crossing with outbound singles
    for inbound in data['InboundItineraryLegs']:
        for pricing_option in inbound['PricingOptions']:
            if ('OpposingLegId' not in pricing_option):
                inbound_singles.append([inbound, pricing_option])

# Reporting for return flights
# Loop over outbound, match their price options with inbound
for outbound in data['OutboundItineraryLegs']:
    for pricing_option in outbound['PricingOptions']:
        # Some legs are singles and need to be cross multiplied manually
        if ('OpposingLegId' not in pricing_option and args.return_date):
            out_price = get_price(pricing_option)
            for inbound_single in inbound_singles:
                in_price = get_price(inbound_single[1])
                price = out_price + in_price
                if (args.details):
                    print json.dumps(dict(
                        outbound=leg_detail_dict(outbound),
                        inbound=leg_detail_dict(inbound),
                        price='%.2f' % price))
                else:
                    print '%s %s %s' % (outbound['Id'], 
                                        inbound_single[0]['Id'], 
                                        out_price + in_price)
                test_min_price(price)
        # Do outbound only and constrained returns
        else:
            if (args.details):
                details = {}
                details['outbound'] = leg_detail_dict(outbound)
            else:
                print outbound['Id'],
            if (args.return_date):
                inbound = inbounds[pricing_option['OpposingLegId']]
                if (args.details):
                    details['inbound'] = leg_detail_dict(inbound)
                else:
                    print ' %s' % inbound['Id'],
            price = get_price(pricing_option)
            if (args.details):
                details['price'] = '%.2f' % price
                print json.dumps(details)
            else:
                print ' %s' % price
            test_min_price(price)

if (args.lowest):
    print '%.2f %s' % (min_price, 
                       data['Query']['UserInfo']['CurrencyId'])

