from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class LOccitaneGBSpider(JSONBlobSpider):
    name = "l_occitane_gb"
    item_attributes = {"brand": "L'Occitane", "brand_wikidata": "Q1880676"}
    start_urls = [
        "https://uk.loccitane.com/on/demandware.store/Sites-OCC_GB-Site/en_GB/Stores-GetStores?countryCode=GB"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "uk.loccitane.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "DNT": "1",
            "Sec-GPC": "1",
            "Alt-Used": "uk.loccitane.com",
            "Connection": "keep-alive",
            "Cookie": "cc-nx-g_OCC_GB=kQQtgBoLZ8y0zgeB3zPG62Gojs3Dkxt4VZboIYU27YU; usid_OCC_GB=5d44472f-f0f8-4da4-92fc-cc1b8d78f626; cc-at_OCC_GB=eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmNkcV9wcmQiLCJraWQiOiJiM2VhOTFmNi0xMjc3LTQzNjktODZlZS1iNDZhNjAzOTJmZTkiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1kaXNjb3Zlcnktc2VhcmNoIHNmY2Muc2hvcHBlci1teWFjY291bnQuYWRkcmVzc2VzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnJ3IHNmY2Muc2hvcHBlci1teWFjY291bnQucGF5bWVudGluc3RydW1lbnRzIHNmY2Muc2hvcHBlci1jdXN0b21lcnMubG9naW4gc2ZjYy5zaG9wcGVyLXN0b3JlcyBzZmNjLXNob3BwZXItY29udGV4dC5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50Lm9yZGVycyBzZmNjLnNob3BwZXItYmFza2V0cy1vcmRlcnMgc2ZjYy5zaG9wcGVyLWN1c3RvbWVycy5yZWdpc3RlciBzZmNjLnNob3BwZXItbXlhY2NvdW50LmFkZHJlc3Nlcy5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnByb2R1Y3RsaXN0cy5ydyBzZmNjLnNob3BwZXItcHJvZHVjdGxpc3RzIHNmY2Muc2hvcHBlci1wcm9tb3Rpb25zIHNmY2Muc2Vzc2lvbl9icmlkZ2Ugc2ZjYy5zaG9wcGVyLWJhc2tldHMtb3JkZXJzLnJ3IHNmY2Muc2hvcHBlci1naWZ0LWNlcnRpZmljYXRlcyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnBheW1lbnRpbnN0cnVtZW50cy5ydyBzZmNjLnNob3BwZXItcHJvZHVjdC1zZWFyY2ggc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wcm9kdWN0bGlzdHMgc2ZjYy5zaG9wcGVyLWNhdGVnb3JpZXMgc2ZjYy5zaG9wcGVyLW15YWNjb3VudCIsInN1YiI6ImNjLXNsYXM6OmJjZHFfcHJkOjpzY2lkOjE3M2VkODcwLWYzNDItNDhiYi1hMDYxLWE4YTA0YWNhZGQwZDo6dXNpZDo1ZDQ0NDcyZi1mMGY4LTRkYTQtOTJmYy1jYzFiOGQ3OGY2MjYiLCJjdHgiOiJzbGFzIiwiaXNzIjoic2xhcy9wcm9kL2JjZHFfcHJkIiwiaXN0IjoxLCJkbnQiOiIwIiwiYXVkIjoiY29tbWVyY2VjbG91ZC9wcm9kL2JjZHFfcHJkIiwibmJmIjoxNzc0NTU1Mjk3LCJzdHkiOiJVc2VyIiwiaXNiIjoidWlkbzpzbGFzOjp1cG46R3Vlc3Q6OnVpZG46R3Vlc3QgVXNlcjo6Z2NpZDphYkJQbUJXZGo5YlVTVTdWSmo3M2JmQWpubDo6c2VzYjpzZXNzaW9uX2JyaWRnZTo6Y2hpZDpPQ0NfR0IiLCJleHAiOjE3NzQ1NTcxMjcsImlhdCI6MTc3NDU1NTMyNywianRpIjoiQzJDLTIwMTU0NTYxNTUwLTk2Nzg3OTQ4MTY4NjQ2MTIyMzA3OTk0NjUifQ.d8J99jEv8PCrBjBhUxCIFfVe4tiUeBrewmtoEwCHZbpMrJBjtjNEmlTnhTDb2T5SI6jf255B9BkEwvfEGYsMWw; dwsid=cQxKbkpRmjSlnGAxNMotIksDjTbEYzYIawaOufGDiyRqdymXDv6Km3j4gZRpZE-LUMw0yOCv9bjwrMcaIsYdiQ==; sid=HlIEN2bCY6xGHfNYGviBZyRdw2_o8M-QiIc; datadome=jqpIJvaHy7eOyed_J_DCH3_zOaZNuHGV6z84Hy47Lkh5gFu~FH4PU8MZsgt4IaefIYqhZ6IdE9PKzpd21qSconuebSQ2K8pGIN7BxEJF2FdWbI89fKlVkYvfbHDCb3br; dwanonymous_bac057757b1caa6b68750df56d7ee283=abBPmBWdj9bUSU7VJj73bfAjnl; __cq_dnt=1; dw_dnt=1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",

        },
    }
    locations_key = ["stores"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
