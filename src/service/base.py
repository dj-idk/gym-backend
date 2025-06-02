from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from src.data.database import Base
from src.schema import Pagination, OrderDirection

# Define generic type variables
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize with the SQLAlchemy model class.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            db: Database session
            obj_in: Schema with create data

        Returns:
            The created model instance
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            db: Database session
            id: ID of the record to get

        Returns:
            The model instance if found, None otherwise
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """
        Get a record by arbitrary filters.

        Args:
            db: Database session
            **kwargs: Filter conditions as keyword arguments

        Returns:
            The model instance if found, None otherwise
        """
        query = select(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_direction: Optional[OrderDirection] = OrderDirection.ASC,
    ) -> Tuple[List[ModelType], Pagination]:
        """
        Get multiple records with pagination and ordering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by
            order_direction: Direction to order (asc or desc)

        Returns:
            Tuple of (list of model instances, pagination info)
        """
        # Count total items for pagination
        count_query = select(func.count()).select_from(self.model)
        total = await db.scalar(count_query)

        # Build the main query
        query = select(self.model)

        # Apply ordering if specified
        if order_by:
            order_column = getattr(self.model, order_by)
            if order_direction == OrderDirection.DESC:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()

        # Calculate pagination info
        current_page = skip // limit + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        pagination = Pagination(
            total=total,
            limit=limit,
            skip=skip,
            current_page=current_page,
            total_pages=total_pages,
            has_previous=current_page > 1,
            has_next=current_page < total_pages,
        )

        return items, pagination

    async def get_multi_by_filter(
        self,
        db: AsyncSession,
        *,
        query_filter: Optional[Select] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_direction: Optional[OrderDirection] = OrderDirection.ASC,
    ) -> Tuple[List[ModelType], Pagination]:
        """
        Get multiple records with custom filter, pagination, and ordering.

        Args:
            db: Database session
            query_filter: Optional SQLAlchemy filter expression
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by
            order_direction: Direction to order (asc or desc)

        Returns:
            Tuple of (list of model instances, pagination info)
        """
        # Count total items for pagination
        count_query = select(func.count()).select_from(self.model)
        if query_filter is not None:
            count_query = count_query.where(query_filter)
        total = await db.scalar(count_query)

        # Build the main query
        query = select(self.model)
        if query_filter is not None:
            query = query.where(query_filter)

        # Apply ordering if specified
        if order_by:
            order_column = getattr(self.model, order_by)
            if order_direction == OrderDirection.DESC:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()

        # Calculate pagination info
        current_page = skip // limit + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        pagination = Pagination(
            total=total,
            limit=limit,
            skip=skip,
            current_page=current_page,
            total_pages=total_pages,
            has_previous=current_page > 1,
            has_next=current_page < total_pages,
        )

        return items, pagination

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update a record.

        Args:
            db: Database session
            db_obj: The model instance to update
            obj_in: Update data as schema or dict

        Returns:
            The updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Delete a record by ID.

        Args:
            db: Database session
            id: ID of the record to delete

        Returns:
            The deleted model instance if found, None otherwise
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
