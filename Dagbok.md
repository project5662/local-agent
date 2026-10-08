# Dagbok

## Syfte med projektet
Jag ville lära mig att bygga en lokal AI-agent som använder en RAG-pipeline för att kunna jobba mot specifika filer. I det här fallet var det ett simulerat lager.

Jag laddade ner olika Qwen-modellvikter (GGUF-format) via Ollama, och modellen körs via Ollama-appen.

Sedan var det dags att bygga RAG-pipelinen, där externa bibliotek sköter embedding (nomic-embed-text) och vektorsökning/cosinelikhet (ChromaDB). Chunkningen av filerna byggde jag själv som Python-funktioner, och testade olika konfigurationer tills resultaten blev rimliga. Resultaten blev rimliga när svaren faktiskt grundades i riktig fakta från filerna som indexerades och söktes igenom.

Att bara chunka och söka räckte dock inte för att få grundade svar. Det krävdes också en hel del system-prompt-arbete: jag visste vilka svar jag ville ha, och utifrån det kunde jag justera, lägga till eller ta bort instruktioner. Jag lade även till nyckelord som agenten kan känna igen i användarens fråga (t.ex. "lager"), som styr den till rätt verktyg.

Jag behövde också bygga egna verktyg (tools) så att agenten kunde klara specifika uppgifter, till exempel beräkna olika lagersaldon.

För att agenten skulle kunna komma ihåg vad en användare skrivit tidigare i en chatt byggde jag sessions-ID: en dict där konversationens kontext sparas, så att agenten kan hämta den därifrån. Dictionaryn raderas när chatten stängs ner och en ny session startas.

Jag lade även till Docker-containerisering, för att kunna skicka hela projektet till exempelvis ett företag som vill använda min AI-assistent själva.

Felsökningen gjordes genom att följa terminalloggar i realtid medan en chatt pågick, för att se om agenten använde rätt verktyg vid rätt tillfälle (via Pythons inbyggda bibliotek `logging`).

Slutligen byggde jag två olika gränssnitt: ett terminalbaserat och ett webbaserat.
