import streamlit as st
import google.generativeai as genai
import os

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Assistente Lions ETS - Supporto Soci",
    page_icon="🦁",
    layout="centered"
)

st.title("🦁 Assistente Lions ETS")
st.subheader("Risposte e chiarimenti per i soci sulla Riforma del Terzo Settore")

st.markdown("""
Benvenuto! Questo assistente è progettato per rispondere alle domande dei soci in merito alla **trasformazione del Lions Club in Ente del Terzo Settore (ETS)**, all'iscrizione al **RUNTS**, ai vantaggi fiscali, agli adempimenti e alle modifiche statutarie.
""")

# 1. Lettura automatica della chiave API (Secrets di Streamlit o Ambiente)
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

# Fallback opzionale se la chiave non è ancora stata salvata nei Secrets
if not api_key:
    api_key = st.sidebar.text_input("Inserisci la tua Gemini API Key (o salvala nei Secrets):", type="password")

if not api_key:
    st.info("👈 La chiave API non è presente nei Secrets di Streamlit Cloud. Inseriscila nella barra laterale per procedere.", icon="🔑")
    st.stop()

# Configurazione API Gemini
genai.configure(api_key=api_key)

# Prompt di sistema completo grounded sui documenti Lions ETS
SYSTEM_PROMPT = """
Sei un assistente esperto specializzato sulla Riforma del Terzo Settore (D.Lgs. 117/2017) e sulla transizione dei Lions Club in Enti del Terzo Settore (ETS) ed iscrizione al RUNTS.
Rispondi alle domande dei soci del Lions Club in modo chiaro, accurato, professionale e basato sulla normativa italiana e sui Vademecum/Statuti-tipo del Multidistretto Lions 108 I.T.A.L.Y.

Punti chiave da ricordare nelle risposte:
1. Iscrizione al RUNTS: Non obbligatoria ma premiale (vantaggi fiscali, 5x1000, co-progettazione P.A., personalità giuridica con responsabilità limitata).
2. Adempimenti principali: Adeguamento dello Statuto (modello-tipo), approvazione e deposito annuale del bilancio entro il 30 giugno, tenuta libri sociali, comunicazione variazioni al RUNTS entro 30 giorni.
3. Soci ed ammissione: Non si usa più la semplice cooptazione tradizionale chiusa; le domande di ammissione seguono criteri trasparenti, non discriminatori, con delibera del C.D. e motivazione/riesame in caso di rigetto.
4. Esempi pratici:
   - 5x1000: Con 30 soci ad alto reddito/medio reddito (es. 50.000 €), il gettito stimato per il Club è significativo (circa 2.160 €/anno se tutti lo destinano).
   - Erogazioni aziendali: Una donazione di 1.000 € da parte di un'azienda genera un risparmio IRES del 24% (240 €), riducendo il costo effettivo netto della donazione a 760 €.
   - Costi: Costi una tantum di passaggio (registrazione, eventuale notaio per personalità giuridica) e costi di gestione annuale (consulenza fiscale, adempimenti RUNTS).

Rispondi sempre in italiano, in modo cortese, strutturato e facile da comprendere per tutti i soci.
"""

# Lista dei modelli supportati in ordine di priorità per velocità e stabilità
PREFERRED_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-3.8-flash",
    "gemini-pro"
]

# Inizializzazione cronologia chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ciao! Sono l'assistente virtuale per la transizione del Club in ETS. Di cosa vorresti parlare? Posso darti informazioni su vantaggi fiscali, statuto, RUNTS o adempimenti."}
    ]

# Visualizzazione dei messaggi precedenti
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Gestione input dell'utente
if user_input := st.chat_input("Fai una domanda sulla Riforma Terzo Settore per i Lions..."):
    # Salva e mostra il messaggio dell'utente
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Elaborazione risposta dell'assistente
    with st.chat_message("assistant"):
        # Alert visivo immediato "Risposta in corso"
        status_box = st.empty()
        status_box.info("⏳ **Risposta in corso...** L'assistente sta elaborando la tua richiesta.")
        
        response_text = ""
        success = False
        last_exception = None

        # Ottimizzazione velocità: invia soltanto la cronologia recente (ultimi 6 messaggi)
        recent_messages = st.session_state.messages[-7:-1]
        chat_history = []
        for msg in recent_messages:
            role = "user" if msg["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg["content"]]})

        # Fallback sequenziale automatico tra i modelli per garantire la risposta
        for model_name in PREFERRED_MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(user_input, stream=True)
                
                # Generatore in streaming: rimuove il banner di attesa al primo chunk
                def stream_chunks():
                    first_chunk = True
                    for chunk in response:
                        if chunk.text:
                            if first_chunk:
                                status_box.empty()
                                first_chunk = False
                            yield chunk.text

                response_text = st.write_stream(stream_chunks())
                status_box.empty()
                success = True
                break
            except Exception as e:
                last_exception = e
                continue

        if success:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            status_box.empty()
            st.error(f"⚠️ Impossibile generare la risposta. Dettaglio errore: {last_exception}")
