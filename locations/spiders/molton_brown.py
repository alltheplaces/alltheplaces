locations/spiders# cat molton_brown.py

from locations.json_blob_spider import JSONBlobSpider
from scrapy.http import Response
from locations.user_agents import BROWSER_DEFAULT

from locations.categories import Categories, apply_category
from locations.items import Feature
from urllib.parse import urljoin


class MoltonBrownSpider(JSONBlobSpider):
    name = "molton_brown"
    item_attributes = {"brand": "Molton Brown", "brand_wikidata": "Q17100584"}
#    start_urls = ["https://api.moltonbrown.com/kaowebservices/v2/moltonbrown-gb/kao/stores"]
    start_urls = ["https://api.cxur-kaocorpor1-p3-public.model-t.cc.commerce.ondemand.com/kaowebservices/v2/moltonbrown-gb/stores/?currentPage=1"]
    locations_key = ["stores"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.moltonbrown.co.uk",
            "referer": "https://www.moltonbrown.co.uk/",
        },
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 10,
    }
