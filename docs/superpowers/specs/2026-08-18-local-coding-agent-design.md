# Lokal kodningsagent med RAG — Design

**Datum:** 2026-08-18
**Status:** Godkänd, redo för implementationsplan

## Syfte

Ett läroprojekt: bygga en agent som körs helt lokalt (ingen molnleverantör för inferens), som kan svara på frågor om och föreslå ändringar i en given kodbas via en RAG-pipeline. Primärt mål är att lära sig hur lokala LLM:er, RAG och agent-loopar fungerar under huven. Sekundärt mål: bygga vidare till ett verktyg som faktiskt används dagligen (till slut som VS Code-tillägg).

Ägaren av projektet skriver den faktiska koden själv för att lära sig — se "Samarbetsläge" nedan.

## Hårdvara / miljö

| Maskin | Specifikation | Roll |
|---|---|---|
| MacBook Air | Apple M5, 24GB unified memory, arm64 | Primär utvecklingsmiljö just nu |
| ASUS Vivobook | Intel Core Ultra 7, Nvidia RTX-laptop-GPU (~6-8GB VRAM, exakt modell overifierad) | Sekundär maskin, måste fungera utan kodändringar |

Kravet är portabilitet: samma kod och samma modellfiler ska fungera på båda utan plattformsspecifika grenar.

## Omfattning v1 (detta projekt)

- **Ingår:** Python-CLI, indexering av en godtycklig projektmapp, RAG-hämtning, agent-loop med read-only-verktyg, förslag på kodändringar i textform.
- **Ingår inte (senare, separata delprojekt):** VS Code-tillägg, skriv-/shell-verktyg för agenten, inkrementell omindexering, hybrid cloud-fallback för svåra uppgifter.

## Arkitektur

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   CLI (REPL)│────▶│  Agent Loop  │────▶│ Ollama (LLM) │
└─────────────┘     │ (Python)     │     └─────────────┘
                     │              │
                     │  ┌────────┐  │     ┌─────────────┐
                     │  │ Tools  │──┼────▶│ Filesystem   │
                     │  └────────┘  │     │ (read/search)│
                     │              │
                     │  ┌────────┐  │     ┌─────────────┐
                     │  │Retriever│─┼────▶│ Chroma       │
                     │  └────────┘  │     │ (vector db)  │
                     └──────────────┘     └─────────────┘
                            ▲
                     ┌──────┴───────┐
                     │  Indexer     │  (separat kommando: `agent index <path>`)
                     └──────────────┘
