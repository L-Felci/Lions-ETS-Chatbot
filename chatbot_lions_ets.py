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

# 1. Recupero automatico della chiave API dai Secrets di Streamlit o dalle variabili d'ambiente
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

# Campo di inserimento manuale visibile solo se la chiave non è presente nei Secrets
if not api_key:
    api_key = st.sidebar.text_input("Inserisci la tua Gemini API Key (o salvala nei Secrets):", type="password")

if not api_key:
    st.info("👈 La chiave API non è presente nei Secrets di Streamlit Cloud. Inseriscila nella barra laterale per procedere.", icon="🔑")
    st.stop()

# Configurazione globale della chiave API
genai.configure(api_key=api_key)

# Prompt di sistema completo e grounded sui documenti Lions ETS
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

# Modelli supportati da provare in ordine (gemini-3.8-flash per primo come richiesto dalle API Gemini)
CANDIDATE_MODELS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-pro"
]

# Inizializzazione della cronologia chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ciao! Sono l'assistente virtuale per la transizione del Club in ETS. Di cosa vorresti parlare? Posso darti informazioni su vantaggi fiscali, statuto, RUNTS o adempimenti."}
    ]

# Mostra i messaggi precedenti nella schermata
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Gestione input del socio
if user_input := st.chat_input("Fai una domanda sulla Riforma Terzo Settore per i Lions..."):
    # Registra e mostra subito la domanda dell'utente
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Risposta dell'assistente
    with st.chat_message("assistant"):
        # Alert visivo d'avviso immediato
        status_box = st.empty()
        status_box.info("⏳ **Risposta in corso...** L'assistente sta elaborando la tua richiesta.")

        # Preparazione rapida dello storico (ultimi 6 messaggi per massimizzare la velocità)
        recent_messages = st.session_state.messages[-7:-1]
        chat_history = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in recent_messages
        ]

        response_text = ""
        success = False
        last_error = None

        for model_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(user_input, stream=True)

                # Generatore per st.write_stream
                def generate_chunks():
                    cleared = False
                    for chunk in response:
                        if chunk.text:
                            if not cleared:
                                status_box.empty()
                                cleared = True
                            yield chunk.text

                response_text = st.write_stream(generate_chunks())
                status_box.empty()
                success = True
                break
            except Exception as e:
                last_error = e
                continue

        if success:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            status_box.empty()
            st.error(f"⚠️ Errore durante la generazione della risposta: {last_error}")


