Class RAG.DocRefVectorSetup Extends %RegisteredObject
{
/// Creates a vector store from the AFHIRData.DocumentReference table using the FastEmbed AllMiniLML6V2 model
ClassMethod EmbedText() As %Status
{
        set emb = ##class(%AI.RAG.Embedding.FastEmbed).Create()
        Set vs = ##class(%AI.RAG.VectorStore.IRIS).%New()
        Set vs.TableName  = "AFHIRData.DocRefVectorStore"
        Set vs.Dimensions = 384
        Set vs.ModelName  = "AllMiniLML6V2"
        Set fields = [{"name":"Patient","type":"varchar(20)","description":"Patient ID"}]
        Write "Building vector store (", vs.TableName, ")...", !
        $$$ThrowOnError(vs.Build(fields))
        Write "  Vector store ready.", !, !


            // 3. Knowledge base - name becomes the tool name exposed to the LLM
    Set kb = ##class(%AI.RAG.KnowledgeBase).%New()
    Set kb.Name = "search_docs"
    Set kb.Description = "IRIS database documentation"
    Set kb.TopK = 3

    $$$ThrowOnError(kb.Build(emb, vs))
    Write "Knowledge base built.", !, !

        set l1 =  "SELECT ID, AttachmentData, Patient "
        set l2 = "FROM AFHIRData.DocumentReference WHERE ContentType='text/plain; charset=utf-8'"
        set query = l1_l2
        set statement = ##class(%SQL.Statement).%New()
        set status = statement.%Prepare(query)
        if $$$ISERR(status) {
            Write "Error preparing SQL statement: ", $System.Status.GetErrorText(status), !
            quit $$$ERROR($$$GeneralError,"Error preparing SQL statement")
        }
        set resultSet = statement.%Execute()
        
        while resultSet.%Next() {

            set src = ""_resultSet.%Get("ID")
            set metadata = {"source": (src), "Patient": (resultSet.%Get("Patient"))} 

            set content = ..HexToString(resultSet.%Get("AttachmentData"))
            Set chunks = kb.AddDocument(content, metadata)
            w chunks, " chunks added for document ID ", resultSet.%Get("ID"), !
        }
        
        Quit $$$OK
}

/// Converts hexidecimal encoded string to a regular string
ClassMethod HexToString(hex As %String) As %String
{
    if ($Length(hex)#2) {
        throw ##class(%Exception.General).%New("Hex string length must be even")
    }

    set out = ""
    for i=1:2:$Length(hex) {
        set out = out_$CHAR($ZHEX($Extract(hex,i,i+1)))
    }

    quit out
}

}
