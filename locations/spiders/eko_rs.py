from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class EkoRSSpider(LighthouseSpider):
    name = "eko_rs"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q111604683", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.ekoserbia.com"]
    start_urls = ["https://www.ekoserbia.com/benzinske-stanice/find-a-station/"]
