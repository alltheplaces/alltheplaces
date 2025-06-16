import logging
import pprint

from locations.exporters.geojson import iter_spider_classes_in_modules
from locations.name_suggestion_index import NSI


def test_item_attributes_type():
    for spider_class in iter_spider_classes_in_modules():
        item_attributes = getattr(spider_class, "item_attributes", {})
        assert isinstance(item_attributes, dict)

        if extras := item_attributes.get("extras"):
            assert isinstance(extras, dict)


def test_item_attributes_brand_strings_match_nsi():
    """
    Check if the brand/operator string from the spider matches the brand/operator in NSI.
    Some edge/complex cases might occur that are not possible to solve right away.
    If you face such a case, please add the spider to the ignored_spiders list.
    """
    ignored_spiders = ["sparkasse_de", "ecars"]  # Overcomplicated in NSI  # Complex brand/operator combination in NSI

    fails = []
    spider_names = set()
    for spider_class in iter_spider_classes_in_modules():
        spider_names.add(spider_class.name)

        if spider_class.name in ignored_spiders:
            continue
        for tree in ["brand", "operator"]:
            item_attributes = getattr(spider_class, "item_attributes", {})
            if not isinstance(item_attributes, dict):
                continue

            # Exit early if the item_attributes are not set
            if not item_attributes.get(tree) or not item_attributes.get("{}_wikidata".format(tree)):
                continue
            # Exit early if brand detection is disabled
            if item_attributes.get("nsi_id") == "N/A":
                continue

            entry = False
            entry_details = []
            matching_entry = False
            for nsi_entry in NSI().iter_nsi(item_attributes.get("{}_wikidata".format(tree))):
                entry = True
                if nsi_entry["tags"].get(tree) == item_attributes.get(tree):
                    matching_entry = True
                else:
                    entry_details.append(nsi_entry["tags"].get(tree))

            if entry:
                # Brand is found in NSI, but the brand name does not match.
                if not matching_entry:
                    logging.error(
                        '{}: "{}" tag "{}" does not match expected {}'.format(
                            spider_class.name, tree, item_attributes.get(tree), set(entry_details)
                        )
                    )
                    fails.append((item_attributes, spider_class.name, entry_details))
            else:
                # Brand is not found in NSI.
                # It doesn't contribute to the fails list, as it's currently out of focus
                # logging.warning(
                #     "Missing {} in NSI: {} {}".format(
                #         tree, item_attributes.get(tree), item_attributes.get("{}_wikidata".format(tree))
                #     )
                # )
                continue
    if fails:
        assert False

    ignored_spiders_list_problems = set(ignored_spiders).difference(spider_names)
    if len(ignored_spiders_list_problems):
        pprint.pp("ignored_spiders bad references:")
        pprint.pp(ignored_spiders_list_problems)
        assert False
