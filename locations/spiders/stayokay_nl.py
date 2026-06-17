from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StayokayNLSpider(SitemapSpider, StructuredDataSpider):
    name = "stayokay_nl"
    item_attributes = {"brand": "Stayokay", "brand_wikidata": "Q732984", "country": "NL"}
    sitemap_urls = ["https://www.stayokay.com/sitemaps/en.xml"]
    sitemap_rules = [(r"/en/hostel/[^/]+$", "parse_sd")]
    wanted_types = ["Hostel"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name", None)
        # Address fields are at top-level in the microdata (not nested in PostalAddress)
        if not item.get("street_address") and ld_data.get("streetAddress"):
            item["street_address"] = ld_data["streetAddress"].strip().rstrip(",").strip()
        if not item.get("city") and ld_data.get("addressLocality"):
            item["city"] = ld_data["addressLocality"]
        if not item.get("postcode") and ld_data.get("postalCode"):
            item["postcode"] = ld_data["postalCode"]
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
