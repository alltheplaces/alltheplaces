from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RougegorgeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "rougegorge_fr"
    item_attributes = {"brand": "RougeGorge", "brand_wikidata": "Q104600739"}
    allowed_domains = ["www.rougegorge.com"]
    sitemap_urls = ["https://www.rougegorge.com/fr-fr/sitemap_4-folder.xml"]
    sitemap_rules = [(r"/fr-fr/magasins/\d+/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data: dict, **kwargs):
        # Hours are parsed from the page instead
        ld_data.pop("openingHours", None)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if not item.get("lat"):
            # Online partners, wholesale accounts and closed stores have no coordinates
            return
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        item["branch"] = item.pop("name").split(" - ", 1)[-1]
        item.pop("image", None)
        # The structured data cuts long street names short
        item["street_address"] = response.xpath('normalize-space(//div[@class="store-details"]//address/div[1])').get()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            # Split days look like "10:00 à 13:00 et 14:00 à 19:00"
            " ".join(response.xpath('//div[@class="store-hours"]/text()').getall()).replace(" et ", ", "),
            days=DAYS_FR,
            delimiters=DELIMITERS_FR,
            closed=CLOSED_FR,
        )
        yield item
