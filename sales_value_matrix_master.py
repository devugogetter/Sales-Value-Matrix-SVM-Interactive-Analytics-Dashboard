import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import base64
import io
import re
import chardet  # For encoding detection

# Initialize app with professional theme
app = Dash(__name__, 
           external_stylesheets=[dbc.themes.LUX],
           suppress_callback_exceptions=True)
server = app.server

# ======================================================================
# DATA PROCESSING FUNCTIONS
# ======================================================================

def process_uploaded_data(contents, filename):
    if not contents:
        return None, "No file uploaded"
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        # Try to detect encoding
        result = chardet.detect(decoded)
        encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
        
        # Handle Excel files disguised as CSV
        if decoded.startswith(b'PK\x03\x04'):
            # It's actually an Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            # It's a CSV file
            df = pd.read_csv(io.BytesIO(decoded), encoding=encoding, engine='python', on_bad_lines='warn')
        
        df.columns = [col.strip() for col in df.columns]
        
        # Identify value columns (yes/no columns)
        value_columns = []
        for col in df.columns:
            try:
                # Clean and standardize values
                unique_vals = df[col].dropna().astype(str).str.strip().str.lower().unique()
                if all(val in ['yes', 'no', 'y', 'n', '1', '0', 'true', 'false'] for val in unique_vals):
                    value_columns.append(col)
            except:
                continue
        
        return df, value_columns
    
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def process_data(df, value_columns):
    # Clean and standardize data
    for col in value_columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
        df[col] = df[col].apply(lambda x: 'Yes' if x in ['yes', 'y', '1', 'true'] else 'No')
    
    # Calculate value score
    df['Value Score'] = df[value_columns].apply(lambda x: x.map({'Yes':1, 'No':0})).sum(axis=1)
    max_score = len(value_columns)
    
    # Map engagement levels
    engagement_map = {
        'Untouched': 0,
        'Freemium': 1,
        'Da-direct': 2,
        'Orders 360 lite': 3,
        'Orders 360 full': 4
    }
    
    # Create engagement level with fallback
    stage_col = None
    for col in df.columns:
        if 'stage' in col.lower() or 'subscription' in col.lower():
            stage_col = col
            break
    
    if stage_col:
        # Clean stage values
        df[stage_col] = df[stage_col].astype(str).str.strip().str.lower()
        df['Engagement Level'] = df[stage_col].map(engagement_map).fillna(0)
    else:
        df['Engagement Level'] = 0
    
    # Quadrant classification
    value_threshold = max_score * 0.65  # 65% of max score
    engagement_threshold = 2.0
    
    conditions = [
        (df['Value Score'] >= value_threshold) & (df['Engagement Level'] >= engagement_threshold),
        (df['Value Score'] < value_threshold) & (df['Engagement Level'] >= engagement_threshold),
        (df['Value Score'] >= value_threshold) & (df['Engagement Level'] < engagement_threshold),
        (df['Value Score'] < value_threshold) & (df['Engagement Level'] < engagement_threshold)
    ]
    
    quadrants = [
        'Strategic Partners', 
        'Growth Opportunities', 
        'High Value Prospects', 
        'Basic Users'
    ]
    
    df['Quadrant'] = np.select(conditions, quadrants, default='Unclassified')
    df['Size'] = df['Value Score'] * 8 + 20  # Dynamic bubble sizing
    
    return df, max_score

# ======================================================================
# APP LAYOUT
# ======================================================================

app.layout = dbc.Container(fluid=True, className="py-4", children=[
    # Header with gradient
    dbc.Row(dbc.Col(className="header-section py-4", children=[
        html.Div([
            html.H1("SALES VALUE MATRIX", className="title mb-2"),
            html.P("Strategic Agency Value & Engagement Analysis", 
                  className="subtitle mb-0")
        ], className="container text-center")
    ]), className="mb-4 shadow"),
    
    # Main content area
    html.Div(id='main-content', children=[
        # Upload section (initially visible)
        dbc.Row(dbc.Col(width=10, lg=8, className="mx-auto", children=[
            dbc.Card(className="shadow-sm", children=[
                dbc.CardHeader("Upload Your CSV/Excel File", className="py-3"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"),
                            html.P("Drag & Drop or ", className="mb-1"),
                            html.P("Select CSV/Excel File", className="font-weight-bold")
                        ]),
                        style={
                            'width': '100%', 'height': '200px', 
                            'borderWidth': '2px', 'borderStyle': 'dashed', 
                            'borderRadius': '10px', 'textAlign': 'center',
                            'cursor': 'pointer', 'paddingTop': '40px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="mt-3 text-center"),
                    dbc.Alert(
                        "Supports CSV and Excel files with agency, group, stage, and value columns",
                        color="secondary",
                        className="mt-3 p-2 text-center"
                    )
                ])
            ])
        ]))
    ]),
    
    # Data stores
    dcc.Store(id='processed-data'),
    dcc.Store(id='value-columns'),
    dcc.Store(id='max-value-score'),
    dcc.Store(id='filename-store')
])

