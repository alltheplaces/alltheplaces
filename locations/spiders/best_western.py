import json
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class BestWesternSpider(SitemapSpider, PlaywrightSpider):
    name = "best_western"

    # Brand mapping is found in HTML of
    # https://www.bestwestern.com/en_US/book/hotels-in-del-mar/best-western-premier-hotel-del-mar/propertyCode.05731.html
    # under `data-brand-list`
    BRANDS_MAPPING = {
        "ADEN": ("Aiden", "Q135247220"),
        "BEST": ("Best Western", "Q830334"),
        "BWSC": ("BW Signature Collection", "Q135249021"),
        "EXRE": ("Executive Residency", "Q135249087"),
        "GLO": ("Glo", "Q135249046"),
        "PLUS": ("Best Western Plus", "Q38623383"),
        "PRMR": ("Best Western Premier", "Q135248460"),
        "PMCL": ("BW Premier Collection", "Q135248830"),
        "SSH": ("SureStay", "Q135246628"),
        "SSSC": ("SureStay Collection", "Q135246644"),
        "SSPL": ("SureStay Plus", "Q135246640"),
        "SSES": ("SureStay Studio", "Q135246687"),
        "SUH": ("Sure Hotel", "Q135246628"),
        "SUPL": ("Sure Hotel", "Q135246628"),  # Sure Hotel Plus
        "SUSC": ("Sure Hotel Collection", "Q135246644"),
        "SUES": ("Sure Hotel Studio", "Q135246687"),
        "SADI": ("Sadie", None),
        "VIB": ("Vib", "Q135249054"),
        "WHDI": ("WorldHotels", "Q135246666"),  # WorldHotels Distinctive
        "WHEL": ("WorldHotels", "Q135246666"),  # WorldHotels Elite
        "WHLX": ("WorldHotels", "Q135246666"),  # WorldHotels Luxury
        "WHCC": ("WorldHotels", "Q135246666"),  # WorldHotels Crafted
        "HMBW": ("@HOME", "Q135249100"),
    }

    sitemap_urls = ["https://www.bestwestern.com/etc/seo/bestwestern/hotels-details.xml"]
    sitemap_rules = [(r"/en_US/book/[^/]+/[^/]+/propertyCode\.\d+\.html$", "parse")]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
    } | DEFAULT_PLAYWRIGHT_SETTINGS

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            if request.callback == self.parse:
                # Extract the hotel ID from the sitemap URL and request the summary API endpoint instead of the hotel page to avoid spider blockage.
                hotel_id = request.url.split("propertyCode.")[1].removesuffix(".html")
                yield Request(
                    url=f"https://public-services.bestwestern.com/resort/{hotel_id}/summary",
                    meta={"website": request.url},
                )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        summary = json.loads(response.xpath("//pre/text()").get())
        brand = self.BRANDS_MAPPING.get(summary["resortCategory"])
        if not brand:
            self.crawler.stats.inc_value(f"{self.name}/unmapped_brand/{summary['resortCategory']}")
            brand = (None, None)
        item = DictParser.parse(summary)
        item["brand"], item["brand_wikidata"] = brand
        item["street_address"] = summary["address1"]
        item["ref"] = summary["resort"]
        item["website"] = response.meta["website"]
        item["extras"]["fax"] = summary["faxNumber"]
        apply_category(Categories.HOTEL, item)
        yield item
