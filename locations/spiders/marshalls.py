import scrapy
import json
from locations.items import GeojsonPointItem

class MarshallsSpider(scrapy.Spider):

    name = "marshalls"
    allowed_domains = ["mktsvc.tjx.com"]

    def start_requests(self):
        urls = [
                'https://mktsvc.tjx.com/storelocator/GetSearchResultsByState',
            ]
        headers = {'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
                   'Origin': 'https://www.marshallsonline.com',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept': 'application/json, text/plain, */*',
                   'Referer': 'https://www.marshallsonline.com/store-finder/by-state',
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'

                   }
        formdata = {'chain': '10', 'lang':'en', 'state':'CA'}

        for url in urls:
            yield scrapy.http.FormRequest(url=url, method='POST', formdata=formdata, headers=headers, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
