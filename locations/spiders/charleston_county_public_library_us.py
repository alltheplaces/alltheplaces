from typing import Iterable

from scrapy import Selector
from scrapy.http import Request, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.drupal_json_api import DrupalJsonApiSpider


class CharlestonCountyPublicLibraryUSSpider(DrupalJsonApiSpider):
    name = "charleston_county_public_library_us"
    item_attributes = {"operator": "Charleston County Public Library System", "operator_wikidata": "Q69490344"}
    drupal_host = "https://www.ccpl.org"
    jsonapi_resource = "node/library_branch"
    geofield_field = "field_branch_geocode"

    def post_process_item(
        self, item: Feature, response: TextResponse, entry: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        if item.get("name") == "Bookmobile":
            return

        attributes = entry.get("attributes") or {}
        item["street_address"] = attributes.get("field_branch_street_address")
        item["city"] = attributes.get("field_branch_city")
        item["state"] = attributes.get("field_branch_state_province")
        item["postcode"] = attributes.get("field_branch_postal_code_zip")
        item["country"] = attributes.get("field_branch_country")
        item["phone"] = attributes.get("field_branch_phone")

        if item.get("lat") is not None and float(item["lat"]) < 0:
            # Folly Beach's stored point has its latitude and longitude transposed.
            item["lat"], item["lon"] = item["lon"], item["lat"]
        if item.get("lat") is None:
            # Bees Ferry West Ashley and Keith Summey North Charleston have no
            # stored point, but every branch has a map of itself embedded.
            extract_google_position(item, Selector(text=attributes.get("field_branch_maps_embed_code") or ""))

        apply_category(Categories.LIBRARY, item)

        # The hours field holds only the standing weekly schedule, which a
        # branch closed for renovation keeps. The closure is applied over it
        # when the branch page is rendered, so hours are read from there.
        yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for row in response.css("li.office-hours__item"):
            day = row.css(".office-hours__item-label::text").get("").strip().rstrip(":")
            # A closed day reads "Closed", or "Closed (Main Renovations)".
            hours = " ".join(row.css(".office-hours__item-slots::text, .office-hours__item-comments::text").getall())
            if "closed" in hours.lower():
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_ranges_from_string("{} {}".format(day, hours))
        yield item
