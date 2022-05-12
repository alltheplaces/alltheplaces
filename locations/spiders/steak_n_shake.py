# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class SteakNShakeSpider(scrapy.Spider):
    name = "steak_n_shake"
    item_attributes = {"brand": "Steak N Shake", "brand_wikidata": "Q7605233"}
    allowed_domains = ["www.steaknshake.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ("https://www.steaknshake.com/locations/",)

    def start_requests(self):
        url = "https://www.steaknshake.com/wp-admin/admin-ajax.php"

        formdata = {"action": "get_location_data_from_plugin"}

        headers = {
            "Host": "www.steaknshake.com",
            "Connection": "keep - alive",
            "Content - Length": "36",
            "sec - ch - ua": ' "Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
            "Accept": "* / *",
            "Content - Type": " application/x-www-form-urlencoded; charset=UTF-8",
            "X - Requested - With": "XMLHttpRequest",
            "sec - ch - ua - mobile": "?0",
            "User - Agent": " Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
            "sec - ch - ua - platform": '"macOS"',
            "Origin": "https: // www.steaknshake.com",
            "Sec - Fetch - Site": "same - origin",
            "Sec - Fetch - Mode": "cors",
            "Sec - Fetch - Dest": "empty",
            "Referer": "https: // www.steaknshake.com / locations /?q = 78704",
            "Accept - Encoding": "gzip, deflate, br",
            "Accept - Language": " en-US,en;q=0.9",
            "Cookie": " _gcl_au=1.1.2003816794.1633380447; _ga=GA1.2.113267977.1633380448; _gid=GA1.2.33610528.1633380448; rewardspopup=visited; _gat_UA-41904139-5=1; _fbp=fb.1.1633442235013.1462044292",
        }

        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            headers=headers,
            formdata=formdata,
            callback=self.parse,
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "ref": store_data["brandChainId"],
                "name": store_data["slug"],
                "addr_full": store_data["address"]["address1"],
                "city": store_data["address"]["city"],
                "state": store_data["address"]["region"],
                "postcode": store_data["address"]["zip"],
                "country": store_data["address"]["country"],
                "phone": store_data["phone1"],
                "lat": store_data["address"]["loc"][1],
                "lon": store_data["address"]["loc"][0],
                "website": response.url,
            }
            yield GeojsonPointItem(**properties)
