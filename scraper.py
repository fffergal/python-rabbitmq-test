#!/usr/bin/env python

import urllib
import re
import xml.dom.minidom
import pika

connection_params = pika.ConnectionParameters(host='localhost')
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
channel.queue_declare(queue='blogs')

def send_message(text):
	channel.basic_publish(exchange='', routing_key='blogs', body=text);

f = urllib.urlopen('http://www.skyscanner.net/blogs')
page_string = f.read()
# I want to try out the XML parser, so lets make it proper XML
page_string = page_string.replace('&', '&amp;')
# Remove all scripts, pretty brutal but easier than making CDATA
page_string = re.sub(r'<script.*?>.*?</script>', '', page_string, 
	count=0, flags=re.DOTALL)
# Fix that img tag
page_string = re.sub(r'<img([^>]*[^/])>', r'<img\1 />', page_string)

document = xml.dom.minidom.parseString(page_string)

divs = document.getElementsByTagName('div');
date_divs = [];
for div in divs:
	div_class = div.getAttribute('class')
	if div_class == 'item-list': date_divs.append(div)

for date_div in date_divs:
	h3 = date_div.getElementsByTagName('h3')[0]
	current_date = h3.firstChild.nodeValue
	lis = date_div.getElementsByTagName('li')
	for li in lis:
		for a in li.getElementsByTagName('a'):
			if a.getElementsByTagName('img'): continue
			title = a.firstChild.nodeValue
			message = current_date + ' - ' + title
			message = message.strip()
			# basic_publish is pretty finicky about unicode 
			message = message.encode('utf-8')
			send_message(message);
			break

