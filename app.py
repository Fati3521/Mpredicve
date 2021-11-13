import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import shap
from fonction import *
import plotly.express as px
from umap import UMAP
plt.style.use('fivethirtyeight')
#sns.set_style('darkgrid')scaler1


def main() :

    #@st.cache
    def load_data_app():
        data=pd.read_csv(r"data_app_brute.csv", sep=";")
        return data
    
    #@st.cache
    def load_data_test():
        data=pd.read_csv(r"data_test_brute.csv", sep=";")
        Num_ouverture=set(data["numero ouverture"])
        return data, Num_ouverture
    
    @st.cache
    def data_brute():
        data=pd.read_csv(r"data8.csv", sep=";")
        scaler1=load_scaler()
        data[['acc_x','acc_y']] = scaler1.transform(data[['acc_x','acc_y']])
        data.loc[data["defaut"]==0,"defaut"]="normal"
        data.loc[data["defaut"]==1,"defaut"]="anormal"
        return data

    #@st.cache
    def load_model():
        model=joblib.load(r"strealit_model.sav")
        return model
    @st.cache
    def load_scaler():
        scaler1 = joblib.load(r"strealit_scaler.sav")
        return scaler1

    #@st.cache
    def pretraitement(sample, id):
        sample=sample[sample["numero ouverture"] == id]
        scaler1=load_scaler()
        sample[['acc_x','acc_y']] = scaler1.transform(sample[['acc_x','acc_y']])
        sample1=extrac_features(sample[['acc_x','acc_y']].reset_index(drop = True))
        return sample1
    
    #@st.cache
    def load_prediction(sample,id, clf):
        data=pretraitement(sample, id)
        score = clf.predict(data)[0]
        comp="normal" if score==0 else "anormal"
        return score

    #@st.cache
    def load_umap(train, sample, id):
        sample=sample[sample["numero ouverture"] == id]
        y_train=train['defaut'].tolist()
        y_test=sample['defaut'].tolist()
        scaler1=load_scaler()
        sample[['acc_x','acc_y']] = scaler1.transform(sample[['acc_x','acc_y']])
        sample1=extrac_features(sample[['acc_x','acc_y']].reset_index(drop = True))
        train[['acc_x','acc_y']] = scaler1.transform(train[['acc_x','acc_y']])
        train1=extrac_features(train[['acc_x','acc_y']].reset_index(drop = True))
        umap_2d = UMAP(n_components=2, init='random', random_state=0)
        proj_2d = pd.DataFrame(umap_2d.fit_transform(train1))
        proj_1d = pd.DataFrame(umap_2d.transform(sample1))
        proj_2d['lable']=y_train
        proj_1d['lable']=y_test
        st.write(set(proj_2d["lable"]))
        return proj_2d, proj_1d
    #@st.cache
    def box_plotly(brute_app, data_test, chk_id):
        brute_test=data_test[data_test["numero ouverture"] == chk_id]
        scaler1=load_scaler()
        brute_test[['acc_x','acc_y']] = scaler1.transform(brute_test[['acc_x','acc_y']])
        brute_test["defaut"]="nouvelle prediction"
        data_fusion=pd.concat([brute_app, brute_test.iloc[:,:-1]])
        fig = px.box(data_fusion, x="defaut", y=feat_id, points="all")
        st.plotly_chart(fig)

    data_app = load_data_app()
    data_test, numero_ouverture = load_data_test()
    targets = data_app.defaut.value_counts()
    brute_app=data_brute()
    feature=['acc_x', 'acc_y', 'acc_z', 'gyr_x', 'gyr_y', 'gyr_z','temp']
    #print(type(numero_ouverture))

    #######################################
    # SIDEBAR
    #######################################

    #Title display
    html_temp = """
    <div style="background-color: tomato; padding:10px; border-radius:10px">
    <h1 style="color: white; text-align:center">MAINTENANCE PREDICTIVE</h1>
    </div>
    <p style="font-size: 20px; font-weight: bold; text-align:center">INTERPRETATION MODELE PREDICTIF</p>
    """
    
    st.markdown(html_temp, unsafe_allow_html=True)
    
    #Loading data……
    
    clf = load_model()
    #Customer ID selection
    st.sidebar.header("**JEU DE DONNEES**")
    #Loading select-box
    #st.sidebar.markdown("<u>Average loan amount (USD) :</u>", unsafe_allow_html=True)
    #fig = px.pie(values=targets.values, names=targets.index) 
    #st.sidebar.plotly_chart(fig)
    fig, ax = plt.subplots(figsize=(5,5))
    plt.pie(targets, explode=[0, 0.1], labels=['No default', 'Default'], autopct='%1.1f%%', startangle=90)
    st.sidebar.pyplot(fig)
    chk_id = st.sidebar.selectbox("Numero Ouverture", numero_ouverture)
   
        
    #######################################
    # HOME PAGE - MAIN CONTENT
    #######################################
    #Display Customer ID from Sidebar
  
    #Customer solvability display
    st.header("**ANALYSE PREDICTION**")
    if st.button('Prediction'):
    #if st.checkbox("Show customer information ?"):
        prediction = load_prediction(data_test, chk_id, clf)
        st.write("**Comportement:**",prediction)
        data_app1, data_test1=load_umap(data_app, data_test,chk_id)
        data_app1["taille"]=1
        data_test1["lable"]=2
        data_test1["taille"]=3
        XX=pd.concat([data_test1, data_app1])
        st.write(set(data_app["defaut"]))
        st.write(set(data_app1["lable"]))
        fig_2d = px.scatter(XX, x=0, y=1, color=XX["lable"], labels={'color': 'lable'}, size="taille")
        #fig_2d.update_layout(showlegend=False)
        st.plotly_chart(fig_2d)
    
    
    #Feature importance / description
    if st.checkbox("Interpretation niveau global ?"):
        shap.initjs()
        X=pretraitement(data_test, chk_id)
        number = st.slider("Pick a number of features…", 0, 20, 5)
        fig, ax = plt.subplots(figsize=(10, 10))
        explainer = shap.TreeExplainer(load_model())
        shap_values = explainer.shap_values(X)
        # Plot summary_plot
        shap.summary_plot(shap_values, X)
        st.pyplot(fig)
        
    else:
        st.markdown("<i>…</i>", unsafe_allow_html=True)
    X=pretraitement(data_test, chk_id)   
    if st.checkbox("Interpretation niveau local Niveau 1"):
        fig, ax = plt.subplots()
 
        explainer = shap.TreeExplainer(load_model())
        shap_values = explainer.shap_values(X)
        # Plot summary_plot
        shap.initjs()
        force_plot=shap.force_plot(explainer.expected_value[1], shap_values[1], X, matplotlib=True,
                    show=False)
        st.pyplot(force_plot) 
        
    else:
        st.markdown("<i>…</i>", unsafe_allow_html=True)
 
    if st.checkbox("Interpretation niveau local Niveau 2"):
        fig, ax = plt.subplots()
 
        explainer = shap.TreeExplainer(load_model())
        shap_values = explainer.shap_values(X)
        fig, ax = plt.subplots(figsize=(10, 10))
        # Plot summary_plot
        shap.initjs()
        shap.decision_plot(explainer.expected_value[1], shap_values[1], X)
        st.pyplot(fig)  
        
    else:
        st.markdown("<i>…</i>", unsafe_allow_html=True)
    
            
    if st.checkbox("Distribution des données"):   
        feat_id = st.selectbox("feature", feature)
        box_plotly(brute_app, data_test, chk_id)
    else:
        st.markdown("<i>…</i>", unsafe_allow_html=True)
       
if __name__ == '__main__':
    main()
