from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_tabulator as dt


#region <OFFCANVAS>
class Button(dbc.Button):
    def __init__(self, type, ent, **kwargs):
        super().__init__(**kwargs)
        self.id = 'btn-' + type + '-' + ent
        self.children = ent
        self.color = 'primary'
        self.outline = True
        self.size = 'sm'

class ButtonGroup(html.Div):
    def __init__(self, type, entities, **kwargs):
        super().__init__(**kwargs)
        self.children = [Button(type, ent) for ent in entities]
        self.style={'width': '100%'}

class Table(dt.DashTabulator):
    def __init__(self, type, **kwargs):
        super().__init__(**kwargs)
        self.id = 'table-' + type.lower()
        self.columns = [
            {"title": 'N°', "field": "index", "width": "10%", "hozAlign": "left", "editor":"input"},
            {"title": 'Entité', "field": "entities", "width": "30%", "hozAlign": "left", "editor":"input"},
            {"title": 'Texte', "field": "words", "width": "60%", "hozAlign": "left", "editor":"input"}]
        self.theme = 'bootstrap/tabulator_bootstrap'

class OffCanvas(dbc.Offcanvas):
    def __init__(self, type, entities, **kwargs):
        super().__init__(**kwargs)
        self.children = [
            ButtonGroup(type, entities, className="d-grid gap-2 col-4 sm-auto"), 
            html.Div(Table(type), style={'padding-top': '20px'})]
        self.id = type.lower() + '-offcanvas'
        self.title = type.title()
        self.is_open = False
#endregion

#region <CARD>
class GraphFigure(dcc.Graph):
    def __init__(self, figure, **kwargs):
        super().__init__(id='graph', **kwargs)
        self.figure = figure
        self.style = {'height': '90vh'}
        self.config = {"modeBarButtonsToAdd": ["drawrect", "eraseshape"]}
        self.color = 'primary'

class CardBody(dbc.CardBody):
    def __init__(self, figure, **kwargs):
        super().__init__(**kwargs)
        self.children = dbc.Spinner(figure)

class ImageCard(dbc.Card):
    def __init__(self, data, fig, **kwargs):
        super().__init__(**kwargs)
        self.id = 'imagebox'
        self.data = data
        self.fig = fig
        self.body = CardBody(GraphFigure(self.fig)) 
        self.footer = dbc.Button(id='btn-save', children='Save', color='primary', size='sm', style={'float': 'right'})
        self.children = [self.body, self.footer]
#endregion