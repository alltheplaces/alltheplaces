from scrapy import Spider
from scrapy.utils.test import get_crawler

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.apply_nsi_categories import ApplyNSICategoriesPipeline


def get_test_objects(spider_name: str, brand_wikidata: str | None = None, operator_wikidata: str | None = None, country: str | None = None, state: str | None = None, categories: list[dict] | None = None) -> (Feature, ApplyNSICategoriesPipeline, Spider):
    spider = Spider(name=spider_name)
    spider.crawler = get_crawler()
    feature_properties = {
        "brand_wikidata": brand_wikidata,
        "operator_wikidata": operator_wikidata,
        "country": country,
        "state": state,
    }
    feature = Feature(**feature_properties)
    if isinstance(categories, list):
        for category in categories:
            apply_category(category, feature)
    return feature, ApplyNSICategoriesPipeline(), spider


def test_skip_nsi_matching():
    item, pipeline, spider = get_test_objects(spider_name="kfc_us", brand_wikidata="Q524757", country="US", state="TX", categories=[Categories.FAST_FOOD.value])
    item["nsi_id"] = "-1"
    pipeline.process_item(item, spider)
    assert item["nsi_id"] == "-1"

    item, pipeline, spider = get_test_objects(spider_name="kfc_us", brand_wikidata="Q524757", country="US", state="TX", categories=[Categories.FAST_FOOD.value])
    item["nsi_id"] = "1234567"
    pipeline.process_item(item, spider)
    assert item["nsi_id"] == "1234567"


def test_brand_missing():
    item, pipeline, spider = get_test_objects(spider_name="kfc_us", operator_wikidata="Q668737")
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_operator_missing():
    item, pipeline, spider = get_test_objects(spider_name="city_of_darwin_cctv_au", brand_wikidata="Q125673118")
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_and_operator_missing():
    item, pipeline, spider = get_test_objects(spider_name="failing_spider")
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_category_missing():
    # Not a fatal condition for brands to be missing a category, but this is
    # likely to change in the future to enhance NSI matching accuracy. It is
    # somewhat rare that a brand will exist in the same region but have two
    # or more feature types. As an example of where this matching can be
    # invalid, consider a brand that can be both a supermarket and a
    # convenience store, with no difference in branding or labelling of each
    # feature.
    item, pipeline, spider = get_test_objects(spider_name="kfc_us", brand_wikidata="Q524757", country="US", state="TX")
    pipeline.process_item(item, spider)
    assert item.get("nsi_id")


def test_brand_category_required():
    # Some brands have two different types of features being operated under
    # the same brand. In these circumstances, a category MUST be supplied to
    # disambiguate between the two types of features to match against.
    item, pipeline, spider = get_test_objects(spider_name="costco_us", brand_wikidata="Q715583", country="US", state="TX", categories=[Categories.CAR_WASH.value])
    pipeline.process_item(item, spider)
    assert item.get("nsi_id")

    # Is this Costco feature shop=wholesale, amenity=car_wash...? No match is
    # possible without the category being specified.
    item, pipeline, spider = get_test_objects(spider_name="costco_us", brand_wikidata="Q715583", country="US", state="TX")
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_operator_category_missing():
    # It is a fatal condition for operators to be missing a category. This
    # differs from brands because it is far more likely for NSI matching to be
    # incorrect for operators if a category is not supplied. Operators
    # typically operate many types of features, whereas brands typically apply
    # to a single type of feature. As an example, an operator may operate
    # sports pitches, playgrounds, car parks, surveillance cameras, public
    # toilets and rubbish bins.
    item, pipeline, spider = get_test_objects(spider_name="city_of_darwin_cctv_au", operator_wikidata="Q125673118", country="AU", state="NT")
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_country_missing():
    # A match is unsuccessful if NSI specifies a brand operating in a specific
    # country, and not globally ("001") but the ATP item fails to specify a
    # country.
    item, pipeline, spider = get_test_objects(spider_name="woolworths_au", brand_wikidata="Q3249145", state="NSW", categories=[Categories.SHOP_SUPERMARKET.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # A match fails if the country is specified as a blank string (not just
    # "None") and there is no global ("001") applicability of the brand.
    item, pipeline, spider = get_test_objects(spider_name="woolworths_au", brand_wikidata="Q3249145", country="", state="NSW", categories=[Categories.SHOP_SUPERMARKET.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_country_invalid():
    # Brand is not known by NSI to operate in a specific country.
    # Country is specified as ISO 3166-2 code.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_gb", brand_wikidata="Q5659832", country="GB", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Brand is not known by NSI to operate in a specific country.
    # Country is specified as a full official name.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_gb", brand_wikidata="Q5659832", country="United Kingdom", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Specified country is entirely invalid.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_gb", brand_wikidata="Q5659832", country="ZZ", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_country_not_required():
    # A match is successful if NSI has a default global entry ("001") and there is
    # no ambiguity in matching without a country/state provided.
    item, pipeline, spider = get_test_objects(spider_name="kfc_us", brand_wikidata="Q524757", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert item.get("nsi_id")


def test_brand_country_required():
    # A match is unsuccessful if NSI specifies a brand operating in a specific
    # country (or countries), but the ATP item fails to specify a country.
    item, pipeline, spider = get_test_objects(spider_name="woolworths_au", brand_wikidata="Q3249145", categories=[Categories.SHOP_SUPERMARKET.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Another failure to specify a country is the country being a blank string
    # (and not just the default "None") value.
    item, pipeline, spider = get_test_objects(spider_name="woolworths_au", brand_wikidata="Q3249145", country="", categories=[Categories.SHOP_SUPERMARKET.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_state_missing():
    # A match is unsuccessful if NSI specifies a brand operating in a specific
    # region, but the ATP item fails to specify a region and only specifies a
    # broader location at a country level.
    item, pipeline, spider = get_test_objects(spider_name="first_national_bank_texas_us", brand_wikidata="Q110622177", country="US", categories=[Categories.BANK.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # A match fails if the state is specified as a blank string (not just
    # "None") and there is no country-wide or global ("001") applicability of
    # the brand.
    item, pipeline, spider = get_test_objects(spider_name="first_national_bank_texas_us", brand_wikidata="Q110622177", country="US", state="", categories=[Categories.BANK.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Failure to match one of multiple specific regions identified.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_us", brand_wikidata="Q5659832", country="US", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_state_invalid():
    # Brand is not known by NSI to operate in a specific region.
    # Region is specified as ISO 3166-2 code.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_us", brand_wikidata="Q5659832", country="US", state="AL", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Brand is not known by NSI to operate in a specific region.
    # Region is specified as a full official name.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_us", brand_wikidata="Q5659832", country="US", state="Alabama", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Specified region is entirely invalid.
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_us", brand_wikidata="Q5659832", country="US", state="ZZ", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")

    # Specified region is a blank string (not the default of None).
    item, pipeline, spider = get_test_objects(spider_name="harolds_chicken_shack_us", brand_wikidata="Q5659832", country="US", state="", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert not item.get("nsi_id")


def test_brand_state_not_required():
    # A match is successful if NSI specifies a brand operating in a country
    # and the ATP item specifies both a country and a region within.
    item, pipeline, spider = get_test_objects(spider_name="kfc_us", brand_wikidata="Q524757", country="US", state="TX", categories=[Categories.FAST_FOOD.value])
    pipeline.process_item(item, spider)
    assert item.get("nsi_id")
