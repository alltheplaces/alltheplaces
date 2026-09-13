from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class OzoneBGSpider(CrawlSpider, StructuredDataSpider):
    name = "ozone_bg"
    item_attributes = {"brand": "Ozone.bg", "brand_wikidata": "Q120717332"}
    # CI's datacenter IP gets a Cloudflare 403 even though the site has no
    # challenge/fingerprint check locally (plain curl/Scrapy both work
    # unproxied) — an IP-reputation block, which requires_proxy fixes since
    # this is a plain (non-browser) spider.
    requires_proxy = "BG"
    start_urls = ["https://www.ozone.bg/our-shops/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https://www\.ozone\.bg/shop-[a-z0-9-]+/$"),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # "magazin-ozone-pro" (excluded via the shop- URL pattern above) carries stale
        # structured data for an unrelated business ("ФотоПавилион"), not Ozone itself.
        item["branch"] = item.pop("name", "").removeprefix("Магазин Ozone ").strip()
        item["name"] = self.item_attributes["brand"]

        apply_category(Categories.SHOP_GAMES, item)

        yield item
