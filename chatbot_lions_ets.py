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

# Prompt di sistema con le linee guida fondamentali grounded sui documenti Lions ETS
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

# Modello predefinito veloce (evitiamo chiamate lente a list_models)
PREFERRED_MODELS = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]

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

    # Genera la risposta con risposta in streaming per feedback immediato
    with st.chat_message("assistant"):
        response_text = ""
        success = False

        # Prepariamo la cronologia di chat
        chat_history = []
        for msg in st.session_state.messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg["content"]]})

        # Tentativo con i modelli veloci in sequenza
        for model_name in PREFERRED_MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                chat = model.start_chat(history=chat_history)
                
                # Streaming della risposta: il testo compare in tempo reale
                response = chat.send_message(user_input, stream=True)
                
                def stream_generator():
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text

                response_text = st.write_stream(stream_generator())
                success = True
                break
            except Exception as e:
                # Se un modello fallisce o non è attivo per quella chiave, passa al successivo
                continue

        if success:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            error_msg = "Non è stato possibile ottenere una risposta. Verificare che la chiave API Gemini inserita nei Secrets sia attiva e valida."
            st.error(error_msg)

