import abc

REPORTS = {
    'backlog_request_completions': {
        'display_name': 'Backlog - Requests and Completions',
        'description': 'Shows the number of products requested and completed by day',
        'query':r'''WITH completed_products AS
                        (SELECT completion_date::date "date",
                        COUNT(name) "count"
                        FROM ordering_scene
                        WHERE completion_date >= now() - interval '2 months'
                        GROUP BY completion_date::date
                        ORDER BY completion_date::date)
                    SELECT
                    o.order_date::date "Date",
                    COUNT(s.name) "Products Ordered",
                    cp.count "Products Completed",
                    COUNT(s.name) - cp.count "Difference"
                    FROM ordering_scene s,
                    completed_products cp,
                    ordering_order o
                    WHERE o.id = s.order_id
                    AND o.order_date::date = cp.date
                    AND o.order_date >= now() - interval '2 months'
                    GROUP BY o.order_date::date, cp.count
                    ORDER BY o.order_date::date'''
    },
    'backlog_input_product_types': {
        'display_name': 'Backlog - Input Types',
        'description': 'Input product type counts',
        'query': r'''SELECT
                     COUNT(*) "Total",
                     SUM(CASE WHEN name LIKE 'LC08%' THEN 1 ELSE 0 END) "OLI/TIRS",
                     SUM(CASE WHEN name LIKE 'LO08%' THEN 1 ELSE 0 END) "OLI",
                     SUM(CASE WHEN name LIKE 'LE07%' THEN 1 ELSE 0 END) "ETM",
                     SUM(CASE WHEN name LIKE 'LT0%' THEN 1 ELSE 0 END) "TM",
                     SUM(CASE WHEN name LIKE 'MOD09%' THEN 1 ELSE 0 END) "MOD09",
                     SUM(CASE WHEN name LIke 'MYD09%' THEN 1 ELSE 0 END) "MYD09",
                     SUM(CASE WHEN name LIKE 'MOD13%' THEN 1 ELSE 0 END) "MOD13",
                     SUM(CASE WHEN name LIKE 'MYD13%' THEN 1 ELSE 0 END) "MYD13",
                     SUM(CASE WHEN name LIKE 'MOD11%' THEN 1 ELSE 0 END) "MOD11",
                     SUM(CASE WHEN name LIKE 'MYD11%' THEN 1 ELSE 0 END) "MYD11",
                     SUM(CASE WHEN name LIKE 'VNP09%' THEN 1 ELSE 0 END) "VNP09",
                     SUM(CASE WHEN name LIKE 'L1C%' OR name LIKE 'S2%' THEN 1 ELSE 0 END) "S2[A|B]"
                     FROM ordering_scene
                     WHERE status not in ('purged', 'cancelled', 'complete', 'unavailable') '''
    },
    'machine_performance': {
        'display_name': 'Machines - 24 Hour Performance',
        'description': 'Number of completions by machine past 24 hours',
        'query': r'''SELECT processing_location "Machine",
                     COUNT(*) "Count"
                     FROM ordering_scene s
                     WHERE s.status = 'complete'
                     AND completion_date > now() - interval '24 hours'
                     GROUP BY processing_location'''
    },
    'machine_product_status': {
        'display_name': 'Machines - Product Status',
        'description': 'Product status counts by machine',
        'query': r'''SELECT
                     processing_location "Machine",
                     SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) "Processing",
                     SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) "Complete",
                     SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) "Error",
                     SUM(CASE WHEN status='retry' THEN 1 ELSE 0 END) "Retry"
                     FROM ordering_scene
                     WHERE status IN ('processing',
                                      'complete',
                                      'error',
                                      'retry')
                     GROUP BY processing_location
                     ORDER BY processing_location'''
    },
    'retry_error': {
        'display_name': 'Retries & Errors',
        'description': 'All items in retry and error status with user notes',
        'query': r'''SELECT
                     s.name "Name",
                     o.orderid "Order ID",
                     s.processing_location "Machine",
                     s.status "Status",
                     s.note "Note" ,
                     s.retry_after "Retry After",
                     '/logfile/' || o.orderid || '/' || s.name as "Order Link"
                     FROM ordering_scene s
                     JOIN ordering_order o ON
                     o.id = s.order_id
                     WHERE s.status
                     IN ('retry', 'error')
                     ORDER BY s.name'''
    },
    'order_counts': {
        'display_name': 'Orders - Counts',
        'description': 'Orders and status per user',
        'query': r'''SELECT COUNT(o.orderid) "Total Orders",
                    SUM(case when o.status = 'complete' then 1 else 0 end) "Complete",
                    SUM(case when o.status = 'ordered' then 1 else 0 end) "Open",
                    u.email "Email",
                    u.first_name "First Name",
                    u.last_name "Last Name"
                    FROM ordering_order o, auth_user u
                    WHERE o.user_id = u.id
                    AND o.status not in ( 'purged', 'cancelled' )
                    GROUP BY u.email, u.first_name, u.last_name
                    ORDER BY "Total Orders" DESC'''
    },
    'order_expiration': {
        'display_name': 'Orders - Expiration',
        'description': 'Expiring orders by date',
        'query': r'''SELECT
                     (o.completion_date + interval '7 days') "Expires",
                     o.orderid "Order",
                     count(s.name) "Product Count"
                     FROM ordering_order o
                     JOIN ordering_scene s ON o.id = s.order_id
                     WHERE o.status = 'complete'
                     GROUP BY o.orderid, o.completion_date
                     ORDER BY "Expires"'''
    },
    'order_product_status': {
        'display_name': 'Orders - Product Status',
        'description': 'Shows orders and product counts by date',
        'query': r'''SELECT o.order_date "Date Ordered",
                     o.orderid "Order ID",
                     COUNT(s.name) "Scene Count",
                     SUM(CASE when s.status in ('complete', 'unavailable') then 1 else 0 end) "C",
                     SUM(CASE when s.status = 'processing' then 1 ELSE 0 END) "P",
                     SUM(CASE when s.status = 'tasked' then 1 ELSE 0 END) "T",
                     SUM(CASE when s.status = 'scheduled' then 1 ELSE 0 END) "Sch",
                     SUM(CASE when s.status = 'oncache' then 1 ELSE 0 END) "OC",
                     SUM(CASE when s.status = 'onorder' then 1 ELSE 0 END) "OO",
                     SUM(CASE when s.status = 'retry' then 1 ELSE 0 END) "R",
                     SUM(CASE when s.status = 'error' then 1 ELSE 0 END) "E",
                     SUM(CASE when s.status = 'submitted' then 1 ELSE 0 END) "S",
                     u.username "User Name"
                     FROM ordering_scene s,
                          ordering_order o,
                          auth_user u
                     WHERE o.id = s.order_id
                     AND u.id = o.user_id
                     AND o.status = 'ordered'
                     GROUP BY
                         o.orderid,
                         u.username,
                         o.order_date
                         ORDER BY o.order_date ASC''',
    },
    'product_counts': {
        'display_name': 'Products - Counts',
        'description': 'Active product totals per user',
        'query': r'''SELECT COUNT(s.name) "Total Active Scenes",
                     SUM(case when s.status in ('complete', 'unavailable') then 1 else 0 end) "Complete",
                     SUM(case when s.status not in ('processing', 'complete', 'unavailable') then 1 else 0 end) "Open",
                     SUM(case when s.status = 'processing' then 1 else 0 end) "Processing",
                     u.email "Email",
                     u.first_name "First Name",
                     u.last_name "Last Name",
                     SUM(case when s.status = 'error' then 1 else 0 end) "Error",
                     SUM(case when s.status = 'retry' then 1 else 0 end) "Retry"
                     FROM ordering_scene s, ordering_order o, auth_user u
                     WHERE s.order_id = o.id
                     AND o.user_id = u.id
                     AND s.status not in ('purged', 'cancelled')
                     GROUP BY u.email, u.first_name, u.last_name
                     ORDER BY "Total Active Scenes" DESC'''
    },
    'product_expiration_counts': {
        'display_name': 'Products - Expiration Counts',
        'description': 'Quantities of expiring products by date',
        'query': r'''SELECT
                     (o.completion_date::date + interval '7 days') "Expiration",
                     count(s.name) "Quantity"
                     FROM ordering_order o
                     JOIN ordering_scene s on o.id = s.order_id
                     WHERE o.status = 'complete'
                     GROUP BY "Expiration"
                     ORDER BY "Expiration"'''
    },
    'product_completion_log': {
        'display_name': 'Products - Completion Log',
        'description': 'Show the last 100 products that have completed',
        'query': r'''SELECT
                     s.completion_date "Completion Date",
                     u.username "Username",
                     o.orderid "Order ID",
                     s.name "Product Name",
                     s.status "Final Status"
                     FROM auth_user u
                     JOIN ordering_order o on u.id = o.user_id
                     JOIN ordering_scene s on o.id = s.order_id
                     WHERE s.completion_date IS NOT NULL
                     AND o.status not in ( 'purged', 'cancelled' )
                     AND s.status not in ( 'purged', 'cancelled' )
                     ORDER BY s.completion_date DESC LIMIT 100'''
    },
    'aggregate_product_counts': {
        'display_name': 'Products - Aggregate Counts',
        'description': 'Displays current status counts for all products',
        'query': r'''SELECT status,
                     COUNT(status)
                     FROM ordering_scene
                     GROUP BY status'''
    },
    'scheduling_running': {
        'display_name': 'Scheduling - Running',
        'description': 'Shows scheduling information for user product requests',
        'query': r'''SELECT u.username "Username",
                     SUM(CASE WHEN s.status = 'processing'
                         THEN 1 ELSE 0 END) "Processing",
                     SUM(CASE WHEN s.status IN
                         ('tasked', 'scheduled')
                         THEN 1 ELSE 0 END) "Queued",
                     SUM(CASE WHEN s.status IN
                         ('processing', 'tasked', 'scheduled')
                         THEN 1 ELSE 0 END) "Total Running",
                     SUM(CASE WHEN s.status IN
                         ('processing', 'submitted', 'error', 'onorder',
                          'retry', 'oncache', 'tasked', 'scheduled')
                         THEN 1 ELSE 0 END) "Open Products",
                     u.email "Email",
                     u.first_name "First Name",
                     u.last_name "Last Name"
                     FROM ordering_scene s
                     JOIN ordering_order o on o.id = s.order_id
                     JOIN auth_user u on u.id = o.user_id
                     WHERE s.status not in ('complete',
                                            'unavailable',
                                            'cancelled',
                                            'purged')
                     GROUP BY u.username,
                              u.email,
                              u.first_name,
                              u.last_name
                     ORDER BY "Total Running" DESC'''
    },
    'scheduling_next_up': {
        'display_name': 'Scheduling - Next Up',
        'description': 'Shows products that will be scheduled to run next',
        'query': r'''WITH order_queue AS
                     (SELECT u.email "email", count(name) "running"
                      FROM ordering_scene s, ordering_order o, auth_user u
                      WHERE
                      u.id = o.user_id
                      AND o.id = s.order_id
                      AND s.status in ('tasked', 'scheduled', 'processing')
                      GROUP BY u.email)
                     SELECT
                     s.name "Scene",
                     o.order_date "Date Ordered",
                     o.orderid "Order ID",
                     q.running "Currently Running Count"
                     FROM ordering_scene s,
                          ordering_order o,
                          auth_user u,
                          order_queue q
                     WHERE u.id = o.user_id
                     AND o.id = s.order_id
                     AND o.status = 'ordered'
                     AND s.status = 'oncache'
                     AND q.email = u.email
                     ORDER BY q.running ASC, o.order_date ASC
                     LIMIT 25'''
    }
}

