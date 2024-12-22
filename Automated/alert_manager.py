from update_registry import UpdateRegistry

class AlertManager:
    """
    Manages the creation and registration of alerts.
    """

    def __init__(self, registry: UpdateRegistry):
        """
        Initialize the AlertManager with a reference to the UpdateRegistry.
        :param registry: An instance of the UpdateRegistry.
        """
        self.registry = registry

    def create_alert(self, alert_name, alert_sql):
        """
        Registers an alert with the centralized registry.
        :param alert_name: Name of the alert.
        :param alert_sql: SQL query that evaluates to TRUE or FALSE.
        """
        self.registry.register_alert(alert_name, alert_sql)
        print(f"Alert '{alert_name}' registered successfully!")
