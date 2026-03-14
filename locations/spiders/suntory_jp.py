from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, Vending, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SuntoryJPSpider(CSVFeedSpider):
    name = "suntory_jp"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ja",
            "Connection": "keep-alive",
            "User-Agent": BROWSER_DEFAULT,
            "Origin": "https://www.suntory.co.jp",
            "Referer": "https://www.suntory.co.jp/",
            "Host": "map.jihan-pi.jp",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        },
    }

    headers = ["id", "lat", "lon"]
    allowed_domains = ["map.jihan-pi.jp"]
    start_urls = ["https://map.jihan-pi.jp/map.csv"]

    item_attributes = {
        "brand_wikidata": "Q1345267",
    }

    def parse_row(self, response, row):
        i = Feature()
        try:
            i["ref"] = row["id"]
            i["lat"] = row["lat"]
            i["lon"] = row["lon"]
            apply_category(Categories.VENDING_MACHINE, i)
            apply_category(Vending.DRINKS, i)
            return i
        except:
            return i
