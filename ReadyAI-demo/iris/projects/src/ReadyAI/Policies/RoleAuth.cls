Class ReadyAI.Policies.RoleAuth Extends %AI.Policy.Authorization
{

Method %CanList(tool As %String) As %Boolean
{
        set roles = $ROLES
        if $FIND(roles, "Doctor") {
            return 1
        }elseif $FIND(roles, "%All") {
            return 1
        }
        else {
            return 0
        }
}

Method %CanExecute(tool As %String) As %Status
{
        set roles = $ROLES
        if $FIND(roles, "Doctor") {
            return $$$OK
        }
        elseif $FIND(roles, "%All") {
                return $$$OK
            }
        else {
            return $$$ERROR($$$AICoreToolAccessDenied, "Access denied: User does not have the 'Doctor' role required to execute this tool.")
        }
}

}
