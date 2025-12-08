from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LocalcoinSpider(JSONBlobSpider):
    name = "localcoin"
    item_attributes = {"brand": "Localcoin", "brand_wikidata": "Q135273843"}
    allowed_domains = ["localcoinatm.com"]
    start_urls = ["https://localcoinatm.com/api/locations/"]
    locations_key = "body"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for language_code in ["en-ca", "en-au", "en-hk"]:
            # en-nz and en-au return the same features.
            yield JsonRequest(url=self.start_urls[0], headers={"x-lc-locale": language_code}, dont_filter=True)

    def parse(self, response: Response) -> Iterable[Feature]:
        if response.json().get("status") == 500:
            # Server is blocking the API call. Continue with the remainder of
            # API calls as not all regions appear to have API calls blocked.
            self.logger.error(
                "API call for ATMs in region {} has been blocked by the server. Continuing to attempt API calls for other regions.".format(
                    response.request.headers.get("x-lc-locale").decode("utf-8")
                )
            )
            return
        yield from super().parse(response)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("location"))
        feature["street_address"] = feature.pop("street", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["isDeleted"] is True or feature["isEnabled"] is False:
            return

        match feature["country"]:
            case "Australia":
                item["website"] = "https://localcoinatm.com/en-au/bitcoin-atm/{}/{}/{}/".format(
                    feature["stateSlug"], feature["citySlug"], feature["slug"]
                )
            case "Canada":
                item["website"] = "https://localcoinatm.com/bitcoin-atm/{}/{}/{}/".format(
                    feature["stateSlug"], feature["citySlug"], feature["slug"]
                )
            case "Hong Kong":
                item["website"] = "https://localcoinatm.com/en-hk/bitcoin-atm/{}/{}/{}/".format(
                    feature["areaSlug"], feature["districtSlug"], feature["slug"]
                )
            case "New Zealand":
                item["website"] = "https://localcoinatm.com/en-nz/bitcoin-atm/{}/{}/{}/".format(
                    feature["stateSlug"], feature["citySlug"], feature["slug"]
                )

        item["opening_hours"] = OpeningHours()
        for day_name in DAYS_FULL:
            open_time_key = "{}OpenHour".format(day_name.lower())
            close_time_key = "{}CloseHour".format(day_name.lower())
            item["opening_hours"].add_range(day_name, feature[open_time_key], feature[close_time_key], "%I:%M %p")

        apply_category(Categories.ATM, item)
        currencies_buyable = [
            code for code, currency in feature["cryptocurrencyFeatures"].items() if currency["buyAvailable"] is True
        ]
        currencies_sellable = [
            code for code, currency in feature["cryptocurrencyFeatures"].items() if currency["sellAvailable"] is True
        ]
        currencies_exchangeable = list(set(currencies_buyable + currencies_sellable))
        item["extras"]["currency:{}".format(feature["currencyCode"])] = "yes"
        apply_yes_no("currency:XBT", item, "btc" in currencies_exchangeable, False)
        apply_yes_no("currency:LTC", item, "ltc" in currencies_exchangeable, False)
        apply_yes_no("currency:XRP", item, "xrp" in currencies_exchangeable, False)
        apply_yes_no("currency:ETH", item, "eth" in currencies_exchangeable, False)
        apply_yes_no("currency:SHIB", item, "shib" in currencies_exchangeable, False)
        apply_yes_no("currency:USDT", item, "usdt" in currencies_exchangeable, False)
        apply_yes_no("currency:ADA", item, "ada" in currencies_exchangeable, False)
        apply_yes_no("cash_in", item, len(currencies_buyable) > 0, False)
        apply_yes_no("cash_out", item, len(currencies_sellable) > 0, False)

        yield item
