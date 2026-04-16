from locations.hours import DAYS_JP
from locations.spiders.costco_au import CostcoAUSpider


class CostcoJPSpider(CostcoAUSpider):
    name = "costco_jp"
    allowed_domains = ["www.costco.co.jp"]
    stores_url = (
        "https://www.costco.co.jp/rest/v2/japan/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
    days = DAYS_JP
    time_format = "%H:%M"
