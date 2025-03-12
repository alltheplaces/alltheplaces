import html
from urllib.parse import urlparse

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.spiders.morrisons_gb import set_operator
from locations.structured_data_spider import StructuredDataSpider


def html_decode_dict(obj: dict):
    for k, v in obj.items():
        if isinstance(v, str):
            obj[k] = html.unescape(v)
        elif isinstance(v, dict):
            html_decode_dict(v)


class StonegateGBSpider(CrawlSpider, StructuredDataSpider):
    name = "stonegate_gb"
    download_delay = 0.2
    STONEGATE = {"brand": "Stonegate", "brand_wikidata": "Q7619176"}
    start_urls = ["https://www.stonegategroup.co.uk/find-your-local/page/1/"]
    rules = [
        Rule(LinkExtractor(allow=r"/page/\d+/$")),
        Rule(LinkExtractor(restrict_xpaths='//a[contains(., "View Site")]'), callback="parse_sd"),
    ]

    brands = {
        "www.feverbars.co.uk": {"brand": "Fever", "cat": Categories.NIGHTCLUB},
        "www.walkaboutbars.co.uk": {"brand": "Walkabout", "brand_wikidata": "Q7962149", "cat": Categories.PUB},
        "www.beatone.co.uk": {"brand": "Be At One", "brand_wikidata": "Q110016786", "cat": Categories.BAR},
        "www.popworldparty.co.uk": {"brand": "Popworld", "cat": Categories.NIGHTCLUB},
        "www.slugandlettuce.co.uk": {"brand": "Slug & Lettuce", "brand_wikidata": "Q7542224"},
        "www.crafted-social.co.uk": {"brand": "Crafted Social"},
        "www.socialpubandkitchen.co.uk": {"brand": "Social Pub & Kitchen"},
        "www.pubsmiths.co.uk": {"brand": "Pubsmiths"},
        "www.greatukpubs.co.uk": {"brand": "Great UK Pubs"},
        "www.craftunionpubs.com": {"brand": "Craft Union", "brand_wikidata": "Q124956771"},
        "www.rosiesclubs.co.uk" : {"brand": "Rosies Clubs"},
        "www.craftunionpubs.com": {"brand": "Craft Union"},
        "www.heritagepubs.co.uk": {"brand": "Heritage Pubs"},
    }

    def pre_process_data(self, ld_data, **kwargs):
        html_decode_dict(ld_data)

    def post_process_item(self, item, response, ld_data, **kwargs):
        set_operator(self.STONEGATE, item)

        brand = self.brands.get(urlparse(response.url).netloc, {})

        item["brand"] = brand.get("brand")
        item["brand_wikidata"] = brand.get("brand_wikidata")
        if cat := brand.get("cat"):
            apply_category(cat, item)
        else:
            apply_category(Categories.PUB, item)

        yield item
