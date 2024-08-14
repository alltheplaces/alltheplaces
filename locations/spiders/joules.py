import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JoulesSpider(SitemapSpider, StructuredDataSpider):
    name = "joules"
    item_attributes = {"brand": "Joules", "brand_wikidata": "Q25351738"}
    start_urls = [
        "https://www.joules.com/storelocator/data/stores"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["BR"]
            item["lat"] = location["LT"]
            item["lon"] = location["LN"]
            item["branch"] = location["NA"]
            name=location["NA"].join(s.split()).lower()+"/"+location["BR"]
            item["website"] = urljoin("https://www.joules.com/storelocator/", name)
            yield item
