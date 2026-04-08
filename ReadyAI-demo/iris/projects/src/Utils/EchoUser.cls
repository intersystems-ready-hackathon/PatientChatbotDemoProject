Class Utils.EchoUser Extends %RegisteredObject
{

/// Echo the current user's username back to them.
/// This is a simple test tool to verify that the agent can call tools and receive responses.
ClassMethod EchoUser() As %DynamicObject
{
        set username = $USERNAME
        set roles = $ROLES
        Return {"Username": (username), "Roles": (roles)}
}

}
