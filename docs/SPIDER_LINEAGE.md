## Spider Lineage

The vast majority of spiders are collecting first party data about a specific brand/chain.
We sometimes call these "brand spiders", these should be well categorised and branded by us, and have original data from
the brand.
We store them in [locations/spiders](../locations/spiders). and  they contain `spider:lineage=S_ATP_BRANDS` in the outputted
`dataset_attributes`.

We also collect government Open Data.
These should also contain license details in `dataset_attributes`.
These spiders are typically bigger than brand spiders, often collecting all of a specific category for a country,
the age of the dataset, or records in the dataset, may be uncomfortably old.
We store them in [locations/government_spiders](../locations/government_spiders), there lineage is `S_ATP_GOVERNMENTS`.

We also collect infrastructure data, these wouldn't typically be called Points of Interest.
These may be anything from trees to electrical sub stations.
These may come from a government, or a company.
We store them in [locations/infrastructure_spiders](../locations/infrastructure_spiders), there lineage is
`S_ATP_INFRASTRUCTURE`.

We also collect data from aggregators, this is likely third party data and as such may contain issues not present in
brand spiders.
We store them in [locations/aggregator_spiders](../locations/aggregator_spiders), there lineage is `S_ATP_AGGREGATORS`.
