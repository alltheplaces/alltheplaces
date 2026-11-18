from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Assu2000FRSpider(SitemapSpider, StructuredDataSpider):
    name = "assu_2000_fr"
    item_attributes = {"brand": "Assu 2000", "brand_wikidata": "Q126596934"}
    allowed_domains = ["agence.assu2000.fr"]
    sitemap_urls = ["https://agence.assu2000.fr/sitemap.xml"]
    sitemap_rules = [(r"/assu-?2000-[^/]+-\d+$", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ASSU 2000 ").removeprefix("ASSU2000 ")
        item["ref"] = response.url.split("-")[-1]
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
