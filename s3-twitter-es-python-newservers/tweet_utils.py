#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2015

@author: mentzera
'''
import re
from textblob import TextBlob
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geojson import Point

class Sentiments:
    POSITIVE = 'Positive'
    NEGATIVE = 'Negative'
    NEUTRAL = 'Neutral'
    CONFUSED = 'Confused'
    
id_field = 'id_str'
is_customer = 'Yes'
is_not_customer = 'No'

emoticons = {Sentiments.POSITIVE:'😀|😁|😂|😃|😄|😅|😆|😇|😈|😉|😊|😋|😌|😍|😎|😏|😗|😘|😙|😚|😛|😜|😝|😸|😹|😺|😻|😼|😽',
             Sentiments.NEGATIVE : '😒|😓|😔|😖|😞|😟|😠|😡|😢|😣|😤|😥|😦|😧|😨|😩|😪|😫|😬|😭|😾|😿|😰|😱|🙀',
             Sentiments.NEUTRAL : '😐|😑|😳|😮|😯|😶|😴|😵|😲',
             Sentiments.CONFUSED: '😕'
             }

tweet_mapping = {'properties': 
                    {'timestamp_ms': {
                                  'type': 'date'
                                  },
                     'text': {
                                  'type': 'string'
                              },
                     'coordinates': {
                          'properties': {
                             'coordinates': {
                                'type': 'geo_point'
                             },
                             'type': {
                                'type': 'string',
                                'index' : 'not_analyzed'
                            }
                          }
                     },
                     'user': {
                          'properties': {
                             'id': {
                                'type': 'long'
                             },
                             'name': {
                                'type': 'string',
                                 "index": "not_analyzed"
                            }
                          }
                     },
                     'sentiments': {
                                  'type': 'string',
                                  'index' : 'not_analyzed'
                              },
                     'isCustomer': {
                                   'type': 'string',
                                   'index': 'not_analyzed'
                              }
                    }
                 }

def _sentiment_analysis(tweet):
    tweet['emoticons'] = []
    tweet['sentiments'] = []
    _sentiment_analysis_by_emoticons(tweet)
    if len(tweet['sentiments']) == 0:
        _sentiment_analysis_by_text(tweet)


def _sentiment_analysis_by_emoticons(tweet):
    for sentiment, emoticons_icons in emoticons.iteritems():
        matched_emoticons = re.findall(emoticons_icons, tweet['text'].encode('utf-8'))
        if len(matched_emoticons) > 0:
            tweet['emoticons'].extend(matched_emoticons)
            tweet['sentiments'].append(sentiment)
    
    if Sentiments.POSITIVE in tweet['sentiments'] and Sentiments.NEGATIVE in tweet['sentiments']:
        tweet['sentiments'] = Sentiments.CONFUSED
    elif Sentiments.POSITIVE in tweet['sentiments']:
        tweet['sentiments'] = Sentiments.POSITIVE
    elif Sentiments.NEGATIVE in tweet['sentiments']:
        tweet['sentiments'] = Sentiments.NEGATIVE

def _sentiment_analysis_by_text(tweet):
    blob = TextBlob(tweet['text'].decode('ascii', errors="replace"))
    sentiment_polarity = blob.sentiment.polarity
    if sentiment_polarity < 0:
        sentiment = Sentiments.NEGATIVE
    elif sentiment_polarity <= 0.2:
                sentiment = Sentiments.NEUTRAL
    else:
        sentiment = Sentiments.POSITIVE
    tweet['sentiments'] = sentiment

def _check_isCustomer(tweet,handlelist):
    if int(tweet['user']['id']) in handlelist['twitterIds']:
        tweet['isCustomer'] = is_customer
    else:
        tweet['isCustomer'] = is_not_customer


def get_tweet(doc,handlelist):
    tweet = {}
    tweet[id_field] = doc[id_field]
    tweet['hashtags'] = map(lambda x: x['text'],doc['entities']['hashtags'])
    geocoder = doc['coordinates']

    if geocoder is not None:
        tweet['coordinates'] = geocoder
    elif doc['place'] is not None:
        try:
            country = doc['place']['country']
            fulladdress = doc['place']['full_name']
            geolocator = Nominatim(country_bias=country, timeout=3)
            location = geolocator.geocode(fulladdress)
            tweet['coordinates'] = Point((location.longitude, location.latitude))

        except GeocoderTimedOut as e:
            print("Error: geocode failed on input %s with message %s" % (fulladdress, e.message))

    else:
        tweet['coordinates'] = Point((149.128894,-35.2819366))  # default to Canberra if geocode not avaiable

    tweet['timestamp_ms'] = doc['timestamp_ms'] 
    tweet['text'] = doc['text']
    tweet['user'] = {'id': doc['user']['id'], 'name': doc['user']['name']}
    tweet['mentions'] = re.findall(r'@\w*', doc['text'])
    _sentiment_analysis(tweet)
    _check_isCustomer(tweet,handlelist)
    return tweet