from typing import Iterable

from scrapy import Spider
from scrapy.http import FormRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TreePlotterSpider(Spider):
    """
    TreePlotter is a hosted web application commonly used by municipal
    governments for managing street trees (as well as other types of trees
    such as those in parks and arboretums). The main website for TreePlotter
    is https://planitgeo.com/treeplotter/

    To use this spider, specify a `folder` (customer-specific instance name)
    and a `layer_name` (probably `trees` but can be other values too). For
    international customers of TreePlotter, different geographic hosting
    arrangements are used and the `host` attribute may also need changing from
    the default of `pg-cloud.com`.

    In the example URL of "https://pg-cloud.com/SampleCustomer/":
      host = "pg-cloud.com"
      folder = "SampleCustomer"

    Be aware that some TreePlotter customers allow the public to modify their
    database and quality can therefore be questionable both in accuracy (such
    as correctly identified species) as well as currency.

    If data cleanup is required, override the `post_process_item` method.
    """

    host: str = "pg-cloud.com"
    folder: str = ""
    layer_name: str = ""

    _species: dict = {}

    # Cookies required to maintain a PHPSESSIONID across requests.
    # robots.txt does not exist and returns a 404 HTML error page.
    custom_settings = {"COOKIES_ENABLED": True, "ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield Request(url=f"https://{self.host}/{self.folder}/", callback=self.parse_cookie)

    def parse_cookie(self, response: Response) -> Iterable[FormRequest]:
        yield from self.request_species_list()

    def request_species_list(self) -> Iterable[FormRequest]:
        formdata = {
            "action": "callFunction",
            "params[funcToCall]": "getLookUpItems",
            "params[args][folder]": self.folder,
            "params[args][tableName]": "species",
            "params[args][lookUpToos]": "",
        }
        yield FormRequest(
            url=f"https://{self.host}/main/server/db.php",
            formdata=formdata,
            method="POST",
            callback=self.parse_species_list,
        )

    def parse_species_list(self, response: Response) -> Iterable[FormRequest]:
        for species_id, species_details in response.json()["results"].items():
            self._species[species_id] = {}
            if latin_name := species_details.get("latin_name"):
                self._species[species_id]["species"] = latin_name
            if genus := species_details.get("genus"):
                self._species[species_id]["genus"] = genus
            if common_name := species_details.get("common_name"):
                self._species[species_id]["taxon:en"] = common_name
            # elif alias := species_details.get("alias"):
            #    self._species[species_id]["taxon:en"] = species["alias"]
        yield from self.request_tree_ids()

    def request_tree_ids(self) -> Iterable[FormRequest]:
        formdata = {
            "action": "callFunction",
            "params[funcToCall]": "retrieveMapPointsStart",
            "params[args][folder]": self.folder,
            "params[args][layerName]": self.layer_name,
            "params[args][extent][]": ["-100000000", "-100000000", "100000000", "100000000"],
            "params[args][uniqueRequestID]": "0",
            "params[args][lastExtent]": "",
            "params[args][hasActives]": "100951",
            "params[args][mandatoryPIDS]": "",
            "params[args][showArchived]": "1",
            "params[args][mustTurnOn]": "",
            "params[args][geom_field]": "geom",
            "params[args][onMap]": "",
            "params[args][maxFeatures]": "1000000",
            "params[args][filtersPkg][settings][andor]": "AND",
            "params[args][filtersPkg][settings][boundToResults]": "1",
        }
        yield FormRequest(
            url=f"https://{self.host}/main/server/db.php",
            formdata=formdata,
            method="POST",
            callback=self.parse_tree_ids,
        )

    def parse_tree_ids(self, response: Response) -> Iterable[FormRequest]:
        tree_ids = response.json()["results"]["pids"]
        if len(tree_ids) != response.json()["results"]["total"]["count"]:
            raise RuntimeError(
                "Requested up to 1000000 features (of a total of {}) but only received {} features.".format(
                    response.json()["results"]["total"]["count"], len(tree_ids)
                )
            )
        for offset in range(0, len(tree_ids), 1000):
            tree_ids_list = tree_ids[offset : offset + 1000]
            yield from self.request_tree_details(tree_ids_list)

    def request_tree_details(self, tree_ids_list: list[int]) -> Iterable[FormRequest]:
        formdata = {
            "action": "callFunction",
            "params[funcToCall]": "retrieveLayers",
            "params[args][folder]": self.folder,
            "params[args][table]": self.layer_name,
            "params[args][mustTurnOn]": "",
            "params[args][extraFields]": "",
            "params[args][uniqueRequestID]": "0",
            "params[args][pids]": ",".join(map(str, tree_ids_list)),
            "params[args][geomField]": "geom",
        }
        yield FormRequest(
            url=f"https://{self.host}/main/server/db.php",
            formdata=formdata,
            method="POST",
            callback=self.parse_tree_details,
        )

    def parse_tree_details(self, response: Response) -> Iterable[Feature]:
        for tree in response.json()["results"][self.layer_name]["geojson"]["features"]:
            properties = {
                "ref": str(tree["properties"]["pid"]),
                "geometry": tree["geometry"],
            }
            apply_category(Categories.NATURAL_TREE, properties)
            if not tree["properties"].get("species_common"):
                if not tree["properties"].get("species_latin"):
                    # Generally a lack of species code means low quality data,
                    # for example, a location where a tree was once located or
                    # is planned to be located, but no tree currently exists.
                    # Ignore these trees (or potential tree sites) if they
                    # have no species code.
                    continue
                else:
                    species_id = str(tree["properties"]["species_latin"])
            else:
                species_id = str(tree["properties"]["species_common"])
            if species_id not in self._species.keys():
                self.logger.warning(
                    "Tree with PID={} has unknown species {}.".format(tree["properties"]["pid"], species_id)
                )
            else:
                properties["extras"].update(self._species[species_id])
            if dbh_cm := tree["properties"].get("dbh_cm"):
                properties["extras"]["diameter"] = f"{dbh_cm} cm"
            elif dbh_dm := tree["properties"].get("dbh"):
                dbh_cm = dbh_dm * 10
                properties["extras"]["diameter"] = f"{dbh_cm} cm"
            yield from self.post_process_item(Feature(**properties), response, tree)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
