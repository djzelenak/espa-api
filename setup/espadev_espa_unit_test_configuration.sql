set search_path = espa_unit_test;

INSERT INTO ordering_configuration (key, value) VALUES
    ('url.dev.orderservice', 'http://host.com'),
    ('url.dev.orderupdate', 'http://host.com'),
    ('url.dev.orderdelivery', 'http://host.com'),
    ('url.dev.registration', 'http://host.com'),
    ('url.dev.internal_cache', 'hostname')
;
