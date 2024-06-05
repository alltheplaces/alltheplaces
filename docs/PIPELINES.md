## Pipelines

After an `Item` is emitted from a spider, it goes through several pipelines before it is exported.
If a spider needs to disable these pipelines, they can by overriding `ITEM_PIPELINES` in `custom_settings`.
See [`fedex.py`](../locations/spiders/fedex.py) for an example.

### `DropAttributesPipeline`

When a spider has `drop_attributes`, we remove those attributes from `Feature`s, this happens early, so it may be re added by other pipelines later on.

### `ApplySpiderLevelAttributesPipeline`

When a spider has `item_attributes`, they are applied to all the `Item`s produced by the `Spider`.
We don't override existing attributes, so the spider is free to override its own `item_attributes`.
This typically includes brand details, however it can be any Item field as well as `extras` where we again only override fields that haven't been set in spider.

## `CountryCodeCleanUpPipeline`

This normalises the `country` attribute to a 2-letter country code.
It first checks if a country name has been provided, and if it can turn it onto a country code.
When this fails or no `country` has been provided, we look at the `Item` to work out the country code.
This can be disabled with a spider level attribute `skip_auto_cc = True`.

1. **Spider name**: when the spider name ends with a single country code we apply that.

   This can be disabled by setting `skip_auto_cc_spider_name = True` in the Spider.

2. **Domain name**: when `website` has a country level tld we use it to set the country code.

   This can be disabled with `skip_auto_cc_domain = True`.

3. **Geocoding**: when the above fail, we try to geocode the `Item` using its latitude and longitude.

   This can be disabled with `skip_auto_cc_geocoder = True`.

## `StateCodeCleanUpPipeline`

Items in Canada or the United States get `state` cleaned up to a 2-letter state code.

## `PhoneCleanUpPipeline`

Phone numbers and phone number-like extra attributes (`fax`, `*:phone` and `*:fax`) are normalized to an international format.
We currently output the original data from spider if we fail to parse it.

## `ExtractGBPostcodePipeline`

We attempt to extract the postcode from `Items` in Ireland or Great Britain that don't have `postcode` but do have `addr_full`.

## `AssertURLSchemePipeline`

We apply the `https` scheme to Items with `image` that are missing a URL scheme.

## `DropLogoPipeline`

Items with `image` that mentions `logo` or `favicon` get dropped.

## `ClosePipeline`

Count Items that are flagged as closed and log other Items that may be closed.
We do this for gathering statistics and debugging.

## `ApplyNSICategoriesPipeline`

Attempt to match Items against Name Suggestion Index ([NSI](https://nsi.guide/)).
When successful, we apply the attributes from NSI to the Item, not overriding the spider-provided attributes.

See [NSI Matching](NSI_MATCHING.md) for more details.

This can be disabled by setting `nsi_id='N/A'` in the Spider.

## `CheckItemPropertiesPipeline`

Count missing and invalid properties provided by the spider.
This pipeline will drop coordinate at and near Null Island, however it won't drop other invalid properties.
