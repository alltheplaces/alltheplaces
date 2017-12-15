import json
import re
import scrapy
from locations.items import GeojsonPointItem
class CoopFoodSpider(scrapy.Spider):
    name = "coopfood"
    allowed_domains = ["api.coop.co.uk"]
    download_delay = 0.5
    state = True
    def start_requests(self):
        for page in range(1000):
            if(self.state==False):
                break
            else:
                url = 'https://api.coop.co.uk/locationservices/finder/food/?location=54.9966124%2C-7.308574799999974&distance=30000000000&always_one=true&format=json&page='+str(page)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse
                )

    def parse(self, response):
      try:
        data = json.loads(response.body_as_unicode())
        if(data['next']==None):
            self.state = False

        for store in data['results']:
                open_hours = store['opening_hours']
                clean_hours = ''
                for  time in open_hours:
                   if(time['opens']!=None and time['closes'] != None):
                    clean_hours = clean_hours +time['name'][:2] +' '+time['opens']+'-'+time['closes']+' ; '
                properties = {
                    "ref": store['url'],
                    "name": store['name'] ,
                    "opening_hours": clean_hours,
                    "website": "https://finder.coop.co.uk"+store['url'],
                    "addr_full":  store['street_address']+" "+store['street_address2']+" "+store['street_address3'],
                    "city": store['town'],
                    "postcode": store['postcode'],
                    "country": 'United Kingdom',
                    "lon": float( store['position']['x']),
                    "lat": float(store['position']['y']),
                    "phone":store["phone"],
                }
                yield GeojsonPointItem(**properties)
      except ValueError:
          self.state =  False
          return