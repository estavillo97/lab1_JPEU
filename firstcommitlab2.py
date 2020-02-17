# -- ------------------------------------------------------------------------------------ -- #
# -- Proyecto: Repaso de python 3 y analisis de precios OHLC                              -- #
# -- Codigo: principal.py - script principal de proyecto                                  -- #
# -- Rep: https://github.com/ITESOIF/MyST/tree/master/Notas_Python/Notas_RepasoPython     -- #
# -- Autor: Francisco ME      y  estavillo agrego cosas                                                              -- #
# -- ------------------------------------------------------------------------------------ -- #

# -- ------------------------------------------------------------- Importar con funciones -- #

import funciones as fn                              # Para procesamiento de datos
import visualizaciones as vs                        # Para visualizacion de datos
import pandas as pd                                 # Procesamiento de datos
from datos import OA_Ak                             # Importar token para API de OANDA

# -- --------------------------------------------------------- Descargar precios de OANDA -- #

# token de OANDA
OA_In = "EUR_USD"                  # Instrumento
OA_Gn = "D"                        # Granularidad de velas
fini = pd.to_datetime("2019-07-06 00:00:00").tz_localize('GMT')  # Fecha inicial
ffin = pd.to_datetime("2019-12-06 00:00:00").tz_localize('GMT')  # Fecha final

# Descargar precios masivos
df_pe = fn.f_precios_masivos(p0_fini=fini, p1_ffin=ffin, p2_gran=OA_Gn,
                             p3_inst=OA_In, p4_oatk=OA_Ak, p5_ginc=4900)

# -- --------------------------------------------------------------- Graficar OHLC plotly -- #

vs_grafica1 = vs.g_velas(p0_de=df_pe.iloc[0:120, :])
vs_grafica1.show()

# -- ------------------------------------------------------------------- Conteno de velas -- #

# multiplicador de precios
pip_mult = 10000

# -- 0A.1: Hora
df_pe['hora'] = [df_pe['TimeStamp'][i].hour for i in range(0, len(df_pe['TimeStamp']))]

# -- 0A.2: Dia de la semana.
df_pe['dia'] = [df_pe['TimeStamp'][i].weekday() for i in range(0, len(df_pe['TimeStamp']))]

# -- 0B: Boxplot de amplitud de velas (close - open).
df_pe['co'] = (df_pe['Close'] - df_pe['Open'])*pip_mult

# -- ------------------------------------------------------------ Graficar Boxplot plotly -- #
vs_grafica2 = vs.g_boxplot_varios(p0_data=df_pe[['co']], p1_norm=False)
vs_grafica2.show()
#%%

def strategy(ticker, start, end, days, MA=False, EMA=False, MACD=False, LongHold=False, LongShort=False):
    """
    calculates the return on a moving average strategy of your choice
    """
    # load the data
    df =   'falta por hacer, usar eur-usd como prueba'
                            end=end)
    # Daily change in the asset value
    df["Difference"] = df["Adj Close"] - df["Adj Close"].shift()

    # only keep the adjusted close and daily change
    df = df[["Adj Close", "Difference"]]

    # choose which moving averages we want
    df = strategies(df=df, days=100, MA=MA, EMA=EMA, MACD=MACD)
    # drop na's from the MA calculations
    df.dropna(inplace=True)

    # DataFrame of the positions we wish to hold
    df_positions = positions(df, MA=MA, EMA=EMA, MACD=MACD)

    df_price_of_strategy = price_of_strategy(df, df_positions, LongHold=LongHold,
                                             LongShort=LongHold, MA=MA, EMA=EMA, MACD=MACD)

    # view summary statistics of the return series of the three strategies
    df_return_of_strategy = strategy_returns(df, df_price_of_strategy)
    df_return_of_strategy.dropna(inplace=True)
    table = erk.summary_stats(df_return_of_strategy, ppp=252)
    return df, table, df_return_of_strategy, df_positions, df_price_of_strategy


