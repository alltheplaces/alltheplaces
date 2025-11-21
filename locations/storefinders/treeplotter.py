from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import FormRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# ------------------------------
# Custom, domain-specific errors
# ------------------------------


class TreePlotterConfigError(Exception):
    """Raised when required spider configuration (host, folder, layer_name) is missing or invalid."""



class TreePlotterAPIError(Exception):
    """Raised when TreePlotter API responses cannot be parsed or do not contain expected structures/keys."""



class TreePlotterDataError(Exception):
    """Raised when TreePlotter returns logically inconsistent or unusable data (e.g., mismatched counts)."""



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

    def _json(self, response: Response) -> dict:
        """
        Parse JSON and normalize exceptions.

        Raises:
            TreePlotterAPIError: if the body is not valid JSON.
        """
        try:
            return response.json()
        except Exception as e:
            raise TreePlotterAPIError(f"Failed to parse JSON from {response.url}") from e

    @staticmethod
    def _expect(mapping: dict, *path: str) -> Any:
        """
        Retrieve a nested key path from a mapping, raising a domain error if missing.

        Raises:
            TreePlotterAPIError: if any key along the path is missing.
        """
        cur = mapping
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                raise TreePlotterAPIError(f"Response missing expected key path: {'/'.join(path)}")
            cur = cur[key]
        return cur

    def start_requests(self) -> Iterable[Request]:
        """
        Entry point.

        Raises:
            TreePlotterConfigError: if required attributes (host, folder, layer_name) are not provided.
        """
        # Validate required configuration upfront to fail fast and clearly.
        if not self.host or not isinstance(self.host, str):
            raise TreePlotterConfigError("Missing or invalid 'host'.")
        if not self.folder or not isinstance(self.folder, str):
            raise TreePlotterConfigError("Missing or invalid 'folder'.")
        if not self.layer_name or not isinstance(self.layer_name, str):
            raise TreePlotterConfigError("Missing or invalid 'layer_name'.")
        yield Request(url=f"https://{self.host}/{self.folder}/", callback=self.parse_cookie)

    def parse_cookie(self, response: Response) -> Iterable[FormRequest]:
        """Initial handshake to establish cookies; immediately proceeds to species list."""
        # No special exceptions expected here beyond network/HTTP handled by Scrapy.
        # If a cookie were required and missing, subsequent API calls would fail and be caught below.
        yield from self.request_species_list()

    def request_species_list(self) -> Iterable[FormRequest]:
        """Issues a request for the species lookup table."""
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
        """
        Build species lookup from API response.

        Raises:
            TreePlotterAPIError: if JSON is invalid or expected keys are missing.
        """
        data = self._json(response)
        try:
            results = self._expect(data, "results")
            # results is expected to be a mapping { species_id: { details... } }
            if not isinstance(results, dict):
                raise TreePlotterAPIError("Species results payload is not a mapping.")
        except TreePlotterAPIError:
            # Re-raise to keep stack/context concise and consistent.
            raise

        for species_id, species_details in response.json()["results"].items():
            # Defensive: ensure per-entry payload is a dict.
            if not isinstance(species_details, dict):
                self.logger.warning("Skipping species_id=%r due to invalid entry type.", species_id)
                continue

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
        """Issues a request for all tree IDs in the target layer."""
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
        """
        Paginate tree IDs in chunks.

        Raises:
            TreePlotterAPIError: if JSON is invalid or keys are missing.
            TreePlotterDataError: if returned counts are inconsistent with requested maxFeatures.
        """
        data = self._json(response)
        results = self._expect(data, "results")

        try:
            total = self._expect(results, "total")
            total_count = total["count"]
        except (TreePlotterAPIError, KeyError, TypeError):
            raise TreePlotterAPIError("Missing results/total/count in tree id response.")

        pids = results.get("pids")
        if not isinstance(pids, list):
            raise TreePlotterAPIError("Missing or invalid results/pids list in tree id response.")

        if len(pids) != total_count:
            raise RuntimeError(
                "Requested up to 1000000 features (of a total of {}) but only received {} features.".format(
                    total_count, len(pids)
                )
            )
        for offset in range(0, len(pids), 1000):
            tree_ids_list = pids[offset : offset + 1000]
            yield from self.request_tree_details(tree_ids_list)

    def request_tree_details(self, tree_ids_list: list[int]) -> Iterable[FormRequest]:
        """Issues a request for detailed tree features by PID chunk."""
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
        """
        Build Feature items from layer response.

        Raises:
            TreePlotterAPIError: if JSON is invalid or expected keys are missing.
        """
        data = self._json(response)

        # Expect structure: results -> <layer_name> -> geojson -> features
        try:
            features = self._expect(data, "results", self.layer_name, "geojson", "features")
        except TreePlotterAPIError:
            raise  # Preserve message; caller will log appropriately.

        if not isinstance(features, list):
            raise TreePlotterAPIError("Feature collection not found or not a list.")

        for tree in features:
            try:
                props = self._expect(tree, "properties")
                geom = tree.get("geometry")
                if not isinstance(props, dict) or not isinstance(geom, dict):
                    raise TreePlotterAPIError("Invalid feature: missing properties/geometry dicts.")
                pid = props.get("pid")
                if pid is None:
                    raise TreePlotterAPIError("Invalid feature: missing 'pid'.")
            except TreePlotterAPIError as e:
                self.logger.warning("Skipping invalid feature: %s", e)
                continue

            properties = {
                "ref": str(tree["properties"]["pid"]),
                "geometry": tree["geometry"],
            }
            apply_category(Categories.NATURAL_TREE, properties)
            # Ensure extras mapping exists before updates
            properties.setdefault("extras", {})

            if not props.get["species_common"]:
                if not props.get["species_latin"]:
                    # Generally a lack of species code means low quality data,
                    # for example, a location where a tree was once located or
                    # is planned to be located, but no tree currently exists.
                    # Ignore these trees (or potential tree sites) if they
                    # have no species code.
                    continue
                else:
                    species_id = str(props["species_latin"])
            else:
                species_id = str(props["species_common"])

            if species_id not in self._species:
                self.logger.warning("Tree with PID=%s has unknown species %s.", props.get("pid"), species_id)
            else:
                properties["extras"].update(self._species[species_id])

            # Diameter handling (prefer cm if present; otherwise convert dm -> cm)
            dbh_cm = props.get("dbh_cm")
            if dbh_cm:
                properties["extras"]["diameter"] = f"{dbh_cm} cm"
            else:
                dbh_dm = props.get("dbh")
                if dbh_dm:
                    try:
                        properties["extras"]["diameter"] = f"{dbh_dm * 10} cm"
                    except Exception:
                        # Be defensive; if conversion fails, skip diameter rather than fail the item.
                        self.logger.debug("Non-numeric dbh encountered for PID=%s", pid)

            # Yield post-processed item; post_process_item may itself raise if overridden incorrectly.
            try:
                yield from self.post_process_item(Feature(**properties), response, tree)
            except Exception as e:
                # Keep crawling even if a single item fails post-processing.
                self.logger.error("post_process_item failed for PID=%s: %s", pid, e)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
