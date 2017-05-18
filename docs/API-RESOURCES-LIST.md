### User API Operations

#### Messages

The HTTP Response Code coming from the server is the primary method of alerting users of the results of their request (success/fail). 
In addition to the HTTP Response Code, the JSON response will also include any `"messages"` which will give clarification of the Response Code, and should always be examined.
 
The JSON response will only contain `"messages"` if there is an associated message field contained. It will only contain one object, either: 
1. **Errors**: An un-recoverable error has occurred
  * `"messages": {"errors": [...]}` 
1. **Warnings**: Nothing wrong has occurred inside the system, but these warnings can later elevate to errors (for example, if a product becomes deprecated). 
  * `"messages": {"warnings": [...]}`
  
#### HTTP Status Codes

The status code will match the desired behavior, depending on the HTTP Method used:

* GET: Performs searches for current system states
  * `200 OK`: The search was performed successfully (**Note:** the result returned may be an empty object)
  * `401 Authenication Failed`: Could not authenticate the username/password combination
  * `403 Forbidden`: The user is not allowed to access the system
  * `404 Not Found`: The server could not perform the requested operation
* POST: For every request, a new state on the server is created 
  * `201 Created`: A new resource has been created, information of which is included in the response
  * `400 Bad Request`: Unable to parse the supplied message
  * `405 Method Not Allowed`: Cannot perform POST
* PUT: Updates a resource, changing it to the desired state
  * `202 Accepted`: The resource has been updated, and the response represents the new state

There are circumstances when the server supersedes the API, and gives information related to its current configuration: 

* Server maintenance: The server is either down for maintenance, or experiencing extreme difficulties
  * `500 Internal Server Error`: This likely means the server is on fire, and system admins are working to restore it
  * `503 Service Unavailable`: This means the server is down for regular maintenance
* Host redirection: The hostname supplied is now living at a new location
  * `301 Moved Permanently`: Use the location header to navigate to the correct page
    * This is usually used for HTTPS redirection, but will also occur during system maintenance
  
#### Schema definitions

The following resources are available for navigating the API, in the hopes that the API itself can guide users through its usage in a straightforward and explicit manner. 

