from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.amai_promap import AmaiPromapSpider


class AmericanMattressUSSpider(AmaiPromapSpider):
    name = "american_mattress_us"
    start_urls = [
        "https://cdn.roseperl.com/storelocator-prod/wtb/americanmattress-1752594684.js?shop=americanmattress.myshopify.com"
    ]
    item_attributes = {"brand": "American Mattress", "brand_wikidata": "Q126896153"}

    async def start(self) -> AsyncIterator[Request]:
        # Skip fetch_js step as the site has bot protection; fetch CDN data endpoint directly
        yield Request(url=self.start_urls[0], callback=self.parse)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BED, item)
        yield item
