import dash
import cv2
import pytesseract as pt
import pandas as pd
import numpy as np
from dash.exceptions import PreventUpdate
from dash import Input, Output, State
from utils import *
from config import cfg

*_, curr_img = init_data(cfg.FOLDER)
#region <OFFCANVAS>
def register_callbacks_tables(app, t):
    @app.callback(
    Output('table-' + t.lower(), 'data'),
    Input('bboxs-store', 'data'),
    Input('index-store', 'data'))
    def update_pro_table(bboxs_data, index_data):
        curr_file = index_data['files'][index_data['index']]
        curr_bboxs = pd.DataFrame(bboxs_data[curr_file])
        curr_bboxs = curr_bboxs[curr_bboxs['types'] == t]
        return curr_bboxs.reset_index().to_dict('records')

def register_callbacks_offcanvas(app, type, entities):
    @app.callback(
        Output(type.lower() + '-offcanvas', 'is_open'),
        Input('key-trigger', 'keydown'), 
        State('canvas-store', 'data'),
        [Input('btn-' + type + '-' + ent, 'n_clicks') for ent in entities]
    )
    def toggle_pratitien(pressed_key,  canvas_state, *argv):
        ctx = dash.callback_context
        trigger = ctx.triggered[0]['prop_id']

        if trigger == 'key-trigger.keydown' and not any(canvas_state.values()):    
            key_pressed = pressed_key['key']
            
            if key_pressed == type.lower()[0]:
                return True

        elif trigger in ['btn-' + type + '-' + ent + '.n_clicks' for ent in entities]:
            return False

        raise PreventUpdate

def register_callback_canvas_state(app, types):
    @app.callback(
        Output('canvas-store', 'data'), 
        [Input(t.lower() + '-offcanvas', 'is_open') for t in types])
    def update_canvas_state(*args):
        return {t: args[i] for i, t in enumerate(types)}
#endregion

#region <ENTITY>
def register_callback_entity(app, types, entities):
    @app.callback(
        Output('ent-store', 'data'),
        Output('type-store', 'data'),
        [Input('btn-' + t + '-' + ent, 'n_clicks') for t in types for ent in entities[t]]
    )
    def update_ent(*args):
        ctx = dash.callback_context
        trigger = ctx.triggered[0]['prop_id']
        type, ent = trigger.split('-')[1].upper(), trigger.split('-')[2].split('.')[0]
        return ent, type
#endregion

#region <CARD>
def register_callback_index(app):
    @app.callback(
    Output('index-store', 'data'),
    Input('key-trigger', 'keydown'), 
    State('index-store', 'data'),
    State('canvas-store', 'data')
    )
    def update_index(pressed_key, data, canvas_states):
        key = pressed_key['key']         
        curr_index = data['index']

        if any(canvas_states.values()):
            raise PreventUpdate
            
        if key == 'ArrowRight':
            data['index'] = (curr_index + 1) % len(data['files'])
            return data

        elif key == 'ArrowLeft':
            data['index'] = (curr_index - 1) % len(data['files'])
            return data

        raise PreventUpdate

def register_callback_image(app, COLOR_MAP):
    @app.callback(
        Output('graph', 'figure'),
        State('graph', 'figure'),
        Input('index-store', 'data'),
        Input('ent-store', 'data'),
        Input('type-store', 'data'),
        State('shapes-store', 'data'),
        )
    def update_image(curr_fig, data, ent, type, shapes):
        global curr_img
        ctx = dash.callback_context
        
        if ctx.triggered[0]['prop_id'] == 'ent-store.data':
            curr_fig['layout']['newshape']['line']['color'] = COLOR_MAP[type][ent]
            return curr_fig

        curr_index = data['index']
        curr_file = data['files'][curr_index]
        curr_shape = shapes[curr_file]
        curr_img = cv2.imread(curr_file)
        curr_fig = readimg(curr_file, ent, curr_shape)
        return curr_fig
#endregion

#region <BBOXS>
def register_callback_shapes(app):
    @app.callback(
        Output('shapes-store', 'data'),
        Input('graph', 'relayoutData'),
        State('shapes-store', 'data'),
        State('index-store', 'data'))
    def update_shapes(relayoutData, shapes, index_data):
        if relayoutData is None:
            raise PreventUpdate
        
        if 'shapes' not in relayoutData.keys():
            raise PreventUpdate

        curr_file = index_data['files'][index_data['index']]
        shapes[curr_file] = relayoutData['shapes']
        return shapes

def register_callbacks_bboxs(app, types):
    @app.callback(
    Output('bboxs-store', 'data'),
    Input('shapes-store', 'data'),
    State('index-store', 'data'),
    State('bboxs-store', 'data'),
    State('ent-store', 'data'),
    State('type-store', 'data'),
    [Input('table-' + t.lower(), 'cellEdited') for t in types])
    def update_bboxs(shapes, index_data, bboxs_data, ent, type,  *args):
        ctx = dash.callback_context
        trigger = ctx.triggered[0]['prop_id']

        if 'cellEdited' in trigger:
            cell_type = trigger.split('.')[0].split('-')[1].upper()
            cell = [args[i] for i, t in enumerate(types) if t == cell_type][0]
            row = cell['row']
            curr_file = index_data['files'][index_data['index']]
            bboxs_data[curr_file]['words'][row['index']] = [row['words']]
            return bboxs_data

        curr_file = index_data['files'][index_data['index']]
        curr_shape = shapes[curr_file]
        curr_bboxs = pd.DataFrame(bboxs_data[curr_file])
        
        if curr_shape is None:
            raise PreventUpdate
        
        # SHAPES IN SHAPES BUT NOT IN BBOXS (STORE)
        shape_bboxs = [format_shape(shape) for shape in curr_shape]
        
        if len(curr_bboxs):
            new_boxes = [box for box in shape_bboxs if cmp_boxes(box, curr_bboxs['bboxs'])]
            
            if len(shape_bboxs):
                for i, box in enumerate(curr_bboxs['bboxs']):
                    if cmp_boxes(box, shape_bboxs):
                        bboxs_data[curr_file]['bboxs'].pop(i)
                        bboxs_data[curr_file]['words'].pop(i)
                        bboxs_data[curr_file]['entities'].pop(i)
                        bboxs_data[curr_file]['types'].pop(i)
        
        else:
            new_boxes = shape_bboxs
        
        new_words = [pt.image_to_string(curr_img[box[1]:box[3], box[0]:box[2]], lang='fra', nice=True).replace("\n", "") for box in new_boxes]

        if len(new_boxes):
            bboxs_data[curr_file]['bboxs'].append(new_boxes)
            bboxs_data[curr_file]['words'].append(new_words)
            bboxs_data[curr_file]['entities'].append(ent)
            bboxs_data[curr_file]['types'].append(type)

        return bboxs_data
#endregion

#region <SAVE>
def register_callback_save(app):
    @app.callback(
        Output('placeholder', 'children'),
        State('bboxs-store', 'data'),
        Input('btn-save', 'n_clicks'))
    def save_bboxs(bboxs, *args):
        bboxs = pd.DataFrame.from_dict(bboxs, orient='index').rename_axis('Path').reset_index(level=0)
        bboxs['words'] = bboxs['words'].apply(lambda x: [_[0].replace('\x0c', '')  for _ in x] if len(x) else x)
        bboxs.to_csv('bboxs.csv', index=False)
#endregion