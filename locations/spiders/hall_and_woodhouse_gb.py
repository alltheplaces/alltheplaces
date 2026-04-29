from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider


class HallAndWoodhouseGBSpider(JSONBlobSpider):
    name = "hall_and_woodhouse_gb"
    item_attributes = {"brand": "Hall & Woodhouse", "brand_wikidata": "Q5642555"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.hall-woodhouse.co.uk/wp-admin/admin-ajax.php?action=pub_locations",
            data="security=b3fd77d261&data={}",
            headers={
                "Host": "www.hall-woodhouse.co.uk",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0",
                "Referer": "https://www.hall-woodhouse.co.uk/our-pubs/",
                "Content-Type": "multipart/form-data",
                "Origin": "https://www.hall-woodhouse.co.uk",
                "Sec-GPC": "1",
                "Alt-Used": "www.hall-woodhouse.co.uk",
                "Connection": "keep-alive",
                "DNT": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
        )
