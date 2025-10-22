import os, io, base64
import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable

# ========== FUNÇÕES AUXILIARES ==========

def parse_hour(h):
    try:
        return int(str(h).lower().replace('h', '').strip())
    except Exception:
        return None

def generate_sample_data():
    horas = [f"{h}h" for h in range(7, 19)]
    operadores = [f"Operador {i}" for i in range(1, 11)]
    data = []
    for op in operadores:
        for h in horas:
            data.append({
                'Hora': h,
                'Operador': op,
                'Qtde. Peças': np.random.randint(20, 200),
                'Qtde. Pedidos': np.random.randint(5, 50)
            })
    df = pd.DataFrame(data)
    df['Hora_num'] = df['Hora'].apply(parse_hour)
    return df

def load_excel(path):
    dfx = pd.read_excel(path, sheet_name='QRY1000')
    dfx.columns = [c.strip() for c in dfx.columns]
    dfx['Hora_num'] = dfx['Hora'].apply(parse_hour)
    return dfx

def df_from_upload(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    dfx = pd.read_excel(io.BytesIO(decoded), sheet_name='QRY1000')
    dfx.columns = [c.strip() for c in dfx.columns]
    dfx['Hora_num'] = dfx['Hora'].apply(parse_hour)
    return dfx

def palette(theme):
    if theme == 'dark':
        return {'bg': '#0e1117', 'card': '#151a22', 'text': '#e8e8e8',
                'kpi1': 'linear-gradient(135deg,#00e3ae,#08b8a2)',
                'kpi2': 'linear-gradient(135deg,#4aa8ff,#7b5cff)',
                'kpi3': 'linear-gradient(135deg,#ffad66,#ff7a59)',
                'template': 'plotly_dark'}
    return {'bg': '#f7f8fb', 'card': '#ffffff', 'text': '#101315',
            'kpi1': 'linear-gradient(135deg,#22d3ee,#38bdf8)',
            'kpi2': 'linear-gradient(135deg,#34d399,#10b981)',
            'kpi3': 'linear-gradient(135deg,#f59e0b,#f97316)',
            'template': 'plotly_white'}

# ========== COMPONENTES ==========

def kpi_card(title, value, gradient, icon):
    return dbc.Card(dbc.CardBody([
        html.Div([
            html.Span(icon, style={'fontSize': '20px', 'marginRight': '6px'}),
            html.Strong(title)
        ]),
        html.H3(f"{value:,}".replace(',', '.'), style={'marginTop': '6px'})
    ]), style={'background': gradient, 'color': '#fff', 'border': '0', 'borderRadius': '14px',
               'boxShadow': '0 5px 20px rgba(0,0,0,.15)'})

def top3_cards(by_operador):
    medals = ['🥇', '🥈', '🥉']
    cards = []
    for i, row in by_operador.head(3).iterrows():
        cards.append(dbc.Card(dbc.CardBody([
            html.Div(f"{medals[i]} {row['Operador']}"),
            html.H5(f"{int(row['Qtde. Peças'])} peças")
        ]), style={'background': '#fff', 'border': '0', 'borderRadius': '12px', 'boxShadow': '0 4px 14px rgba(0,0,0,.1)'}))
    return cards

def make_panel(prefix, title):
    return html.Div([
        dcc.Upload(id=f'upload-{prefix}',
                   children=html.Div(['📁 Clique para importar outro arquivo (.xlsx)']),
                   multiple=False,
                   style={'display': 'inline-block', 'padding': '8px 14px', 'borderRadius': '10px',
                          'border': '1px dashed #9ca3af', 'cursor': 'pointer', 'marginBottom': '14px'},
                   accept='.xlsx'),
        html.Div(id=f'file-msg-{prefix}', style={'marginBottom': '10px', 'fontStyle': 'italic'}),
        dbc.Row([
            dbc.Col(html.Div(id=f'kpi1-{prefix}'), md=4),
            dbc.Col(html.Div(id=f'kpi2-{prefix}'), md=4),
            dbc.Col(html.Div(id=f'kpi3-{prefix}'), md=4),
        ], className='g-3 mb-3'),
        dbc.Row([
            dbc.Col(dcc.Graph(id=f'g-pecas-{prefix}', config={'displayModeBar': False}, style={'height': '420px'}), md=7),
            dbc.Col(dcc.Graph(id=f'g-pedidos-{prefix}', config={'displayModeBar': False}, style={'height': '420px'}), md=5),
        ], className='g-3 mb-3'),
        dbc.Row([
            dbc.Col(dcc.Graph(id=f'g-hora-{prefix}', config={'displayModeBar': False}, style={'height': '380px'}), md=8),
            dbc.Col(html.Div(id=f'top3-{prefix}', className='d-grid gap-2'), md=4)
        ], className='g-3 mb-3')
    ])

# ========== INICIALIZAÇÃO ==========
# ========== INICIALIZAÇÃO ==========

external_stylesheets = [dbc.themes.LUX]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True  # <-- ESSA LINHA É A CHAVE
)
server = app.server

