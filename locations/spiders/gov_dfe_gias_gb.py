from datetime import datetime, timedelta

import pyproj
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category, get_category_tags
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import clean_address
from locations.settings import ITEM_PIPELINES


class GovDfeGiasGBSpider(CSVFeedSpider):
    download_timeout = 400
    name = "gov_dfe_gias_gb"
    # Using yesterday because it may run early in the morning and 'today' may not be ready
    yesterday = datetime.today() - timedelta(1)
    start_urls = [
        f"https://ea-edubase-api-prod.azurewebsites.net/edubase/downloads/public/edubasealldata{yesterday.year}{yesterday.month:02d}{yesterday.day:02d}.csv"
    ]
    dataset_attributes = {
        "license": "Open Government Licence v3.0",
        "license:website": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "license:wikidata": "Q99891702",
        "attribution": "required",
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0.",
    }
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.count_operators.CountOperatorsPipeline": None},
    }
    # British OSGB36 -> lat/lon (https://epsg.io/4326)
    coord_transformer = pyproj.Transformer.from_crs(27700, 4326)

    def adapt_response(self, response):
        fixed_response = response.replace(body=response.text.encode("ISO8859-1", "ignore").decode("utf-8", "ignore"))
        return fixed_response

    def parse_row(self, response, row):
        item = Feature()
        if (
            row["EstablishmentStatus (name)"] in ["Closed", "Open, but proposed to close"]
            and row["ReasonEstablishmentClosed (name)"] == "Closure"
        ):
            if row["CloseDate"] in ["", "01-01-1900"]:
                set_closed(item)
            else:
                set_closed(item, datetime.strptime(row["CloseDate"], "%d-%m-%Y"))
        elif (
            row["EstablishmentStatus (name)"] == "Proposed to open"
            and row["ReasonEstablishmentOpened (name)"] == "New Provision"
            and row["OpenDate"] != ""
        ):
            item["extras"]["start_date"] = datetime.strptime(row["OpenDate"], "%d-%m-%Y").strftime("%Y-%m-%d")
        elif row["EstablishmentStatus (name)"] != "Open":
            return

        self.set_category(item, row)
        if get_category_tags(item) is None:
            return

        if row.get("Easting") not in ["0", ""] and row.get("Northing") not in ["0", ""]:
            item["lat"], item["lon"] = self.coord_transformer.transform(row.get("Easting"), row.get("Northing"))

        item["ref"] = row["URN"]
        item["extras"]["ref:edubase"] = row["URN"]
        item["name"] = row["EstablishmentName"]
        item["extras"]["min_age"] = row.get("StatutoryLowAge")
        if row.get("StatutoryHighAge") == "99":
            item["extras"]["max_age"] = "none"
        else:
            item["extras"]["max_age"] = row.get("StatutoryHighAge")
        item["extras"]["capacity"] = row.get("SchoolCapacity")
        item["street_address"] = row.get("Street")
        item["city"] = row.get("Town")
        item["postcode"] = row.get("Postcode")
        item["street_address"] = clean_address(
            [
                row.get("Street"),
                row.get("Locality"),
                row.get("Address3"),
                row.get("Town"),
                row.get("County (name)"),
                row.get("Postcode"),
            ]
        )
        if website := row.get("SchoolWebsite"):
            if not website.lower().startswith("http"):
                item["website"] = "https://{}".format(website)
        item["phone"] = row.get("TelephoneNum")
        item["extras"]["ref:GB:uprn"] = row.get("UPRN")

        self.set_operator(item, row)
        self.set_religion(item, row)

        return item

    def set_category(self, item, row):
        if row.get("EstablishmentTypeGroup (name)") in [
            "Academies",
            "Free Schools",
            "Independent schools",
            "Local authority maintained schools",
            "Special schools",
            "Welsh schools",
        ]:
            establishment_type = row.get("TypeOfEstablishment (name)")
            if establishment_type == "Local authority nursery school":
                apply_category(Categories.KINDERGARTEN, item)
            elif establishment_type in ["16-19", "16 to 19", "City technology college"]:
                apply_category(Categories.COLLEGE, item)
            else:
                apply_category(Categories.SCHOOL, item)
        elif row.get("EstablishmentTypeGroup (name)") == "Colleges":
            apply_category(Categories.COLLEGE, item)
        elif row.get("EstablishmentTypeGroup (name)") == "Universities":
            apply_category(Categories.UNIVERSITY, item)
        elif row.get("EstablishmentTypeGroup (name)") == "Other types":
            if row.get("TypeOfEstablishment (name)") in ["British schools overseas", "Offshore schools"]:
                apply_category(Categories.SCHOOL, item)
            else:
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/unhandled_other_type/{row.get('TypeOfEstablishment (name)')}"
                )
                return
        elif row.get("EstablishmentTypeGroup (name)") == "Online provider":
            return
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_type/{row.get('EstablishmentTypeGroup (name)')}")
            return

    def set_operator(self, item, row):
        if row.get("TypeOfEstablishment (name)") in [
            "Community school",
            "Community special school",
            "Pupil referral unit",
            "Local authority nursery school",
            "Welsh establishment",
        ]:
            item["operator"] = row["LA (name)"]
            item["extras"]["operator:type"] = "government"
        elif row.get("Trusts (name)") != "":
            item["operator"] = row["Trusts (name)"]
            item["extras"]["operator:type"] = "private"
        elif row.get("SchoolSponsors (name)") != "":
            item["operator"] = row["Trusts (name)"]
            item["extras"]["operator:type"] = "private"
        elif row.get("Federations (code)") != "":
            item["operator"] = row["Trusts (name)"]
            item["extras"]["operator:type"] = "private"

    def set_religion(self, item, row):
        row_religion = row.get("ReligiousCharacter (name)")
        no_religion = ["Does not apply", "None"]
        if row_religion == "" or any([religion in row_religion for religion in no_religion]):
            return

        christian = [
            "Anglican",
            "Baptist",
            "Catholic",
            "Christian",
            "Church of England",
            "Congregational Church",
            "Free Church",
            "Greek Orthodox",
            "Inter- / non- denominational",
            "Methodist",
            "Moravian",
            "Protestant",
            "Quaker",
            "Seventh Day Adventist",
            "United Reformed Church",
        ]
        muslim = ["Islam", "Muslim", "Sunni Deobandi"]

        if "Buddhist" in row_religion:
            item["extras"]["religion"] = "buddhist"
        elif any([religion in row_religion for religion in christian]):
            item["extras"]["religion"] = "christian"
        elif "Hindu" in row_religion:
            item["extras"]["religion"] = "hindu"
        elif "Jewish" in row_religion:
            item["extras"]["religion"] = "jewish"
        elif "Multi-faith" in row_religion:
            item["extras"]["religion"] = "multifaith"
        elif any([religion in row_religion for religion in muslim]):
            item["extras"]["religion"] = "muslim"
        elif "Sikh" in row_religion:
            item["extras"]["religion"] = "sikh"
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_religion/{row.get('ReligiousCharacter (name)')}")