def plot_strategy(ticker, start, end, df):
    """
    Plot the performance of the strategy vs the performance of the asset
    """

    fig = plt.figure(figsize=(20, 10))
    ax1 = plt.plot(df)
    ax1 = plt.title("Comparing simple investment strategies for " +
                    ticker + " between " + start + " and " + end, fontsize=22)
    ax1 = plt.xlabel("Date", fontsize=18)
    ax1 = plt.ylabel("Price", fontsize=18)
    ax1 = plt.legend(list(df_return_of_strategy.columns), prop={"size": 22}, loc="upper left")
    plt.grid(True)
    plt.show()


def strategies(df, days, MA=False, EMA=False, MACD=False):
    """
    Add selected moving averages to the DataFrame
    """
    if MA == True:
        # simple moving average
        df["MA"] = df["Adj Close"].rolling(window=days).mean()

    if EMA == True:
        # exponential moving average
        df["EMA"] = df["Adj Close"].ewm(span=days).mean()

    if MACD == True:
        # exponential moving average
        df["EMA_26"] = df["AAPL.Adjusted"].ewm(span=26).mean()
        df["EMA_126"] = df["AAPL.Adjusted"].ewm(span=126).mean()

    return df


def positions(df, MA=False, EMA=False, MACD=False):
    """
    calculates the positions we should hold each day according to each strategy
    """
    df_positions = pd.DataFrame(index=df.index)
    if MA == True:
        # Add position type for each day for the MA
        MA_Position = []
        for i in range(0, df.shape[0]):
            if df["Adj Close"].iloc[i] > df["MA"].iloc[i]:
                MA_Position.append("Long")
            else:
                MA_Position.append("Short")
        df_positions["MA_Position"] = MA_Position

    if EMA == True:
        # Add position type for each day for the EMA
        EMA_Position = []
        for i in range(0, df.shape[0]):
            if df["Adj Close"].iloc[i] > df["EMA"].iloc[i]:
                EMA_Position.append("Long")
            else:
                EMA_Position.append("Short")
        df_positions["EMA_Position"] = EMA_Position

    if MACD == True:
        # Add position type for each day for the EMA
        MACD_Position = []
        for i in range(0, df.shape[0]):
            if df["EMA_26"].iloc[i] > df["EMA_126"].iloc[i]:
                MACD_Position.append("Long")
            else:
                MACD_Position.append("Short")
        df_positions["MACD_Position"] = MACD_Position

    return df_positions


