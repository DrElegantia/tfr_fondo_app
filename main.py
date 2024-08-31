import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Funzioni di calcolo

def calcola_imposta_media(ral):
    if ral < 15000:
        imposta = ral * 0.23
    elif ral < 28000:
        imposta = (ral - 15000) * 0.25 + 15000 * 0.23
    elif ral < 50000:
        imposta = (ral - 28000) * 0.35 + 13000 * 0.25 + 15000 * 0.23
    else:  # ral >= 50000
        imposta = (ral - 50000) * 0.43 + 22000 * 0.35 + 13000 * 0.25 + 15000 * 0.23
    return imposta / ral


def calcola_imposta_tfr_fondo(tfr_annuo_fondo, anni):
    # Aliquota base
    aliquota_base = 15

    # Calcola la riduzione dell'aliquota dopo 15 anni
    if anni > 15:
        riduzione_annuale = (anni - 15) * 0.3
    else:
        riduzione_annuale = 0

    # Calcola l'aliquota effettiva, con un minimo del 9%
    aliquota = max(aliquota_base - riduzione_annuale, 9)

    # Calcola l'imposta sul TFR
    tfr_netto = tfr_annuo_fondo * (1-aliquota / 100)

    return tfr_netto

# Input dell'utente
st.title("Calcolo del TFR: Azienda vs Fondo Pensione")


st.warning("""
**⚠️ Attenzione:**

- **Consultazione con un esperto legale:** Per garantire che tutti gli aspetti normativi siano rispettati, ti consigliamo vivamente di consultare un esperto in diritto del lavoro e previdenza sociale.

- **Documentazione e avvisi legali:** Ricorda che i calcoli forniti dall'applicazione sono solo indicativi. La normativa fiscale può cambiare, quindi è importante leggere attentamente il codice sorgente disponibile qui https://github.com/DrElegantia/tfr_fondo_app/blob/main/main.py . Prima di prendere decisioni basate su questi calcoli, ti consigliamo di parlare con un consulente fiscale o finanziario.
""")

ral = st.number_input("Inserisci la tua RAL (in Euro):", min_value=0.0, value=35000.0, step=1000.0)
anni = st.number_input("Inserisci gli anni di lavoro:", min_value=1, value=30)
percentuale_tfr = st.number_input("Percentuale RAL accantonata a TFR:", min_value=0.0, value=6.91, step=0.01)
inflazione = st.number_input("Inflazione media annua (%):", min_value=0.0, value=3.0, step=0.1)
tasso_rivalutazione_fondo = st.number_input("Tasso di rivalutazione del fondo (%):", min_value=0.0,
                                            value=inflazione * 0.75 + 1.5, step=0.1)
quota_datore_fondo = st.number_input("Quota della RAL accantonata dal datore di lavoro al fondo pensione (%):",
                                     min_value=0.0, value=1.0, step=0.1)
quota_dipendente_fondo = st.number_input("Quota della RAL accantonata dal dipendente al fondo pensione (%):",
                                         min_value=0.0, value=1.0, step=0.1)
quota_obbligazionario = st.number_input("Quota titoli di stato del fondo (%) (tassazione al 12.5%):", min_value=0.0, value=50.0, step=1.0)
quota_azionario = st.number_input("Quota azioni del fondo (%) (tassazione al 20%):", min_value=0.0, value=100-quota_obbligazionario, max_value=100-quota_obbligazionario, step=1.0)


# Lista per accumulare i risultati cumulativi
tfr_netto_cumulativo = []

# Variabile per tenere traccia della somma cumulativa
somma_cumulativa = 0

