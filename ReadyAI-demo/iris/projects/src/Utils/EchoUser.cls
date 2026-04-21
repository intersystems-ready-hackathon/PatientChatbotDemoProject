Class Utils.EchoUser Extends %RegisteredObject
{

/// Echo the current user's username back to them.
ClassMethod EchoUser() As %DynamicObject
{
        set username = $USERNAME
        set roles = $ROLES
        Return {"Username": (username), "Roles": (roles)}
}

}
