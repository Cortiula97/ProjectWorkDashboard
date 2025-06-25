import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
import plotly


class ChartGenerator:
    def __init__(self, df):
        self.df = df
        # Palette colori professionale e centralizzata
        self.colors = {
            "soil": "#a5682a",
            "air_humidity": "#6a82fb",
            "feed": "#ff9f43",
            "water": "#fc5c7d",
            "temp": "#ff6347",
            "comfort_zone": "rgba(40, 167, 69, 0.1)",
            "grid": "rgba(0, 0, 0, 0.07)",
            "text": "#343a40",
        }
        self.default_layout = {
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {
                "family": "Segoe UI, Arial, sans-serif",
                "size": 12,
                "color": self.colors["text"],
            },
            "hovermode": "x unified",
            "showlegend": True,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
            "margin": {"l": 60, "r": 30, "t": 80, "b": 50},
        }

    def _create_empty_chart(self, message):
        """Crea un grafico vuoto con messaggio"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#6c757d"),
        )
        fig.update_layout(height=300, **self.default_layout)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def create_humidity_chart(self):
        """Grafico umidità terreno e aria migliorato"""
        humidity_data = self.df[self.df["parametro"] == "Umidità"].copy()
        if humidity_data.empty:
            return self._create_empty_chart("Nessun dato di umidità disponibile")

        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=("Umidità Terreno (%)", "Umidità Aria (%)"),
            vertical_spacing=0.2,
            shared_xaxes=True,
        )

        soil_humidity = humidity_data[
            humidity_data["asset"] == "Terreno"
        ].sort_values("data")

        if not soil_humidity.empty:
            fig.add_trace(
                go.Scatter(
                    x=soil_humidity["data"],
                    y=soil_humidity["valore"],
                    mode="lines+markers",
                    name="Terreno",
                    line=dict(color=self.colors["soil"], width=2.5),
                    marker=dict(size=4),
                ),
                row=1,
                col=1,
            )

        air_humidity = humidity_data[humidity_data["asset"] == "Aria"].sort_values(
            "data"
        )
        if not air_humidity.empty:
            fig.add_trace(
                go.Scatter(
                    x=air_humidity["data"],
                    y=air_humidity["valore"],
                    mode="lines+markers",
                    name="Aria",
                    line=dict(color=self.colors["air_humidity"], width=2.5),
                    marker=dict(size=4),
                ),
                row=2,
                col=1,
            )

        fig.update_layout(height=500, **self.default_layout)
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor=self.colors["grid"]
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor=self.colors["grid"]
        )
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def create_resources_chart(self):
        """Grafico risorse migliorato"""
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Livello Mangime (%)", "Livello Acqua (%)"),
            horizontal_spacing=0.1,
        )

        feed_data = self.df[
            (self.df["parametro"] == "Silos") & (self.df["asset"] == "Mangime")
        ].sort_values("data")
        if not feed_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=feed_data["data"],
                    y=feed_data["valore"],
                    mode="lines",
                    name="Mangime",
                    line=dict(color=self.colors["feed"], width=3),
                    fill="tozeroy",
                    fillcolor="rgba(255, 159, 67, 0.2)",
                ),
                row=1,
                col=1,
            )

        water_data = self.df[
            (self.df["parametro"] == "Serbatoio") & (self.df["asset"] == "Acqua")
        ].sort_values("data")
        if not water_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=water_data["data"],
                    y=water_data["valore"],
                    mode="lines",
                    name="Acqua",
                    line=dict(color=self.colors["water"], width=3),
                    fill="tozeroy",
                    fillcolor="rgba(252, 92, 125, 0.2)",
                ),
                row=1,
                col=2,
            )

        fig.update_layout(height=400, **self.default_layout)
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor=self.colors["grid"]
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor=self.colors["grid"],
            range=[0, 101],
        )
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def create_temperature_chart(self):
        """Grafico temperatura migliorato"""
        temp_data = self.df[
            (self.df["parametro"] == "Temperatura")
            & (self.df["asset"] == "Aria")
        ].sort_values("data")
        if temp_data.empty:
            return self._create_empty_chart(
                "Nessun dato di temperatura disponibile"
            )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=temp_data["data"],
                y=temp_data["valore"],
                mode="lines",
                name="Temperatura",
                line=dict(color=self.colors["temp"], width=3),
            )
        )

        fig.add_hrect(
            y0=25,
            y1=30,
            fillcolor=self.colors["comfort_zone"],
            layer="below",
            line_width=0,
            annotation_text="Zona Comfort",
            annotation_position="top left",
        )

        fig.update_layout(
            title_text="Temperatura Aria (°C)",
            height=400,
            yaxis_title="Temperatura (°C)",
            **self.default_layout,
        )
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor=self.colors["grid"]
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor=self.colors["grid"]
        )
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def create_dashboard_summary(self, latest_data):
        """Crea indicatori KPI con logica migliorata"""
        kpis = []
        kpi_config = {
            "Umidità_Terreno": {
                "title": "Umidità Terreno",
                "unit": "%",
                "thresholds": {"critical": 10, "low": 30, "high": 80},
                "icon": "💧",
            },
            "Umidità_Aria": {
                "title": "Umidità Aria",
                "unit": "%",
                "thresholds": {"critical": None, "low": 50, "high": 70},
                "icon": "🌫️",
            },
            "Silos_Mangime": {
                "title": "Livello Mangime",
                "unit": "%",
                "thresholds": {"critical": 20, "low": 40, "high": None},
                "icon": "🌾",
            },
            "Serbatoio_Acqua": {
                "title": "Livello Acqua",
                "unit": "%",
                "thresholds": {"critical": 20, "low": 40, "high": None},
                "icon": "💧",
            },
            "Temperatura_Aria": {
                "title": "Temperatura",
                "unit": "°C",
                "thresholds": {"critical": None, "low": 20, "high": 30},
                "icon": "🌡️",
            },
        }

        for key, config in kpi_config.items():
            if key in latest_data:
                value = latest_data[key]["value"]
                if isinstance(value, (int, float)):
                    status = self._determine_status(value, config["thresholds"])
                    kpis.append(
                        {
                            "title": config["title"],
                            "value": int(value)
                            if value == int(value)
                            else round(value, 1),
                            "unit": config["unit"],
                            "status": status,
                            "icon": config["icon"],
                        }
                    )
        return kpis

    def _determine_status(self, value, thresholds):
        """Determina lo status per la classe CSS"""
        # La logica qui deve essere precisa per i colori
        if thresholds.get("critical") is not None and value <= thresholds.get("critical"):
            return "critical"
        if thresholds.get("low") is not None and value < thresholds.get("low"):
            return "low"
        if thresholds.get("high") is not None and value > thresholds.get("high"):
            return "high"
        return "good"