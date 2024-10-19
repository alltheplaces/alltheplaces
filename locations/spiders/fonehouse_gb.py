import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FonehouseGBSpider(CrawlSpider, StructuredDataSpider):
    name = "fonehouse_gb"
    item_attributes = {
        "brand": "fonehouse",
        "brand_wikidata": "Q130535827",
        "country": "GB",
    }

    start_urls = ["https://www.fonehouse.co.uk/store-finder"]
    rules = [Rule(LinkExtractor(allow=r"/stores/([^/]+)$"), callback="parse")]
    wanted_types = ["LocalBusiness"]

    def parse(self, response):
        ldjson = response.xpath('//script[@type="application/ld+json"]/text()[contains(.,\'"LocalBusiness"\')]').get()
        data = json.decoder.JSONDecoder(strict=False).raw_decode(ldjson, ldjson.index("{"))[0]
        properties = {
            "ref": response.url,
            "name": data.get("name"),
            "phone": data.get("telephone"),
            "street_address": data.get("address", {}).get("streetAddress"),
            "city": data.get("address", {}).get("addressLocality"),
            "state": data.get("address", {}).get("addressRegion"),
            "country": data.get("address", {}).get("addressCountry"),
            "geometry": data.get("geometry", {}).get("geo"),
            "website": response.url,
            # "opening_hours": oh.as_opening_hours(),
        }
        item = Feature(**properties)
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