# ======================================================================
# CALLBACKS
# ======================================================================

@app.callback(
    [Output('upload-status', 'children'),
     Output('main-content', 'children'),
     Output('processed-data', 'data'),
     Output('value-columns', 'data'),
     Output('max-value-score', 'data'),
     Output('filename-store', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def handle_upload(contents, filename):
    if not contents:
        return no_update, no_update, no_update, no_update, no_update, no_update
    
    df, value_columns = process_uploaded_data(contents, filename)
    
    if df is None:
        return dbc.Alert(value_columns, color="danger"), no_update, no_update, no_update, no_update, no_update
    
    # Process data
    processed_df, max_score = process_data(df, value_columns)
    
    # Get physician groups and agencies
    group_col = next((col for col in processed_df.columns if 'group' in col.lower()), None)
    agency_col = next((col for col in processed_df.columns if 'agency' in col.lower() and 'name' in col.lower()), None)
    
    group_options = []
    agency_options = []
    
    if group_col:
        group_options = [{'label': group, 'value': group} 
                        for group in processed_df[group_col].unique()]
    
    if agency_col:
        agency_options = [{'label': agency, 'value': agency} 
                         for agency in processed_df[agency_col].unique()]
    
    # Create visualization layout with fixed areas
    visualization_layout = [
        # Main visualization area (top)
        dbc.Row([
            # Filters sidebar
            dbc.Col(width=3, children=[
                dbc.Card(className="shadow-sm h-100", children=[
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Filters & Controls", className="mb-0"),
                            dbc.Button(
                                html.I(className="fas fa-redo"),
                                id='reset-app',
                                color="link",
                                className="float-end p-0"
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ], className="py-3"),
                    dbc.CardBody([
                        html.Div([
                            html.Small(f"File: {filename}", className="text-muted d-block mb-3"),
                            dbc.Badge("Data Loaded", color="success", className="mb-3")
                        ]),
                        
                        html.Label("Physician Groups", className="font-weight-bold"),
                        dcc.Dropdown(
                            id='group-filter',
                            options=group_options,
                            value=[opt['value'] for opt in group_options] if group_options else None,
                            multi=True,
                            placeholder="All Groups",
                            className="mb-4"
                        ),
                        
                        html.Label("Agencies", className="font-weight-bold"),
                        dcc.Dropdown(
                            id='agency-filter',
                            options=agency_options,
                            multi=True,
                            placeholder="All Agencies",
                            className="mb-4"
                        ),
                        
                        html.Label("View Mode", className="font-weight-bold"),
                        dbc.RadioItems(
                            id='view-mode',
                            options=[
                                {'label': ' Quadrant Analysis', 'value': 'quadrant'},
                                {'label': ' Feature Adoption', 'value': 'heatmap'}
                            ],
                            value='quadrant',
                            className="mb-4"
                        ),
                        
                        html.Label("Quadrant Display", className="font-weight-bold"),
                        dbc.Checklist(
                            id='quadrant-toggle',
                            options=[{'label': ' Show Quadrant Zones', 'value': 'show'}],
                            value=['show'],
                            switch=True,
                            className="mb-4"
                        ),
                        
                        dbc.Button("Reset View", 
                                  id='reset-btn',
                                  color="outline-primary",
                                  className="w-100 mt-3",
                                  outline=True)
                    ])
                ])
            ]),
            
            # Visualization area
            dbc.Col(width=9, children=[
                dbc.Card(className="shadow-sm h-100", children=[
                    dbc.CardBody(className="p-0", children=[
                        dcc.Graph(
                            id='main-visualization', 
                            className='h-100', 
                            config={'displayModeBar': True, 'displaylogo': False},
                            style={'height': '70vh'}  # Fixed height for top area
                        )
                    ])
                ])
            ])
        ], className="mb-4"),  # Add margin at bottom
        
        # Agency details area (fixed at bottom)
        dbc.Collapse(
            dbc.Row([
                dbc.Col(width=12, children=[
                    dbc.Card(className="shadow-sm", children=[
                        dbc.CardHeader("Agency Details", className="py-3"),
                        dbc.CardBody(id='agency-details-landscape', children=[
                            html.Div(className="text-center py-4", children=[
                                html.I(className="fas fa-mouse-pointer fa-2x mb-3", style={"color": "#adb5bd"}),
                                html.P("Select an agency to view details", className="text-muted mb-0")
                            ])
                        ])
                    ])
                ])
            ]),
            id='agency-details-collapse',
            is_open=False,
            className="mt-4"  # Add top margin
        )
    ]
    
    return [
        dbc.Alert(f"Successfully processed: {filename} ({len(processed_df)} agencies)", color="success"),
        visualization_layout,
        processed_df.to_json(date_format='iso', orient='split'),
        value_columns,
        max_score,
        filename
    ]

@app.callback(
    [Output('main-visualization', 'figure'),
     Output('agency-details-collapse', 'is_open'),
     Output('agency-details-landscape', 'children')],
    [Input('processed-data', 'data'),
     Input('value-columns', 'data'),
     Input('max-value-score', 'data'),
     Input('group-filter', 'value'),
     Input('agency-filter', 'value'),
     Input('view-mode', 'value'),
     Input('quadrant-toggle', 'value'),
     Input('main-visualization', 'clickData')]
)
def update_visualization(data_json, value_columns, max_score, selected_groups, 
                         selected_agencies, view_mode, show_quadrants, click_data):
    # Initialize with empty figure if no data
    if not data_json or not value_columns:
        return go.Figure(), False, no_update
    
    # Load data
    df = pd.read_json(data_json, orient='split')
    
    # Find relevant columns
    agency_col = next((col for col in df.columns if 'agency' in col.lower() and 'name' in col.lower()), 'Agency Name')
    group_col = next((col for col in df.columns if 'group' in col.lower()), 'Physician Group')
    stage_col = next((col for col in df.columns if 'stage' in col.lower() or 'subscription' in col.lower()), 'Sales Stage (Subscription)')
    
    # Apply filters
    if selected_groups and group_col in df.columns:
        df = df[df[group_col].isin(selected_groups)]
    
    if selected_agencies and agency_col in df.columns:
        df = df[df[agency_col].isin(selected_agencies)]
    
    # Define colors
    quadrant_colors = {
        'Strategic Partners': '#4C72B0',
        'Growth Opportunities': '#55A868',
        'High Value Prospects': '#FFA07A',
        'Basic Users': '#C44E52',
        'Unclassified': '#777777'
    }
    
    # Handle quadrant view
    if view_mode == 'quadrant':
        fig = go.Figure()
        
        # Add quadrant backgrounds if enabled
        if 'show' in show_quadrants and max_score > 0:
            value_threshold = max_score * 0.65
            engagement_threshold = 2.0
            
            fig.add_shape(type="rect", 
                          x0=value_threshold, y0=engagement_threshold, 
                          x1=max_score, y1=4.5,
                          fillcolor=quadrant_colors['Strategic Partners'], 
                          opacity=0.08, line_width=0)
            
            fig.add_shape(type="rect", 
                          x0=0, y0=engagement_threshold, 
                          x1=value_threshold, y1=4.5,
                          fillcolor=quadrant_colors['Growth Opportunities'], 
                          opacity=0.08, line_width=0)
            
            fig.add_shape(type="rect", 
                          x0=value_threshold, y0=0, 
                          x1=max_score, y1=engagement_threshold,
                          fillcolor=quadrant_colors['High Value Prospects'], 
                          opacity=0.08, line_width=0)
            
            fig.add_shape(type="rect", 
                          x0=0, y0=0, 
                          x1=value_threshold, y1=engagement_threshold,
                          fillcolor=quadrant_colors['Basic Users'], 
                          opacity=0.08, line_width=0)
        
        # Add bubbles with physician group differentiation
        if group_col in df.columns:
            for group in df[group_col].unique():
                group_df = df[df[group_col] == group]
                fig.add_trace(go.Scatter(
                    x=group_df['Value Score'],
                    y=group_df['Engagement Level'],
                    mode='markers',
                    marker=dict(
                        size=group_df['Size'],
                        sizemode='diameter',
                        sizemin=5,
                        opacity=0.85,
                        line=dict(width=1.5, color='white')
                    ),
                    text=group_df[agency_col],
                    customdata=group_df[[agency_col, group_col, 'Value Score', 'Quadrant']],
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Group: %{customdata[1]}<br>"
                        "Value Score: %{customdata[2]}/" + str(max_score) + "<br>"
                        "Quadrant: %{customdata[3]}<extra></extra>"
                    ),
                    name=group
                ))
        else:
            fig.add_trace(go.Scatter(
                x=df['Value Score'],
                y=df['Engagement Level'],
                mode='markers',
                marker=dict(
                    size=df['Size'],
                    sizemode='diameter',
                    sizemin=5,
                    opacity=0.85,
                    line=dict(width=1.5, color='white'),
                    color=df['Quadrant'],
                    colors=list(quadrant_colors.values())
                ),
                text=df[agency_col],
                customdata=df[[agency_col, 'Value Score', 'Quadrant']],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Value Score: %{customdata[1]}/" + str(max_score) + "<br>"
                    "Quadrant: %{customdata[2]}<extra></extra>"
                )
            ))
        
        # Add quadrant boundaries if max_score is valid
        if max_score > 0:
            value_threshold = max_score * 0.65
            engagement_threshold = 2.0
            
            fig.add_shape(type="line", 
                          x0=value_threshold, y0=0, 
                          x1=value_threshold, y1=4.5,
                          line=dict(color="#555", width=2, dash='dash'))
            
            fig.add_shape(type="line", 
                          x0=0, y0=engagement_threshold, 
                          x1=max_score, y1=engagement_threshold,
                          line=dict(color="#555", width=2, dash='dash'))
            
            # Quadrant labels
            fig.add_annotation(
                x=value_threshold + (max_score - value_threshold)/2, 
                y=engagement_threshold + (4.5 - engagement_threshold)/2, 
                text="Strategic Partners", 
                showarrow=False,
                font=dict(size=14, color=quadrant_colors['Strategic Partners'])
            )
            
            fig.add_annotation(
                x=value_threshold/2, 
                y=engagement_threshold + (4.5 - engagement_threshold)/2, 
                text="Growth Opportunities", 
                showarrow=False,
                font=dict(size=14, color=quadrant_colors['Growth Opportunities'])
            )
            
            fig.add_annotation(
                x=value_threshold + (max_score - value_threshold)/2, 
                y=engagement_threshold/2, 
                text="High Value Prospects", 
                showarrow=False,
                font=dict(size=14, color=quadrant_colors['High Value Prospects'])
            )
            
            fig.add_annotation(
                x=value_threshold/2, 
                y=engagement_threshold/2, 
                text="Basic Users", 
                showarrow=False,
                font=dict(size=14, color=quadrant_colors['Basic Users'])
            )
        
        # Layout configuration
        fig.update_layout(
            xaxis=dict(
                title='Value Adoption Score', 
                range=[-0.5, max_score + 0.5] if max_score > 0 else None,
                gridcolor='#f0f2f6'
            ),
            yaxis=dict(
                title='Engagement Level', 
                range=[-0.2, 4.7],
                tickvals=[0, 1, 2, 3, 4],
                ticktext=['Untouched', 'Freemium', 'DA-Direct', 'Orders 360 Lite', 'Orders 360 Full'],
                gridcolor='#f0f2f6'
            ),
            plot_bgcolor='rgba(255,255,255,0.95)',
            paper_bgcolor='#f8f9fa',
            font=dict(family="Lato, sans-serif", color="#343a40"),
            margin=dict(l=50, r=50, t=30, b=50),
            hoverlabel=dict(bgcolor='white', font_size=12),
            showlegend=group_col in df.columns,
            legend_title="Physician Groups",
            transition={'duration': 500}
        )
    
    # Handle feature matrix view
    elif view_mode == 'heatmap':
        # Prepare data for heatmap
        heat_df = df.sort_values(by='Value Score', ascending=False)
        
        fig = px.imshow(
            heat_df[value_columns].replace({'Yes': 1, 'No': 0}).T,
            y=value_columns,
            x=heat_df[agency_col],
            aspect='auto',
            color_continuous_scale=[[0, '#f0f0f0'], [1, '#4C72B0']]
        )
        
        # Add annotations
        annotations = []
        for i, agency in enumerate(heat_df[agency_col]):
            for j, feature in enumerate(value_columns):
                value = heat_df[heat_df[agency_col] == agency][feature].values[0]
                annotations.append(dict(
                    x=agency,
                    y=feature,
                    text="✓" if value == "Yes" else "✗",
                    showarrow=False,
                    font=dict(size=12, color="#2c3e50" if value == "Yes" else "#adb5bd")
                ))
        
        fig.update_layout(
            annotations=annotations,
            xaxis_title="",
            yaxis_title="",
            plot_bgcolor='rgba(255,255,255,0.95)',
            paper_bgcolor='#f8f9fa',
            font=dict(family="Lato, sans-serif", color="#343a40"),
            margin=dict(l=150, r=20, t=30, b=100),
            height=700,
            xaxis=dict(tickangle=45, tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=11))
        )
        fig.update(data=[{'colorbar': {'title': 'Adoption'}}])
    
    # Handle agency selection
    agency_details = no_update
    details_open = False
    
    if click_data:
        try:
            # Get clicked agency name
            if view_mode == 'heatmap':
                agency_name = click_data['points'][0]['x']
            else:
                agency_name = click_data['points'][0]['text']
            
            agency_data = df[df[agency_col] == agency_name].iloc[0]
            
            # Create feature badges
            feature_badges = []
            for feature in value_columns:
                status = "success" if agency_data[feature] == 'Yes' else "secondary"
                feature_badges.append(
                    dbc.ListGroupItem([
                        dbc.Row([
                            dbc.Col(html.Span(feature, className="text-truncate")), 
                            dbc.Col(
                                dbc.Badge("Adopted" if agency_data[feature] == 'Yes' else "Not Adopted", 
                                          color=status, 
                                          className="float-end"),
                                width="auto"
                            )
                        ], className="align-items-center")
                    ], className="py-2")
                )
            
            # Create details card
            details_content = []
            
            # Agency info section
            if group_col in agency_data:
                details_content.append(
                    dbc.Row([
                        dbc.Col([
                            html.Div(className="mb-3", children=[
                                html.Small("Physician Group", className="text-muted d-block"),
                                html.Strong(agency_data[group_col], className="d-block")
                            ])
                        ], width=6),
                        dbc.Col([
                            html.Div(className="mb-3", children=[
                                html.Small("Value Score", className="text-muted d-block"),
                                html.Strong(f"{agency_data['Value Score']}/{max_score}", className="d-block")
                            ])
                        ], width=6)
                    ])
                )
            
            if stage_col in agency_data:
                details_content.append(
                    html.Div(className="mb-3", children=[
                        html.Small("Sales Stage", className="text-muted d-block"),
                        html.Strong(agency_data[stage_col], className="d-block")
                    ])
                )
            
            details_content.append(
                html.Div(className="mb-3", children=[
                    html.Small("Strategic Quadrant", className="text-muted d-block"),
                    dbc.Badge(agency_data['Quadrant'], 
                              color="primary" if agency_data['Quadrant'] == "Strategic Partners" else 
                                    "success" if agency_data['Quadrant'] == "Growth Opportunities" else
                                    "warning" if agency_data['Quadrant'] == "High Value Prospects" else "danger",
                              className="mt-1")
                ])
            )
            
            details_content.append(html.Hr(className="my-3"))
            details_content.append(html.H5("Feature Adoption", className="mb-3"))
            details_content.append(dbc.ListGroup(feature_badges, flush=True, className="mb-3"))
            
            agency_details = details_content
            details_open = True
        except Exception as e:
            print(f"Error loading details: {e}")
            agency_details = dbc.Alert("Could not load agency details", color="danger")
            details_open = True
    
    return fig, details_open, agency_details

