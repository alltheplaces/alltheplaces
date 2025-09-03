from scrapy import Spider


class AddressSpider(Spider):
    custom_settings = {
        "ITEM_PIPELINES": {
            "locations.pipelines.duplicates.DuplicatesPipeline": 200,
            "locations.pipelines.drop_attributes.DropAttributesPipeline": 250,
            "locations.pipelines.apply_spider_level_attributes.ApplySpiderLevelAttributesPipeline": 300,
            "locations.pipelines.apply_spider_name.ApplySpiderNamePipeline": 350,
            "locations.pipelines.clean_strings.CleanStringsPipeline": 354,
            "locations.pipelines.country_code_clean_up.CountryCodeCleanUpPipeline": 355,
            "locations.pipelines.state_clean_up.StateCodeCleanUpPipeline": 356,
            "locations.pipelines.address_clean_up.AddressCleanUpPipeline": 357,
            "locations.pipelines.phone_clean_up.PhoneCleanUpPipeline": None,
            "locations.pipelines.email_clean_up.EmailCleanUpPipeline": None,
            "locations.pipelines.geojson_geometry_reprojection.GeoJSONGeometryReprojectionPipeline": None,
            "locations.pipelines.extract_gb_postcode.ExtractGBPostcodePipeline": None,
            "locations.pipelines.assert_url_scheme.AssertURLSchemePipeline": None,
            "locations.pipelines.drop_logo.DropLogoPipeline": None,
            "locations.pipelines.closed.ClosePipeline": None,
            "locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None,
            "locations.pipelines.check_item_properties.CheckItemPropertiesPipeline": 750,
            "locations.pipelines.geojson_multipoint_simplification.GeoJSONMultiPointSimplificationPipeline": None,
            "locations.pipelines.count_categories.CountCategoriesPipeline": None,
            "locations.pipelines.count_brands.CountBrandsPipeline": None,
            "locations.pipelines.count_operators.CountOperatorsPipeline": None,
        }
    }
