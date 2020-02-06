import abc


class ProductionProviderInterfaceV0(object, metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def queue_products(order_name_tuple_list, processing_location, job_name):
        """ Allows the caller to place products into queued status in bulk """
        return

    @abc.abstractmethod
    def mark_product_complete(self, name, orderid, processing_loc=None,
                              completed_file_location=None, destination_cksum_file=None,
                              log_file_contents=None):
        """ Marks product complete in the local and in EE system if applicable """
        return

    @abc.abstractmethod
    def set_product_unavailable(self, name, orderid,
                                processing_loc=None, error=None, note=None):
        """ Marks product unavailable locally and in EE system if applicable  """
        return

    @staticmethod
    @abc.abstractmethod
    def set_products_unavailable(products, reason):
        """Bulk updates products to unavailable status and updates EE if
        necessary.
        Keyword args:
        products - A list of models.Scene objects
        reason - The user facing reason the product was rejected
        """
        return

    @abc.abstractmethod
    def update_status(self, name, orderid,
                      processing_loc=None, status=None):
        """ update a scene's status """
        return

    @abc.abstractmethod
    def update_product(self, action, name=None, orderid=None, processing_loc=None,
                       status=None, error=None, note=None,
                       completed_file_location=None,
                       cksum_file_location=None,
                       log_file_contents=None):
        """ wrapper method for update_status, set_product_error,
        set_product_unavailable, mark_product_complete """
        return

    @abc.abstractmethod
    def set_product_retry(self, name, orderid, processing_loc,
                          error, note, retry_after, retry_limit=None):
        """ Set a product to retry status """
        return

    @abc.abstractmethod
    def set_product_error(self, name, orderid, processing_loc, error):
        """ handle product error  """
        return

    @abc.abstractmethod
    def get_products_to_process(self, record_limit=500,
                                for_user=None,
                                priority=None,
                                product_types=None,
                                encode_urls=False):
        """Find scenes that are oncache and return them as properly formatted
        json per the interface description between the web and processing tier"""
        return

    @abc.abstractmethod
    def load_ee_orders(self):
        """ Loads all the available orders from lta into
        our database and updates their status
        """
        return

    @abc.abstractmethod
    def handle_retry_products(self, products):
        """ handles all products in retry status """
        return

    @abc.abstractmethod
    def send_initial_emails(self, orders):
        """ sends initial emails """
        return

    @abc.abstractmethod
    def handle_submitted_plot_products(self, plot_scenes):
        """ Moves plot products from submitted to oncache status once all
            their underlying rasters are complete or unavailable """
        return

    @abc.abstractmethod
    def send_completion_email(self, order):
        """ public interface to send the completion email """
        return

    @abc.abstractmethod
    def update_order_if_complete(self, order_id):
        """Method to send out the order completion email
        for orders if the completion of a scene
        completes the order

        Keyword args:
        order_id -- id of the order

        """
        return

    @abc.abstractmethod
    def finalize_orders(self, orders):
        """Checks all open orders in the system and marks them complete if all
        required scene processing is done"""
        return

    @abc.abstractmethod
    def purge_orders(self, send_email=False):
        """ Will move any orders older than X days to purged status and will also
        remove the files from disk"""
        return

    @abc.abstractmethod
    def handle_orders(self):
        """Logic handler for how we accept orders + products into the system"""
        return

    @abc.abstractmethod
    def handle_stuck_jobs(self, scenes):
        """Method to handle orphaned Mesos tasks"""
        return
