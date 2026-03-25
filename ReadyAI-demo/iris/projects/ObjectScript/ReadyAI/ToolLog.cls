Class ReadyAI.ToolLog Extends %Persistent
{

Property ToolName As %String;

Property ToolCall As %Library.DynamicObject;

Property Metadata As %Library.DynamicObject;

Property Result As %Library.DynamicObject;

Property Duration As %Integer;

Property Status As %Status;

Property Timestamp As %DateTime;

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
</Data>
<DataLocation>^READYAI.ToolLogD</DataLocation>
<DefaultData>ToolLogDefaultData</DefaultData>
<IdLocation>^READYAI.ToolLogD</IdLocation>
<IndexLocation>^READYAI.ToolLogI</IndexLocation>
<StreamLocation>^READYAI.ToolLogS</StreamLocation>
<Type>%Storage.Persistent</Type>
}

}
