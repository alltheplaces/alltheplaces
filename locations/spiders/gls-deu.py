import scrapy
import json
import csv

class GenspiderSpider(scrapy.Spider):
    name = 'glsdeu'
    allowed_domains = ['api.gls-pakete.de']
    index = 1
    start_urls = ['https://api.gls-pakete.de/parcelshops?version=4&coordinates=50.88246,8.91596&distance=50']
    usedLongLat = []
    deList = []

    with open('../searchable_points/eu_centroids_40km_radius_country.csv', 'r') as openFile:
      results = csv.reader(openFile)
      for result in results:
          if(result[3] == 'DE'):
              data = {
                  "longitude": result[2],
                  "latitude": result[1]
              }
              deList.append(data)


    def parse(self, response):

        firstResults = json.loads(response.body)
        results = firstResults['shops']
        for result in results:
            address = result['address']
            coordinates = address['coordinates']
            longitude = coordinates['longitude']
            latitude = coordinates['latitude']
            name = address['name']
            state = 1

            if(GenspiderSpider.usedLongLat):
                for used in GenspiderSpider.usedLongLat:
                    if(used['longitute'] == float(longitude) and used['latitude'] == float(latitude)):
                        state = 0

            if(state == 1):
                dictToAdd = {
                    "longitute": float(longitude),
                    "latitude": float(latitude)
                }

                GenspiderSpider.usedLongLat.append(dictToAdd)

                yield {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(longitude), float(latitude)]
                    },
                    "properties": {
                        "name": name
                    }
                }


        next_link = 'https://api.gls-pakete.de/parcelshops?version=4&coordinates=' + str(format(float(GenspiderSpider.deList[GenspiderSpider.index]['latitude']), '.5f')) + ',' + str(format(float(GenspiderSpider.deList[GenspiderSpider.index]['longitude']), '.5f')) + '&distance=50'

        if GenspiderSpider.index < 16477:
            GenspiderSpider.index += 1
            print(GenspiderSpider.index)
            yield response.follow(next_link, callback=self.parse)
