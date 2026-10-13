"""Interactive Streamlit dashboard. Launch: streamlit run src/scheduler/dashboard.py"""
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from scheduler.cli import format_time
from scheduler.dashboard_utils import busy_minutes, schedule_csv, schedule_rows
from scheduler.editor import flatten_sessions, rows_to_data
from scheduler.io import load_sessions
from scheduler.models import DAYS
from scheduler.optimizer import solve

SAMPLE = Path(__file__).resolve().parents[2] / 'examples' / 'sample.json'
STRATEGIES = {
    'Balanced': (1, 60),
    'Minimize idle time': (1, 0),
    'Minimize active days': (0, 1),
}


def calendar_chart(result):
    fig = go.Figure()
    for i, assignment in enumerate(result.assignments):
        fig.add_trace(go.Bar(
            x=[(assignment.end - assignment.start) / 60],
            y=[assignment.day], base=[assignment.start / 60], orientation='h',
            name=assignment.name, text=[assignment.name], textposition='inside',
            hovertemplate=(f'{assignment.name}<br>{assignment.day} '
                           f'{format_time(assignment.start)}–{format_time(assignment.end)}<extra></extra>'),
            marker=dict(color=f'hsl({(i * 71 + 205) % 360}, 58%, 49%)'),
            showlegend=False,
        ))
    fig.update_layout(
        barmode='overlay', height=430, bargap=0.22,
        margin=dict(l=10, r=10, t=15, b=45),
        xaxis=dict(title='Time of day', tickmode='array',
                   tickvals=list(range(7, 24)), ticktext=[f'{h:02d}:00' for h in range(7, 24)],
                   range=[7, 24], showgrid=True, gridcolor='rgba(130,130,130,0.2)'),
        yaxis=dict(categoryorder='array', categoryarray=list(reversed(DAYS))),
        legend=dict(orientation='h'),
    )
    return fig


