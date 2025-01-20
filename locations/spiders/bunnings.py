import scrapy
from scrapy import Spider

from locations.dict_parser import DictParser


class BunningsSpider(Spider):
    name = "bunnings"
    item_attributes = {"brand": "Bunnings", "brand_wikidata": "Q4997829"}

    def start_requests(self):
        yield scrapy.Request(
            url="https://api.prod.bunnings.com.au/v1/stores/country/AU?fields=FULL",
            headers={
                "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkJGRTFEMDBBRUZERkVDNzM4N0E1RUFFMzkxNjRFM0MwMUJBNzVDODciLCJ4NXQiOiJ2LUhRQ3VfZjdIT0hwZXJqa1dUandCdW5YSWMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2J1bm5pbmdzLmNvbS5hdS8iLCJuYmYiOjE3MzU4ODUzNjIsImlhdCI6MTczNTg4NTM2MiwiZXhwIjoxNzM2MzE3MzYyLCJhdWQiOlsiQ2hlY2tvdXQtQXBpIiwiY3VzdG9tZXJfYnVubmluZ3MiLCJodHRwczovL2J1bm5pbmdzLmNvbS5hdS9yZXNvdXJjZXMiXSwic2NvcGUiOlsiY2hrOmV4ZWMiLCJjbTphY2Nlc3MiLCJlY29tOmFjY2VzcyIsImNoazpwdWIiXSwiYW1yIjpbImV4dGVybmFsIl0sImNsaWVudF9pZCI6ImJ1ZHBfZ3Vlc3RfdXNlcl9hdSIsInN1YiI6IjI5ODRkYWNmLWU2YjEtNDYyNS1hNjM4LTdkYTU1YThlYTQ3MCIsImF1dGhfdGltZSI6MTczNTg4NTM2MiwiaWRwIjoibG9jYWxsb29wYmFjayIsImItaWQiOiIyOTg0ZGFjZi1lNmIxLTQ2MjUtYTYzOC03ZGE1NWE4ZWE0NzAiLCJiLXJvbGUiOiJndWVzdCIsImItdHlwZSI6Imd1ZXN0IiwibG9jYWxlIjoiZW5fQVUiLCJiLWNvdW50cnkiOiJBVSIsImFjdGl2YXRpb25fc3RhdHVzIjoiRmFsc2UiLCJ1c2VyX25hbWUiOiIyOTg0ZGFjZi1lNmIxLTQ2MjUtYTYzOC03ZGE1NWE4ZWE0NzAiLCJiLXJiYWMiOlt7ImFzYyI6IjgwYjM5NGM1LThiOGItNGE3My1hMTVkLTljYmNmMTE1NGU2OCIsInR5cGUiOiJDIiwicm9sIjpbIkNISzpHdWVzdCJdfV0sInNpZCI6IjNGMThGMDk2NEEwRTc5ODI0NDczMzhGOURGRjJERDA5IiwianRpIjoiMDRBM0UyQjkzRTBBRUI2QTkyNjFGNTE2MUUxQjk5NTAifQ.FqWatu2TJth5LVW9gMiy9_0Ki5t6uYh9L837wj-zqPX_xbtoHGZUJ8QkEy3oe5u2IXm0TCJZSRzAAoG3JALIogN9NIfqrkxeDBat0EPMXUDsh4seFReDZPylzbSxJEnWRVxApCzbMBl6dIFCJOGl1xcoikmLdGgP1zSiB7ugE-d7DxQf9btNnyRUhsbyE_kgEi7yWO0FlCzHoKdDZyfWbQgQEcmVzp8U7eWmRdEueCNl99SJK9coOAYGpjF-f4FB5u364xMHaKqR_SfhB2_dAPGdeU7_lSzr4hhaQ4iJuvIBe4ZKJd2lcI0MqM3F0X40p19Mzgg-Ln-p0uyIhI1NLg",
                "clientId": "mHPVWnzuBkrW7rmt56XGwKkb5Gp9BJMk",
                "country": "AU",
                "locale": "en_AU",
            },
        )

    def parse(self, response):
        for store in response.json()["data"]["pointOfServices"]:
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["name"] = store["displayName"]
            yield item
