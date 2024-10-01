import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser

BRANDS = {
    "americinn": ["AmericInn", "Q4742493"],
    "baymont": ["Baymont by Wyndham", "Q4874634"],
    "caesars-rewards": ["Caesars Rewards", None],
    "days-inn": ["Days Inn", "Q1047239"],
    "dazzler": ["Dazzler", None],
    "dolce": ["Dolce Hotels and Resorts", "Q28402655"],
    "echo-suites": ["ECHO Suites", None],
    "esplendor": ["Esplendor by Wyndham", None],
    "hawthorn-extended-stay": ["Hawthorn Suites by Wyndham", "Q5685511"],
    "hojo": ["Howard Johnson", "Q5919997"],
    "laquinta": ["La Quinta by Wyndham", "Q6464734"],
    "microtel": ["Microtel Inns & Suites", "Q6840402"],
    "ramada": ["Ramada", "Q1502859"],
    "registry-collection": ["Registry Collection", None],
    "super-8": ["Super 8", "Q5364003"],
    "trademark": ["Trademark Collection by Wyndham", "Q112144846"],
    "travelodge": ["Travelodge", "Q7836087"],
    "tryp": ["TRYP", "Q6153452"],
    "vienna-house": ["Vienna House", "Q2523363"],
    "wingate": ["Wingate by Wyndham", "Q8025144"],
    "wyndham-alltra": ["Wyndham Alltra", None],
    "wyndham-garden": ["Wyndham Garden", "Q112144847"],
    "wyndham-grand": ["Wyndham Grand", "Q112144849"],
    "wyndham-vacations": ["Wyndham Vacation Clubs", "Q112144845"],
    "wyndham": ["Wyndham Hotels and Resorts", "Q8040120"],
}


class WyndhamSpider(SitemapSpider):
    name = "wyndham"
    allowed_domains = ["www.wyndhamhotels.com"]
    sitemap_urls = ["https://www.wyndhamhotels.com/sitemap.xml"]
    sitemap_follow = [r"https:\/\/www\.wyndhamhotels\.com\/sitemap_en-us_([\w]{2})_properties_\d\.xml"]
    sitemap_rules = [(r"https:\/\/www\.wyndhamhotels\.com\/([-\w]+)\/([-\w]+)\/([-\w]+)\/overview", "parse_property")]
    custom_settings = {"REDIRECT_ENABLED": False}
    requires_proxy = True
    drop_attributes = {"image"}

    def parse_property(self, response):
        item = LinkedDataParser.parse(response, "Hotel")

        if item is None:
            return

        ref = re.search(r'var overview_propertyId = "([\d]+)";', response.text)

        if ref:
            item["ref"] = ref.group(1)
        else:
            item["ref"] = response.url.replace("https://www.wyndhamhotels.com/", "").replace("/overview", "")

        brand_id = re.match(self.sitemap_rules[0][0], response.url).group(1)

        if brand := BRANDS.get(brand_id):
            item["brand"] = brand[0]
            item["brand_wikidata"] = brand[1]
        else:
            item["brand"] = brand_id
            self.crawler.stats.inc_value(f"atp/wyndham/unknown_brand/{brand_id}")

        if brand_id == "super-8":
            apply_category(Categories.MOTEL, item)
        else:
            apply_category(Categories.HOTEL, item)

        return item

