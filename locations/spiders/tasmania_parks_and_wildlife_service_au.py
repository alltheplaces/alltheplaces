from copy import deepcopy

from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.settings import ITEM_PIPELINES


class TasmaniaParksAndWildlifeServiceAUSpider(Spider):
    name = "tasmania_parks_and_wildlife_service_au"
    item_attributes = {
        "state": "Tasmania",
        "operator": "Tasmania Parks and Wildlife Service",
        "operator_wikidata": "Q7687416",
    }
    allowed_domains = ["parks.tas.gov.au"]
    start_urls = ["https://parks.tas.gov.au/where-to-stay/map-of-stays"]
    custom_settings = {
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
    }

    def parse(self, response):
        js_blob = response.xpath('//div[@class="pws--map-container"]//script/text()').get()
        for line in js_blob.splitlines():
            coordinates = []
            if line.startswith("L.marker("):
                # Coordinates are given as (lat, lon)
                coordinate_pair = list(map(str.strip, line.split("[", 1)[1].split("]", 1)[0].split(",", 1)))
                coordinates.append((coordinate_pair[1], coordinate_pair[0]))
            elif line.startswith("L.geoJSON("):
                # Coordinates are given as (lon, lat) for GeoJSON
                coordinate_pairs = line.split('"coordinates": [[', 1)[1].split("]]", 1)[0].replace(" ", "").split("],[")
                for coordinate_pair in coordinate_pairs:
                    coordinates.append(tuple(coordinate_pair.split(",", 1)))
            else:
                continue
            properties = {
                "name": line.split("<b>", 1)[1]
                .split("</b>", 1)[0]
                .replace(" walker camping", "")
                .replace(" camping", "")
                .replace(" accommodation", ""),
                "website": "https://parks.tas.gov.au" + line.split("<a href='", 1)[1].split("'", 1)[0],
            }
            yield Request(
                url=properties["website"],
                meta={"properties": properties, "coordinates": coordinates},
                callback=self.parse_location,
            )

    def parse_location(self, response):
        for site_number, coordinate in enumerate(response.meta["coordinates"]):
            properties = deepcopy(response.meta["properties"])
            slug = response.url.split("/")[-1]
            if len(response.meta["coordinates"]) > 1:
                properties["ref"] = f"{slug}_{site_number}"
            else:
                properties["ref"] = slug
            properties["lat"] = coordinate[1]
            properties["lon"] = coordinate[0]
            properties["website"] = response.url
            if response.xpath('//img[contains(@data-src, "/icons/camping.png")]'):
                apply_category(Categories.TOURISM_CAMP_SITE, properties)
            elif response.xpath('//img[contains(@data-src, "/icons/cabin.png")]'):
                if response.xpath('//img[contains(@data-src, "/icons/Ranger.png")]'):
                    apply_category(Categories.TOURISM_CHALET, properties)
                else:
                    apply_category(Categories.TOURISM_WILDERNESS_HUT, properties)
            else:
                # Other types of accommodation which can be quite
                # varied, without an easy and reliable way to
                # tag these features with specific tourism tags.
                apply_category({"tourism": "yes"}, properties)
            apply_yes_no(
                Extras.TENT_SITES, properties, response.xpath('//img[contains(@data-src, "/icons/camping.png")]'), False
            )
            apply_yes_no(
                Extras.CARAVAN_SITES,
                properties,
                response.xpath('//img[contains(@data-src, "/icons/Caravan-site.png")]'),
                False,
            )
            apply_yes_no(
                Extras.BARBEQUES, properties, response.xpath('//img[contains(@data-src, "/icons/BBQ.png")]'), False
            )
            apply_yes_no(
                Extras.PICNIC_TABLES,
                properties,
                response.xpath('//img[contains(@data-src, "/icons/Picnic-area.png")]'),
                False,
            )
            apply_yes_no(
                Extras.TOILETS, properties, response.xpath('//img[contains(@data-src, "/icons/toilets.png")]'), False
            )
            apply_yes_no(
                Extras.SHOWERS, properties, response.xpath('//img[contains(@data-src, "/icons/shower.png")]'), False
            )
            yield Feature(**properties)
