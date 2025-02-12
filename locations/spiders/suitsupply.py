import json

from scrapy.selector import Selector
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines

COUNTRY_DEFAULT_LANGUAGE = {
    "AE": "en-ae",
    "AU": "en-au",
    "BE": "en-be",
    "CA": "en-ca",
    "CH": "en-ch",
    "CN": "zh-cn",
    "DE": "de-de",
    "DK": "en-dk",
    "EE": "en-ee",
    "ES": "es-es",
    "FI": "en-fi",
    "FR": "fr-fr",
    "GB": "en-gb",
    "IT": "it-it",
    "LT": "en-lt",
    "LV": "en-lv",
    "NL": "en-nl",
    "SE": "sv-se",
    "US": "en-us",
}
SEARCH_COUNTRIES = {
    "AE",
    "AU",
    "BE",
    "CA",
    "CH",
    "CN",
    "CO",
    "DE",
    "DK",
    "EE",
    "ES",
    "FI",
    "FR",
    "GB",
    "IT",
    "KR",
    "LT",
    "LV",
    "NL",
    "PA",
    "SE",
    "US",
}


class SuitsupplySpider(Spider):
    name = "suitsupply"
    item_attributes = {"brand": "Suitsupply", "brand_wikidata": "Q17149142"}
    start_urls = [
        f"https://suitsupply.com/on/demandware.store/Sites-USA-Site/en_US/Stores-FindStores?country={country}"
        for country in SEARCH_COUNTRIES
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        # This part doesn't have all the stores shown on the website, but it does have a lot more useful information.
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["website"] = (
                f"https://suitsupply.com/{COUNTRY_DEFAULT_LANGUAGE.get(item['country'], 'en-us')}/stores/{item['ref'].removeprefix('stores-')}"
            )

            oh = OpeningHours()
            for data in location["storeHoursData"]:
                if data["open"] != "--:--":
                    oh.add_range(DAYS_3_LETTERS_FROM_SUNDAY[int(data["day"])], data["open"], data["close"])
            item["opening_hours"] = oh

            yield item

        # This is the part that's actually shown on the website. Dupe filter will figure out which ones we already parsed.
        for location in json.loads(response.json()["locations"]):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")

            sel = Selector(text=location["infoWindowHtml"])
            item["ref"] = sel.xpath("//@data-store-id").get()
            item["addr_full"] = merge_address_lines(
                sel.xpath(
                    "//span[starts-with(@class, 'store__info-line ') and not(contains(@class, 'store__hours'))]/text()"
                ).getall()
            )
            item["website"] = response.urljoin(sel.xpath("//@href").get())

            yield item
