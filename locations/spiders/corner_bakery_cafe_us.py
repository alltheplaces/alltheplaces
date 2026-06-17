from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CornerBakeryCafeUSSpider(CrawlSpider, StructuredDataSpider):
    name = "corner_bakery_cafe_us"
    item_attributes = {"brand": "Corner Bakery", "brand_wikidata": "Q5171598"}
    allowed_domains = ["cornerbakerycafe.com"]
    start_urls = ["https://cornerbakerycafe.com/locations/all"]
    rules = [Rule(LinkExtractor(allow=r"/location/[-\w]+/?$"), callback="parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url
        item["branch"] = item.pop("name", "")
        # Address fields are flat in microdata (not nested under PostalAddress)
        item["street_address"] = ld_data.get("streetAddress")
        item["city"] = ld_data.get("addressLocality")
        item["state"] = ld_data.get("addressRegion")
        item["postcode"] = ld_data.get("postalCode")
        apply_category(Categories.CAFE, item)
        yield item
