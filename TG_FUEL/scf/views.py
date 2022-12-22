from importlib.resources import path
from pickle import TRUE
from scf.models import mytable
import pandas as pd
import numpy as np
import io
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
import pickle
from bs4 import BeautifulSoup
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from .models import *

from .serializers import *

def getPredictions(Flight, acType, Month, ESAD, depCeiling, depVisibility, depLight, depTS, depSH, depRA, arrCeiling, arrVisibility, arrLight, arrTS, arrSH, arrRA, medAirborne, meddiffAirborne, sdAirborne, sddiffAirborne):
    model = pickle.load(open("C:/Users/acer/tg/web/TG_FUEL/scf/ML_Model.sav", "rb"))
    scaled = pickle.load(open("C:/Users/acer/tg/web/TG_FUEL/scf/scalerY.sav", "rb"))
    scaled2 = pickle.load(open("C:/Users/acer/tg/web/TG_FUEL/scf/scalerX.sav", "rb"))
    encoded = pickle.load(open("C:/Users/acer/tg/web/TG_FUEL/scf/encodeFlight.sav", "rb"))
    encoded2 = pickle.load(open("C:/Users/acer/tg/web/TG_FUEL/scf/encodeAcType.sav", "rb"))

    Flight_en = encoded.transform([Flight])
    ac_en = encoded2.transform([acType])
    input_scaled = scaled2.transform([[Flight_en, ac_en, Month, ESAD, depCeiling, depVisibility, depLight, depTS, depSH, depRA, arrCeiling, arrVisibility, arrLight, arrTS, arrSH, arrRA, medAirborne, meddiffAirborne, sdAirborne, sddiffAirborne]])[0]
    lstscaled = [[1, input_scaled[0], input_scaled[1], input_scaled[2], input_scaled[3], input_scaled[4], input_scaled[5], input_scaled[6], input_scaled[7], input_scaled[8], input_scaled[9], input_scaled[10], input_scaled[11], input_scaled[12], input_scaled[13], input_scaled[14], input_scaled[15], input_scaled[16], input_scaled[17], input_scaled[18], input_scaled[19]]]
    predicted = model.predict(lstscaled)
    
    if np.isnan(predicted[0]):
        err_massage = "Your data contains null value."
        err = {
            "status": 404,
            "message": err_massage
        }
        return Response(err)

    repredict = predicted[0].reshape(-1, 1)
    prediction = scaled.inverse_transform(repredict)

    return prediction[0]

class test_APIView(APIView):
    def get(self, request, *args, **kwargs):
        err = { 
            "status": 404,
            "message": "Page not found."
        }
        return Response(err)

    def post(self, request, *args, **kwargs):
        # Check Type of File Uploaded
        file_memory = request.data.get('file')
        if file_memory == "":
            err = { 
                "status": 404,
                "message": "You don't attached any file, you must entered the .xml file."
             }
            return Response(err)
        else:
            file_name = file_memory.name
            file_format = file_name.split(".")[-1]
            if file_format == "xml":
                pass
            else:
                err_massage = "File type not match because you attached the .{} file.".format(file_format)
                err = { 
                    "status": 404,
                    "message": err_massage
                }
                return Response(err)

        serializer = file_serializer(data=request.data)
        serializer.is_valid()

        json = JSONRenderer().render(serializer.validated_data['file'])
        soup = BeautifulSoup(json[3:], 'lxml')
        
        raw_flight = str(soup.find_all('flightnumber'))
        raw_date = str(soup.find_all('flightdate'))
        raw_taxi = str(soup.find_all('taxifuel'))
        raw_trip = str(soup.find_all('tripfuel'))
        raw_alternate = str(soup.find_all('alternatefuel'))
        raw_finalreserve = str(soup.find_all('finalreservefuel'))
        raw_flighttime = str(soup.find_all('flighttime'))
        flight = (raw_flight).split('<')[1].split('>')[1]
        date = (raw_date).split('<')[1].split('>')[1]
        date = date[:-1]
        taxi = (raw_taxi).split('<')[1].split('>')[1]
        trip = (raw_trip).split('<')[-2].split('>')[-1]
        alternate = (raw_alternate).split('<')[1].split('>')[1]
        finalreserve = (raw_finalreserve).split('<')[1].split('>')[1]
        flighttime = (raw_flighttime).split('<')[1].split('>')[1]
        time = flighttime.split("PT")[1]
        time = time.split("M")[0]
        flighttime_mn = (int(time.split("H")[0])*60)+(int(time.split("H")[1]))
        
        flightlst = []
        datelst = []
        taxiOutFuellst = []
        tripFuellst = []
        alternatelst = []
        finalReservelst = []
        minimum95 = []
        scf95 = []
        timelst = []
        
        flightlst.append(flight)
        datelst.append(date)
        taxiOutFuellst.append(float(taxi))
        tripFuellst.append(float(trip))
        alternatelst.append(float(alternate))
        finalReservelst.append(float(finalreserve))
        timelst.append(int(flighttime_mn))

        try:
            query_scf = mytable.objects.filter(flight = flight).values("scf95")
            scf = query_scf[0]['scf95']
            scf_cal = (float(scf))*flighttime_mn
            scf_cal = round(scf_cal, 2)
            scf95.append(scf_cal)
            ramp = float(taxi) + float(alternate) + float(finalreserve) + float(trip) + float(scf_cal)
            result = round(ramp, 2)
            minimum95.append(result)
        except:
            minimum95.append("N/A")
            scf95.append("N/A")

        list_of_tuples = list(zip(datelst, flightlst, timelst, taxiOutFuellst, alternatelst, finalReservelst, tripFuellst, minimum95, scf95))

        df = pd.DataFrame(list_of_tuples, columns = ['Date', 'Flight', 'FlightTime_Minute', 'TaxiOutFuel', 'AlternateFuel', 'FinalReserveFuel', 'TripFuel', 'Minimum95', 'SCF95'])
        
        df['TaxiOutFuel'] = df['TaxiOutFuel'].apply(lambda x : "{:,}".format(x))
        df['AlternateFuel'] = df['AlternateFuel'].apply(lambda x : "{:,}".format(x))
        df['FinalReserveFuel'] = df['FinalReserveFuel'].apply(lambda x : "{:,}".format(x))
        df['TripFuel'] = df['TripFuel'].apply(lambda x : "{:,}".format(x))
        df['FlightTime_Minute'] = df['FlightTime_Minute'].apply(lambda x : "{:,}".format(x))

        try:
            df['Minimum95'] = df['Minimum95'].apply(lambda x : "{:,}".format(x))
            df['SCF95'] = df['SCF95'].apply(lambda x : "{:,}".format(x))
        except:
            pass

        dt_now = str(datetime.datetime.now())
        dt_now_str = "".join(dt_now.split(":"))
        file_export_name = "output_{}.xlsx".format(dt_now_str)
        path_name = "output/" + file_export_name
        df.to_excel(path_name)
        df_with_path = df
        df_with_path["pathName"] = path_name
        df_with_path["status"] = 200
        df_with_path["message"] = "Request success"
        dict_df = df_with_path.to_dict('records')

        return Response(dict_df)