def price_of_strategy(df, df_positions, LongHold=False, LongShort=False, MA=False, EMA=False, MACD=False):
    """
    given a DataFrame containing one or more position vectors,
    Create price process of the strategies, adding the daily change if we are long
    subtracting if we are short.
    """
    df_price_of_strategy = pd.DataFrame(index=df_positions.index)
    df_price_of_strategy["asset price"] = df["Adj Close"]
    # long hold will long the strategy if condition is met, but instead of shorting it will
    # simply sell and wait for another entry point. A better version of this would be to
    # buy bonds instead of holding cash.
    if LongHold == True:
        if MA == True:
            LongHold = [0] * df.shape[0]
            LongHold[0] = df["Adj Close"].iloc[0]
            for i in range(1, df_positions.shape[0]):
                if df_positions["MA_Position"].iloc[i] == "Long":
                    LongHold[i] = LongHold[i - 1] + df["Difference"].iloc[i]
                else:
                    LongHold[i] = LongHold[i - 1]
            df_price_of_strategy["LongHold MA"] = LongHold

        if EMA == True:
            LongHold = [0] * df.shape[0]
            LongHold[0] = df["Adj Close"].iloc[0]
            for i in range(1, df_positions.shape[0]):
                if df_positions["EMA_Position"].iloc[i] == "Long":
                    LongHold[i] = LongHold[i - 1] + df["Difference"].iloc[i]
                else:
                    LongHold[i] = LongHold[i - 1]
            df_price_of_strategy["LongHold EMA"] = LongHold

        if MACD == True:
            LongHold = [0] * df.shape[0]
            LongHold[0] = df["Adj Close"].iloc[0]
            for i in range(1, df_positions.shape[0]):
                if df_positions["MACD_Position"].iloc[i] == "Long":
                    LongHold[i] = LongHold[i - 1] + df["Difference"].iloc[i]
                else:
                    LongHold[i] = LongHold[i - 1]
            df_price_of_strategy["LongHold MACD"] = LongHold

    if LongShort == True:
        if MA == True:
            LongShort = [0] * df.shape[0]
            LongShort[0] = df["Adj Close"].iloc[0]
            for i in range(1, df.shape[0]):
                if df_positions["MA_Position"].iloc[i] == "Long":
                    LongShort[i] = LongShort[i - 1] + df["Difference"].iloc[i]
                else:
                    LongShort[i] = LongShort[i - 1] - df["Difference"].iloc[i]
            df_price_of_strategy["LongShort MA"] = LongShort

        if EMA == True:
            LongShort = [0] * df.shape[0]
            LongShort[0] = df["Adj Close"].iloc[0]
            for i in range(1, df.shape[0]):
                if df_positions["EMA_Position"].iloc[i] == "Long":
                    LongShort[i] = LongShort[i - 1] + df["Difference"].iloc[i]
                else:
                    LongShort[i] = LongShort[i - 1] - df["Difference"].iloc[i]
            df_price_of_strategy["LongShort EMA"] = LongShort

        if MACD == True:
            LongShort = [0] * df.shape[0]
            LongShort[0] = df["Adj Close"].iloc[0]
            for i in range(1, df.shape[0]):
                if df_positions["MACD_Position"].iloc[i] == "Long":
                    LongShort[i] = LongShort[i - 1] + df["Difference"].iloc[i]
                else:
                    LongShort[i] = LongShort[i - 1] - df["Difference"].iloc[i]
            df_price_of_strategy["LongShort MACD"] = LongShort
    return df_price_of_strategy


def strategy_returns(df, df_price_of_strategy):
    """
    input the price series of a strategy and output the return series
    """
    df_return_of_strategy = pd.DataFrame(index=df_price_of_strategy.index)
    cols = df_price_of_strategy.columns

    for priceSeries in cols:
        df_return_of_strategy[priceSeries] = (df_price_of_strategy[priceSeries]
                                              - df_price_of_strategy[priceSeries].shift()) / (
                                             df_price_of_strategy[priceSeries])

    return df_return_of_strategy
