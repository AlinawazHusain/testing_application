from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import desc, update, select , asc, and_
from sqlalchemy.orm import load_only
from sqlalchemy.exc import SQLAlchemyError
from config.exceptions import (
    DatabaseError, NotFoundError
)



"""
Database Helper Functions for Async Operations

This module provides a set of asynchronous database helper functions for performing common
CRUD operations using SQLAlchemy's asynchronous API. The functions support operations such as
insertion, updating, fetching records, and calculating percentages based on table attributes.

Functions:
----------
- insert_into_table(session: AsyncSession, model, kwargs):
    Inserts a new record into the specified table/model and returns the inserted instance.

- update_table(session: AsyncSession, model, filters: dict, update_data: dict):
    Updates records in the specified table/model that match the given filters and returns the updated record.

- fetch_from_table(session: AsyncSession, model, columns: list = None, filters: dict = None, order_by: str = None):
    Fetches records from the specified table/model based on the given filters and ordering, returning results as a list of dictionaries.

- get_tuple_instance(session: AsyncSession, model, filters: dict, extra_conditions=None, order_by=None, limit=None):
    Fetches a single record from the specified table/model based on the provided filters and conditions, returning a single instance or `None`.

- update_percentage_excluding(session: AsyncSession, model, filters: dict, exclude_attributes: list, percentage_attribute_name):
    Calculates and updates a percentage attribute based on the number of non-null fields in an instance, excluding specified fields.

- update_percentage_including(session: AsyncSession, model, filters: dict, include_attributes: list, percentage_attribute_name):
    Calculates and updates a percentage attribute based on the number of non-null fields in an instance, including only specified fields.

- insert_multiple_tables(session: AsyncSession, inserts: dict):
    Inserts multiple records into different tables in a single session, given a dictionary of models and corresponding data.

- fetch_multiple_tables(session: AsyncSession, table_attributes: dict, filters: dict = None):
    Fetches records from multiple tables based on specified attributes and filters, returning a dictionary of results for each table.

Error Handling:
---------------
All functions are designed to handle database errors (SQLAlchemyError) and will automatically
rollback any ongoing transactions in case of failure, raising a custom `DatabaseError` or `NotFoundError`
as appropriate.

"""



        
async def insert_into_table(session: AsyncSession, model, kwargs):
    """
    Inserts a new record into the specified table/model and returns the inserted instance.
    
    :param session: The database session object.
    :param model: The SQLAlchemy model representing the table to insert data into.
    :param kwargs: A dictionary of column names and their values for the new record.
    :return: The inserted model instance.
    :raises DatabaseError: If an error occurs during the insert operation.
    """
    
    try:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.commit()
        return instance
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to insert record: {str(e)}")






async def update_table(session: AsyncSession, model, filters: dict, update_data: dict):
    """
    Updates records in the specified table/model that match the given filters and returns the updated record.

    :param session: The database session object.
    :param model: The SQLAlchemy model representing the table to update.
    :param filters: A dictionary of filter criteria to find the records to update.
    :param update_data: A dictionary of column names and new values to update the records.
    :return: A dictionary representing the updated record.
    :raises DatabaseError: If an error occurs during the update operation.
    :raises NotFoundError: If no records match the filter criteria.
    """
    
    try:
        stmt = (
            update(model)
            .where(*[getattr(model, key) == value for key, value in filters.items() if value is not None])
            .values(**update_data)
            .returning(*[getattr(model, column.name) for column in model.__table__.columns])
        )
        result = await session.execute(stmt)
        updated_row = result.fetchone()
        if not updated_row:
            raise NotFoundError(message="Record not found")
        return dict(updated_row._mapping)
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to update record: {str(e)}")







async def fetch_from_table(session: AsyncSession,
                           model,
                           columns: list = None,
                           filters: dict = None,
                           order_by: str = None, 
                           ):
    
    """
    Fetches records from the specified table/model based on the given filters and ordering,
    returning results as a list of dictionaries.
    
    :param session: The database session object.
    :param model: The SQLAlchemy model representing the table to fetch data from.
    :param columns: A list of column names to select (optional). Defaults to all columns.
    :param filters: A dictionary of filter criteria (optional).
    :param order_by: A string specifying the column to order the results by (optional).
    :return: A list of dictionaries containing the selected records.
    :raises DatabaseError: If an error occurs during the fetch operation.
    """
    
    try:
        selected_columns = [getattr(model, col) for col in columns] if columns else model.__table__.columns
        query = select(*selected_columns)

        if filters:
            # If filters is a dict, keep using filter_by
            if isinstance(filters, dict):
                query = query.filter_by(**filters)
            # If filters is a list of SQLAlchemy expressions
            elif isinstance(filters, list):
                query = query.filter(and_(*filters))

        if order_by:
            direction = asc
            if order_by.startswith("-"):
                direction = desc
                order_by = order_by[1:]
            if hasattr(model, order_by):
                query = query.order_by(direction(getattr(model, order_by)))

        result = await session.execute(query)
        rows = result.all()

        if not rows:
            return []

        if columns is None:
            columns = [col.name for col in model.__table__.columns]

        return [dict(zip(columns, row)) for row in rows]

    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to fetch record: {str(e)}")





