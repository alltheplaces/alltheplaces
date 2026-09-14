from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TorchysTacosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "torchys_tacos_us"
    item_attributes = {"brand": "Torchy's Tacos", "brand_wikidata": "Q106769573"}
    sitemap_urls = ["https://torchystacos.com/sitemap.xml"]
    # Each location has a single public page, its online-ordering page.
    sitemap_rules = [(r"^https://torchystacos\.com/([^/]+)/order$", "parse_sd")]
    wanted_types = ["Restaurant"]
    # The site's twitter:site meta tag contains "Torchy's Tacos", not a handle.
    search_for_twitter = False
    # og:image/twitter:image are the same generic brand logo on every page, not a store photo.
    search_for_image = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # JSON-LD "name" is the location name only, e.g. "Kyle" / "88th & Wads".
        item["branch"] = item.pop("name")
        source_url = next(iter(response.meta.get("redirect_urls", ())), response.url)
        item["ref"] = source_url.removesuffix("/order").rsplit("/", 1)[-1]
        apply_category(Categories.FAST_FOOD, item)
        yield item
