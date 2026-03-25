Class Test.CompleteExample Extends %AI.ToolSet
{

XData Definition [ MimeType = application/xml ]
{
<ToolSet Name="CompleteExample">
            <Description>Demonstrates all ToolSet features.</Description>

            <!-- 1. Inline Tools
            <Tool Name="Echo" Method="Echo">
                <Description>Echo back the input.</Description>
                <Parameters>
                    <Parameter Name="text" Type="string" Required="true">
                        <Description>Text to echo</Description>
                    </Parameter>
                </Parameters>
            </Tool> -->

            <!-- 2. Include Other ToolSets -->
            <Include Class="%AI.Tools.SQL">
                <Requirement Name="ReadOnly" Value="1"/>
            </Include>

            <Policies>
                <Audit Class="%AI.Policy.ConsoleAudit" />
            </Policies>    

            <!-- 3. Include with Filtering -->
            <Include Class="%AI.Tools.FileSystem">
                <!-- <Filter>
                    <Include Name="read_file"/>
                    <Include Name="list_directory"/>
                    <Exclude Name="delete_file"/>
                    <Exclude Name="write_file"/>
                </Filter> -->
            </Include>

        </ToolSet>
}

Method Echo(args As %DynamicObject) As %String
{
        Return "Echo: " _ args.text
}

}