def run():
    st.set_page_config(page_title='Smart Schedule Optimizer', page_icon='📅', layout='wide')
    st.title('📅 Smart Schedule Optimizer')
    st.caption('Constraint programming · OR-Tools CP-SAT · release candidate')

    st.sidebar.header('Data & constraints')
    uploaded = st.sidebar.file_uploader('Upload schedule JSON', type=['json'])
    try:
        source = json.loads(uploaded.getvalue().decode('utf-8')) if uploaded else json.loads(SAMPLE.read_text(encoding='utf-8'))
        load_sessions(source)
    except (UnicodeDecodeError, json.JSONDecodeError, OSError, ValueError) as exc:
        st.error(f'Invalid input: {exc}')
        st.stop()

    # Change the editor identity only when a different source file is uploaded.
    source_id = (uploaded.getvalue() if uploaded else b'example')
    import hashlib
    source_hash = hashlib.sha256(source_id).hexdigest()[:12]
    if st.session_state.get('source_hash') != source_hash:
        st.session_state.source_hash = source_hash
        st.session_state.edit_rows = flatten_sessions(source)

    slot = st.sidebar.selectbox('Slot size (minutes)', [5, 10, 15, 30, 60], index=2)
    min_break = st.sidebar.number_input('Minimum break (minutes)', min_value=0, max_value=120, value=0, step=slot)
    time_limit = st.sidebar.slider('Solver time limit (seconds)', 1, 60, 15)
    strategy = st.sidebar.selectbox('Optimization strategy', list(STRATEGIES) + ['Custom weights'])
    if strategy == 'Custom weights':
        idle_weight = st.sidebar.number_input('Idle minute weight', min_value=0, max_value=1000, value=1)
        day_weight = st.sidebar.number_input('Active day weight', min_value=0, max_value=10000, value=60)
    else:
        idle_weight, day_weight = STRATEGIES[strategy]

    st.subheader('1 · Edit sessions and availability')
    st.caption('One row = one availability window. Repeat a session name to add another window; keep its duration identical. Times use HH:MM (24-hour).')
    with st.form('schedule_editor'):
        edited = st.data_editor(
            st.session_state.edit_rows, num_rows='dynamic', hide_index=True,
            width='stretch', key=f'editor_{source_hash}',
            column_config={
                'session': st.column_config.TextColumn('Session', required=True),
                'duration': st.column_config.NumberColumn('Duration (min)', min_value=1, step=5, required=True),
                'day': st.column_config.SelectboxColumn('Day', options=list(DAYS), required=True),
                'start': st.column_config.TextColumn('Start HH:MM', required=True),
                'end': st.column_config.TextColumn('End HH:MM', required=True),
            },
        )
        apply = st.form_submit_button('Apply changes', type='primary')
    if apply:
        try:
            candidate = rows_to_data(edited.to_dict('records') if hasattr(edited, 'to_dict') else edited)
            st.session_state.edit_rows = flatten_sessions(candidate)
            st.success('Changes validated and applied.')
        except (ValueError, TypeError) as exc:
            st.error(f'Invalid editor data: {exc}')

    try:
        data = rows_to_data(st.session_state.edit_rows)
        sessions = load_sessions(data)
        if not sessions:
            st.info('Add at least one session to generate a schedule.')
            st.stop()
        if idle_weight == 0 and day_weight == 0:
            raise ValueError('At least one optimization weight must be positive.')
        if min_break % slot:
            raise ValueError('Minimum break must be a multiple of the selected slot size.')
        result = solve(sessions, slot_minutes=slot, max_seconds=time_limit,
                       min_break=int(min_break), idle_weight=int(idle_weight), day_weight=int(day_weight))
    except ValueError as exc:
        st.error(f'Cannot solve: {exc}')
        st.stop()

    st.subheader('2 · Optimized schedule')
    st.caption(f'Solver status: **{result.status}** · Strategy: **{strategy}**')
    if result.idle_minutes is None:
        st.warning('No feasible schedule returned. Try increasing availability, reducing breaks or changing the slot size.')
        st.stop()
    a, b, c, d = st.columns(4)
    a.metric('Sessions', len(result.assignments))
    b.metric('Busy time', f'{busy_minutes(result) / 60:g} h')
    c.metric('Idle time', f'{result.idle_minutes} min')
    d.metric('Active days', result.active_days)
    st.plotly_chart(calendar_chart(result), width='stretch')
    st.dataframe(schedule_rows(result), width='stretch', hide_index=True)
    st.download_button('Download schedule CSV', schedule_csv(result), 'optimized_schedule.csv', 'text/csv')
    st.download_button('Download edited input JSON', json.dumps(data, indent=2), 'schedule_input.json', 'application/json')

    st.divider()
    st.subheader('3 · Compare strategies')
    if st.button('Run strategy comparison'):
        comparisons = []
        for label, (iw, dw) in STRATEGIES.items():
            other = solve(sessions, slot_minutes=slot, max_seconds=time_limit,
                          min_break=int(min_break), idle_weight=iw, day_weight=dw)
            comparisons.append(dict(strategy=label, status=other.status,
                                    idle_minutes=other.idle_minutes, active_days=other.active_days))
        st.session_state.comparisons = comparisons
        st.session_state.comparison_signature = (json.dumps(data, sort_keys=True), slot, min_break, time_limit)
    signature = (json.dumps(data, sort_keys=True), slot, min_break, time_limit)
    if st.session_state.get('comparison_signature') == signature:
        comparisons = st.session_state.comparisons
        st.dataframe(comparisons, width='stretch', hide_index=True)
        feasible = [c for c in comparisons if c['idle_minutes'] is not None]
        if feasible:
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Idle minutes', x=[c['strategy'] for c in feasible],
                                 y=[c['idle_minutes'] for c in feasible]))
            fig.add_trace(go.Scatter(name='Active days', x=[c['strategy'] for c in feasible],
                                     y=[c['active_days'] for c in feasible], yaxis='y2',
                                     mode='lines+markers'))
            fig.update_layout(yaxis=dict(title='Idle minutes'),
                              yaxis2=dict(title='Active days', overlaying='y', side='right', rangemode='tozero'),
                              margin=dict(l=15, r=15, t=30, b=30), height=350)
            st.plotly_chart(fig, width='stretch')
        st.caption('Compare metrics rather than objective scores, which use different weights. FEASIBLE does not prove optimality.')
    else:
        st.caption('Run comparison to evaluate the three strategies using the current input.')

    with st.expander('View validated input JSON'):
        st.json(data)


if __name__ == '__main__':
    run()
