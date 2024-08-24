from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from locations.spiders.tiger_wheel_and_tyre_za import TigerWheelAndTyreZASpider


class PieCityZASpider(TigerWheelAndTyreZASpider):
    name = "pie_city_za"
    item_attributes = {"brand": "Pie City", "brand_wikidata": "Q116619195"}
    start_urls = ["https://pcsl.goreview.co.za/store-locator"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/piecity\d+\.goreview\.co\.za\/store-information\?store-locator=pcsl$"),
            callback="parse",
        )
    ]
    url_prefix = "piecity"
