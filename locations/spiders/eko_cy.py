from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class EkoCYSpider(LighthouseSpider):
    name = "eko_cy"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q111604705", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.eko.com.cy"]
    start_urls = ["https://www.eko.com.cy/pratiria/katastimata/"]
