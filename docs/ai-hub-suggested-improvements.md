# AI Hub Suggested Enhancements and Notable Limitations


## 1. MCP Config Store User Login 

The Config Store holds static configurations for MCP servers which are easily accessible through the langchain_intersystems SDK - this is a definite improvement over using langchain-mcp-adapters. However, this prevents having true RBAC or role-auditing to remote MCP servers.

To login to remote http MCP servers, you would as a standard use a Auth Header (Bearer/Basic) to the request, by doing the auth here, you can use audit policies to track which user is accessing the MCP server. 

However, it is not possible (as far as I can identify) to create MCP server configurations which dynamically adds the accessing username to the configuration. Therefore, access can either be controlled at the configuration level, or the MCP tooling level, but not both. 


## 2. Langchain Vector Store and %AI.RAG are incompatible 

The Langchain Vector Store can be attached to an existing table, providing that table has the vectors in a column named "embedding" and that column has a description. 

The %AI.RAG knowledge base can create vector tables easily with vectors automatically being stored in the column "vectors". 

It would be very easy to make these compatible (so a langchain vector store can be added to a %AI.RAG) by either renaming the column in %AI.RAG or editing IRISVectorStore to search for "embedding" or "vector" 

Compatibility would allow creation of a vector store using %AI.RAG.FastEmbed on the server-side, with langchain being used for client connections. 

## 3. %AI.RAG Inflexability

In general, I find the %AI.RAG package quite inflexible - for example, I can't find a way to use the FastEmbed tool to create vectors without creating a knowledge-base tool, adding it to a tool manager, and querying against it.  

The RUST-based AllMiniLM implementation is impressively fast, but the inflexibility makes it difficult to use for all but the standard knowledge-base workflow. Hybrid searches involving filtering on a column, don't seem to be possible. 


## 4. Query Tool 

A neat enhancement would be to allow class queries to automatically be serialised into AI tools. This would allow creation of Query tools with very limited or  specific scope without having to mix SQL with objectscript

E.g.

```objectscript
Class Sample.SQLQuerys extends %AI.QueryTool
{
    Query SearchPatientsBySurname(PatientSurname As %String) As %SQLQuery(ROWSPEC = "ID:%String,GivenName:%String,FamilyName:%String,BirthDate:%Date") [ SqlProc ]
{
        SELECT ID, GivenName, FamilyName, BirthDate 
        FROM AFHIRData.Patient 
        WHERE FamilyName = :PatientSurname
}
}

```


## Minor Cosmetic MCP thing: 

When accessing a remote HTTP server with Langchain-mcp-adapters, every transaction finishes with `Session termination failed: 202`, without any sign of failure (tools execute fine). GPT-5.4 tells me that this is because the MCP standard OK response is 200, not 202. Doesn't cause any issue but looks a bit offputting. 