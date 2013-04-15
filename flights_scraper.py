#!/usr/bin/env python

import argparse
import urllib
import re
import json
import flights_reporter

# Arguments and usage documentation
arg_parser = argparse.ArgumentParser(description='Get flight info.')
arg_parser.add_argument('from_airport', help='From airport code')
arg_parser.add_argument('to_airport', help='To airport code')
arg_parser.add_argument('depart_date', 
                        help='Date of departure as YYMMDD')
arg_parser.add_argument('return_date', help='Return date as YYMMDD', 
                        nargs='?')
arg_parser.add_argument('--details', action='store_true', 
                        help='Show flight details as JSON')
arg_parser.add_argument('--rabbitmq', action='store_true', 
                        help='Report to local RabbitMQ')
arg_parser.add_argument('--lowest', action='store_true', 
                        help='Show lowest price at end of output. '
                        'Useful for validation by cross referencing '
                        'with Skyscanner website.')
args = arg_parser.parse_args()

# Get a session key for the flight into we want
# Construct a URL with the airports and dates
session_key_url = 'http://www.skyscanner.net/flights/{}/{}/{}/'.format(
    args.from_airport, args.to_airport, args.depart_date)
if (args.return_date):
    session_key_url += '{}/'.format(args.return_date)
session_file = urllib.urlopen(session_key_url)
session_page_string = session_file.read()
# Get the session key from a script embedded in the document
m = re.search(r'"SessionKey":"([a-z0-9-]+)"', session_page_string)
session_key = m.group(1)

# Use the session key to get the information in handy JSON format
data_url = 'http://www.skyscanner.net/dataservices/routedate/v2.0/{}'
data_url = data_url.format(session_key)
data_file = urllib.urlopen(data_url)
data = json.load(data_file)
# JSON is nice and simple, no more parsing required

# Now to put the data together in a clear/useful way then output it

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
carriers = dictify(data['Carriers'])
stations = dictify(data['Stations'])

# We have all we need to initialise the reporter. The reporter handles
# the various methods of output.
reporter = flights_reporter.Reporter(
    carriers, stations, details=args.details, rabbitmq=args.rabbitmq)

# Calculating prices will need to be done a few times
def get_price(pricing_option):
    price = 0
    # Multiple quotes means multipart booking, sum up
    for quote_id in pricing_option['QuoteIds']:
        quote = quotes[quote_id]
        price += float(quote['Price'])
    return price

# Figuring if it's the min price will be done a lot
min_price = None
def test_min_price(candidate):
    global min_price
    if (not min_price or candidate < min_price):
        min_price = candidate

# Collect inbound singles for crossing with outbound singles
inbound_singles = []
if (args.return_date):
    for inbound in data['InboundItineraryLegs']:
        # Each pricing option needs to be considered separately
        for pricing_option in inbound['PricingOptions']:
            # This means it's a single
            if ('OpposingLegId' not in pricing_option):
                inbound_singles.append([inbound, pricing_option])

# Loop over outbound, match their price options with inbound
for outbound in data['OutboundItineraryLegs']:
    for pricing_option in outbound['PricingOptions']:
        # Some legs are singles and need to be cross multiplied manually
        if ('OpposingLegId' not in pricing_option and args.return_date):
            out_price = get_price(pricing_option)
            for inbound_single in inbound_singles:
                in_price = get_price(inbound_single[1])
                price = out_price + in_price
                reporter.report(outbound, inbound, price)
                test_min_price(price)
        # Do outbound only and constrained returns
        else:
            inbound = None
            if (args.return_date):
                inbound = inbounds[pricing_option['OpposingLegId']]
            price = get_price(pricing_option)
            reporter.report(outbound, inbound, price)
            test_min_price(price)

if (args.lowest):
    print '%.2f %s' % (min_price, 
                       data['Query']['UserInfo']['CurrencyId'])

