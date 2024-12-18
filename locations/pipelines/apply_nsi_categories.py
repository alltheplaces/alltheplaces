from typing import Iterable

from scrapy import Spider

from locations.categories import get_category_tags
from locations.items import Feature
from locations.name_suggestion_index import NSI


class ApplyNSICategoriesPipeline:
    nsi = NSI()
    wikidata_cache = {}

    def process_item(self, item: Feature, spider: Spider) -> Iterable[Feature]:
        if item.get("nsi_id"):
            # Skip NSI matching and tag synchronisation upon spider request. A
            # spider must set attribute "nsi_id = -1" to skip NSI matching.
            # nsi_id is NOT a stable identifier and should not be set manually
            # by a spider unless it does so by lookup of the current NSI
            # database.
            return item

        brand_operator_qcode = item.get("brand_wikidata", item.get("operator_wikidata"))
        if not brand_operator_qcode:
            # Failure to match due to missing brand_wikidata or
            # operator_wikidata fields on the item. One or both of these
            # fields must be supplied.
            spider.crawler.stats.inc_value("atp/nsi/match_failed")
            spider.crawler.stats.inc_value("atp/nsi/brand_or_operator_missing")
            return item

        if not get_category_tags(item) and item.get("brand_wikidata"):
            # Not a fatal condition for NSI matching because many ATP spiders
            # do not specify top level category tags which could be used to
            # match with NSI. It is rare enough that an NSI entry is
            # mismatched for brands as most brand Wikidata items only have a
            # single top level category applicable.
            #
            # NOTE: In the future once ATP spiders specify top level category
            #       tags universally, this logic is expected to change to
            #       treat an ATP spider missing a category as being fatal to
            #       NSI matching.
            #
            # Example of a typical problem this check prevents:
            #   Brand operates a supermarket chain that has a liquor shop,
            #   pharmacy or fuel station adjoining or nearby, but there is a
            #   single common brand and single common Wikidata item known to
            #   NSI for all of these types of features. For example, NSI knows
            #   of "Costco" in the US with Wikidata item Q715583 being both
            #   shop/warehouse and amenity/car_wash. The only field different
            #   in NSI entries is the category.
            spider.crawler.stats.inc_value("atp/nsi/category_missing")
        elif not get_category_tags(item):
            # Failure to match due to missing top level category tags on the
            # ATP item, preventing matching with NSI operator entries. Most
            # ATP spiders matching against NSI operator entries already
            # specify a top level category, and it is quite common for
            # mismatches to occur without a top level category being defined.
            #
            # Example of a typical problem this check prevents:
            #   Local government organisation operating playgrounds, roads,
            #   street furniture, sports fields, etc does so in the same
            #   region with a single applicable Wikidata item. ATP has no way
            #   of knowing which of numerous NSI entries associated with the
            #   local government organisation is applicable if no category is
            #   specified.
            spider.crawler.stats.inc_value("atp/nsi/match_failed")
            spider.crawler.stats.inc_value("atp/nsi/category_missing")
            return item

        if not item.has_valid_country_code():
            # Not a fatal condition for NSI matching because both the ATP and
            # NSI items may have global applicability (e.g. "001" for NSI).
            # However, it's still worth collecting statistics.
            spider.crawler.stats.inc_value("atp/nsi/country_missing")

        if brand_operator_qcode not in self.wikidata_cache:
            # wikidata_cache will usually only hold one thing, but can contain
            # more with more complex spiders. The key thing is that we don't
            # have to call nsi.iter_nsi on every process_item.
            self.wikidata_cache[brand_operator_qcode] = list(self.nsi.iter_nsi(brand_operator_qcode))

        nsi_matches = self.wikidata_cache.get(brand_operator_qcode)

        if len(nsi_matches) == 0 and item.get("brand_wikidata"):
            # Failure to match due to the ATP item specifying a Wikidata item
            # for a brand, but NSI does not know of this Wikidata item.
            # It is suggested that a change be submitted to:
            # https://github.com/osmlab/name-suggestion-index
            spider.crawler.stats.inc_value("atp/nsi/match_failed")
            spider.crawler.stats.inc_value("atp/nsi/brand_unknown")
            return item
        elif len(nsi_matches) == 0 and item.get("operator_wikidata"):
            # Failure to match due to the ATP item specifying a Wikidata item
            # for an operator, but NSI does not know of this Wikidata item.
            # It is suggested that a change be submitted to:
            # https://github.com/osmlab/name-suggestion-index
            spider.crawler.stats.inc_value("atp/nsi/match_failed")
            spider.crawler.stats.inc_value("atp/nsi/operator_unknown")
            return item

        # Sometimes a brand and operator are the same across both NSI's
        # "brand" and "operator" namespaces. For example, "KFC" is listed in
        # NSI as being both "amenity/fast_food" in NSI's "brand" namespace,
        # and also listed as "amenity/toilets" in NSI's "operator" namespace.
        # Possible matches should be narrowed down to one of the NSI's
        # namespaces only, depending on whether the ATP item specifies a
        # "brand_operator" and/or "operator_wikidata" value.
        if item.get("brand_wikidata"):
            nsi_matches = list(filter(lambda x: self.nsi_entry_is_brand(x), nsi_matches))
        elif item.get("operator_wikidata"):
            nsi_matches = list(filter(lambda x: self.nsi_entry_is_operator(x), nsi_matches))

        if get_category_tags(item):
            nsi_matches = list(filter(lambda x: self.nsi_entry_has_all_tags(x, get_category_tags(item)), nsi_matches))

            if len(nsi_matches) == 0:
                # Failure to match due to NSI not knowing of the brand/operator
                # with the same top level category tags. For example, "Costco" is
                # known in NSI as being both "shop/warehouse" and
                # "amenity/car_wash". However if the ATP item is "amenity/pub", a
                # match to NSI is not possible as NSI first needs updating to
                # reflect the brand "Costco" opening pubs adjoining their
                # warehouses.
                spider.crawler.stats.inc_value("atp/nsi/match_failed")
                spider.crawler.stats.inc_value("atp/nsi/category_unknown")
                return item

        location_code = item.get_iso_3166_2_code()
        if not location_code:
            location_code = item.get("country")
        nsi_matches = list(filter(lambda x: self.nsi_entry_includes_location(x, location_code), nsi_matches))

        if len(nsi_matches) == 0:
            # Failure to match due to NSI not knowing of the brand/operator
            # operating within the ATP items designated country and first
            # level subdivision. For example, "Chick-fil-A" is known in NSI
            # to operate in 3 countries, but Andorra ("AD") is not one them.
            spider.crawler.stats.inc_value("atp/nsi/match_failed")
            spider.crawler.stats.inc_value("atp/nsi/location_unknown")
            return item

        if len(nsi_matches) == 1 and (not get_category_tags(item) or not location_code):
            # Imperfect match where one NSI entry is returned, but a category
            # match wasn't possible so there is a remaining risk that a
            # mismatch has occurred. Alternatively or additionally, a location
            # match wasn't possible.
            spider.crawler.stats.inc_value("atp/nsi/match_imperfect")
            self.apply_nsi_tags(nsi_matches[0], item)
            return item
        elif len(nsi_matches) == 1:
            # Perfect match where only one NSI entry is returned matching the
            # ATP item.
            spider.crawler.stats.inc_value("atp/nsi/match_perfect")
            self.apply_nsi_tags(nsi_matches[0], item)
            return item

        # Reaching this point means that more than one NSI entry is matching
        # the ATP item. This may occur if NSI knows of "KFC" (of the same
        # Wikidata item) branded fast food restaurants operating globally, but
        # also knows of some country or region specific KFC operations that
        # have their own NSI entries. If the ATP item does not specify a
        # country and first level subvision, both of the two KFC NSI entries
        # could be returned at this point. Matching fails here because it's
        # unknown which of the multiple NSI matches to apply.
        spider.crawler.stats.inc_value("atp/nsi/match_failed")
        spider.crawler.stats.inc_value("atp/nsi/multiple_matches")
        return item

    @staticmethod
    def nsi_entry_is_brand(nsi_entry: dict) -> bool:
        """
        Check that a provided NSI entry is in NSI's "brand" category.
        :param nsi_entry: NSI entry as a dictionary.
        :return: True if the supplied NSI entry is within NSI's "brand"
                 category, and False otherwise.
        """
        if not nsi_entry.get("tags"):
            return False
        if nsi_entry["tags"].get("brand:wikidata"):
            return True
        return False

    @staticmethod
    def nsi_entry_is_operator(nsi_entry: dict) -> bool:
        """
        Check that a provided NSI entry is in NSI's "operator" category.
        :param nsi_entry: NSI entry as a dictionary.
        :return: True If the supplied NSI entry is within NSI's "operator"
                 category, and False otherwise.
        """
        if not nsi_entry.get("tags"):
            return False
        if nsi_entry["tags"].get("operator:wikidata") and not nsi_entry["tags"].get("brand_wikidata"):
            return True
        return False

    @staticmethod
    def nsi_entry_has_all_tags(nsi_entry: dict, tags: dict) -> bool:
        """
        Check that a provided NSI entry has all of the provided tags.
        :param nsi_entry: NSI entry as a dictionary.
        :param tags: dictionary of OSM tags to compare, such as
                     {"shop": "supermarket"}, case sensitive.
        :return: True if the supplied NSI entry contains all of the provided
                 OSM tags, and False otherwise. If the NSI entry and supplied
                 tags are both undefined, this function returns True.
        """
        if not nsi_entry.get("tags") or not isinstance(tags, dict):
            return False
        for key, value in tags.items():
            if key not in nsi_entry["tags"].keys():
                return False
            if nsi_entry["tags"][key] != value:
                return False
        return True

    @staticmethod
    def nsi_entry_includes_location(nsi_entry: dict, location_code: str | None) -> bool:
        """
        Check that a provided NSI entry applies to the supplied ISO 3166-1
        alpha-2 or ISO 3166-2 location code.
        :param nsi_entry: NSI entry as a dictionary.
        :param location_code: ISO 3166-1 alpha-2 code or ISO 3166-2 code,
                              such as "US" or "US-TX", case insensitive. Can
                              also be None in which case an NSI match will
                              only occur if it applies globally ("001").
        :return: True if the supplied NSI entry applies to the supplied
                 location code, and False otherwise.
        """
        if not nsi_entry.get("locationSet") or not (isinstance(location_code, str) or location_code is None):
            return False
        if not nsi_entry["locationSet"].get("include"):
            return False
        if len(nsi_entry["locationSet"]["include"]) == 0 and location_code is None:
            return True
        if "001" in nsi_entry["locationSet"]["include"] and location_code is None:
            return True
        if location_code is None:
            return False
        if nsi_entry["locationSet"].get("exclude"):
            excluded_location_codes = list(
                map(lambda x: x.replace(".geojson", ""), nsi_entry["locationSet"]["exclude"])
            )
            if location_code.lower().split("-")[0] in excluded_location_codes:
                return False
            if location_code.lower() in excluded_location_codes:
                return False
        if "001" in nsi_entry["locationSet"]["include"]:
            return True
        included_location_codes = list(map(lambda x: x.replace(".geojson", ""), nsi_entry["locationSet"]["include"]))
        if location_code.lower().split("-")[0] in included_location_codes:
            return True
        if location_code.lower() in included_location_codes:
            return True
        return False

    @staticmethod
    def apply_nsi_tags(nsi_entry: dict, item: Feature) -> None:
        """
        Apply missing tags from an NSI entry to an ATP Feature. Existing tags
        on the ATP Feature are not overwritten. Instead, the mismatching tags
        from the NSI entry are ignored.
        :param nsi_entry: NSI entry as a dictionary.
        :param item: ATP Feature to apply missing tags to.
        """
        item["nsi_id"] = nsi_entry["id"]

        if not nsi_entry.get("tags"):
            # No tags to apply.
            return

        extras = item.get("extras", {})
        for key, value in nsi_entry["tags"].items():
            if key == "brand:wikidata":
                key = "brand_wikidata"
            elif key == "operator:wikidata":
                key = "operator_wikidata"
            if key in item.fields:
                if item.get(key) is None:
                    item[key] = value
            else:
                if extras.get(key) is None:
                    extras[key] = value
        item["extras"] = extras