class test_ML(APIView):
    def get(self, request, *args, **kwargs):
        serializer = file_ml_model(data=request.data)
        serializer.is_valid()
        
        ml_file = serializer.validated_data['file']
        decoded_flight = ml_file.read().decode()
        io_flight = io.StringIO(decoded_flight)
        ml_file = pd.read_csv(io_flight)

        err = { 
            "status": 404,
            "message": "Page not found."
        }

        return Response(err)

    # our result page view
    def post(self, request, *args, **kwargs):
        print(request.data)
        file_memory = request.data.get('file')
        if file_memory == "":
            err = { 
                "status": 404,
                "message": "You don't attached any file, you must entered the .csv file."
             }
            return Response(err)
        else:
            file_name = file_memory.name   
            file_format = file_name.split(".")[-1]
            if file_format == "csv":
                pass
            else:
                err_massage = "File type not match because you attached the .{} file.".format(file_format)
                err = { 
                    "status": 404,
                    "message": err_massage
                }
                return Response(err)

        serializer = file_ml_model(data=request.data)
        serializer.is_valid()
        
        ml_file = serializer.validated_data['file']
        decoded_flight = ml_file.read().decode()
        io_flight = io.StringIO(decoded_flight)
        ml_file = pd.read_csv(io_flight)

        time_data = pd.read_csv('C:/Users/acer/tg/web/TG_FUEL/scf/Time data Unmerge.csv')
        
        try:
            Flight = ml_file['Flight'].values[0]
            acType = ml_file['acType'].values[0]
            Month = ml_file['Month'].values[0]
            ESAD = ml_file['ESAD'].values[0]
            depCeiling = ml_file['depCeiling'].values[0]
            depVisibility = ml_file['depVisibility'].values[0]
            depLight = ml_file['depLight'].values[0]
            depTS = ml_file['depTS'].values[0]
            depSH = ml_file['depSH'].values[0]
            depRA = ml_file['depRA'].values[0]
            arrCeiling = ml_file['arrCeiling'].values[0]
            arrVisibility = ml_file['arrVisibility'].values[0]
            arrLight = ml_file['arrLight'].values[0]
            arrTS = ml_file['arrTS'].values[0]
            arrSH = ml_file['arrSH'].values[0]
            arrRA = ml_file['arrRA'].values[0]
        except:
            err_massage = "Your data not match with the template"
            err = { 
                "status": 404,
                "message": err_massage
            }
            return Response(err)

        try:
            medAirborne = time_data[(time_data['Flight'] == Flight) & (time_data['Aircraft Type'] == acType) & (time_data['Month'] == Month)]['medAirborne'].values[0]
            meddiffAirborne = time_data[(time_data['Flight'] == Flight) & (time_data['Aircraft Type'] == acType) & (time_data['Month'] == Month)]['meddiffAirborne'].values[0]
            sdAirborne = time_data[(time_data['Flight'] == Flight) & (time_data['Aircraft Type'] == acType) & (time_data['Month'] == Month)]['sdAirborne'].values[0]
            sddiffAirborne = time_data[(time_data['Flight'] == Flight) & (time_data['Aircraft Type'] == acType) & (time_data['Month'] == Month)]['sddiffAirborne'].values[0]
            planAirborne = ml_file['planAirborne'].values[0]
        except:
            err_massage = "Not have data in Flight '{}', Aircraft Type '{}' and Month '{}'".format(Flight, acType, Month)
            err = {
                "status": 404,
                "message": err_massage
            }
            return Response(err)

        try:
            result_mn = getPredictions(Flight, acType, Month, ESAD, depCeiling, depVisibility, depLight, depTS, depSH, depRA, arrCeiling, arrVisibility, arrLight, arrTS, arrSH, arrRA, medAirborne, meddiffAirborne, sdAirborne, sddiffAirborne)[0]
        except:
            err_massage = "If compare with template, your value not correct or contains null value."
            err = {
                "status": 404,
                "message": err_massage
            }
            return Response(err)

        result = result_mn*planAirborne
        
        Flightlst = []
        Flightlst.append(Flight)
        acTypelst = []
        acTypelst.append(acType)
        Monthlst = []
        Monthlst.append(Month)
        ESADlst = []
        ESADlst.append(ESAD)
        depCeilinglst = []
        depCeilinglst.append(depCeiling)
        depVisibilitylst = []
        depVisibilitylst.append(depVisibility)
        depLightlst = []
        depLightlst.append(depLight)
        depTSlst = []
        depTSlst.append(depTS)
        depSHlst = []
        depSHlst.append(depSH)
        depRAlst = []
        depRAlst.append(depRA)
        arrCeilinglst = []
        arrCeilinglst.append(arrCeiling)
        arrVisibilitylst = []
        arrVisibilitylst.append(arrVisibility)
        arrLightlst = []
        arrLightlst.append(arrLight)
        arrTSlst = []
        arrTSlst.append(arrTS)
        arrSHlst = []
        arrSHlst.append(arrSH)
        arrRAlst = []
        arrRAlst.append(arrRA)
        planAirbornelst = []
        planAirbornelst.append(planAirborne)
        medAirbornelst = []
        medAirbornelst.append(medAirborne)
        meddiffAirbornelst = []
        meddiffAirbornelst.append(meddiffAirborne)
        sdAirbornelst = []
        sdAirbornelst.append(sdAirborne)
        sddiffAirbornelst = []
        sddiffAirbornelst.append(sddiffAirborne)
        resultlst = []
        resultlst.append(result)

        list_of_tuples = list(zip(Flightlst, acTypelst, Monthlst, ESADlst, depCeilinglst, depVisibilitylst, depLightlst, depTSlst, depSHlst, depRAlst, arrCeilinglst, arrVisibilitylst, arrLightlst, arrTSlst, arrSHlst, arrRAlst, planAirbornelst, medAirbornelst, meddiffAirbornelst, sdAirbornelst, sddiffAirbornelst, resultlst))

        df = pd.DataFrame(list_of_tuples, columns = ["Flight", "acType", "Month", "ESAD", "depCeilinglst", "depVisibilitylst", "depLightlst", "depTSlst", "depSHlst", "depRAlst", "arrCeilinglst", "arrVisibilitylst", "arrLightlst", "arrTSlst", "arrSHlst", "arrRAlst", "planAirborne", "medAirborne", "meddiffAirborne", "sdAirborne", "sddiffAirborne", "result"])
        
        dt_now = str(datetime.datetime.now())
        dt_now_str = "".join(dt_now.split(":"))
        file_export_name = "ML_output_{}.xlsx".format(dt_now_str)
        path_name = "output/" + file_export_name
        df.to_excel(path_name)
        df_with_path = df
        df_with_path["pathName"] = path_name
        df_with_path["status"] = 200
        df_with_path["message"] = "Request success"
        dict_df = df_with_path.to_dict('records')

        return Response(dict_df)

def home(request):
    context={'file':FilesAdmin.objects.all()}
    return render(request, 'blog/home.html', context)

def download(request,path):
    file_path=os.path.join(settings.MEDIA_ROOT,path)
    if os.path.exists(file_path):
        with open(file_path,'rb')as fh:
            response=HttpResponse(fh.read(),content_type="application/adminupload")
            response['Content-Disposition']='inline;filename='+os.path.basename(file_path)
            return response

    raise Http404