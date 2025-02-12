from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PioneerCASpider(SitemapSpider, StructuredDataSpider):
    name = "pioneer_ca"
    item_attributes = {"brand": "Pioneer", "brand_wikidata": "Q7196684"}
    sitemap_urls = ["https://www.pioneer.ca/sitemap-stores.xml"]
    sitemap_rules = [(r"/en/find-station/[^/]+/[^/]+/$", "parse")]
    wanted_types = ["GasStation"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None

        services = response.xpath('//h4[@class="station__icons-list-icon-title"]/text()').getall()
        apply_yes_no(Extras.ATM, item, "ATM" in services)
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in services)
        apply_yes_no(Extras.SELF_CHECKOUT, item, "Pay at pump" in services)

        if "Open 24h" in services:
            item["opening_hours"] = "24/7"

        apply_category(Categories.FUEL_STATION, item)

        yield item
