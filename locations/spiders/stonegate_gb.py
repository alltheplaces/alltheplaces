from urllib.parse import urlparse

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.spiders.morrisons_gb import set_operator
from locations.structured_data_spider import StructuredDataSpider


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
        "www.feverbars.co.uk": {"brand": "Fever"},
        "www.walkaboutbars.co.uk": {"brand": "Walkabout", "brand_wikidata": "Q7962149"},
        "www.beatone.co.uk": {"brand": "Be At One", "brand_wikidata": "Q110016786"},
        "www.popworldparty.co.uk": {"brand": "Popworld"},
        "www.slugandlettuce.co.uk": {"brand": "Slug & Lettuce", "brand_wikidata": "Q7542224"},
        "www.crafted-social.co.uk": {"brand": "Crafted Social"},
        "www.greatukpubs.co.uk": {"brand": "Great UK Pubs"},
        "www.craftunionpubs.com": {"brand": "Craft Union"},
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        set_operator(self.STONEGATE, item)

        if brand := self.brands.get(urlparse(response.url).netloc):
            item.update(brand)
        else:
            apply_category(Categories.PUB, item)

        yield item
