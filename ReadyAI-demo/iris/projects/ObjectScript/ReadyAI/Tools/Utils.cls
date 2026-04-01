Class ReadyAI.Tools.Utils Extends %RegisteredObject
{

/// Escape non-ASCII characters to ASCII-safe form for safe JSON transport
ClassMethod SafeString(pStr As %String) As %String
{
    quit $ZCVT(pStr, "O", "UTF8")
}

}
