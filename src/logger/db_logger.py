from models.log_models import DriverDatabaseUpdateLogs , MfoDatabaseUpdateLogs

async def driver_db_logger(session , driver_uuid : str,table_name,table_row_unique_identifier ,table_row_unique_identifier_value, table_attribute_names:list,
                          attribute_previous_values:list , attribute_updated_values:list , session_id, device_id):
    
    """
    Logs database updates for a specific driver by storing the details of the update in the `DriverDatabaseUpdateLogs` model.

    This function creates a log entry for each updated attribute in the specified table, recording the previous and updated
    values, along with the driver UUID, table name, unique identifier, session ID, and device ID.

    Args:
        session (AsyncSession): The database session used to add the log entries.
        driver_uuid (str): The unique identifier of the driver making the update.
        table_name (str): The name of the table where the update occurred.
        table_row_unique_identifier (str): The column name used to uniquely identify the row being updated.
        table_row_unique_identifier_value (str): The value of the unique identifier for the updated row.
        table_attribute_names (list): A list of attribute names that were updated in the table.
        attribute_previous_values (list): A list of previous values for each updated attribute.
        attribute_updated_values (list): A list of updated values for each updated attribute.
        session_id (str): The unique identifier for the session during which the update occurred.
        device_id (str): The device identifier from which the update was made.

    Returns:
        None: This function does not return any value. It commits the log entries to the database.
    """
    
    
    for i in range(len(attribute_updated_values)):
        log_data = {
            "driver_uuid" : driver_uuid,
            "table_name" : table_name,
            "table_attribute_name" : table_attribute_names[i],
            "attribute_previous_value" : str(attribute_previous_values[i]),
            "attribute_updated_value" : str(attribute_updated_values[i]),
            "table_row_unique_identifier" : table_row_unique_identifier,
            "table_row_unique_identifier_value" : table_row_unique_identifier_value,
            "session_id" : session_id,
            "device_id" : device_id,
        }
        instance = DriverDatabaseUpdateLogs(**log_data)
        session.add(instance)
    return






async def mfo_db_logger(session , mfo_uuid : str,table_name, table_row_unique_identifier ,table_row_unique_identifier_value, table_attribute_names:list,
                          attribute_previous_values:list , attribute_updated_values:list , session_id, device_id):
    
    """
    Logs database updates for a specific MFO by storing the details of the update in the `MfoDatabaseUpdateLogs` model.

    This function creates a log entry for each updated attribute in the specified table, recording the previous and updated
    values, along with the MFO UUID, table name, unique identifier, session ID, and device ID.

    Args:
        session (AsyncSession): The database session used to add the log entries.
        mfo_uuid (str): The unique identifier of the MFO making the update.
        table_name (str): The name of the table where the update occurred.
        table_row_unique_identifier (str): The column name used to uniquely identify the row being updated.
        table_row_unique_identifier_value (str): The value of the unique identifier for the updated row.
        table_attribute_names (list): A list of attribute names that were updated in the table.
        attribute_previous_values (list): A list of previous values for each updated attribute.
        attribute_updated_values (list): A list of updated values for each updated attribute.
        session_id (str): The unique identifier for the session during which the update occurred.
        device_id (str): The device identifier from which the update was made.

    Returns:
        None: This function does not return any value. It commits the log entries to the database.
    """
    
    
    for i in range(len(attribute_updated_values)):
        log_data = {
            "mfo_uuid" : mfo_uuid,
            "table_name" : table_name,
            "table_attribute_name" : table_attribute_names[i],
            "attribute_previous_value" : str(attribute_previous_values[i]),
            "attribute_updated_value" : str(attribute_updated_values[i]),
            "table_row_unique_identifier" : table_row_unique_identifier,
            "table_row_unique_identifier_value" : table_row_unique_identifier_value,
            "session_id" : session_id,
            "device_id" : device_id,
        }
        instance = MfoDatabaseUpdateLogs(**log_data)
        session.add(instance)
    return