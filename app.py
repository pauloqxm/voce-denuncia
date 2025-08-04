

import panel as pn
import pandas as pd
import folium
from datetime import datetime

pn.extension()

novo_popup_info_html = '''<div style="font-family: 'Segoe UI', sans-serif; background: #f0f4ff; border: 2px solid #2A4D9B; border-radius: 10px; padding: 12px; max-width: 300px;">
  <h3 style="margin-top: 0; color: #2A4D9B; font-size: 18px;">🚨 Denúncia Registrada</h3>
  <p style="margin: 6px 0;"><strong>👤 Nome:</strong> {nome}</p>
  <p style="margin: 6px 0;"><strong>📌 Tipo:</strong> {tipo}</p>
  <p style="margin: 6px 0;"><strong>🏙️ Bairro:</strong> {bairro}</p>
  <p style="margin: 6px 0;"><strong>🧾 Relato:</strong> {relato}</p>
  <p style="margin: 6px 0;"><strong>📅 Data:</strong> {data}</p>
  {imagem}
</div>'''

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
selected_index = pn.widgets.IntInput(name="Índice Selecionado", value=-1, visible=False)

mapa_pane = pn.pane.HTML(height=500, sizing_mode="stretch_width")
tabela_widget = pn.widgets.DataFrame(df[["Nome", "Bairro", "Tipo de Denúncia", "Breve relato", "SubmissionDate"]], width=1000)

def atualizar_visual(tipo, bairro):
    filtered_df = df.copy()
    if tipo != "Todos":
        filtered_df = filtered_df[filtered_df["Tipo de Denúncia"] == tipo]
    if bairro != "Todos":
        filtered_df = filtered_df[filtered_df["Bairro"] == bairro]

    tabela_widget.value = filtered_df[["Nome", "Bairro", "Tipo de Denúncia", "Breve relato", "SubmissionDate"]]

    mapa_html = "<div style='height: 500px;'>Mapa não pôde ser gerado.</div>"
    if not filtered_df.empty:
        mapa = folium.Map(location=[filtered_df["Latitude"].mean(), filtered_df["Longitude"].mean()], zoom_start=13)
        for idx, row in filtered_df.iterrows():
            if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
                imagem_html = ""
                if pd.notnull(row.get("Foto_URL", "")):
                    imagem_html = f'<a href="{row["Foto_URL"]}" target="_blank"><img src="{row["Foto_URL"]}" width="200"></a>'
                popup_info = novo_popup_info_html.format(
                    nome=row.get("Nome"),
                    tipo=row.get("Tipo de Denúncia"),
                    bairro=row.get("Bairro"),
                    relato=row.get("Breve relato"),
                    data=row.get("SubmissionDate"),
                    imagem=imagem_html
                )
                marker = folium.Marker(
                    [row["Latitude"], row["Longitude"]],
                    popup=folium.Popup(popup_info, max_width=300),
                    icon=folium.Icon(color="blue", icon="info-sign")
                )
                marker.add_to(mapa)
        mapa_html = mapa._repr_html_()
    mapa_pane.object = mapa_html

@pn.depends(tipo_select.param.value, bairro_select.param.value)
def interface(tipo, bairro):
    atualizar_visual(tipo, bairro)
    return pn.Column(
        pn.pane.Markdown("### 🗺️ Mapa das Denúncias"),
        mapa_pane,
        pn.pane.Markdown("### 📄 Lista de Denúncias"),
        tabela_widget
    )

template = pn.template.FastListTemplate(
    title="📋 Denúncias Populares",
    sidebar=[
        "### Filtros",
        tipo_select,
        bairro_select,
    ],
    main=[
        interface
    ],
    accent_base_color="#2A4D9B",
    header_background="#2A4D9B"
)

template.servable()
