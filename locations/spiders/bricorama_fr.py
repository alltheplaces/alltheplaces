import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

STORE_URL_RE = re.compile(r"/magasin/[^/]+/(\d+)$")


class BricoramaFRSpider(CrawlSpider, StructuredDataSpider):
    name = "bricorama_fr"
    item_attributes = {"brand": "Bricorama", "brand_wikidata": "Q2925146"}
    start_urls = ["https://www.bricorama.fr/magasins?device=mobile"]
    rules = [Rule(LinkExtractor(r"/magasin/[^/]+/(\d+)$"), "parse")]
    wanted_types = ["HomeAndConstructionBusiness"]
    # Site now blocks plain requests with a Cloudflare 403 on every page, including robots.txt.
    requires_proxy = "FR"

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data["openingHoursSpecification"] = None  # Malformed and out of sync with HTML

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Some links redirect to the generic "/magasins" store locator
        # (a delisted store) or to a rebranded store on the sibling
        # Bricomarché site (same corporate group, shared JSON-LD
        # template), which still carries a stray LocalBusiness block.
        # Only keep items that landed on a genuine store URL.
        match = STORE_URL_RE.search(response.url)
        if not match:
            return

        # The JSON-LD "@id"/name-derived ref is not guaranteed unique
        # across stores; use the numeric store code from the URL instead.
        item["ref"] = match.group(1)

        item["branch"] = item.pop("name").removeprefix("Bricorama ")
        if postcode := item.get("postcode"):
            item["postcode"] = str(postcode)
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
