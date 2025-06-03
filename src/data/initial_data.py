from uuid import uuid4
from .user import Role, Permission


def get_initial_permissions():
    """Define initial permissions for the application."""
    return [
        Permission(id=uuid4(), name="user:read", description="Can read user data"),
        Permission(
            id=uuid4(), name="user:write", description="Can create/update user data"
        ),
        Permission(id=uuid4(), name="user:delete", description="Can delete users"),
        Permission(
            id=uuid4(), name="service:read", description="Can read service data"
        ),
        Permission(
            id=uuid4(), name="service:write", description="Can create/update services"
        ),
        Permission(
            id=uuid4(), name="service:delete", description="Can delete services"
        ),
        Permission(
            id=uuid4(), name="purchase:read", description="Can read purchase data"
        ),
        Permission(
            id=uuid4(), name="purchase:write", description="Can create/update purchases"
        ),
        Permission(
            id=uuid4(), name="purchase:refund", description="Can process refunds"
        ),
        Permission(id=uuid4(), name="coach:read", description="Can read coach data"),
        Permission(
            id=uuid4(), name="coach:write", description="Can create/update coach data"
        ),
        Permission(id=uuid4(), name="analytics:read", description="Can view analytics"),
        Permission(
            id=uuid4(), name="ticket:read", description="Can read support tickets"
        ),
        Permission(
            id=uuid4(), name="ticket:write", description="Can respond to tickets"
        ),
        Permission(id=uuid4(), name="ticket:assign", description="Can assign tickets"),
    ]


def get_initial_roles(permissions):
    """Define initial roles for the application."""
    perm_dict = {p.name: p for p in permissions}

    # Member role
    member_role = Role(
        id=uuid4(),
        name="member",
        description="Regular gym member",
        permissions=[
            perm_dict["service:read"],
            perm_dict["purchase:read"],
            perm_dict["coach:read"],
            perm_dict["ticket:read"],
            perm_dict["ticket:write"],
        ],
    )

    # Coach role
    coach_role = Role(
        id=uuid4(),
        name="coach",
        description="Gym trainer/coach",
        permissions=[
            perm_dict["service:read"],
            perm_dict["coach:read"],
            perm_dict["coach:write"],
            perm_dict["ticket:read"],
            perm_dict["ticket:write"],
        ],
    )

    # Support staff role
    support_role = Role(
        id=uuid4(),
        name="support",
        description="Customer support staff",
        permissions=[
            perm_dict["user:read"],
            perm_dict["service:read"],
            perm_dict["purchase:read"],
            perm_dict["coach:read"],
            perm_dict["ticket:read"],
            perm_dict["ticket:write"],
            perm_dict["ticket:assign"],
        ],
    )

    # Admin role (has all permissions)
    admin_role = Role(
        id=uuid4(),
        name="admin",
        description="System administrator",
        permissions=list(perm_dict.values()),
    )

    return [member_role, coach_role, support_role, admin_role]
