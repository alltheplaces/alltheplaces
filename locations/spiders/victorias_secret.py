from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VictoriasSecretSpider(SitemapSpider, StructuredDataSpider):
    name = "victorias_secret"
    item_attributes = {"brand": "Victoria's Secret", "brand_wikidata": "Q332477"}
    allowed_domains = ["stores.victoriassecret.com"]
    sitemap_urls = ["https://stores.victoriassecret.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z-]+-[a-z]?\d+\.html$", "parse")]
    wanted_types = ["ClothingStore"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Delist stores that are present in the sitemap but serves their parent city or region page.
        if not (card := response.xpath('//div[contains(@class, "location-card-wrap")]')):
            return

        item["ref"] = card.xpath(".//*[@data-fid]/@data-fid").get()
        item["name"] = None
        branch = card.xpath("./preceding-sibling::h2[1]/text()").get()
        if not branch.startswith("Victoria's Secret"):
            item["branch"] = branch.removesuffix(" VS")

        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes([Clothes.UNDERWEAR, Clothes.WOMEN], item)

        yield item
