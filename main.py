import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Funzioni di calcolo

def calcola_reddito_netto(ral):
    # Definiamo gli scaglioni di reddito e le aliquote corrispondenti
    scaglioni = [15000, 28000, 50000]
    aliquote = [23, 25, 35, 43]

    # Inizializziamo l'imposta totale
    imposta_totale = 0
    reddito = ral

    # Calcoliamo l'imposta per ogni scaglione
    for i in range(len(scaglioni)):
        if reddito > scaglioni[i]:
            if i == len(scaglioni) - 1:
                # Se siamo nell'ultimo scaglione, consideriamo tutto il reddito residuo
                reddito_soggetto = reddito - scaglioni[i]
            else:
                # Altrimenti, consideriamo solo la parte che eccede lo scaglione corrente
                reddito_soggetto = min(reddito - scaglioni[i], scaglioni[i + 1] - scaglioni[i])
            imposta_totale += reddito_soggetto * aliquote[i] / 100
        else:
            break

    # Per la parte di reddito che eccede l'ultimo scaglione
    if reddito > scaglioni[-1]:
        imposta_totale += (reddito - scaglioni[-1]) * aliquote[-1] / 100

    # Calcoliamo il reddito netto sottraendo l'imposta totale
    reddito_netto = reddito - imposta_totale
    imposta_media=reddito_netto/ral

    return imposta_media

def calcola_imposta_tfr_fondo(tfr_annuo_fondo, anni):
    aliquota_base = 15
    riduzione = min((anni - 15) * 0.3, 6)
    aliquota = max(aliquota_base - riduzione, 9)
    return tfr_annuo_fondo * (1 - aliquota / 100)




# Input dell'utente
st.title("Calcolo del TFR: Azienda vs Fondo Pensione")

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
quota_obbligazionario = st.number_input("Quota titoli di stato del fondo (%):", min_value=0.0, value=50.0, step=1.0)
quota_azionario = st.number_input("Quota azioni e eobbligazioni del fondo (%):", min_value=0.0, value=100-quota_obbligazionario, max_value=100-quota_obbligazionario, step=1.0)


#tfr azienda

TFR=ral*percentuale_tfr/100
TFR_accantonato_netto=calcola_reddito_netto(TFR*12)*TFR
TFR_rivalutazione=TFR*(inflazione*0.75+1.5)/100
TFR_rivalutazione_netta=TFR_rivalutazione*(1-0.17)
TFR_azienda_netto=TFR_accantonato_netto+TFR_rivalutazione_netta
TFR_azienda_lordo=TFR+TFR_rivalutazione
data = {
    "Anno": list(range(1, anni + 1)),
    "TFR Azienda Lordo Annua": TFR_azienda_lordo,
    "TFR Azienda Netto Annua": TFR_azienda_netto,
    "Rivalutazione TFR Annua":TFR_rivalutazione,
    "Rivalutazione TFR Annua Netta":TFR_rivalutazione_netta
}

df = pd.DataFrame(data)
df["TFR Azienda Lordo Annua"]=df["TFR Azienda Lordo Annua"].cumsum()+df["Rivalutazione TFR Annua"].cumsum()
df["TFR Azienda Netto Annua"]=df["TFR Azienda Netto Annua"].cumsum()+df["Rivalutazione TFR Annua Netta"].cumsum()



#tfr fondo
TFR_fondo=ral*(percentuale_tfr+quota_dipendente_fondo+quota_datore_fondo)/100
TFR_fondo_rivalutazione=TFR_fondo*tasso_rivalutazione_fondo/100
TFR_fondo_rivalutazione_netta=TFR_fondo_rivalutazione-TFR_fondo_rivalutazione*(quota_obbligazionario*12.5+quota_azionario*20)/10000

data_2 = {
    "Anno": list(range(1, anni + 1)),
    "TFR Fondo Lordo Annua": TFR_fondo,
    "Rivalutazione TFR Fondo Annua":TFR_fondo_rivalutazione,
    "Rivalutazione TFR Fondo Annua Netta":TFR_fondo_rivalutazione_netta
}

df_Fondo = pd.DataFrame(data_2)
anno_max = df_Fondo['Anno'].max()

# Applica la funzione usando il massimo anno
df_Fondo['TFR Fondo Netto Annua'] = df_Fondo.apply(
    lambda row: calcola_imposta_tfr_fondo(row['TFR Fondo Lordo Annua'], anno_max),
    axis=1
)
df_Fondo["TFR Fondo Lordo Annua"]=df_Fondo["TFR Fondo Lordo Annua"].cumsum()+df_Fondo["Rivalutazione TFR Fondo Annua"].cumsum()
df_Fondo["TFR Fondo Netto Annua"]=df_Fondo["TFR Fondo Netto Annua"].cumsum()+df_Fondo["Rivalutazione TFR Fondo Annua Netta"].cumsum()


# Grafico con Plotly
st.subheader("Grafico dell'andamento del TFR")
fig = go.Figure()

fig.add_trace(go.Scatter(x=df["Anno"], y=df["TFR Azienda Lordo Annua"], mode='lines+markers',
                         name="TFR Azienda Lordo Accumulato", line=dict(color='blue')))
fig.add_trace(go.Scatter(x=df["Anno"], y=df["TFR Azienda Netto Annua"], mode='lines+markers',
                         name="TFR Azienda Netto Accumulato", line=dict(color='cyan')))
fig.add_trace(go.Scatter(x=df_Fondo["Anno"], y=df_Fondo["TFR Fondo Lordo Annua"], mode='lines+markers',
                         name="TFR Fondo Lordo Accumulato", line=dict(color='red')))
fig.add_trace(go.Scatter(x=df_Fondo["Anno"], y=df_Fondo["TFR Fondo Netto Annua"], mode='lines+markers',
                         name="TFR Fondo Netto Accumulato", line=dict(color='orange')))

fig.update_layout(
    title="Andamento del TFR Azienda vs Fondo Pensione",
    xaxis_title="Anni",
    yaxis_title="Importo (€)",
    legend_title="Tipologia TFR"
)

st.plotly_chart(fig)
