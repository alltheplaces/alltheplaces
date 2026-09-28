from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Location pages come from the locator subdomain's page sitemap, which also
# lists the state and city index pages, so only the three level paths are
# followed.
#
# Each page carries a schema.org LocalBusiness record with address,
# coordinates, phone and hours. Its name is the brand rather than the branch,
# so the branch comes from the city.
#
# The hours carry seconds ("07:30:00"), so the spider sets time_format
# accordingly.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class TireBarnUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tire_barn_us"
    item_attributes = {"brand": "Tire Barn Warehouse"}
    allowed_domains = ["locations.tirebarn.com"]
    sitemap_urls = ["https://locations.tirebarn.com/sitemap_index.xml"]
    sitemap_rules = [(r"^https://locations\.tirebarn\.com/[a-z]{2}/[^/]+/([^/]+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    time_format = "%H:%M:%S"
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.replace("https://locations.tirebarn.com/", "")
        item["name"] = None
        item["branch"] = item.get("city")
        item["website"] = response.url

        apply_category(Categories.SHOP_TYRES, item)

        yield item
