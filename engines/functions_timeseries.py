import numpy as np
import pandas as pd
#import plotly
#from plotly.plotly import plot_mpl
from pyramid.arima import auto_arima
#import matplotlib.pyplot as plt
import itertools
import warnings
import statsmodels.api as sm
from pyramid.arima import auto_arima
import re
import os
from pandas import read_csv
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error,mean_absolute_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
from datetime import timedelta



from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Activation, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.utils import shuffle

import math





def windows(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out
        
#LSTM

def create_dataset(dataset, window_size = 1):
    data_X, data_Y = [], []
    for i in range(len(dataset) - window_size - 1):
        a = dataset[i:(i + window_size), 0]
        data_X.append(a)
        data_Y.append(dataset[i + window_size, 0])
    return(np.array(data_X), np.array(data_Y))

# Define the model.
def fit_model_new(train_X, train_Y, window_size = 1):
    model2 = Sequential()
    model2.add(LSTM(input_shape = (window_size, 1), 
               units = window_size, 
               return_sequences = True))
    model2.add(Dropout(0.5))
    model2.add(LSTM(256))
    model2.add(Dropout(0.5))
    model2.add(Dense(1))
    model2.add(Activation("linear"))
    model2.compile(loss = "mse", 
              optimizer = "adam")
    model2.summary()

    # Fit the first model.
    model2.fit(train_X, train_Y, epochs = 80, 
              batch_size = 1, 
              verbose = 2)
    return(model2)


    
def predict_and_score(model, X, Y,scaler):
    # Make predictions on the original scale of the data.
    pred_scaled =model.predict(X)
    pred = scaler.inverse_transform(pred_scaled)
    # Prepare Y data to also be on the original scale for interpretability.
    orig_data = scaler.inverse_transform([Y])
    # Calculate RMSE.
    score = mean_squared_error(orig_data[0], pred[:, 0])
    mae = mean_absolute_error(orig_data[0], pred[:, 0])
    return(score, pred, pred_scaled,mae)




def mean_absolute_percentage_error(y_true, y_pred): 
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100



def anomaly_uni_LSTM(lista_datos,desv_mse=0):
    temp= pd.DataFrame(lista_datos,columns=['values'])
    data_raw = temp.values.astype("float32")

    scaler = MinMaxScaler(feature_range = (0, 1))
    dataset = scaler.fit_transform(data_raw)


    print(data_raw)
    TRAIN_SIZE = 0.70

    train_size = int(len(dataset) * TRAIN_SIZE)
    test_size = len(dataset) - train_size
    train, test = dataset[0:train_size, :], dataset[train_size:len(dataset), :]
    #print("Number of entries (training set, test set): " + str((len(train), len(test))))

    # Create test and training sets for one-step-ahead regression.
    window_size = 1
    train_X, train_Y = create_dataset(train, window_size)
    test_X, test_Y = create_dataset(test, window_size)
    forecast_X, forecast_Y = create_dataset(dataset,window_size)
    #print("Original training data shape:")
    #print(train_X.shape)


    train_X = np.reshape(train_X, (train_X.shape[0], 1, train_X.shape[1]))
    test_X = np.reshape(test_X, (test_X.shape[0], 1, test_X.shape[1]))
    forecast_X = np.reshape(forecast_X, (forecast_X.shape[0], 1, forecast_X.shape[1]))
    
    #print("New training data shape:")
    #print(train_X.shape)
    #print(train_X)


    #############new engine LSTM
    model = Sequential()
    model.add(LSTM(100, input_shape=(train_X.shape[1], train_X.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mse', optimizer='adam')
    history = model.fit(train_X, train_Y, epochs=300, batch_size=100, validation_data=(test_X, test_Y), verbose=0, shuffle=False)

    yhat = model.predict(test_X)
    
    
    yhat_inverse = scaler.inverse_transform(yhat.reshape(-1, 1))
    testY_inverse = scaler.inverse_transform(test_Y.reshape(-1, 1))

    print (len(test_X))
    print (len(test_Y))
    lista_puntos = np.arange(len(test_X), len(test_X) + len(test_Y),1)
    
    #print (yhat_inverse)
    print (lista_puntos)
    testing_data = pd.DataFrame(yhat_inverse,index =lista_puntos,columns=['Prediction'])

    
    
    
    rmse = math.sqrt(mean_squared_error(testY_inverse, yhat_inverse))
    mse=mean_squared_error(testY_inverse, yhat_inverse)
    #print('Test RMSE: %.3f' % rmse)
    mae = mean_absolute_error(testY_inverse, yhat_inverse)
    #print ('test mae LSTM = ' +str(mae))

    #print testY_inverse
    #print yhat_inverse

    #print ('fin')



    #model2=fit_model_new(train_X, train_Y)


    #mse_train, train_predict, train_predict_scaled,mae_train = predict_and_score(model2, train_X, train_Y,scaler)
    #mse_test, test_predict, test_predict_scaled,mae_test = predict_and_score(model2, test_X, test_Y,scaler)
    
    #print ("predict")
    #print (test_predict)
    #print ("test")
    #print (test)



    
    df_aler = pd.DataFrame()
    test=scaler.inverse_transform([test_Y])
    
    df_aler['real_value'] = test[0]
    
    df_aler['expected value'] = yhat_inverse
    df_aler['step'] = np.arange(0, len(yhat_inverse),1)
    df_aler['mae']=mae
    df_aler['mse']=mse
    df_aler['anomaly_score'] = abs(df_aler['expected value'] - df_aler['real_value']) / df_aler['mae']
    
    
    df_aler_ult = df_aler[:5]

    df_aler_ult = df_aler_ult[(df_aler_ult.index==df_aler.index.max())|(df_aler_ult.index==((df_aler.index.max())-1))
                             |(df_aler_ult.index==((df_aler.index.max())-2))|(df_aler_ult.index==((df_aler.index.max())-3))
                             |(df_aler_ult.index==((df_aler.index.max())-4))]
    if len(df_aler_ult) == 0:
        exists_anom_last_5 = 'FALSE'
    else:
        exists_anom_last_5 = 'TRUE'
    


    df_aler = df_aler[(df_aler['anomaly_score']> 2)]

    max = df_aler['anomaly_score'].max()
    min = df_aler['anomaly_score'].min()
    df_aler['anomaly_score']= ( df_aler['anomaly_score'] - min ) /(max - min)
    
    
    max = df_aler_ult['anomaly_score'].max()
    min = df_aler_ult['anomaly_score'].min()
 
    df_aler_ult['anomaly_score']= ( df_aler_ult['anomaly_score'] - min ) /(max - min)

    pred_scaled =model.predict(forecast_X)
    pred = scaler.inverse_transform(pred_scaled)
    
    print(pred)
    print ('prediccion')
    
    #print("Training data score: %.2f MSE" % mse_train)
    #print("Test data score: %.2f MSE" % mse_test)


    engine_output={}



    engine_output['rmse'] = str(math.sqrt(mse))
    engine_output['mse'] = int(mse)
    engine_output['mae'] = int(mae)
    #print ('mae' + str(mae))
    engine_output['present_status']=exists_anom_last_5
    engine_output['present_alerts']=df_aler_ult.fillna(0).to_dict(orient='record')
    engine_output['past']=df_aler.fillna(0).to_dict(orient='record')
    engine_output['engine']='LTSM'
    df_future= pd.DataFrame(pred[:15],columns=['value'])
    df_future['value']=df_future.value.astype("float64")
    df_future['step']= np.arange( len(lista_datos),len(lista_datos)+15,1)
    #print(df_future)
    engine_output['future'] = df_future.to_dict(orient='record')
    testing_data.Prediction.astype("float64")
    testing_data['step']=testing_data.index
    testing_data.step.astype("float64")

    engine_output['debug'] = testing_data.to_dict(orient='record')

    return (engine_output)










def anomaly_AutoArima(lista_datos,desv_mse=0):
    
    lista_puntos = np.arange(0, len(lista_datos),1)
    
    
    
    

    df = pd.DataFrame()
    df['puntos'] = lista_puntos
    df['valores'] = lista_datos

    df.set_index('puntos',inplace=True,drop=False)
    #print df
    tam_train = int(len(df)*0.7)
    #print tam_train
    df_train = df[:tam_train]
    #print('Tamanio train: {}'.format(df_train.shape))
    df_test = df[tam_train:]
    #print('Tamanio test: {}'.format(df_test.shape))
    
    engine_output={}
    
    stepwise_model = auto_arima(df_train['valores'], start_p=1, start_q=1, max_p=3, max_q=3, m=12,
                              start_P=0, seasonal=True, d=1, D=1, trace=False, approx=False,
                              error_action='ignore',  # don't want to know if an order does not work
                              suppress_warnings=True,  # don't want convergence warnings
                              c=False,
                              disp=-1,
                              stepwise=False)  # set to stepwise
    
    #stepwise_model = auto_arima(df_train['valores'],trace=False, approx=False,
                              #error_action='ignore',  # don't want to know if an order does not work
                              #suppress_warnings=True,  # don't want convergence warnings
                              #c=False,
                              #disp=-1,
                              #stepwise=False) 
    
    #print(stepwise_model.aic())
    
    #print ('ARima')
    stepwise_model.fit(df_train['valores'])

    fit_forecast_pred = stepwise_model.predict_in_sample(df_train['valores'])
    fit_forecast = pd.DataFrame(fit_forecast_pred,index = df_train.index,columns=['Prediction'])
    
    future_forecast_pred = stepwise_model.predict(n_periods=len(df_test['valores']))
    future_forecast = pd.DataFrame(future_forecast_pred,index = df_test.index,columns=['Prediction'])

    list_test = df_test['valores'].values
    mse_test = (future_forecast_pred - list_test)

    mse = mean_squared_error(list_test, future_forecast_pred)

    #print('El error medio del modelo_test es: {}'.format(mse))
    rmse = np.sqrt(mse)
    #print('El root error medio del modelo_test es: {}'.format(rmse))

    mse_abs_test = abs(mse_test)

    #diff = abs(mse_abs_test - rmse)

    df_aler = pd.DataFrame(future_forecast_pred,index = df_test.index,columns=['expected value'])
    df_aler['step'] = df_test['puntos']
    df_aler['real_value'] = df_test['valores']

    #df_aler['diff_mse_test'] = diff
    df_aler['mse'] = mse
    df_aler['rmse'] = rmse
    
    df_aler['mae'] = mean_absolute_error(list_test, future_forecast_pred)


    df_aler['anomaly_score'] = abs(df_aler['expected value'] - df_aler['real_value']) / df_aler['mae']
    
    print ('ultimas alertas')
    
    df_aler_ult = df_aler[:5]

    df_aler_ult = df_aler_ult[(df_aler_ult.index==df_aler.index.max())|(df_aler_ult.index==((df_aler.index.max())-1))
                             |(df_aler_ult.index==((df_aler.index.max())-2))|(df_aler_ult.index==((df_aler.index.max())-3))
                             |(df_aler_ult.index==((df_aler.index.max())-4))]
    if len(df_aler_ult) == 0:
        exists_anom_last_5 = 'FALSE'
    else:
        exists_anom_last_5 = 'TRUE'
    


    df_aler = df_aler[(df_aler['anomaly_score']> 2)]

    max = df_aler['anomaly_score'].max()
    min = df_aler['anomaly_score'].min()
    df_aler['anomaly_score']= ( df_aler['anomaly_score'] - min ) /(max - min)
    
    
    max = df_aler_ult['anomaly_score'].max()
    min = df_aler_ult['anomaly_score'].min()
 
    df_aler_ult['anomaly_score']= ( df_aler_ult['anomaly_score'] - min ) /(max - min)

    
    #df_aler.sort_values(by=['diff_mse_test'],inplace= True, ascending = False)
    #range_mse = (desv_mse*error)
    #df_aler = df_aler[(df_aler['diff_mse_test']> range_mse)]
    
    




    ############## ANOMALY FINISHED, 
    print ("anomaly finished. Start forecasting")

    
    ############## FORECAST START
    updated_model = stepwise_model.fit(df['valores'])
    
    forecast = updated_model.predict(n_periods=5)
    

    engine_output['rmse'] = rmse
    engine_output['mse'] = mse
    engine_output['mae'] = mean_absolute_error(list_test, future_forecast_pred)
    engine_output['present_status']=exists_anom_last_5
    engine_output['present_alerts']=df_aler_ult.fillna(0).to_dict(orient='record')
    engine_output['past']=df_aler.fillna(0).to_dict(orient='record')
    engine_output['engine']='Autoarima'
    df_future= pd.DataFrame(forecast,columns=['value'])
    df_future['value']=df_future.value.astype("float32")
    df_future['step']= np.arange( len(lista_datos),len(lista_datos)+5,1)
    engine_output['future'] = df_future.to_dict(orient='record')
    testing_data  = pd.DataFrame(future_forecast_pred,index = df_test.index,columns=['expected value'])
    testing_data['step']=testing_data.index
    engine_output['debug'] = testing_data.to_dict(orient='record')
    
    return (engine_output)





def anomaly_holt(lista_datos,desv_mse=0):
    
    lista_puntos = np.arange(0, len(lista_datos),1)


    df = pd.DataFrame()
    df['puntos'] = lista_puntos
    df['valores'] = lista_datos

    df.set_index('puntos',inplace=True,drop=False)
    #print df
    tam_train = int(len(df)*0.7)
    print (" train length" + str(tam_train))
    
    df_train = df[:tam_train]
    #print('Tamanio train: {}'.format(df_train.shape))
    df_test = df[tam_train:]
    #print('Tamanio test: {}'.format(df_test.shape))

    engine_output={}
    


    ####################ENGINE START
    stepwise_model =  ExponentialSmoothing(df_train['valores'],seasonal_periods=1 )
    fit_stepwise_model = stepwise_model.fit()


    fit_forecast_pred_full = fit_stepwise_model.fittedvalues

    future_forecast_pred = fit_stepwise_model.forecast(len(df_test['valores']))
    test_values = pd.DataFrame(future_forecast_pred.values,index = df_test.index,columns=['expected value'])





    ##### sliding windows
    
    ventanas=windows(lista_datos,10)
    
    print(ventanas[0])
    training_data=[]
    count=0
    
    forecast_pred10 =[]
    real_pred10=[]
    for slot in ventanas:
        if count != 0:    
            stepwise_model =  ExponentialSmoothing(training_data,seasonal_periods=1 )
            fit_stepwise_model = stepwise_model.fit()


            future_forecast_pred = fit_stepwise_model.forecast(len(slot))
            forecast_pred10.extend(future_forecast_pred)
            real_pred10.extend(slot)
            training_data.extend(slot)
            
        else:
            training_data.extend(slot)
            forecast_pred10.extend(slot)
            real_pred10.extend(slot)
            count=1

    print ('windows prediction')
    #print ( forecast_pred10)
    #print ( real_pred10)
    
    print ('windows mae '  + str(mean_absolute_error(forecast_pred10, real_pred10)))
    
        ####################ENGINE START

    ##########GRID to find seasonal n_periods
    mae_period = 99999
    best_period=0
    for period in range(2,50):
        print ("el periodo es " + str(period))
        stepwise_model =  ExponentialSmoothing(df_train['valores'],seasonal_periods=12 ,trend='add', seasonal='add', )
        fit_stepwise_model = stepwise_model.fit()


        #fit_forecast_pred_full = fit_stepwise_model.fittedvalues

        future_forecast_pred = fit_stepwise_model.forecast(len(df_test['valores']))
        mae_temp = mean_absolute_error(future_forecast_pred.values,df_test['valores'].values)
        if mae_temp < mae_period:
            best_period=period
            mae_period=mae_temp
        else:
            print ("mae:" + str(mae_temp))
    print ("######best mae is " + str(mae_period) + " with the period " + str(best_period))
    



    list_test = df_test['valores'].values
    mse_test = (future_forecast_pred - list_test)
    #print (mse_test)
    print (future_forecast_pred.values)
    
    print(list_test)

    mse = mean_squared_error(future_forecast_pred.values,list_test)
    #print error

    print('El error medio del modelo_test es: {}'.format(mse))
    rmse = np.sqrt(mse)
    print('El root error medio del modelo_test es: {}'.format(rmse))

    mse_abs_test = abs(mse_test)

    #diff = abs(mse_abs_test - rmse)

    df_aler = pd.DataFrame(forecast_pred10,index = df.index,columns=['expected value'])
    df_aler['step'] = df['puntos']
    df_aler['real_value'] = real_pred10
    
   
    #df_aler['diff_mse_test'] = diff
    df_aler['mse'] = mse
    df_aler['rmse'] = rmse
    df_aler['mae'] = mean_absolute_error(list_test, future_forecast_pred)
    df_aler['anomaly_score'] = abs(df_aler['expected value'] - df_aler['real_value']) / df_aler['mae']
    
    

    df_aler_ult = df_aler[:5]

    df_aler_ult = df_aler_ult[(df_aler_ult.index==df_aler.index.max())|(df_aler_ult.index==((df_aler.index.max())-1))
                             |(df_aler_ult.index==((df_aler.index.max())-2))|(df_aler_ult.index==((df_aler.index.max())-3))
                             |(df_aler_ult.index==((df_aler.index.max())-4))]
    if len(df_aler_ult) == 0:
        exists_anom_last_5 = 'FALSE'
    else:
        exists_anom_last_5 = 'TRUE'
    
    
    df_aler = df_aler[(df_aler['anomaly_score']> 2)]
    max = df_aler['anomaly_score'].max()
    min = df_aler['anomaly_score'].min()
 
    df_aler['anomaly_score']= ( df_aler['anomaly_score'] - min ) /(max - min)
    
    
    #df_aler.sort_values(by=['diff_mse_test'],inplace= True, ascending = False)
    
    #range_mse = (desv_mse*error)
    #df_aler = df_aler[(df_aler['diff_mse_test']> range_mse)]
    
    max = df_aler_ult['anomaly_score'].max()
    min = df_aler_ult['anomaly_score'].min()
 
    df_aler_ult['anomaly_score']= ( df_aler_ult['anomaly_score'] - min ) /(max - min)
    
    
    
    print ("anomaly finished. Start forecasting")
    
    
    stepwise_model1 =  ExponentialSmoothing(df['valores'],seasonal_periods=len(df['valores']) , seasonal='add')
    print ("pasa el entreno")
    fit_stepwise_model1 = stepwise_model1.fit()
    future_forecast_pred1 = fit_stepwise_model1.forecast(5)
    print ("pasa el forecast")
    

    engine_output['rmse'] = rmse
    engine_output['mse'] = mse
    engine_output['mae'] = mean_absolute_error(list_test, future_forecast_pred)
    engine_output['present_status']=exists_anom_last_5
    engine_output['present_alerts']=df_aler_ult.fillna(0).to_dict(orient='record')
    engine_output['past']=df_aler.fillna(0).to_dict(orient='record')
    engine_output['engine']='Holtwinters'
#    engine_output['future']= future_forecast_pred1.to_dict()
    print ("solo falta el future")
    df_future= pd.DataFrame(future_forecast_pred1,columns=['value'])
    df_future['value']=df_future.value.astype("float32")
    df_future['step']= np.arange( len(lista_datos),len(lista_datos)+5,1)
    engine_output['future'] = df_future.to_dict(orient='record')
    #test_values = pd.DataFrame(future_forecast_pred.values,index = df_train.index,columns=['Prediction'])
    test_values['step'] = test_values.index
    engine_output['debug'] = test_values.to_dict(orient='record')
    
    
    return engine_output


#def anomaly_holt(lista_datos,desv_mse=0):
    
    #lista_puntos = np.arange(0, len(lista_datos),1)

    #df = pd.DataFrame()
    #df['puntos'] = lista_puntos
    #df['valores'] = lista_datos

    #df.set_index('puntos',inplace=True)
    ##print df
    #tam_train = int(len(df)*0.7)
    
    #df_train = df[:tam_train]
    ##print('Tamanio train: {}'.format(df_train.shape))
    #df_test = df[tam_train:]
    ##print('Tamanio test: {}'.format(df_test.shape))
    
    #stepwise_model =  ExponentialSmoothing(df_train,seasonal_periods=len(df_train) , seasonal='add')
    #fit_stepwise_model = stepwise_model.fit()


    #fit_forecast_pred = fit_stepwise_model.fittedvalues

    #future_forecast_pred = fit_stepwise_model.forecast(len(df_test))

    #list_test = df_test['valores'].values
    #mse_test = (future_forecast_pred - list_test)
    ##print (mse_test)
    #print (future_forecast_pred.values)

    #print(list_test)

    #error = mean_squared_error(future_forecast_pred.values,list_test)
    ##print error

    #print('El error medio del modelo_test es: {}'.format(error))
    #rmse = np.sqrt(error)
    #print('El root error medio del modelo_test es: {}'.format(rmse))

    #mse_abs_test = abs(mse_test)

    #diff = abs(mse_abs_test - rmse)

    #df_aler = pd.DataFrame(mse_abs_test,index = df_test.index,columns=['mse_abs_time_test'])
    #df_aler['diff_mse_test'] = diff
    #df_aler['mse'] = error
    #df_aler['rmse'] = rmse
    #df_aler.sort_values(by=['diff_mse_test'],inplace= True, ascending = False)
    #range_mse = (desv_mse*error)
    #df_aler = df_aler[(df_aler['diff_mse_test']> range_mse)]
    
    #df_aler_ult = df_aler[:5]

    #df_aler_ult = df_aler_ult[(df_aler_ult.index==df_aler.index.max())|(df_aler_ult.index==((df_aler.index.max())-1))
                             #|(df_aler_ult.index==((df_aler.index.max())-2))|(df_aler_ult.index==((df_aler.index.max())-3))
                             #|(df_aler_ult.index==((df_aler.index.max())-4))]
    #if len(df_aler_ult) == 0:
        #exists_anom_last_5 = 'FALSE'
    #else:
        #exists_anom_last_5 = 'TRUE'
    
    #return (rmse,df_aler,exists_anom_last_5, df_aler_ult)





def forecast_holt(lista_datos, num_fut):
    
    lista_puntos = np.arange(0, len(lista_datos),1)

    df = pd.DataFrame()
    df['puntos'] = lista_puntos
    df['valores'] = lista_datos

    df.set_index('puntos',inplace=True)

    stepwise_model =  ExponentialSmoothing(df,seasonal_periods=len(df) , seasonal='add')
    fit_stepwise_model = stepwise_model.fit()
    
    fit_forecast_pred = fit_stepwise_model.fittedvalues

    future_forecast_pred = fit_stepwise_model.forecast(num_fut)
    
    df_result = pd.DataFrame({'puntos':future_forecast_pred.index, 'valores':future_forecast_pred.values})    
    df_result.set_index('puntos',inplace=True)
    return (df_result)


def anomaly_LSTM(list_var,desv_mse=0):
    print ('entra ne le modelo')
    print (list_var)
    df_var = pd.DataFrame()
    for i in range(len(list_var)):
        df_var['var_{}'.format(i)] = list_var[i]
        df_var['var_{}'.format(i)] = list_var[i]
    
    print ('entra ne le modelo')
    tam_train = int(len(df_var)*0.7)
    values = df_var.values
    train = values[:tam_train, :]
    print 'train',len(train)

    test = values[tam_train:, :]
    print 'test',len(test)
    
    train_X, train_y = train[:, :-1], train[:, -1]

    test_X, test_y = test[:, :-1], test[:, -1]
    

    train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
    test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))

    model = Sequential()
    model.add(LSTM(30, input_shape=(train_X.shape[1], train_X.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mae', optimizer='adam')
    # fit network
    
    history = model.fit(train_X, train_y, epochs=30, batch_size=72, validation_data=(test_X, test_y), verbose=0, shuffle=False)

    # make a prediction
    yhat = model.predict(test_X)
    mse = (mean_squared_error(test_y, yhat))
    #print('Test MSE: %.3f' % mse)
    rmse = np.sqrt(mse)
    print('El root error medio del modelo_test es: {}'.format(rmse))

    yhat = yhat.ravel()

    df_aler = pd.DataFrame()

    
    df_aler['real_value'] = test_y
    df_aler['expected_value'] = yhat
    

    #mse_test = (yhat - test_y)
    #mse_abs_test = abs(mse_test)


    
    #df_aler = pd.DataFrame(future_forecast.yhat,index = future_forecast.index,columns=['expected_value'])
   
    df_aler['mse'] = mse
    df_aler['puntos'] = df_aler.index
    df_aler['puntos'] = df_aler['puntos'] + tam_train
    df_aler.set_index('puntos',inplace=True)
    #df_aler['real_value'] = future_forecast.test_y
    print('paso')
    
    df_aler['rmse'] = rmse
    mae = mean_absolute_error(yhat, test_y)
    df_aler['mae'] = mean_absolute_error(yhat, test_y)
    print(df_aler.info())

    
    #df_aler['anomaly_score'] = abs(df_aler['expected value'] - df_aler['real_value']) / df_aler['mae']
    df_aler['anomaly_score'] = abs(df_aler['expected_value']-df_aler['real_value'])/df_aler['mae']
    df_aler_ult = df_aler[:5]
    df_aler = df_aler[(df_aler['anomaly_score']> 2)]
    max = df_aler['anomaly_score'].max()
    min = df_aler['anomaly_score'].min()
 
    df_aler['anomaly_score']= ( df_aler['anomaly_score'] - min ) /(max - min)
    
    print ('anomaly')

    df_aler_ult = df_aler[:5]

    df_aler_ult = df_aler_ult[(df_aler_ult.index==df_aler.index.max())|(df_aler_ult.index==((df_aler.index.max())-1))
                             |(df_aler_ult.index==((df_aler.index.max())-2))|(df_aler_ult.index==((df_aler.index.max())-3))
                             |(df_aler_ult.index==((df_aler.index.max())-4))]
    if len(df_aler_ult) == 0:
        exists_anom_last_5 = 'FALSE'
    else:
        exists_anom_last_5 = 'TRUE'
    max = df_aler_ult['anomaly_score'].max()
    min = df_aler_ult['anomaly_score'].min()
 
    df_aler_ult['anomaly_score']= ( df_aler_ult['anomaly_score'] - min ) /(max - min)
  
    #print (df_aler)
    #print (exists_anom_last_5)
    #print ( df_aler_ult)
    #return (df_aler,exists_anom_last_5, df_aler_ult)
    
    
    ##############FORECAST PREDICTION
    values = df_var.values
    num_fut=5
    
    test1_X, test1_y = values[:, :-1], values[:, -1]

    test1_X = test1_X.reshape((test1_X.shape[0], 1, test1_X.shape[1]))
    
    model = Sequential()
    model.add(LSTM(50, input_shape=(test1_X.shape[1], test1_X.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mae', optimizer='adam')
    # fit network
    
    history = model.fit(test1_X, test1_y, epochs=50, batch_size=72, verbose=0, shuffle=False)
    
    len_fore = len(test1_X) - num_fut
    fore = test1_X[len_fore:]
    yhat = model.predict(fore)
    
    lista_result = np.arange(len(test1_X), (len(test1_X)+num_fut),1)
    df_result_forecast = pd.DataFrame({'puntos':lista_result, 'valores':yhat[:,0]})
    df_result_forecast.set_index('puntos',inplace=True)
    df_result_forecast['valores']=df_result_forecast['valores'].astype(str)
    df_result_forecast['step'] = df_result_forecast.index


    engine_output={}
    engine_output['rmse'] = rmse
    engine_output['mse'] = mse
    engine_output['mae'] = mae
    engine_output['present_status']=exists_anom_last_5
    engine_output['present_alerts']=df_aler_ult.to_dict(orient='record')
    engine_output['past']=df_aler.to_dict(orient='record')
    engine_output['engine']='LSTM'
    engine_output['future']= df_result_forecast.to_dict(orient='record')
    
    #print ("el resultado de LSTM es")
    #print (engine_output)
    
    return (engine_output)


def forecast_LSTM(list_var,num_fut):
    df_var = pd.DataFrame()
    for i in range(len(list_var)):
        df_var['var_{}'.format(i)] = list_var[i]
        df_var['var_{}'.format(i)] = list_var[i]

    values = df_var.values

    test_X, test_y = values[:, :-1], values[:, -1]

    test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
    
    model = Sequential()
    model.add(LSTM(50, input_shape=(test_X.shape[1], test_X.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mae', optimizer='adam')
    # fit network
    
    history = model.fit(test_X, test_y, epochs=50, batch_size=72, verbose=0, shuffle=False)
    
    len_fore = len(test_X) - num_fut
    fore = test_X[len_fore:]
    yhat = model.predict(fore)
    
    lista_result = np.arange(len(test_X), (len(test_X)+num_fut),1)
    df_result = pd.DataFrame({'puntos':lista_result, 'valores':yhat[:,0]})
    df_result.set_index('puntos',inplace=True)
    return (df_result)


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def model_univariate(lista_datos,num_fut,desv_mse):
    engines_output={}
    debug = {}
    
    try:
        engines_output['LSTM'] = anomaly_uni_LSTM(lista_datos,desv_mse)
        debug['LSTM'] = engines_output['LSTM']['debug']
    except Exception as e: 
        print(e)
        print ('ERROR: exception executing LSTM univariate')
    
    try:
        engines_output['arima'] = anomaly_AutoArima(lista_datos,desv_mse)
        debug['arima'] = engines_output['arima']['debug']
    except  Exception as e: 
        print(e)
        print ('ERROR: exception executing Autoarima')
    
    try:
        engines_output['Holtwinters'] = anomaly_holt(lista_datos,desv_mse)
        debug['Holtwinters'] = engines_output['Holtwinters']['debug']
    except  Exception as e: 
        print(e)
        print ('ERROR: exception executing Holtwinters')
    
    best_mae=999999999
    winner='Holtwinters'
    print ('el tamanio es ')
    print (len(engines_output))
    for key, value in engines_output.iteritems():
        print (value['mae'])
        print(key)
        if value['mae'] < best_mae:
            best_mae=value['mae']
            winner=key
        print(winner)
            
            
    
        
    print winner
    
    temp= {}
    temp['debug']=debug
    return merge_two_dicts(engines_output[winner] , temp)
    
 
 
 

def model_multivariate(list_var,num_fut,desv_mse):
    
    
    engines_output={}
    
    try:
        engines_output['LSTM'] = anomaly_LSTM(list_var,desv_mse)
        print (engines_output['LSTM'])
    except   Exception as e: 
        print(e)
        print ('ERROR: exception executing LSTM')
    
    best_mae=999999999
    winner='LSTM'
    print ('el tamanio es ')
    print (len(engines_output))
    for key, value in engines_output.iteritems():
        if value['mae'] < best_mae:
            best_rmse=value['mae']
            winner=key
        
    print winner
    return engines_output[winner]