'laboratorio'
'''Este laboratorio sirve para generar nueva información de los precios a partir de los históricos en formato  OHLC (Open, High, Low, Close). Esta nueva información generada, la mayoría almacenada como nuevas columnas dentro del DataFrame que contiene los precios históricos OHLC, puede ser utilizada también como "variables explicativas" en modelos predictivos (ya sean de regresión o de clasificación). El enfóque de los cálculos que deberás de realizar para este laboratorio es "estadístico" utilizando información de las "velas".  También vas a poner en práctica algunos códigos simples para graficar utilizando la librería de Plotly, todo esto utilizando una lógica de organizar el código con base a "funciones" y scripts separados (algo bastante útil para proyectos aplicados de python).
Deberás de incluir en esta entrega sólamente la liga del repositorio donde se encuentra tu laboratorio. El repositorio deberá de contener, por lo menos, dos archivos. El script de tus códigos hechos (un archivo .py) y el notebook con tu versión final, donde escribirás texto y código con comentarios (utilizando el formato de notebooks que te pase).
Las funciones contenidas en el ejemplo visto en clase fueron:
['hora'] : Hora de la vela
La hora expresada en formato de 24hrs, en la que ocurrió la vela.
['dia'] : Dia de la semana de la vela
Día de la semana en formato numérico (0 = domingo, 1 = lunes, etc), en el que ocurrió la vela.
vs.g_boxplot: Boxplot de amplitud de velas (close - open).
Diagrama de caja y bigote para visualizar la dispersión de los "pips" de diferencia entre el precio Close y el precio Open de cada vela. También para resaltar los atípicos de los datos utilizados.
Las funciones a desarrollar individualmente son las siguientes:
(1pt) ['mes'] : Mes en el que ocurrió la vela.
Utilizando la columna de TimeStamp calcula el "Mes" en el que ocurrió la vela.
(1pt) ['sesion'] : Sesion de la vela
Sesión bursátil en la que ocurrió la vela,  el valor dentro de la columna deberás de colocarlo siguiendo la siguiente regla:
'asia':  si en la columna ['hora'] tiene alguno de estos valores -> 22, 23, 0, 1, 2, 3, 4, 5, 6, 7
'asia_europa': si en la columna ['hora'] tiene alguno de estos valores -> 8
'europa': si en la columna ['hora'] tiene alguno de estos valores -> 9, 10, 11, 12 
'europa_america': si en la columna ['hora'] tiene alguno de estos valores -> 13, 14, 15, 16
'america': si en la columna ['hora'] tiene alguno de estos valores -> 17, 18, 19, 20, 21
Recuerda que el ['TimeStamp'] de los precios que están descargándose en el código está en huso horario UTC, así que no aplicará a las horas de Guadalajara", sino, a las horas de cualquier centro bursátil que esté bajo el huso horario UTC, como lo es el caso de Londres que tiene huso horario GMT = 0.
(1pt) ['oc']: Amplitud de vela (en pips).
Calcular la diferencia entre las columnas ['Open'] y ['Close'], expresarla en pips.
(1pt) ['hl']: Amplitud de extremos (en pips).
Calcular la diferencia entre las columnas ['High'] y ['Low'], expresarla en pips.
(.5pt) ['sentido'] : Sentido de la vela (alcista o bajista)
En esta columna debes de asignarle el valor de 'alcista' para cuando ['Close'] >= ['Open'] y 'bajista' en el caso contrario.
(.5pt) ['sentido_c'] Conteo de velas consecutivas alcistas/bajistas.
En el DataFrame de los precios OHLC, para cada renglon, ir acumulando el valor de velas consecutivas ALCISTAS o BAJISTAS e ir haciendo el conteo de ocurrencia para cada caso. Se comienza el conteo a partir de la primera repetición, por ejemplo, ['sentido_c'] tendrá un 2  en el tiempo t cuando en el tiempo t-2 y tiempo t-1 haya sido el mismo valor que en el tiempo t. En este ejemplo ['sentido_c'] tendría un 2 (en el tiempo t-2 fue la primera vela, y la vela en tiempo t-1 y en tiempo t fueron 2 velas fueron consecutivamente en el mismo sentido).
(1pt) Ventanas móviles de volatilidad
Utiliza la columna de ['hl'] como una medida de "volatilidad" en pips de las velas. Con esta columna, genera las siguientes columnas haciendo una "ventana móvil" del máximo de esos últimos n valores. Las columnas serán 3, una para cada valor de la "volatilidad móvil" para 5, 25 y 50 velas de histórico respectivamente.
['volatilidad_5']: Utilizando la información de las 5 anteriores velas.
['volatilidad_25']: Utilizando la información de las 25 anteriores velas.
['volatilidad_50']: Utilizando la información de las 50 anteriores velas.
Recuerda que la "volatilidad" en una serie de tiempo financiera es, usualmente, la desviación estándar de los rendimientos, sin embargo, uno puedeo proponer otros "estadísticos" para representar la "variabilidad" entre los datos. En este caso, probaremos generar esta información sólo tomando en cuenta la columna ['hl']. Así que, no es necesario calcular rendimientos en esta ocasión.
(1pt) Gráfica con Plotly
Realiza una propuesta de gráfica utilizando alguna de las columnas que has generado y la librería plotly. Las reglas son las siguientes:
Tiene que tener título de gráfica
Tiene que tener título de eje x y etiquetas de eje x
Tiene que tener título de eje y y etiquetas de eje y
Se debe de poder visualizar una leyenda (en cualquier posición).'''