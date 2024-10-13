import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.items import Feature


class CycleSpotJPSpider(CrawlSpider):
    name = "cycle_spot_jp"
    item_attributes = {"brand": "サイクルスポット", "brand_wikidata": "Q93620124", "extras": Categories.SHOP_BICYCLE.value}
    allowed_domains = ["www.cyclespot.net"]
    start_urls = ["https://www.cyclespot.net/shops-list"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.cyclespot\.net\/[^/]+\/?$", restrict_xpaths='//div[@id="prefecture"]//a'
            ),
            callback=None,
            follow=True,
        ),
        Rule(LinkExtractor(allow=r"^https:\/\/www\.cyclespot\.net\/shops\/[^/]+\/?$"), callback="parse", follow=False),
    ]

    def parse(self, response):
        if not response.xpath('//div[@class="cs_wpsl_shopinfomation"]'):
            # Some location pages are blank and need skipping
            return
        properties = {
            "ref": response.url.split("/(?!$)")[-1],
            "name": response.xpath('//div[@class="cs_wpsl_shopinfomation"]/p[1]/b/text()').get().strip(),
            "addr_full": re.sub(
                r"\s+", " ", response.xpath('//div[@class="cs_wpsl_shopinfomation"]/p[2]/text()').get().strip()
            ),
            "phone": re.search(
                r"([\d\-.]{8,})",
                " ".join(
                    response.xpath(
                        '//div[@class="cs_wpsl_shopinfomation"]/p/i[contains(@class, "fa-phone")]/parent::p//text()'
                    ).getall()
                ),
            ).group(1),
            "website": response.url,
        }
        extract_google_position(properties, response)

        yield Feature(**properties)