STATS = {
    'stat_open_orders': {
        'display_name': 'Open Orders',
        'description': 'Number of open orders in the system',
        'query': r'''SELECT
                     COUNT(orderid) "statistic"
                     FROM ordering_order
                     WHERE status = 'ordered' '''
    },
    'stat_waiting_users': {
        'display_name': 'Waiting Users',
        'description': 'Number of users with open orders in the system',
        'query': r'''SELECT
                     COUNT(DISTINCT user_id) "statistic"
                     FROM ordering_order
                     WHERE status = 'ordered'  '''
    },
    'stat_backlog_depth': {
        'display_name': 'Backlog Depth',
        'description': 'Number of products to be fulfilled',
        'query': r'''SELECT COUNT(*) "statistic"
                     FROM ordering_scene
                     WHERE status
                     NOT IN ('purged', 'complete', 'unavailable', 'cancelled')'''
    },
    'stat_products_complete_24_hrs': {
        'display_name': 'Products Complete 24hrs',
        'description': 'Number of products completed last 24 hrs',
        'query': r'''SELECT COUNT(*) "statistic"
                     FROM ordering_scene s
                     WHERE s.status = 'complete'
                     AND completion_date > now() - interval '24 hours' '''
    },
    'stat_onorder_depth': {
        'display_name': 'Products \'onorder\'',
        'description': 'Current count for products onorder',
        'query': r'''SELECT COUNT(id) "statistic"
                     FROM ordering_scene s
                     WHERE s.status = 'onorder' '''
    }
}