async def get_tuple_instance(session: AsyncSession, model, filters: dict, extra_conditions=None, order_by=None, limit=None):
    
    """
    Fetches a single record from the specified table/model based on the provided filters and conditions,
    returning a single instance or `None`.
    
    :param session: The database session object.
    :param model: The SQLAlchemy model representing the table to fetch data from.
    :param filters: A dictionary of filter criteria to find the record.
    :param extra_conditions: Additional conditions to apply to the query (optional).
    :param order_by: A list of ordering conditions (optional).
    :param limit: A limit on the number of records to fetch (optional).
    :return: The fetched record or `None` if no record matches the filters.
    :raises DatabaseError: If an error occurs during the fetch operation.
    """
    
    try:
        conditions = [getattr(model, key) == value for key, value in filters.items()]
        if extra_conditions:
            conditions.extend(extra_conditions)

        query = select(model).where(*conditions)
        
        # Apply ordering if specified
        if order_by:
            query = query.order_by(*order_by)
        
        # Apply limit if specified
        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to get tuple instance: {str(e)}")




async def update_percentage_excluding(session: AsyncSession, model, filters: dict, exclude_attributes: list, percentage_attribute_name):
    """
    Updates a percentage attribute based on the number of non-null fields in an instance, excluding specified fields, 
    and returns the calculated percentage.

    :param session: The database session object.
    :param model: The SQLAlchemy model representing the table to update.
    :param filters: A dictionary of filter criteria to find the instance.
    :param exclude_attributes: A list of attributes (columns) to exclude from the calculation.
    :param percentage_attribute_name: The name of the attribute to update with the calculated percentage.
    :return: The calculated percentage as a float (between 0 and 100).
    :raises NotFoundError: If no record matches the filter criteria.
    :raises DatabaseError: If an error occurs during the update operation.
    """
    
    try:
        instance = await get_tuple_instance(session, model, filters)
        if not instance:
            raise NotFoundError("Instance not found")
        exclude_attributes = set(exclude_attributes or [])
        all_fields = [col.name for col in model.__table__.columns if col.name not in exclude_attributes]
        non_null_fields = sum(1 for field in all_fields if getattr(instance, field) is not None)
        total_fields = len(all_fields)
        percentage = round((non_null_fields / total_fields) * 100, 2) if total_fields > 0 else 0.0
        setattr(instance, percentage_attribute_name, percentage)
        return percentage  
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to update percentage: {str(e)}")







async def update_percentage_including(session: AsyncSession, model, filters: dict, include_attributes: list, percentage_attribute_name):
    
    """
    Updates a percentage attribute based on the number of non-null fields in an instance, including only specified fields, 
    and returns the calculated percentage.

    :param session: The database session object.
    :param model: The SQLAlchemy model representing the table to update.
    :param filters: A dictionary of filter criteria to find the instance.
    :param include_attributes: A list of attributes (columns) to include in the calculation.
    :param percentage_attribute_name: The name of the attribute to update with the calculated percentage.
    :return: The calculated percentage as a float (between 0 and 100).
    :raises NotFoundError: If no record matches the filter criteria.
    :raises DatabaseError: If an error occurs during the update operation.
    """
    
    try:
        instance = await get_tuple_instance(session, model, filters)
        if not instance:
            raise NotFoundError("Instance not found")
        include_attributes = set(include_attributes or [])
        all_fields = [col.name for col in model.__table__.columns if col.name in include_attributes]
        non_null_fields = sum(1 for field in all_fields if getattr(instance, field) is not None)
        total_fields = len(all_fields)
        percentage = round((non_null_fields / total_fields) * 100, 2) if total_fields > 0 else 0.0
        setattr(instance, percentage_attribute_name, percentage)
        return percentage  
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to update percentage: {str(e)}")




async def insert_multiple_tables(session: AsyncSession, inserts: dict):
    """
    Inserts multiple records into different tables in a single session, given a dictionary of models and corresponding data, 
    and returns the inserted instances.

    :param session: The database session object.
    :param inserts: A dictionary where keys are SQLAlchemy models and values are dictionaries of data to insert.
    :return: A dictionary where keys are models and values are the corresponding inserted instances.
    :raises DatabaseError: If an error occurs during the insert operation.
    """
    
    try:
        instances = {model: model(**data) for model, data in inserts.items()}
        session.add_all(instances.values())
        return instances
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to insert into multiple tables: {str(e)}")


      
        
        
async def fetch_multiple_tables(session: AsyncSession, table_attributes: dict, filters: dict = None):
    """
    Fetches records from multiple tables based on specified attributes and filters, returning a dictionary of results for each table.

    :param session: The database session object.
    :param table_attributes: A dictionary where keys are tables (SQLAlchemy models) and values are lists of column attributes to fetch.
    :param filters: A dictionary of filter criteria for each table (optional).
    :return: A dictionary where keys are table names and values are lists of records (as dictionaries).
    :raises DatabaseError: If an error occurs during the fetch operation.
    """
    
    try:
        result = {}
        for table, attributes in table_attributes.items():
            query = select(table).options(load_only(*[getattr(table, attr) for attr in attributes]))
            if filters and table in filters:
                query = query.filter_by(**filters[table])
            res = await session.execute(query)
            result[table.__name__] = [row._asdict() for row in res.mappings().all()] 
        return result
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseError(message=f"Failed to fetch multiple tables: {str(e)}")
