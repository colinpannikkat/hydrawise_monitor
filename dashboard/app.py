from shared import df, get_df
from src.helpers import (
    get_one_month_back_in_datetime,
    filter_dataframe_by_date
)
from datetime import datetime

from shiny import App, render, reactive, ui, run_app
import matplotlib.pyplot as plt
import pandas as pd
import logging


zone_group = (
    df[['zone', 'zone_num']]
    .drop_duplicates()
    .sort_values('zone_num')
)

zone_choices = {
    row.zone_num: f"{row.zone_num}: {row.zone}"
    for _, row in zone_group.iterrows()
}

title = "Hydrawise Irrigation Monitoring"

app_ui = ui.page_fluid(
    ui.panel_title(title, title),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "zone",
                "Select irrigation zone",
                choices=zone_choices
            ),
            ui.input_switch("outliers", "Toggle Outliers", value=True),
            ui.input_date_range(
                "date_range",
                "Date Range",
                start=get_one_month_back_in_datetime(),
                end=datetime.today()),
            ui.input_action_button("refresh", "Refresh Data"),
            width=300,
            style="padding: 20px;"
        ),
        ui.output_plot("irrigation_for_zone"),
        ui.output_plot("total_irrigation_over_time"),
        style="padding: 30px;"
    ),
    ui.tags.style(
        """
        .container-fluid {
            padding: 40px !important;
        }
        """
    )
)


def server(input, output, session):

    trigger = reactive.Value(0)

    @reactive.calc
    @render.plot
    def irrigation_for_zone():
        trigger.get()
        group = df[df['zone_num'] == int(input.zone())]
        group = filter_dataframe_by_date(group, *input.date_range())
        zone_name = group['zone'].unique()[0]

        fig, ax = plt.subplots(figsize=(8, 4))
        group_time_fmt = pd.to_datetime(group['datetime']).dt.strftime('%Y-%m-%d %H:%M')
        ax.plot(group_time_fmt, group['gpm'], marker='o', linestyle='-', color='tab:blue')

        if input.outliers():
            outliers = group['outlier_mad']
            ax.scatter(group_time_fmt[outliers], group['gpm'][outliers], color='red', s=80, label='Outlier (MAD)')
            if outliers.any():
                ax.legend()

        ax.set_title(f"{zone_name} Irrigation", fontsize=14, fontweight='bold')
        ax.set_xlabel('Datetime', fontsize=12)
        ax.set_ylabel('GPM', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        return fig

    @reactive.calc
    @render.plot
    def total_irrigation_over_time():
        trigger.get()
        group = df.copy()
        group = filter_dataframe_by_date(group, *input.date_range())

        group['date'] = pd.to_datetime(group['datetime']).dt.date
        agg = group.groupby(['date'])['gpm'].sum().reset_index()

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(
            agg['date'],
            agg['gpm'],
            marker='o',
            linestyle='-',
        )

        ax.set_title("Total Irrigation over Time", fontsize=14, fontweight='bold')
        ax.set_xlabel('Datetime', fontsize=12)
        ax.set_ylabel('Total GPM', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        return fig

    @reactive.Effect
    @reactive.event(input.refresh)
    def _():
        global df

        logging.info("Fetching updated irrigation data.")
        df = get_df()

        trigger.set(trigger.get() + 1)


app = App(app_ui, server)
run_app(app, port=0)
