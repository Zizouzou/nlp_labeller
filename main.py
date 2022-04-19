import dash
import dash_bootstrap_components as dbc
from dash_extensions import Keyboard
from dash import dcc, html

from callbacks import *
from components import OffCanvas, ImageCard
from utils import *

import plotly.express as px
from config import cfg


app = dash.Dash(__name__, server=True, external_stylesheets=[dbc.themes.LUX], prevent_initial_callbacks=True)

#region <CONFIG>
cfg.merge_from_file('config.yaml')
TYPES = cfg.TYPES
ENTITIES = {t: cfg.ENTITIES[i] for (i, t) in enumerate(TYPES)}

COLORMAP = px.colors.sequential.Viridis
ENT_COLOR = {t: {ent: COLORMAP[i] for (i, ent) in enumerate(ENTITIES[t])} for t in TYPES}
#endregion

#region <INIT>
init_data, init_shapes, init_bboxs, curr_img = init_data(cfg.FOLDER)
curr_type = TYPES[0]
curr_ent = ENTITIES[curr_type][0]
#endregion

#region <STORAGE>
data_store = dcc.Store(id='index-store', storage_type=cfg.STORAGE, data=init_data)
shapes_store = dcc.Store(id='shapes-store', storage_type=cfg.STORAGE, data=init_shapes)
bboxs_store = dcc.Store(id='bboxs-store', storage_type=cfg.STORAGE, data=init_bboxs)
ent_store = dcc.Store(id='ent-store', storage_type=cfg.STORAGE, data=curr_ent)
type_store = dcc.Store(id='type-store', storage_type=cfg.STORAGE, data=curr_type)
canvas_store = dcc.Store(id='canvas-store', storage_type=cfg.STORAGE, data={t:False for t in TYPES})
storage = html.Div([data_store, shapes_store, bboxs_store, ent_store, type_store, canvas_store])
#endregion

#region <UI>
keyboard = Keyboard(id='key-trigger')
offcanvas = [OffCanvas(t, ENTITIES[t]) for t in TYPES]
card = ImageCard(init_data, readimg(curr_img, curr_ent))
#endregion

#region <CALLBACKS>
register_callback_entity(app, TYPES, ENTITIES)
register_callback_canvas_state(app, TYPES)
register_callback_index(app)
register_callback_image(app, ENT_COLOR)
register_callback_shapes(app)
register_callbacks_bboxs(app, TYPES)
register_callback_save(app)

for t in TYPES:
    register_callbacks_tables(app, t)
    register_callbacks_offcanvas(app, t, entities=ENTITIES[t])
#endregion

app.layout = html.Div([dbc.Container(offcanvas, fluid=True), keyboard, storage, card, html.P(id='placeholder')])

if __name__ == "__main__":
    app.title = cfg.TITLE
    app.run_server(debug=True)