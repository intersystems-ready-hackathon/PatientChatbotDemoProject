Class Utils.EchoUser Extends %AI.Tool
{

/// Echo the current user's username back to them.
/// This is a simple test tool to verify that the agent can call tools and receive responses.
Method EchoUser() As %DynamicObject
{
        set username = $USERNAME
        set roles = $ROLES
        Return {"Username": (username), "Roles": (roles)}
}

ClassMethod GetRoles() As %String
{
        
                 
        Return $ROLES
}


}
