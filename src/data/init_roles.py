from .initial_data import get_initial_permissions, get_initial_roles

from .user import Role
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def init_roles_and_permissions(db: AsyncSession):
    """Initialize the database with default roles and permissions"""

    existing_roles = await db.execute(select(Role))
    if existing_roles.scalars().first():
        return

    permissions = get_initial_permissions()
    db.add_all(permissions)
    await db.commit()

    roles = get_initial_roles(permissions)
    db.add_all(roles)
    await db.commit()
