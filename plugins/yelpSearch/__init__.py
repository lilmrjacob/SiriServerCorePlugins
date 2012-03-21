#!/usr/bin/python
# -*- coding: utf-8 -*-
# by Alex 'apexad' Martin
# help from: muhkuh0815 & gaVRos
# multilanguage support by cytec

import re
import urllib2, urllib
import json
import random

from plugin import *

from siriObjects.baseObjects import AceObject, ClientBoundCommand
from siriObjects.systemObjects import GetRequestOrigin,Location
from siriObjects.uiObjects import AddViews, AssistantUtteranceView
from siriObjects.localsearchObjects import Business, MapItem, MapItemSnippet, Rating

yelp_api_key = APIKeyForAPI("yelp")

res = {
     'searchString': {
          'en-US': u'(find|show|where).* (nearest|nearby|closest) (.*)',
          'en-GB': u'(find|show|where).* (nearest|nearby|closest) (.*)',
          'de-DE': u'(finde|zeige|wo).* (nächste|nächstes|nächstes|nahe|in der nähe|in der umgebung) (.*)'
     },
     'searching': {
          'en-US': u'Searching...',
          'en-GB': u'Searching...',
          'de-DE': u'Suche...'
     },
     'results': {
          'en-US': u'I found {0} {1} results... {2} of them are fairly close to you:',
          'en-GB': u'I found {0} {1} results... {2} of them are fairly close to you:',
          'de-DE': u'Ich habe {0} {1} Ergebnisse gefunden... {2} davon ganz in deiner N\xe4he:'
     },
     'no-results': {
          'en-US': u'I\'m sorry but I did not find any results for {0} near you!',
          'en-GB': u'I\'m sorry but I did not find any results for {0} near you!',
          'de-DE': u'Es tut mir leid aber ich konnte keine Ergebnisse für {0} in deiner Nähe finden'
     }
}

helpPhrases = {
     'en-US': u'find nearest xy, show closest xy',
     'en-GB': u'find nearest xy, show closest xy',
     'de-DE': u'finde nächstes xy, finde in der umgebung xy'
}


class yelpSearch(Plugin):


     @register('en-US', res['searchString']['en-US'])
     @register('en-GB', res['searchString']['en-GB'])
     @register('de-DE', res['searchString']['de-DE'])
     def yelp_search(self, speech, language, regex):
          self.say(res['searching'][language],' ')
          mapGetLocation = self.getCurrentLocation()
          latitude = mapGetLocation.latitude
          longitude = mapGetLocation.longitude
          Title = regex.group(regex.lastindex).strip()
          Query = urllib.quote_plus(str(Title.encode("utf-8")))
          random_results = random.randint(2,15)
          yelpurl = "http://api.yelp.com/business_review_search?term={0}&lat={1}&long={2}&radius=5&limit=20&ywsid={3}".format(str(Query),latitude,longitude,str(yelp_api_key))
          try:
               jsonString = urllib2.urlopen(yelpurl, timeout=20).read()
          except:
               jsonString = None
          if jsonString != None:
               response = json.loads(jsonString)
               if (response['message']['text'] == 'OK') and (len(response['businesses'])):
                    response['businesses'] = sorted(response['businesses'], key=lambda business: float(business['distance']))
                    yelp_results = []
                    for result in response['businesses']:
                         rating = Rating(value=result['avg_rating'], providerId='YELP', count=result['review_count'])
                         details = Business(totalNumberOfReviews=result['review_count'],name=result['name'],rating=rating)
                         if (len(yelp_results) < random_results):
                              mapitem = MapItem(label=result['name'], street=result['address1'], stateCode=result['state_code'], postalCode=result['zip'],latitude=result['latitude'], longitude=result['longitude'])
                              mapitem.detail = details
                              yelp_results.append(mapitem)
                         else:
                              break
                    mapsnippet = MapItemSnippet(items=yelp_results)
                    count_min = min(len(response['businesses']),random_results)
                    count_max = max(len(response['businesses']),random_results)
                    view = AddViews(self.refId, dialogPhase="Completion")
                    responseText = res['results'][language].format(str(count_max), str(Title), str(count_min))
                    view.views = [AssistantUtteranceView(speakableText=responseText, dialogIdentifier="yelpSearchMap"), mapsnippet]
                    self.sendRequestWithoutAnswer(view)
               else:
                    self.say(res['no-results'][language].format(str(Title)))
          else:
               self.say(res['no-results'][language].format(str(Title)))
          self.complete_request()