MULTISTATS = {
    'stat_products_complete_1_hrs_sensor': {
        'display_name': 'Products Complete 1hrs - Sensor',
        'description': 'Number of products completed last 1 hrs, sorted by Sensor',
        'groupby': 'sensor',
        'query': r'''SELECT COALESCE(COUNT(*), 0) "statistic",
                            CASE WHEN split_part(s.name, '_', 2) = '' THEN
                                CASE WHEN s.sensor_type = 'landsat' THEN left(s.name, 3) ELSE left(s.name, 7) END
                                ELSE left(s.name, 4) END "sensor"
                     FROM ordering_scene s
                     WHERE s.status = 'complete'
                     AND completion_date > now() - interval '1 hours'
                     GROUP BY "sensor" '''
    },
    'stat_products_complete_1_hrs_machine': {
        'display_name': 'Products Complete 1hrs - Machine',
        'description': 'Number of products completed last 1 hrs, sorted by Machine',
        'groupby': 'machine',
        'query': r'''SELECT COALESCE(COUNT(*), 0) "statistic",
                            s.processing_location "machine"
                     FROM ordering_scene s
                     WHERE s.status = 'complete'
                     AND completion_date > now() - interval '1 hours'
                     GROUP BY "machine" '''
    }
}


class ReportingProviderInterfaceV0(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def listing(self, show_query):
        """
        :param show_query:
        :return: return Dict of available reports
        """

    @abc.abstractmethod
    def run(self, name):
        """
        :param name:
        :return OrderedDict of results for report
        """
        return


