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

    def create_alert(self, alert_name, alert_sql, twitter_info, ai_prompt_info, additional_queries):
        """
        Registers an alert with the centralized registry.
        :param alert_name: Name of the alert.
        :param alert_sql: SQL query that evaluates to TRUE or FALSE.
        :param twitter_info: Twitter script for the alert.
        :param ai_prompt_info: AI prompt for processing.
        :param additional_queries: List of additional SQL queries.
        """
        # Build the metadata structure
        metadata = {
            "twitter_info": twitter_info,
            "ai_prompt_info": ai_prompt_info,
            "additional_queries": additional_queries
        }

        # Register the alert in the registry
        self.registry.register_alert(alert_name, alert_sql, metadata)
        print(f"Alert '{alert_name}' registered successfully!")

