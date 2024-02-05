import json
from json import JSONDecodeError

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.spiders.century_21 import Century21Spider


class Century21FRSpider(CrawlSpider):
    name = "century_21_fr"
    item_attributes = Century21Spider.item_attributes
    start_urls = ["https://www.century21.fr/trouver_agence/"]
    rules = [Rule(LinkExtractor("trouver_agence/d-"), callback="parse")]

    def parse(self, response, **kwargs):
        try:
            data = response.xpath("//@data-agencies").get()
            locations = json.loads(data)
        except JSONDecodeError:
            self.logger.error("Invalid json found on {}".format(response.url))
            return
        for location in locations:
            yield Feature(
                ref=location["ref_agence"],
                lat=location["lat"],
                lon=location["lng"],
                name=location["nom"],
                street_address=location["address"],
                postcode=location["code_postal"],
                city=location["ville"],
                country="FR",
                phone=location["tel"],
                website=response.urljoin(location["absolute_url"]),
            )