df_fat0 = generate_sample_data()
df_sep0 = generate_sample_data()

store_fat = dcc.Store(id='data-fat', data=df_fat0.to_dict('records'))
store_sep = dcc.Store(id='data-sep', data=df_sep0.to_dict('records'))
theme_store = dcc.Store(id='theme', data='light')

# Pequeno estilo inline com efeito visual nos cards
fade_style = html.Link(
    rel='stylesheet',
    href='https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'
)

header = dbc.Row([
    dbc.Col(html.H2("Painel Operacional", className="mb-0"), md=8),
    dbc.Col(
        dbc.Button("🌞", id="theme-toggle", n_clicks=0, outline=True, color="secondary"),
        md=4, className="text-md-end"
    )
], className="g-2 mb-3")

tabs = dbc.Tabs([
    dbc.Tab(label="Faturamento", tab_id="fat"),
    dbc.Tab(label="Separação", tab_id="sep")
], id="tabs", active_tab="fat", className="mb-3")

app.layout = html.Div([
    fade_style,
    store_fat, store_sep, theme_store,
    dbc.Container([
        header,
        tabs,
        html.Div(id="tab-content", className="animate__animated animate__fadeIn")
    ], fluid=True, className="py-3", id="root")
])

# ========== CALLBACKS ==========
@app.callback(Output('tab-content', 'children'), Input('tabs', 'active_tab'))
def render_tab(active):
    if active == 'fat':
        return make_panel('fat', 'Faturamento')
    return make_panel('sep', 'Separação')

# Resto do código (callbacks de upload e atualização dos gráficos)
# Mantém tudo igual ao que já está no seu arquivo

# Upload
@app.callback(
    Output('data-fat', 'data'),
    Output('file-msg-fat', 'children'),
    Input('upload-fat', 'contents'),
    State('upload-fat', 'filename'),
    prevent_initial_call=True
)
def update_fat(contents, filename):
    if not contents:
        return no_update, "Nenhum arquivo enviado."
    try:
        df = df_from_upload(contents)
        return df.to_dict('records'), f"📊 Arquivo importado: {filename}"
    except Exception as e:
        return no_update, f"❌ Erro ao importar: {e}"

@app.callback(
    Output('data-sep', 'data'),
    Output('file-msg-sep', 'children'),
    Input('upload-sep', 'contents'),
    State('upload-sep', 'filename'),
    prevent_initial_call=True
)
def update_sep(contents, filename):
    if not contents:
        return no_update, "Nenhum arquivo enviado."
    try:
        df = df_from_upload(contents)
        return df.to_dict('records'), f"📊 Arquivo importado: {filename}"
    except Exception as e:
        return no_update, f"❌ Erro ao importar: {e}"

def register_panel_callbacks(prefix, store_id, titles):
    @app.callback(
        Output(f'kpi1-{prefix}', 'children'),
        Output(f'kpi2-{prefix}', 'children'),
        Output(f'kpi3-{prefix}', 'children'),
        Output(f'g-pecas-{prefix}', 'figure'),
        Output(f'g-pedidos-{prefix}', 'figure'),
        Output(f'g-hora-{prefix}', 'figure'),
        Output(f'top3-{prefix}', 'children'),
        Input(store_id, 'data'),
        Input('theme', 'data')
    )
    def update(data, theme):
        p = palette(theme)
        df = pd.DataFrame(data)
        by_op = df.groupby('Operador', as_index=False)[['Qtde. Peças','Qtde. Pedidos']].sum().sort_values('Qtde. Peças', ascending=False)
        by_hr = df.groupby('Hora_num', as_index=False)[['Qtde. Peças','Qtde. Pedidos']].sum()
        by_hr['Hora'] = by_hr['Hora_num'].astype(str) + 'h'
        fig1 = px.bar(by_op, y='Operador', x='Qtde. Peças', orientation='h', text='Qtde. Peças', template=p['template'])
        fig2 = px.bar(by_op, x='Operador', y='Qtde. Pedidos', text='Qtde. Pedidos', template=p['template'])
        fig3 = px.line(by_hr, x='Hora', y='Qtde. Peças', markers=True, template=p['template'])
        k1 = kpi_card(titles[0], int(df['Qtde. Peças'].sum()), p['kpi1'], '📦')
        k2 = kpi_card(titles[1], int(df['Qtde. Pedidos'].sum()), p['kpi2'], '🧾')
        k3 = kpi_card(titles[2], df['Operador'].nunique(), p['kpi3'], '👤')
        return k1, k2, k3, fig1, fig2, fig3, top3_cards(by_op)

register_panel_callbacks('fat', 'data-fat', ['Peças Faturadas','Pedidos Faturados','Operadores de Faturamento'])
register_panel_callbacks('sep', 'data-sep', ['Peças Separadas','Pedidos Separados','Operadores de Separação'])

if __name__ == "__main__":
    app.run(debug=True)
