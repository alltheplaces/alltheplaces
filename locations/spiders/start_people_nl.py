import re
import unicodedata
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider


class StartPeopleNLSpider(AlgoliaSpider):
    name = "start_people_nl"
    item_attributes = {"brand": "Start People", "brand_wikidata": "Q2646530"}
    api_key = "7ef98d08dec110abea45c4b680b9c2ee"
    app_id = "9WV1AQ1QUR"
    index_name = "prd_start_people_office"
    # The index also holds closed offices and another brand; this is the store finder's own filter.
    myfilter = "isDeleted:false AND isPublished:true AND isSearchable:true AND brand:'Start People'"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["sourceOfficeId"]
        item["branch"] = item.pop("name").removeprefix("Start People ")
        item["housenumber"] = "{}{}".format(feature.get("streetNumber") or "", feature.get("streetNumberSuffix") or "")
        if item["phone"] == "nvt":
            item["phone"] = None

        # The index has no page URL: the site builds the slug from the office name this way.
        slug = re.sub(r"[̀-ͯ]", "", unicodedata.normalize("NFD", feature["name"]))
        slug = re.sub(r"[^ \-_0-9A-Za-z.À-ÖØ-öø-ÿ]+", " ", slug)
        slug = re.sub(r"[_ ]+", "-", slug).replace(".", "").lower().strip("-")
        item["website"] = "https://www.startpeople.nl/vestiging/{}-{}".format(re.sub(r"-+", "-", slug), item["ref"])

        item["opening_hours"] = OpeningHours()
        for day, hours in (feature.get("weeklyOpeningPeriods") or {}).items():
            item["opening_hours"].add_range(day, hours.get("openingTime"), hours.get("closingTime"))

        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        yield item
