import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class MarcsSpider(CrawlSpider):
    name = "marcs"
    item_attributes = {"brand": "Marc's", "brand_wikidata": "Q17080259"}
    allowed_domains = ["marcs.com"]
    start_urls = ["https://www.marcs.com/store-finder"]
    rules = [Rule(LinkExtractor(allow="store-finder/"), callback="parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):

        ldjson = response.xpath('//script[@type="application/ld+json"]/text()[contains(.,\'"Store"\')]').get()
        data = json.decoder.JSONDecoder().raw_decode(ldjson, ldjson.index("{"))[0]

        lmjson = response.xpath('//script[@type="text/javascript"]/text()[contains(.,"initMap()")]').get()

        openHourFiltered = [row for row in data.get("openingHours") if ":" in row]
        oh = OpeningHours()
        oh.from_linked_data({"openingHours": openHourFiltered})

        properties = {
            "ref": response.url,
            "name": data.get("name"),
            "phone": data.get("telephone"),
            "street_address": data.get("address", {}).get("streetAddress"),
            "city": data.get("address", {}).get("addressLocality"),
            "state": data.get("address", {}).get("addressRegion"),
            "country": data.get("address", {}).get("addressCountry"),
            "lat": self.find_between(lmjson, "lat = '", "';").strip(),
            "lon": self.find_between(lmjson, "lng = '", "';").strip(),
            "website": response.url,
            "opening_hours": oh.as_opening_hours(),
        }

        yield GeojsonPointItem(**properties)
