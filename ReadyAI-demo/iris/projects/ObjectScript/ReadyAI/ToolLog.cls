Class ReadyAI.ToolLog Extends %Persistent
{

Property ToolName As %String;

Property ToolCall As %Library.DynamicObject;

Property Metadata As %Library.DynamicObject;

Property Result As %Library.DynamicObject;

Property Duration As %Integer;

Property Status As %Status;

Property Timestamp As %DateTime;

Property Username As %String;

Storage Default
{
<Data name="Metadata">
<Attribute>Metadata</Attribute>
<Structure>node</Structure>
<Subscript>"Metadata"</Subscript>
</Data>
<Data name="Result">
<Attribute>Result</Attribute>
<Structure>node</Structure>
<Subscript>"Result"</Subscript>
</Data>
<Data name="ToolCall">
<Attribute>ToolCall</Attribute>
<Structure>node</Structure>
<Subscript>"ToolCall"</Subscript>
</Data>
<Data name="ToolLogDefaultData">
<Value name="1">
<Value>%%CLASSNAME</Value>
</Value>
<Value name="2">
<Value>ToolName</Value>
</Value>
<Value name="3">
<Value>Duration</Value>
</Value>
<Value name="4">
<Value>Status</Value>
</Value>
<Value name="5">
<Value>Timestamp</Value>
</Value>
<Value name="6">
<Value>Username</Value>
</Value>
</Data>
<DataLocation>^ReadyAI.ToolLogD</DataLocation>
<DefaultData>ToolLogDefaultData</DefaultData>
<IdLocation>^ReadyAI.ToolLogD</IdLocation>
<IndexLocation>^ReadyAI.ToolLogI</IndexLocation>
<StreamLocation>^ReadyAI.ToolLogS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
