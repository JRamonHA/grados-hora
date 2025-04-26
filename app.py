import pandas as pd
from iertools.read import read_epw
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget
import plotly.graph_objects as go

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_file(
            "file", "Cargar archivo EPW", accept=[".epw"],
            button_label="Examinar", placeholder="Ningún archivo seleccionado"
        ),
        ui.input_numeric("t_cal", "Calentamiento", value=0),
        ui.input_numeric("t_enf", "Enfriamiento", value=0),
        ui.input_selectize("resample", "Frecuencia", {"A": "Mensual", "B": "Anual"}),
        open="always", position="right", bg="#f8f8f8",
    ),
    ui.layout_columns(
        ui.card("Gráfica de temperatura", output_widget("temp_plot")),
        ui.card("Grados hora de disconfort", ui.output_data_frame("discomfort_df")),
        col_widths=(8, 4),
    ),
)

def server(input, output, session):
    @reactive.calc
    def epw_data():
        f = input.file()
        if not f:
            return pd.DataFrame()
        return read_epw(f[0]["datapath"], alias=True, year=2025)

    def format_result(df_res, freq):
        df_res = df_res.reset_index().rename(columns={df_res.index.name: "Fecha"})
        df_res["GHCal"] = df_res["GHCal"].round(1)
        df_res["GHEnf"] = df_res["GHEnf"].round(1)

        if freq == "ME":
            df_res["Mes"] = df_res["Fecha"].dt.month.map(MESES)
            df_res["Mes"] = pd.Categorical(
                df_res["Mes"],
                categories=list(MESES.values()),
                ordered=True
            )
            return df_res[["Mes", "GHCal", "GHEnf"]]
        else:
            df_res["Año"] = df_res["Fecha"].dt.year
            return df_res[["Año", "GHCal", "GHEnf"]]

    @reactive.calc
    def discomfort_data():
        df = epw_data().copy()
        if df.empty:
            return pd.DataFrame()
        df["GHCal"] = (input.t_cal() - df["To"]).clip(lower=0)
        df["GHEnf"] = (df["To"] - input.t_enf()).clip(lower=0)
        freq = "ME" if input.resample() == "A" else "YE"
        series_cal = df["GHCal"].resample(freq).sum()
        series_enf = df["GHEnf"].resample(freq).sum()
        df_res = pd.DataFrame({
            "GHCal": series_cal,
            "GHEnf": series_enf
        })
        return format_result(df_res, freq)

    @render.data_frame
    def discomfort_df():
        return discomfort_data()

    @render_widget
    def temp_plot():
        df = epw_data().copy()
        df.index = pd.to_datetime(df.index)
        df["Fecha"] = df.index.strftime("%Y-%m-%d %H:%M:%S")
        if df.empty:
            return go.Figure()

        fig = go.Figure()
        # Línea de temperatura
        fig.add_trace(
            go.Scatter(
                x=df["Fecha"],
                y=df["To"],
                mode="lines",
                name="Temperatura",
                line=dict(color="#636EFA")
            )
        )
        # Línea de calentamiento ligada al input t_cal()
        set_cal = input.t_cal()
        fig.add_trace(
            go.Scatter(
                x=df["Fecha"],
                y=[set_cal] * len(df["Fecha"]),
                mode="lines",
                name="Calentamiento",
                line=dict(color="#EF553B")
            )
        )
        # Línea de enfriamiento ligada al input t_enf()
        set_enf = input.t_enf()
        fig.add_trace(
            go.Scatter(
                x=df["Fecha"],
                y=[set_enf] * len(df["Fecha"]),
                mode="lines",
                name="Enfriamiento",
                line=dict(color="#00CC96")
            )
        )
        # Ajustes de ejes 
        fig.update_xaxes(
            tickmode="auto",
            tickformat="%Y-%m-%d",
            type="date",
            dtick="M1"
        )
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="Tiempo",
            yaxis_title="Temperatura (°C)",
            legend=dict(
                orientation="h",
                y=-0.2,
                x=0.5,
                xanchor="center",
                itemwidth=80,            
                entrywidth=0.3,          
                entrywidthmode="fraction",    
                traceorder="normal"
            ),
            margin=dict(t=30, b=30, l=0, r=0)
        )
        return fig

app = App(app_ui, server)
