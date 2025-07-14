import html
import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class BestWesternSpider(scrapy.spiders.SitemapSpider):
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
        "SUH": ("Sure Hotel", "Q135246620"),
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
    sitemap_rules = [(r"/en_US/book/[-\w]+/[-\w]+/propertyCode\.\d+\.html$", "parse_hotel")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}
    download_delay = 4
    requires_proxy = True

    def parse_hotel(self, response):
        hotel_details = response.xpath('//div[@id="hotel-details-info"]/@data-hoteldetails').get()

        if not hotel_details:
            return

        hotel = json.loads(html.unescape(hotel_details))
        summary = hotel["summary"]
        brand = self.BRANDS_MAPPING.get(summary["resortCategory"])
        if not brand:
            self.crawler.stats.inc_value(f"{self.name}/unmapped_brand/{summary['resortCategory']}")
            brand = (None, None)
        item = DictParser.parse(summary)
        item["brand"], item["brand_wikidata"] = brand
        item["street_address"] = summary["address1"]
        item["website"] = response.url
        item["ref"] = summary["resort"]
        item["extras"]["fax"] = summary["faxNumber"]
        try:
            # It's a big hotel chain, worth a bit of work to get the imagery.
            image_path = hotel["imageCatalog"]["Media"][0]["ImagePath"]
            item["image"] = "https://images.bestwestern.com/bwi/brochures/{}/photos/1024/{}".format(
                summary["resort"], image_path
            )
        except IndexError:
            pass

        apply_category(Categories.HOTEL, item)

        yield item
