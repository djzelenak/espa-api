## Change Notes
###### February 2020
* Remove deprecated validictory library
* Update validation schema to support JSON Schema Draft 3
* Unit test updates to support new validation_provider.py
###### December 2019
* Porting to Python 3
* Remove support for Python 2
###### October 2019
* Transition from Hadoop to Mesos computer cluster
* Added support for Sentinel-2 level-2 products
###### September 2019
* Transition to using M2M JSON API and off SOAP services
###### March-June 2019
* Added support for ordering VIIRS daily NDVI and daily 500-m SR
* Added support for ordering MODIS daily NDVI
* Additional error handling
* Updated ordering restrictions
* Implemented a 10000 open unit limit
###### March 2018
* Final deprecation of Landsat Precollection-based & Cfmask products
###### November 2017
* Changes to Landsat "ST" terminology (staff only)
* Image extents (below 80N/S) must match +/-3 UTM zones
* Pixel Resize must match output projection
###### October 2017
* Restrict orders of only Landsat Level-1
* Add human-readable `title` to objects in JSON order-schema
* Add allowed `pixel_units` against output projections
###### September 2017
* Modify email if all products in order fail
###### August 2017
* Begin using M2M for input validation
###### July 2017
* Upgrade remote calls for Hadoop2
* Add production-api reset queued/processing scene status
###### June 2017
* Ability to cancel orders
* Put all errors/warnings in "messages" JSON field
* Remove CFMask product (replaced by `pixel_qa`)
* Bug fixes for API responses (HTTP Codes, Messages)
* Add JSON filters to available-products, orders, and item-status
* Remove `POST` http method from available-products
###### April 2017
* Restrict ordering of pre-collection landsat inputs
###### March 2017
* Allow MODIS LST (MxD11A1) products
###### January 2017
* Allow Landsat Collections processing
* Allow tm4 and olitirs8 LST products
* Allow MODIS Collection 6 product ordering
* Change email subject line prefix to "USGS ESPA"
* Catch OSError if product download not found
