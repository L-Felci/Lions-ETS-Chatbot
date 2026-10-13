import streamlit as st
import google.generativeai as genai
import os

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Assistente Lions ETS - FAQ & Supporto Soci",
    page_icon="🦁",
    layout="centered"
)

st.title("🦁 Assistente Lions ETS")
st.subheader("Risposte e chiarimenti per i soci sulla Riforma del Terzo Settore")

st.markdown("""
Benvenuto! Questo assistente è progettato per rispondere alle domande dei soci in merito alla **trasformazione del Lions Club in Ente del Terzo Settore (ETS)**, all'iscrizione al **RUNTS**, ai vantaggi fiscali, agli adempimenti e alle modifiche statutarie.
""")

# Gestione della chiave API
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Inserisci la tua Gemini API Key (o configurala nei Secrets di Streamlit):", type="password")

if not api_key:
    st.info("👈 Per iniziare, inserisci la chiave API di Google Gemini nella barra laterale oppure salvala nei Secrets dell'app.", icon="🔑")
    st.stop()

# Configurazione di Gemini
genai.configure(api_key=api_key)

# Prompt di sistema sintetico e ottimizzato per la massima velocità di risposta
SYSTEM_PROMPT = """
Sei un assistente esperto sulla Riforma del Terzo Settore (D.Lgs. 117/2017) e sulla transizione dei Lions Club in Enti del Terzo Settore (ETS) ed iscrizione al RUNTS.
Rispondi ai soci del Lions Club in modo chiaro, conciso, sintetico e professionale.

Punti chiave:
1. RUNTS: Non obbligatorio ma premiale (vantaggi fiscali, 5x1000, co-progettazione P.A., personalità giuridica con responsabilità limitata).
2. Adempimenti: Adeguamento dello Statuto (modello-tipo), deposito annuale del bilancio entro il 30 giugno, tenuta libri sociali, comunicazione variazioni al RUNTS entro 30 giorni.
3. Soci ed ammissione: Procedura trasparente, non discriminatoria, delibera del C.D. e motivazione/riesame in caso di rigetto (non più cooptazione chiusa).
4. Esempi pratici:
   - 5x1000: 30 soci con reddito medio 50.000 € -> ~2.160 €/anno per il Club.
   - Erogazioni aziende: Donazione di 1.000 € -> risparmio IRES del 24% (240 €), costo netto effettivo 760 €.
   - Costi: Una tantum per passaggio (registrazione/notaio) + costi annuali di gestione e contabilità.

Sii diretto, rispondi sempre in italiano ed evita preamboli inutili per velocizzare la lettura.
"""

# Modello ultra-veloce raccomandato
FAST_MODEL = "gemini-1.5-flash"

# Inizializzazione della cronologia di chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ciao! Sono l'assistente virtuale per la transizione del Club in ETS. Di cosa vorresti parlare? Posso darti informazioni su vantaggi fiscali, statuto, RUNTS o adempimenti."}
    ]

# Visualizzazione dei messaggi precedenti
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input dell'utente
if user_input := st.chat_input("Fai una domanda sulla Riforma Terzo Settore per i Lions..."):
    # Aggiungi il messaggio utente
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Genera la risposta con alert di caricamento ed esecuzione in streaming
    with st.chat_message("assistant"):
        # 1. Alert visivo immediato di elaborazione in corso
        progress_alert = st.info("⏳ **Risposta in corso...** L'assistente sta elaborando la richiesta sui documenti Lions ETS.", icon="🔄")
        
        # Prepariamo la cronologia di chat limitata agli ultimi messaggi per massima velocità
        chat_history = []
        recent_messages = st.session_state.messages[-7:-1] # Mantiene solo gli ultimi messaggi per evitare rallentamenti da contesto lungo
        for msg in recent_messages:
            role = "user" if msg["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg["content"]]})

        try:
            model = genai.GenerativeModel(
                model_name=FAST_MODEL,
                system_instruction=SYSTEM_PROMPT
            )
            chat = model.start_chat(history=chat_history)
            
            # Generazione in streaming
            response = chat.send_message(user_input, stream=True)
            
            # Rimuoviamo l'alert visivo appena inizia lo streaming del testo
            progress_alert.empty()
            
            def stream_generator():
                for chunk in response:
                    if chunk.text:
                        yield chunk.text

            response_text = st.write_stream(stream_generator())
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            progress_alert.empty()
            # Tentativo di fallback veloce su gemini-2.0-flash se il primo modello fallisce
            try:
                model_fallback = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=SYSTEM_PROMPT
                )
                chat_fallback = model_fallback.start_chat(history=chat_history)
                response_fallback = chat_fallback.send_message(user_input, stream=True)
                
                def stream_generator_fb():
                    for chunk in response_fallback:
                        if chunk.text:
                            yield chunk.text

                response_text = st.write_stream(stream_generator_fb())
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as ex:
                st.error(f"Errore durante la generazione: {ex}")



