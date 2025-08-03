
import panel as pn
import pandas as pd
import folium
from datetime import datetime

pn.extension()

def carregar_dados():
    try:
        url = "https://docs.google.com/spreadsheets/d/1MV2b4e3GNc_rhA32jeMuVNhUQWz6HkP7xrC42VscYIk/export?format=csv"
        df = pd.read_csv(url)
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()
        df.rename(columns={"_submission_time": "SubmissionDate"}, inplace=True)

        try:
            df["SubmissionDate"] = pd.to_datetime(df["SubmissionDate"]).dt.strftime('%d/%m/%Y %H:%M')
        except:
            pass

        df["Latitude"] = pd.to_numeric(df["Latitude"].astype(str).str.replace(",", "."), errors='coerce')
        df["Longitude"] = pd.to_numeric(df["Longitude"].astype(str).str.replace(",", "."), errors='coerce')

        if "Foto_URL" in df.columns:
            df["Foto_URL"] = df["Foto_URL"].astype(str).str.replace(",", ".", regex=False)
            df["Foto_URL"] = df["Foto_URL"].apply(lambda x: x if str(x).startswith(('http://', 'https://')) else None)

        return df
    except Exception as e:
        return pd.DataFrame()

df = carregar_dados()

tipo_unique = sorted(df["Tipo de Denúncia"].dropna().unique())
bairro_unique = sorted(df["Bairro"].dropna().unique())

tipo_select = pn.widgets.Select(name="Tipo de Denúncia", options=["Todos"] + tipo_unique)
bairro_select = pn.widgets.Select(name="Bairro", options=["Todos"] + bairro_unique)

@pn.depends(tipo_select, bairro_select)
def atualizar_mapa(tipo, bairro):
    filtered_df = df.copy()
    if tipo != "Todos":
        filtered_df = filtered_df[filtered_df["Tipo de Denúncia"] == tipo]
    if bairro != "Todos":
        filtered_df = filtered_df[filtered_df["Bairro"] == bairro]

    mapa_html = "<div style='height: 500px;'>Mapa não pôde ser gerado.</div>"
    if not filtered_df.empty:
        mapa = folium.Map(location=[filtered_df["Latitude"].mean(), filtered_df["Longitude"].mean()], zoom_start=13)
        for _, row in filtered_df.iterrows():
            if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
                imagem_html = ""
                if pd.notnull(row.get("Foto_URL", "")):
                    imagem_html = f'<a href="{row["Foto_URL"]}" target="_blank"><img src="{row["Foto_URL"]}" width="200"></a>'
                popup_info = f'''
                    <div style="font-family: Arial;">
                        <h4>🚨 Denúncia Registrada</h4>
                        <b>Nome:</b> {row.get("Nome")}<br>
                        <b>Tipo:</b> {row.get("Tipo de Denúncia")}<br>
                        <b>Bairro:</b> {row.get("Bairro")}<br>
                        <b>Relato:</b> {row.get("Breve relato")}<br>
                        <b>Data:</b> {row.get("SubmissionDate")}<br>
                        {imagem_html}
                    </div>
                '''
                folium.Marker([row["Latitude"], row["Longitude"]], popup=folium.Popup(popup_info, max_width=300)).add_to(mapa)
        mapa_html = mapa._repr_html_()
    return pn.pane.HTML(mapa_html, height=500)

@pn.depends(tipo_select, bairro_select)
def atualizar_tabela(tipo, bairro):
    filtered_df = df.copy()
    if tipo != "Todos":
        filtered_df = filtered_df[filtered_df["Tipo de Denúncia"] == tipo]
    if bairro != "Todos":
        filtered_df = filtered_df[filtered_df["Bairro"] == bairro]
    return pn.widgets.DataFrame(filtered_df[["Nome", "Bairro", "Tipo de Denúncia", "Breve relato", "SubmissionDate"]], width=1000)

dashboard = pn.Column(
    pn.pane.Markdown("## 📋 Denúncias Recebidas"),
    pn.Row(tipo_select, bairro_select),
    pn.pane.Markdown("### 🗺️ Mapa das Denúncias"),
    atualizar_mapa,
    pn.pane.Markdown("### 📄 Lista de Denúncias"),
    atualizar_tabela
)

dashboard.servable()
