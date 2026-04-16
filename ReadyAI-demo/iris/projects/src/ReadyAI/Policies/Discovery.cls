Class ReadyAI.Policies.Discovery Extends %AI.Policy.Discovery
{   
    Parameter STATEFUL=0; 
    /// Checks if the user has a specific role 
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

    /// Decides whether a tool should be listed based on the required role and user roles
    Method Resolve(fullCatalog As %DynamicArray) As %DynamicArray
    {   
        set ^DiscoveryCall(1) = fullCatalog
        // Check whether the user has a role that grants full access to all tools
        set fullAccess = ..CheckRoles("%All")

        if fullAccess {
            return fullCatalog
        } 

        set resolvedCatalog = []
        
        // Iterate through the catalog of tools and include only those for which the user has the required role
        for i=1:1:$length(fullCatalog) {

            set tool = fullCatalog.GetAt(i)
            set includeTool = 1


            set requiredRole = tool.%Get("Metadata").%Get("Role")
            if requiredRole'="" {
                if '..CheckRoles(requiredRole) {
                    set includeTool = 0
                }
            }
            if includeTool {
                do resolvedCatalog.Insert(tool)
            }
        }
        return resolvedCatalog
    }
}
