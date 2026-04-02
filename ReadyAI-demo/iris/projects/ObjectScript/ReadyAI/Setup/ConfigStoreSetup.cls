Class ReadyAI.Setup.ConfigStoreSetup Extends %RegisteredObject
{

ClassMethod Setup() As %Status
{
    set sc = $$$OK

    Do ##class(%ConfigStore.Configuration).Delete("AI.LLM.readyai")

    set llmConfig = {
        "model_provider": "openai",
        "model": "gpt-4o-mini"
    }

    set sc = ##class(%ConfigStore.Configuration).Create("AI", "LLM", "", "gpt-5-nano", llmConfig)
    if $$$ISERR(sc) {
        write "ERROR creating LLM config: ", $System.Status.GetErrorText(sc), !
        quit sc
    }

    write "ConfigStore ready: AI.LLM.readyai (openai / gpt-4o-mini)", !
    quit $$$OK
}

ClassMethod SetupWithAPIKey(pAPIKey As %String) As %Status
{
    set sc = $$$OK

    New $NAMESPACE
    set $NAMESPACE = "%SYS"

    Do ##class(Security.Resources).Create("OpenAIUser")
    Do ##class(Security.Resources).Create("OpenAIAdminRole")
    Do ##class(%Wallet.KeyValue).Delete("ReadyAI-Secrets.OpenAI")
    Do ##class(%Wallet.Collection).Delete("ReadyAI-Secrets")

    set collectionProps = {"UseResource": "OpenAIUser", "EditResource": "OpenAIAdminRole"}
    set sc = ##class(%Wallet.Collection).Create("ReadyAI-Secrets", collectionProps)
    if $$$ISERR(sc) { write "ERROR creating Wallet collection: ", $System.Status.GetErrorText(sc), !  quit sc }

    set secret = {"Usage": "CUSTOM", "Secret": {"api_key": (pAPIKey)}}
    set sc = ##class(%Wallet.KeyValue).Create("ReadyAI-Secrets.OpenAI", secret)
    if $$$ISERR(sc) { write "ERROR creating Wallet secret: ", $System.Status.GetErrorText(sc), !  quit sc }

    set $NAMESPACE = "READYAI"

    Do ##class(%ConfigStore.Configuration).Delete("AI.LLM.readyai")

    set llmConfig = {"model_provider": "openai", "model": "gpt-4o-mini", "api_key": "secret://ReadyAI-Secrets.OpenAI#api_key"}

    set sc = ##class(%ConfigStore.Configuration).Create("AI", "LLM", "", "gpt-5-nano", llmConfig)
    if $$$ISERR(sc) {
        write "ERROR creating LLM config: ", $System.Status.GetErrorText(sc), !
        quit sc
    }

    write "ConfigStore ready: AI.LLM.readyai (openai / gpt-4o-mini, API key in Wallet)", !
    quit $$$OK
}

}
