set search_path = espa_unit_test;

INSERT INTO ordering_configuration (key, value) VALUES

-- api.external.lta
    ('url.dev.orderservice', 'http://host.com'),
    ('url.dev.orderupdate', 'http://host.com'),
    ('url.dev.orderdelivery', 'http://host.com'),
    ('url.dev.registration', 'http://host.com'),
    ('url.dev.earthexplorer', 'http://host.com'),
    ('url.dev.internal_cache', 'hostname'),
    ('url.dev.external_cache', 'hostname'),

-- api.external.ers
    ('url.dev.ersapi', 'http://host.com'),

-- api.external.lpdaac
    ('url.dev.modis.datapool', 'hostname:port'),

-- api.notification.email
    ('url.dev.status_url', 'http://host.com')

;