@app.callback(
    Output('main-visualization', 'figure', allow_duplicate=True),
    [Input('reset-btn', 'n_clicks')],
    prevent_initial_call=True
)
def reset_view(n_clicks):
    if n_clicks:
        return go.Figure()
    return no_update

@app.callback(
    Output('main-content', 'children', allow_duplicate=True),
    [Input('reset-app', 'n_clicks')],
    prevent_initial_call=True
)
def reset_application(n_clicks):
    if n_clicks:
        # Return to upload section
        return dbc.Row(dbc.Col(width=10, lg=8, className="mx-auto", children=[
            dbc.Card(className="shadow-sm", children=[
                dbc.CardHeader("Upload Your CSV/Excel File", className="py-3"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"),
                            html.P("Drag & Drop or ", className="mb-1"),
                            html.P("Select CSV/Excel File", className="font-weight-bold")
                        ]),
                        style={
                            'width': '100%', 'height': '200px', 
                            'borderWidth': '2px', 'borderStyle': 'dashed', 
                            'borderRadius': '10px', 'textAlign': 'center',
                            'cursor': 'pointer', 'paddingTop': '40px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="mt-3 text-center"),
                    dbc.Alert(
                        "Supports CSV and Excel files with agency, group, stage, and value columns",
                        color="secondary",
                        className="mt-3 p-2 text-center"
                    )
                ])
            ])
        ]))
    return no_update

# ======================================================================
# RUN APPLICATION
# ======================================================================
if __name__ == '__main__':
    app.run(debug=True, port=8051)