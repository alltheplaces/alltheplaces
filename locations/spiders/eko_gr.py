from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class EkoGRSpider(LighthouseSpider):
    name = "eko_gr"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q31283948", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.eko.gr"]
    start_urls = ["https://www.eko.gr/pratiria/katastimata/"]
