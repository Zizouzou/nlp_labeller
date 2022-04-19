import plotly.express as px
import numpy as np
import pandas as pd
import cv2
from pathlib import Path

#region <CONFIG>
#TODO: REPLACE BY CONFIG FILE
ENTITIES = ['ADELI', 'RPPS']
COLORMAP = px.colors.qualitative.Light24
ENT_COLOR = {ent: COLORMAP[i] for (i, ent) in enumerate(ENTITIES)}
#endregion

def readimg(img, ent, shapes=None):
    if type(img) == str:
        fig = px.imshow(cv2.imread(img), binary_backend="jpg")

    else:
        fig = px.imshow(img, binary_backend="jpg")

    fig.update_layout(
        newshape_line_color=ENT_COLOR[ent],
        margin=dict(l=0, r=0, b=0, t=0, pad=1),
        dragmode="drawrect",
        hovermode=False,
        newshape_line_width=2,
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        shapes=shapes
        )

    fig.update_traces(hoverinfo="skip")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig

def format_shape(shape):
    x0, y0, x1, y1 = (shape['x0'], shape['y0'], shape['x1'], shape['y1'])
    x0, y0, x1, y1 = (int(x) for x in (x0, y0, x1, y1))
    box = np.array([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)])
    return box.astype(np.uint)

def cmp_boxes(box1, boxes):
    return np.min([np.abs(box1 - box2).sum() for box2 in boxes]) > 0

def clean_list(list):
    while [] in list:
        list.remove([])

    return list

def get_keys(ENTS):
    keys = {}
    for ent in ENTS:
        if ent[0] in keys.keys():
            continue

        elif ent.lower()[0] in keys.keys():
            keys[ent[0]] = ent

        else:
            keys[ent.lower()[0]] = ent
    
    return keys

def init_data(FOLDER):
    init_data = {'index': 0, 'prev_index': 0, 'files': [str(_) for _ in Path(FOLDER).glob('*')]}
    init_shapes = {file: None for file in init_data['files']}
    init_bboxs = {file: pd.DataFrame({'bboxs': [], 'words': [], 'entities': [], 'types': []}).to_dict('list') for file in init_data['files']}
    curr_img = cv2.imread(init_data['files'][0])
    return init_data, init_shapes, init_bboxs, curr_img