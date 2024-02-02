import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PizzaHutTRSpider(scrapy.Spider):
    name = "pizza_hut_tr"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    def start_requests(self):
        yield JsonRequest(
            url="https://api.pizzahut.com.tr/api/web/Restaurants/GetRestaurants?getAll=true",
            headers={
                "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjM4NUI0QjAyRENBMzQxMDMwNDhBN0EyNzQxRDc3NTA1MjlGM0RDMkYiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJPRnRMQXR5alFRTUVpbm9uUWRkMUJTbnozQzgifQ.eyJuYmYiOjE3MDY2MDQwMjksImV4cCI6MTcwNzIwODgyOSwiaXNzIjoiaHR0cDovL2F1dGgucGl6emFodXQuY29tLnRyIiwiYXVkIjpbImh0dHA6Ly9hdXRoLnBpenphaHV0LmNvbS50ci9yZXNvdXJjZXMiLCJwaXp6YWh1dGFwaSJdLCJjbGllbnRfaWQiOiJ3ZWIiLCJzdWIiOiJyb2J1c2VyQGNsb2Nrd29yay5jb20udHIiLCJhdXRoX3RpbWUiOjE3MDY2MDQwMjksImlkcCI6ImxvY2FsIiwiZW1haWwiOiJyb2J1c2VyQGNsb2Nrd29yay5jb20udHIiLCJ1aWQiOiIyNCIsInBlcnNvbmlkIjoiMzAwMDMyOTM5MDc5IiwibmFtZXN1cm5hbWUiOiJQSCBEVU1NWSIsImxjdG9rZW4iOiJWclE0Rk81WTlwSktNZk9LbW9PSGZTTDE2OTdlc3FfajdIMEZGYU01Z25XMzVyTXpCdzRQMmkzS1pVcWF4Vy1reWVHcjZNYkhIc3Z2VkxQTG1KTkdqY29IdEQ1WUtJT0FiemRxQ1VaOEpHM2w5bHptRlJfQkdYbjlCTUxHUTcwaG5GdXhPTVRoeEd4RFV3bmJfbHprU1NnSE14eWFhQTUtSURxelNOSUZCY2Y3R2NuQ1BOSlgxUlBJR3h0WFN3N1Bjcmk4dkZVQ2hYS2trVEIxTEhrdi1rX0ZicGlOQVFfOFZFOGlvSWlyOEVYTEpZV2U0VWM5RXFoUDU3Tm5CbjBNYmlNNDFXcnBqSFNiRVNtZ3pUZ0NPWGt2ZEZ3WHhiRVdjdXU1Y0tHMG5NQXFOQmdWTGtwbHZRT0VmX1YyZzdMdkhGeVVSeC1YamsxUDIyRVlzTl9tOEpyaEVKWVNXOElLbXhLOUd0X1UzOHBNRnpvTUVLdXNrUWdiM2VWZVhPY1ZteUlDNlEiLCJsY3JlZnJlc2h0b2tlbiI6IjczN2U3MjBkMjI1NjQyNDM4N2UwYTNlZmMzOGU4ZWZmIiwicGVyc29uZW1haWwiOiJkdW1teUBtYXdhcmlkZ2lkYS5jb20iLCJzY29wZSI6WyJwaXp6YWh1dGFwaSIsIm9mZmxpbmVfYWNjZXNzIl0sImFtciI6WyI3NjU2QkFGM0YxNUE2NTA0QkJGM0NFRTgyOTA5MkRGQSJdfQ.N2hwVhTm31_RgXRu2_lV1CU0KWqiGGbzG2UVWUWge8aYMJDMhEK_oQmsh8mEvrZq_pGnlb3PTIdO2L4Jx08ohu0675pKlKl1BBDiappMzy2sjsAoxMI49B9EQKIKpdJAzPoiMhV2jpFNkrIyXouJzUrTpTowqkl45TOLZLBxGH7tc-kfwkYac8vOii81__fTq2_xFQaiv_wloA5avktYU8n68WHjVbROvFiM8_cb8xMFEpWE51bIqLZpk51yuCMUHOlEaj2orzptHRJjvWIFIwEpwENtOMjG4L54x7LUpHMJ-VeVa7JRK0B2G9FEQJrhqoh9G_Sf556On0SSfZ9iJQ"
            },
        )

    def parse(self, response):
        for poi in response.json()["result"]:
            item = DictParser.parse(poi)
            apply_category(Categories.RESTAURANT, item)
            latitude = poi.get("latitude")
            longitude = poi.get("longitude")

            if latitude is not None and longitude is not None:
                item["lat"] = latitude.replace(",", ".")
                item["lon"] = longitude.replace(",", ".")

            yield item