# Ciclo per ogni anno
for anno in range(1, anni + 1):
    # Definisci i dati per l'anno corrente
    df = pd.DataFrame({
        'Anno': [anno],
        'Quota TFR': [ral * (percentuale_tfr / 100)],
        'Tasso di rivalutazione': [(inflazione * 0.75 + 1.5) / 100]
    })

    # Calcola 'Montante', 'Rivalutazione lorda', 'Rivalutazione netta', 'Imposta sulle quote'
    df['Montante'] = df['Quota TFR'] * (1 + df['Tasso di rivalutazione']) ** (anni - df['Anno'])
    df['Rivalutazione lorda'] = -df['Quota TFR'] + df['Montante']
    df['Rivalutazione netta'] = df['Rivalutazione lorda'] * (1 - 0.17)
    df['Imposta sulle quote'] = calcola_imposta_media(df['Quota TFR'][0] * 12)
    df['TFR netto'] = df['Rivalutazione netta'] + df['Quota TFR'][0] * (1 - df['Imposta sulle quote'][0])

    # Aggiungi il TFR netto alla somma cumulativa
    somma_cumulativa += df['TFR netto'][0]
    tfr_netto_cumulativo.append(somma_cumulativa)

# Creiamo un DataFrame finale con i risultati
df_finale = pd.DataFrame({
    'Anno': range(1, anni + 1),
    'TFR netto cumulativo': tfr_netto_cumulativo
})

somma_cumulativa_2 = 0
tfr_netto_cumulativo_2 = []

for anno in range(1, anni + 1):
    # Definisci i dati per l'anno corrente
    df_2 = pd.DataFrame({
        'Anno': [anno],
        'Quota TFR': [ral * (percentuale_tfr + quota_datore_fondo + quota_dipendente_fondo) / 100],
        'Tasso di rivalutazione': [tasso_rivalutazione_fondo / 100]
    })

    # Calcolo del montante e della rivalutazione
    df_2['Montante'] = df_2['Quota TFR'] * (1 + df_2['Tasso di rivalutazione']) ** (anni - anno)
    df_2['Rivalutazione lorda'] = -df_2['Quota TFR'] + df_2['Montante']
    df_2['Rivalutazione netta'] = df_2['Rivalutazione lorda'] - df_2['Rivalutazione lorda'] * (
        quota_azionario / 100 * 0.2 + quota_obbligazionario / 100 * 0.125)

    df_2['TFR netto'] = df_2['Rivalutazione netta'] + calcola_imposta_tfr_fondo(df_2['Quota TFR'], anni)



    # Aggiungi il TFR netto alla somma cumulativa
    somma_cumulativa_2 += df_2['TFR netto'][0]
    tfr_netto_cumulativo_2.append(somma_cumulativa_2)

# Creiamo un DataFrame finale con i risultati
df_finale_2 = pd.DataFrame({
    'Anno': range(1, anni + 1),
    'TFR netto cumulativo': tfr_netto_cumulativo_2
})



# Grafico con Plotly
tfr_fondo_totale = df_finale_2['TFR netto cumulativo'].max()
tfr_totale = df_finale['TFR netto cumulativo'].max()

# Creazione del grafico a barre con Plotly
fig = go.Figure(data=[
    go.Bar(name='Fondo pensione', x=['Fondo pensione'], y=[tfr_fondo_totale]),
    go.Bar(name='TFR azienda', x=['TFR azienda'], y=[tfr_totale])
])

# Aggiornamento del layout del grafico
fig.update_layout(
    xaxis_title='Opzioni',
    yaxis_title='Euro',
    barmode='group'
)

# Utilizzo di Streamlit per visualizzare il grafico
st.title('Grafico a Barre del TFR Netto')
st.plotly_chart(fig)

# Grafico con Plotly
st.subheader("Grafico dell'andamento del TFR netto")
fig = go.Figure()


fig.add_trace(go.Scatter(x=df_finale_2["Anno"], y=df_finale_2['TFR netto cumulativo'], mode='lines+markers',
                         name="TFR Fondo Pensione", line=dict(color='red')))
fig.add_trace(go.Scatter(x=df_finale["Anno"], y=df_finale['TFR netto cumulativo'], mode='lines+markers',
                         name="TFR Azienda", line=dict(color='orange')))

fig.update_layout(
    title="Andamento del TFR Azienda vs Fondo Pensione",
    xaxis_title="Anni",
    yaxis_title="Importo (€)",
    legend_title="Tipologia TFR"
)

st.plotly_chart(fig)
