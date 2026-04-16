Class ReadyAI.Policies.RoleAuth Extends %AI.Policy.Authorization
{
    Parameter STATEFUL=0;
    ClassMethod CheckRoles(pRole As %String) As %Boolean
    {
        set roles = $ROLES
        if $FIND(roles, pRole) {
            return 1
        } 
        else {
            return 0
        }
    }

    Method %CanExecute(tool As %String, call As %DynamicObject, metadata As %DynamicObject) As %Status
    {   
        if ..CheckRoles("%All") {
            return $$$OK
        }

        set requiredRole = metadata.%Get("Role") 
        
        if requiredRole'="" {
            if '..CheckRoles(requiredRole) {
                return $$$ERROR($$$AICoreToolAccessDenied, "User does not have the required role: " _ requiredRole)
            }
        }
        return $$$OK
    }
}