HTTP Method	| URI	| Action
---|---|---
[GET](#api)  |  `/api/`  |  Lists all available versions of the api.
[GET](#apiOps)  |  `/api/v0`  |  Lists all available api operations.
[GET](#apiProdsGet)  |  `/api/v0/available-products/<product_id>`  |  Lists the available output products for the supplied input.
[POST](#apiProdsPost)  |  `/api/v0/available-products`  |  Lists available products for the supplied inputs. Also classifies the inputs by sensor or lists as 'not implemented' if the values cannot be ordered or determined.
[GET](#apiProj)  |  `/api/v0/projections`  |  Lists and describes available projections. This is a dump of the schema defined that constrains projection info.
[GET](#apiFormats)  |  `/api/v0/formats`  |  Lists all available output formats
[GET](#apiResamp)  |  `/api/v0/resampling-methods`  |  Lists all available resampling methods
[GET](#apiOrderSchema)  |  `/api/v0/order-schema`  |  Retrieves order schema definition


#### User

The following endpoints exist for validating that the ERS authentication service is working. 

HTTP Method	| URI	| Action
---|---|---
[GET](#apiUser)  |  `/api/v0/user`  |  Returns user information for the authenticated user.


#### Orders

HTTP Method	| URI	| Action
---|---|---
[POST](#apiSubmitOrder)  |  `/api/v0/order ` |  Accepts requests for processing. The order is validated, and an orderid is returned.
[PUT](#apiUpdateOrder)  |  `/api/v0/order ` |  
[GET](#apiStatus)  |  `/api/v0/order-status/<ordernum>`  |  Retrieves a submitted orders status
[GET](#apiOrderDetails)  |  `/api/v0/order/<ordernum>`  |  Retrieves details for a submitted order. Some information may be omitted from this response depending on access privileges.
[GET](#apiOrders)  |  `/api/v0/list-orders`  |  List orders for the authenticated user.
[GET](#apiOrdersEmail)  |  `/api/v0/list-orders/<email>`  |  Lists orders for the supplied email. Necessary to support user collaboration. Accepts JSON filters.

#### Scenes

These endpoints are the only access to the real-time status of the final output products. 

HTTP Method	| URI	| Action
---|---|---
[GET](#apiItemStats)  |  `/api/v0/item-status/<ordernum>`  |  Retrieve the status and details for all products in an order.
[GET](#apiProdStats)  |  `/api/v0/item-status/<ordernum>/<itemnum>`  |  Retrieve status and details for a particular product in an order


#### Known Issues

* POST requests from most MS Windows terminals/command-prompts require json 
objects be wrapped in double quotes with internal strings wrapped in escaped 
double quotes. For example:
```"{\"olitirs8\": {\"inputs\": [\"LC08_L1TP_027027_20160722_20170221_01_T1\"],\"products...```
For more info, see [Issue #42](https://github.com/USGS-EROS/espa-api/issues/42#issuecomment-263454906)

---

**GET /api**<a id="api"></a>

Lists all available versions of the api.
```json
curl --user username:password https://espa.cr.usgs.gov/api

{
    "versions": {
        "v0": {
            "description": "First release of the ESPA API"
        }
    }
}
```

**GET /api/v0**<a id="apiOps"></a>

Lists all available api operations.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0
{
    "description": "Version 0 of the ESPA API",
    "operations": {
        "/api": {
            "function": "list versions",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0": {
            "function": "list operations",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0/available-products": {
            "comments": "sceneids should be delivered in the product_ids parameter, comma separated if more than one",
            "function": "list available products per sceneid",
            "methods": [
                "HEAD",
                "POST"
            ]
        },
        "/api/v0/available-products/<product_ids>": {
            "comments": "comma separated ids supported",
            "function": "list available products per sceneid",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0/formats": {
            "function": "list available output formats",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
            "/api/v0/order": {
            "function": "point for accepting processing requests via HTTP POST with JSON body. Errors are returned to user, successful validation returns an orderid",
            "methods": [
                "POST"
            ]
        },
        "/api/v0/order/<ordernum>": {
            "function": "retrieves a submitted order",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0/list-orders": {
            "function": "list orders for authenticated user",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0/list-orders/<email>": {
            "function": "list orders for supplied email, for user collaboration",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0/projections": {
            "function": "list available projections",
            "methods": [
                "HEAD",
                "GET"
            ]
        },
        "/api/v0/resampling-methods": {
            "function": "list available resampling methods",
            "methods": [
                "HEAD",
                "GET"
            ]
        }
    }
}

```

**GET /api/v0/user**<a id="apiUser"></a>

Returns user information for the authenticated user.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/user

{
  "email": "production@email.com",
  "first_name": "Production",
  "last_name": "Person",
  "roles": [
    "user",
    "production"
  ],
  "username": "production"
}
```
   
**GET /api/v0/available-products/\<product_id\>**<a id="apiProdsGet"></a>

Lists the available output products for the supplied input.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/available-products/LE07_L1TP_027027_20160730_20160831_01_T1
{
    "etm7": {
        "inputs": [
            "LE07_L1TP_029030_20170221_20170319_01_T1"
        ], 
        "products": [
            "source_metadata", 
            "l1", 
            "toa", 
            "bt", 
            "cloud", 
            "sr", 
            "lst", 
            "swe", 
            "sr_ndvi", 
            "sr_evi", 
            "sr_savi", 
            "sr_msavi", 
            "sr_ndmi", 
            "sr_nbr", 
            "sr_nbr2", 
            "stats"
        ]
    }
}
```

**POST /api/v0/available-products**<a id="apiProdsPost"></a>

Lists available products for the supplied inputs.  Also classifies the inputs by sensor or lists as 'not implemented' if the values cannot be ordered or determined.

```json
curl  --user username:password -d '{"inputs":["LE07_L1TP_029030_20170221_20170319_01_T1",
               "MOD09A1.A2000073.h12v11.005.2008238080250.hdf", "bad_scene_id"]}' https://espa.cr.usgs.gov/api/v0/available-products
{
    "etm7": {
        "inputs": [
            "LE07_L1TP_029030_20170221_20170319_01_T1"
        ], 
        "products": [
            "source_metadata", 
            "l1", 
            "toa", 
            "bt", 
            "cloud", 
            "sr", 
            "lst", 
            "swe", 
            "sr_ndvi", 
            "sr_evi", 
            "sr_savi", 
            "sr_msavi", 
            "sr_ndmi", 
            "sr_nbr", 
            "sr_nbr2", 
            "stats"
        ]
    }, 
    "mod09a1": {
        "inputs": [
            "MOD09A1.A2000073.h12v11.005.2008238080250.hdf"
        ], 
        "outputs": [
            "l1", 
            "stats"
        ]
    }, 
    "not_implemented": [
        "bad_scene_id"
    ]
}
```

**GET /api/v0/projections**<a id="apiProj"></a>

Lists and describes available projections.  This is a dump of the schema defined that constrains projection info.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/projections
{
    "aea": {
        "properties": {
            "central_meridian": {
                "maximum": 180, 
                "minimum": -180, 
                "required": true, 
                "type": "number"
            }, 
            "datum": {
                "enum": [
                    "wgs84", 
                    "nad27", 
                    "nad83"
                ], 
                "required": true, 
                "type": "string"
            }, 
            "false_easting": {
                "required": true, 
                "type": "number"
            }, 
            "false_northing": {
                "required": true, 
                "type": "number"
            }, 
            "latitude_of_origin": {
                "maximum": 90, 
                "minimum": -90, 
                "required": true, 
                "type": "number"
            }, 
            "standard_parallel_1": {
                "maximum": 90, 
                "minimum": -90, 
                "required": true, 
                "type": "number"
            }, 
            "standard_parallel_2": {
                "maximum": 90, 
                "minimum": -90, 
                "required": true, 
                "type": "number"
            }
        },
        "type": "object"
    }, 
    "lonlat": {
        "type": "null"
    }, 
    "ps": {
        "properties": {
            "false_easting": {
                "required": true, 
                "type": "number"
            }, 
            "false_northing": {
                "required": true, 
                "type": "number"
            }, 
            "latitude_true_scale": {
                "abs_rng": [
                    60, 
                    90
                ], 
                "required": true, 
                "type": "number"
            }, 
            "longitudinal_pole": {
                "maximum": 180, 
                "minimum": -180, 
                "required": true, 
                "type": "number"
            }
        }, 
        "type": "object"
    }, 
    "sinu": {
        "properties": {
            "central_meridian": {
                "maximum": 180, 
                "minimum": -180, 
                "required": true, 
                "type": "number"
            }, 
            "false_easting": {
                "required": true, 
                "type": "number"
            }, 
            "false_northing": {
                "required": true, 
                "type": "number"
            }
        }, 
        "type": "object"
    },
    "utm": {
        "properties": {
            "zone": {
                "maximum": 60, 
                "minimum": 1, 
                "required": true, 
                "type": "integer"
            }, 
            "zone_ns": {
                "enum": [
                    "north", 
                    "south"
                ], 
                "required": true, 
                "type": "string"
            }
        }, 
        "type": "object"
    }
}        
```

**GET /api/v0/formats**<a id="apiFormats"></a>

Lists all available output formats
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/formats

{
  "formats": [
    "gtiff", 
    "hdf-eos2", 
    "envi"
  ]
}
```

**GET /api/v0/resampling-methods**<a id="apiResamp"></a>

Lists all available resampling methods
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/resampling-methods

{
  "resampling_methods": [
    "nn", 
    "bil", 
    "cc"
  ]
}
```

**GET /api/v0/list-orders**<a id="apiOrders"></a>

List orders for the authenticated user.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/list-orders

{
  "orders": [
    "production@email.com-101015143201-00132", 
    "production@email.com-101115143201-00132"
  ]
}
```

**GET /api/v0/list-orders/\<email\>**<a id="apiOrdersEmail"></a>

Lists orders for the supplied email.  Necessary to support user collaboration.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/list-orders/production@email.com

{
  "orders": [
    "production@email.com-101015143201-00132", 
    "production@email.com-101115143201-00132"
  ]
}
```

**GET /api/v0/order-status/\<ordernum\>**<a id="apiStatus"></a>

Retrieves a submitted orders status

```json
{
 "orderid": "production@usgs.gov-07282016-135122",
 "status": "complete"
}
```

**GET /api/v0/order/\<ordernum\>**<a id="apiOrderDetails"></a>

Retrieves details for a submitted order. Some information may be omitted from this response depending on access privileges.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/order/production@usgs.gov-03072016-081013
{
  "completion_date": "2016-08-01T14:47:08.589621",
  "note": "",
  "order_date": "2016-08-01T14:17:48.589621",
  "order_source": "espa",
  "order_type": "level2_ondemand",
  "orderid": "production@usgs.gov-03072016-081013",
  "priority": "normal",
  "product_options": null,
  "product_opts": {
    "format": "gtiff",
    "tm5": {
      "inputs": [
        "LT05_L1TP_026028_20111022_20160830_01_T1"
      ],
      "products": [
        "sr"
      ]
    }
  },
  "status": "complete"
}
```

**GET /api/v0/item-status/\<ordernum\>**<a id="apiItemStats"></a>

Retrieve the status and details for all products in an order.
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/item-status/production@usgs.gov-03072016-081013

{
 "orderid": {
             "production@usgs.gov-07282016-135122": [
                {
                       "cksum_download_url": "http://espa.cr.usgs.gov/orders/production@usgs.gov-07282016-135122/LC080270272016072201T1-SC20160728135757.md5",
                       "completion_date": "2016-08-01T14:17:08.589621",
                       "name": "LC08_L1TP_027027_20160722_20170221_01_T1",
                       "note": "",
                       "product_dload_url": "http://espa.cr.usgs.gov/orders/production@usgs.gov-07282016-135122/LC080270272016072201T1-SC20160728135757.tar.gz",
                       "status": "complete"
                },
                {
                       "cksum_download_url": "http://espa.cr.usgs.gov/orders/production@usgs.gov-08042016-120321-382/LT050260282011102201T1-SC20160804121126.md5",
                       "completion_date": "2016-08-01T14:17:08.589621",
                       "name": "LT05_L1TP_026028_20111022_20160830_01_T1",
                       "note": "",
                       "product_dload_url": "http://espa.cr.usgs.gov/orders/production@usgs.gov-08042016-120321-382/LT050260282011102201T1-SC20160804121126.tar.gz",
                       
                       "status": "complete"
                }
             ]
         }
 }

```

**GET /api/v0/item-status/\<ordernum\>/\<itemnum\>**<a id="apiProdStats"></a>

Retrieve status and details for a particular product in an order
```json
curl --user username:password https://espa.cr.usgs.gov/api/v0/item-status/production@usgs.gov-03072016-081013/LC08_L1TP_027027_20160722_20170221_01_T1

{
 "orderid": {
             "production@usgs.gov-07282016-135122": [
                {
                       "cksum_download_url": "http://espa.cr.usgs.gov/orders/production@usgs.gov-07282016-135122/LC080270272016072201T1-SC20160728135757.md5",
                       "completion_date": "2016-08-01T14:17:08.589621",
                       "name": "LC08_L1TP_027027_20160722_20170221_01_T1",
                       "note": "",
                       "product_dload_url": "http://espa.cr.usgs.gov/orders/production@usgs.gov-07282016-135122/LC080270272016072201T1-SC20160728135757.tar.gz",
                       "status": "complete"
                }
             ]
         }
 }

```

**POST /api/v0/order**<a id="apiSubmitOrder"></a>

Accepts requests for process from an HTTP POST with a JSON body.  The body is validated and any errors are returned to the caller.  Otherwise, an orderid is returned.

```
POST requests using curl from MS Windows require json objects be wrapped in double quotes
with internal strings wrapped in escaped double quotes
"{\"inputs\":[\"LE07_L1TP_027027_20160730_20160831_01_T1\", \"MOD09A1.A2000073.h12v11.005.2008238080250.hdf\", \"bad_scene_id\"]}"
```

```json

curl --user username:password -d '{"olitirs8": {
                                                    "inputs": ["LC08_L1TP_027027_20160722_20170221_01_T1"], 
                                                    "products": ["sr"]
                                                 }, 
                                     "format": "gtiff", 
                                     "resize": {
                                                "pixel_size": 60, 
                                                "pixel_size_units": "meters"
                                                }, 
                                     "resampling_method": "nn", 
                                     "plot_statistics": true, 
                                     "projection": {
                                                    "aea": {
                                                            "standard_parallel_1": 29.5,
                                                            "standard_parallel_2": 45.5,
                                                            "central_meridian": -96.0,
                                                            "latitude_of_origin": 23.0,
                                                            "false_easting": 0.0,
                                                            "false_northing": 0.0,
                                                            "datum": "wgs84"
                                                            }
                                                    },
                                     "image_extents": {
                                                        "north": 0.0002695,
                                                        "south": 0,
                                                        "east": 0.0002695,
                                                        "west": 0,
                                                        "units": "dd"
                                                    },
                                     "note": "this is going to be sweet..."
                                     }' https://espa.cr.usgs.gov/api/v0/order

Returns:
{
    "orderid": "production@email.com-101015143201-00132"
}
```


**GET /api/v0/order-schema**<a id="apiOrderSchema"></a>
 
Retrieves order schema definition
```javascript
curl --user username:password https://espa.cr.usgs.gov/api/v0/order-schema

{"oneormoreobjects": ["myd09gq",
                       "myd09ga",
                       "oli8",
                       "myd13q1",
                       "tm4",
                       "tm5",
                       "etm7",
                       "mod13a1",
                       "mod13a2",
                       "mod13a3",
                       "mod09a1",
                       "mod09ga",
                       "myd13a2",
                       "myd13a3",
                       "olitirs8",
                       "myd13a1",
                       "mod13q1",
                       "myd09q1",
                       "mod09q1",
                       "myd09a1",
                       "mod09gq"],
 "properties": {"etm7": {"properties": {"inputs": {"ItemCount": "inputs",
                                                       "items": {"pattern": "^le07_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$",
                                                                  "type": "string"},
                                                       "minItems": 1,
                                                       "required": True,
                                                       "type": "array",
                                                       "uniqueItems": True},
                                           "products": {"items": {"enum": ["source_metadata",
                                                                              "l1",
                                                                              "toa",
                                                                              "bt",
                                                                              "cloud",
                                                                              "sr",
                                                                              "lst",
                                                                              "swe",
                                                                              "sr_ndvi",
                                                                              "sr_evi",
                                                                              "sr_savi",
                                                                              "sr_msavi",
                                                                              "sr_ndmi",
                                                                              "sr_nbr",
                                                                              "sr_nbr2",
                                                                              "stats"],
                                                                    "type": "string"},
                                                         "minItems": 1,
                                                         "required": True,
                                                         "restricted": True,
                                                         "stats": True,
                                                         "type": "array",
                                                         "uniqueItems": True}},
                           "type": "object"},
                 "format": {"enum": ["gtiff", "hdf-eos2", "envi"],
                             "required": True,
                             "type": "string"},
                 "image_extents": {"dependencies": ["projection"],
                                    "extents": 200000000,
                                    "properties": {"east": {"required": True,
                                                              "type": "number"},
                                                    "north": {"required": True,
                                                               "type": "number"},
                                                    "south": {"required": True,
                                                               "type": "number"},
                                                    "units": {"enum": ["dd",
                                                                         "meters"],
                                                               "required": True,
                                                               "type": "string"},
                                                    "west": {"required": True,
                                                              "type": "number"}},
                                    "type": "object"},
                 "mod09a1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod09a1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod09ga": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod09ga\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod09gq": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod09gq\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod09q1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod09q1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod13a1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod13a1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod13a2": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod13a2\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod13a3": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod13a3\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "mod13q1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^mod13q1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd09a1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd09a1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd09ga": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd09ga\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd09gq": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd09gq\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd09q1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd09q1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd13a1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd13a1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd13a2": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd13a2\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd13a3": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd13a3\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "myd13q1": {"properties": {"inputs": {"ItemCount": "inputs",
                                                          "items": {"pattern": "^myd13q1\\.a\\d{7}\\.h\\d{2}v\\d{2}\\.005\\.\\d{13}$",
                                                                     "type": "string"},
                                                          "minItems": 1,
                                                          "required": True,
                                                          "type": "array",
                                                          "uniqueItems": True},
                                              "products": {"items": {"enum": ["l1",
                                                                                 "stats"],
                                                                       "type": "string"},
                                                            "minItems": 1,
                                                            "required": True,
                                                            "restricted": True,
                                                            "stats": True,
                                                            "type": "array",
                                                            "uniqueItems": True}},
                              "type": "object"},
                 "note": {"blank": True,
                           "required": False,
                           "type": "string"},
                 "oli8": {"properties": {"inputs": {"ItemCount": "inputs",
                                                       "items": {"pattern": "^lo08_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$",
                                                                  "type": "string"},
                                                       "minItems": 1,
                                                       "required": True,
                                                       "type": "array",
                                                       "uniqueItems": True},
                                           "products": {"items": {"enum": ["source_metadata",
                                                                              "l1",
                                                                              "toa",
                                                                              "stats"],
                                                                    "type": "string"},
                                                         "minItems": 1,
                                                         "required": True,
                                                         "restricted": True,
                                                         "stats": True,
                                                         "type": "array",
                                                         "uniqueItems": True}},
                           "type": "object"},
                 "olitirs8": {"properties": {"inputs": {"ItemCount": "inputs",
                                                           "items": {"pattern": "^lc08_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$",
                                                                      "type": "string"},
                                                           "minItems": 1,
                                                           "required": True,
                                                           "type": "array",
                                                           "uniqueItems": True},
                                               "products": {"items": {"enum": ["source_metadata",
                                                                                  "l1",
                                                                                  "toa",
                                                                                  "bt",
                                                                                  "cloud",
                                                                                  "sr",
                                                                                  "sr_ndvi",
                                                                                  "sr_evi",
                                                                                  "sr_savi",
                                                                                  "sr_msavi",
                                                                                  "sr_ndmi",
                                                                                  "sr_nbr",
                                                                                  "sr_nbr2",
                                                                                  "stats",
                                                                                  "swe"],
                                                                        "type": "string"},
                                                             "minItems": 1,
                                                             "required": True,
                                                             "restricted": True,
                                                             "stats": True,
                                                             "type": "array",
                                                             "uniqueItems": True}},
                               "type": "object"},
                 "plot_statistics": {"type": "boolean"},
                 "projection": {"properties": {"aea": {"properties": {"central_meridian": {"maximum": 180,
                                                                                                "minimum": -180,
                                                                                                "required": True,
                                                                                                "type": "number"},
                                                                          "datum": {"enum": ["wgs84",
                                                                                               "nad27",
                                                                                               "nad83"],
                                                                                     "required": True,
                                                                                     "type": "string"},
                                                                          "false_easting": {"required": True,
                                                                                             "type": "number"},
                                                                          "false_northing": {"required": True,
                                                                                              "type": "number"},
                                                                          "latitude_of_origin": {"maximum": 90,
                                                                                                  "minimum": -90,
                                                                                                  "required": True,
                                                                                                  "type": "number"},
                                                                          "standard_parallel_1": {"maximum": 90,
                                                                                                   "minimum": -90,
                                                                                                   "required": True,
                                                                                                   "type": "number"},
                                                                          "standard_parallel_2": {"maximum": 90,
                                                                                                   "minimum": -90,
                                                                                                   "required": True,
                                                                                                   "type": "number"}},
                                                          "type": "object"},
                                                 "lonlat": {"type": "null"},
                                                 "ps": {"properties": {"false_easting": {"required": True,
                                                                                            "type": "number"},
                                                                         "false_northing": {"required": True,
                                                                                             "type": "number"},
                                                                         "latitude_true_scale": {"abs_rng": [60,
                                                                                                               90],
                                                                                                  "required": True,
                                                                                                  "type": "number"},
                                                                         "longitudinal_pole": {"maximum": 180,
                                                                                                "minimum": -180,
                                                                                                "required": True,
                                                                                                "type": "number"}},
                                                         "type": "object"},
                                                 "sin": {"properties": {"central_meridian": {"maximum": 180,
                                                                                                 "minimum": -180,
                                                                                                 "required": True,
                                                                                                 "type": "number"},
                                                                           "false_easting": {"required": True,
                                                                                              "type": "number"},
                                                                           "false_northing": {"required": True,
                                                                                               "type": "number"}},
                                                           "type": "object"},
                                                 "utm": {"properties": {"zone": {"maximum": 60,
                                                                                    "minimum": 1,
                                                                                    "required": True,
                                                                                    "type": "integer"},
                                                                          "zone_ns": {"enum": ["north",
                                                                                                 "south"],
                                                                                       "required": True,
                                                                                       "type": "string"}},
                                                          "type": "object"}},
                                 "single_obj": True,
                                 "type": "object"},
                 "resampling_method": {"enum": ["nn", "bil", "cc"],
                                        "type": "string"},
                 "resize": {"properties": {"pixel_size": {"ps_dd_rng": [0.0002695,
                                                                            0.0449155],
                                                             "ps_meter_rng": [30,
                                                                               5000],
                                                             "required": True,
                                                             "type": "number"},
                                             "pixel_size_units": {"enum": ["dd",
                                                                             "meters"],
                                                                   "required": True,
                                                                   "type": "string"}},
                             "type": "object"},
                 "tm4": {"properties": {"inputs": {"ItemCount": "inputs",
                                                      "items": {"pattern": "^lt04_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$",
                                                                 "type": "string"},
                                                      "minItems": 1,
                                                      "required": True,
                                                      "type": "array",
                                                      "uniqueItems": True},
                                          "products": {"items": {"enum": ["source_metadata",
                                                                             "l1",
                                                                             "toa",
                                                                             "bt",
                                                                             "cloud",
                                                                             "sr",
                                                                             "swe",
                                                                             "sr_ndvi",
                                                                             "sr_evi",
                                                                             "sr_savi",
                                                                             "sr_msavi",
                                                                             "sr_ndmi",
                                                                             "sr_nbr",
                                                                             "sr_nbr2",
                                                                             "stats"],
                                                                   "type": "string"},
                                                        "minItems": 1,
                                                        "required": True,
                                                        "restricted": True,
                                                        "stats": True,
                                                        "type": "array",
                                                        "uniqueItems": True}},
                          "type": "object"},
                 "tm5": {"properties": {"inputs": {"ItemCount": "inputs",
                                                      "items": {"pattern": "^lt05_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$",
                                                                 "type": "string"},
                                                      "minItems": 1,
                                                      "required": True,
                                                      "type": "array",
                                                      "uniqueItems": True},
                                          "products": {"items": {"enum": ["source_metadata",
                                                                             "l1",
                                                                             "toa",
                                                                             "bt",
                                                                             "cloud",
                                                                             "sr",
                                                                             "lst",
                                                                             "swe",
                                                                             "sr_ndvi",
                                                                             "sr_evi",
                                                                             "sr_savi",
                                                                             "sr_msavi",
                                                                             "sr_ndmi",
                                                                             "sr_nbr",
                                                                             "sr_nbr2",
                                                                             "stats"],
                                                                   "type": "string"},
                                                        "minItems": 1,
                                                        "required": True,
                                                        "restricted": True,
                                                        "stats": True,
                                                        "type": "array",
                                                        "uniqueItems": True}},
                          "type": "object"}},
 "set_ItemCount": ["inputs", 5000],
 "type": "object"}
```