```

Allt kommunicerar över `localhost` (Ollamas REST-API på port 11434). Inget skickas till någon extern tjänst under körning — se "Lokalitet och säkerhet" nedan.

## Komponenter

### Indexer (`agent index <mapp>`)
- Går igenom en projektmapp rekursivt.
- Hoppar över `.git`, `node_modules`, binärfiler, och annat brus (kombination av `.gitignore`-regler + inbyggd standardlista).
- Klipper varje fil i chunks (~200-400 rader, med litet överlapp mellan chunks).
- Skickar varje chunk till Ollamas embedding-endpoint (`nomic-embed-text`).
- Sparar vektor + metadata (filväg, radnummer, filtyp) i en Chroma-collection persisterad till disk (en collection per indexerad mapp).
- v1 bygger om hela indexet vid varje körning — ingen inkrementell uppdatering.

### Retriever
- Tar en fritextfråga, embeddar den via samma modell som indexeraren.
- Hämtar topp-k (konfigurerbart, default t.ex. 5) mest lika chunks från Chroma.
- Returnerar chunks med metadata så agenten kan referera till exakt fil/rad.

### Tools (v1 — alla read-only)
- `read_file(path)` — läser en hel fil eller ett radintervall.
- `search_code(query)` — semantisk sökning via Retriever (RAG).
- `grep(pattern)` — exakt textsökning, komplement till semantisk sökning för när man vet exakt vad man letar efter.
- `list_dir(path)` — listar filer/mappar.
- `propose_edit(...)` — modellen skriver ut en föreslagen diff/kodändring i sitt textsvar. Skriver **inte** till disk.

### Agent Loop
- Skickar systemprompt + verktygsdefinitioner + konversationshistorik till Ollamas chat-API (OpenAI-kompatibelt tool-calling-format).
- Om modellen anropar ett verktyg: kör verktygsfunktionen i Python, mata tillbaka resultatet i konversationen, loopa.
- Avsluta loopen när modellen ger ett slutgiltigt textsvar utan verktygsanrop (med ett tak på antal loop-iterationer som skydd mot oändliga loopar).

### CLI
- `agent index <path>` — bygger/bygger om RAG-index för en projektmapp.
- `agent chat` — startar en REPL-session mot en tidigare indexerad mapp, håller konversationskontext över flera turer.

## Modellval

| Maskin | Chattmodell | Embeddingmodell |
|---|---|---|
| Mac M5, 24GB | `qwen2.5-coder:7b` (default), `qwen2.5-coder:14b` som kvalitetsalternativ | `nomic-embed-text` |
| Vivobook, Core Ultra 7 + RTX ~6-8GB | `qwen2.5-coder:7b` | `nomic-embed-text` |

Motivering: `qwen2.5-coder:7b` (Q4_K_M-kvantisering via Ollama) är den gemensamma baslinjen som är snabb och GPU-resident på båda maskinerna. 14B är en Mac-specifik lyxoption när svarskvalitet prioriteras över hastighet. Exakt VRAM på Vivobooken är overifierad (6 eller 8GB) — verifieras när den maskinen sätts upp; 7B fungerar oavsett.

## Lokalitet och säkerhet

- **Nätverk:** `ollama pull` hämtar modellvikter över internet (engångskostnad per modell, cachas lokalt). All efterföljande inferens/chatt/RAG sker helt lokalt via `localhost:11434` — ingen kod eller data skickas till någon molntjänst under användning.
- **Filformat:** Modeller distribueras som GGUF (binära vikter), inte som körbar kod eller Python pickle — GGUF kan inte exekvera godtycklig kod vid inladdning, till skillnad från äldre `.pt`/`.bin`-checkpoints.
- **Modellernas ursprung:** `qwen2.5-coder` (Alibaba) och `nomic-embed-text` (Nomic AI) är etablerade, brett använda open-weight-modeller — inte formellt säkerhetsreviderade, men väl beprövade av en stor community.
- **Verktygsbegränsning:** Agentens verktyg är read-only i v1 (ingen skriv- eller shell-åtkomst), så värsta möjliga utfall av ett modellmisstag är ett dåligt textförslag, inte förstörd kod eller körda kommandon.

## Felhantering

- Om Ollama-servern inte svarar, eller en efterfrågad modell inte är nedladdad: tydligt felmeddelande med exakt kommando att köra (`ollama pull <modell>`), ingen krasch med stacktrace.
- Indexering som stöter på en fil den inte kan läsa (t.ex. binärfil som slank igenom filtret) hoppar över filen och loggar en varning, avbryter inte hela indexeringen.

## Testning

- `pytest` för deterministiska delar: chunking-logik, filfiltrering/ignore-regler, tool-funktionerna (`read_file`, `grep`, `list_dir`), Chroma-integration.
- Agent-loopens LLM-svar testas inte med exakta text-asserts (modellsvar varierar mellan körningar) — verifieras interaktivt via `agent chat`. Eventuella smoke-tests kollar att loopen inte kraschar och att verktyg faktiskt anropas, inte exakt innehåll i svaret.

## Samarbetsläge (hur projektet byggs)

Detta är ett läroprojekt där ägaren skriver den faktiska implementationskoden för hand. Arbetsflöde per ny fil:

1. Claude anger filnamn, var filen ska ligga, dess ansvar, och pseudokod/skelett (funktionssignaturer + kommentarer om logikflöde) — ingen färdig implementation.
2. Ägaren skriver den riktiga koden manuellt.
3. Claude granskar koden, förklarar avvägningar/koncept, innan nästa fil påbörjas.

Detta fångas som arbetssätt i den kommande implementationsplanen.

## Framtida steg (uttryckligen utanför denna spec)

- VS Code-tillägg (TypeScript) som tunt skal ovanpå samma Python-motor.
- Skriv-/shell-verktyg för agenten (med tydliga godkännandesteg/guardrails).
- Inkrementell omindexering.
- Hybrid cloud-fallback för svåra uppgifter, om lokal modellkvalitet blir en begränsning.
