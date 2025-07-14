from json import loads
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BitrocketAUSpider(SitemapSpider):
    name = "bitrocket_au"
    item_attributes = {"brand": "BitRocket", "brand_wikidata": "Q135284228"}
    allowed_domains = ["www.bitrocket.co"]
    sitemap_urls = ["https://www.bitrocket.co/wp-sitemap-posts-page-1.xml"]
    sitemap_rules = [(r"^https:\/\/www\.bitrocket\.co\/locations\/(?:[^\/]+\/){4}$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "name": response.xpath(
                '//section[@id="particles"]/div/div/div/div[1]/div/*[self::h1 or self::h2]/text()'
            ).get(),
            "addr_full": merge_address_lines(
                response.xpath('//section[@id="particles"]/div/div/div/div[3]/div/h2/text()').getall()
            ),
            "state": response.url.split("/locations/", 1)[1].split("/", 1)[0].upper(),
            "website": response.url,
            "image": response.xpath("//article/div/div/section[2]/div/div[1]//img/@src").get(),
            "opening_hours": OpeningHours(),
        }

        if map_settings_json := response.xpath('//div[contains(@class, "wpgmza_map")]/@data-settings').get():
            map_settings = loads(map_settings_json)
            properties["lat"] = map_settings["map_start_lat"]
            properties["lon"] = map_settings["map_start_lng"]
        if not properties.get("lat") or not properties.get("lon"):
            extract_google_position(properties, response)

        properties["addr_full"] = properties["addr_full"].split("Australia", 1)[0].strip().removesuffix(",").strip()

        hours_without_day_names = response.xpath(
            "//article/div/div/section[2]/div/div[2]/div/section/div/div[2]//span/text()"
        ).getall()
        hours_with_day_names = ""
        for day_index, day_name in enumerate(DAYS_FULL):
            if day_index > len(hours_without_day_names) - 1:
                # Some ATMs only provide opening hours for M-F and don't
                # mention hours for weekends.
                break
            hours_with_day_names = hours_with_day_names + " " + day_name + ": " + hours_without_day_names[day_index]
        hours_with_day_names = hours_with_day_names.upper().replace("24 HOURS", "12:00 AM - 11:59 PM")
        properties["opening_hours"].add_ranges_from_string(hours_with_day_names)

        apply_category(Categories.ATM, properties)
        properties["extras"]["currency:XBT"] = "yes"
        properties["extras"]["currency:AUD"] = "yes"
        transaction_types_table = response.xpath("//article/div/div/section[2]/div/div[3]/div/section[1]/div")
        apply_yes_no(
            "cash_in",
            properties,
            "fa-check" in transaction_types_table.xpath("./div[1]/div/div[2]//i/@class").get(""),
            False,
        )
        apply_yes_no(
            "cash_out",
            properties,
            "fa-check" in transaction_types_table.xpath("./div[2]/div/div[2]//i/@class").get(""),
            False,
        )

        yield Feature(**properties)
