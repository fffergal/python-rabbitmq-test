#!/usr/bin/env python

import argparse
import pika
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

min_price = None
if (args.return_date):
    # Reporting for return flights
    # Loop over outbound, match their price options with inbound
    # Some legs are singles and need to be cross multiplied manually
    outbound_singles = []
    for outbound in data['OutboundItineraryLegs']:
        for pricing_option in outbound['PricingOptions']:
            if ('OpposingLegId' not in pricing_option):
                outbound_singles.append([outbound, pricing_option])
                continue
            inbound = inbounds[pricing_option['OpposingLegId']]
            # Multiple quotes means multipart booking, sum up
            price = 0
            for quote_id in pricing_option['QuoteIds']:
                quote = quotes[quote_id]
                price += float(quote['Price'])
            print '{} {} {}'.format(outbound['Id'], inbound['Id'], 
                                    price)
            if (not min_price or price < min_price):
                min_price = price

    # If there are any outbound singles, cross multiply them with 
    # inbound ones.
    if (len(outbound_singles)):
        for inbound in data['InboundItineraryLegs']:
            for pricing_option in inbound['PricingOptions']:
                if ('OpposingLegId' not in pricing_option):
                    in_price = 0
                    for in_quote_id in pricing_option['QuoteIds']:
                        in_quote = quotes[in_quote_id]
                        in_price += float(in_quote['Price'])
                    for outbound_single in outbound_singles:
                        out_price = 0
                        q_ids = outbound_single[1]['QuoteIds']
                        for out_quote_id in q_ids:
                            out_quote = quotes[out_quote_id]
                            out_price += float(out_quote['Price'])
                        price = out_price + in_price
                        print '{} {} {}'.format(
                                    outbound_single[0]['Id'], 
                                    inbound['Id'], out_price + in_price)
                        if (not min_price or price < min_price):
                            min_price = price

else:
    # Handle one way journeys
    for outbound in data['OutboundItineraryLegs']:
        for pricing_option in outbound['PricingOptions']:
            price = 0
            for quote_id in pricing_option['QuoteIds']:
                quote = quotes[quote_id]
                price += float(quote['Price'])
            print '{} {}'.format(outbound['Id'], price)
            if (not min_price or price < min_price):
                min_price = price

print data['Query']['UserInfo']['CurrencyId']
print min_price
