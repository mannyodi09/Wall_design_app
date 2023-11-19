import streamlit as st
import pandas as pd
import math as math
from handcalcs.decorator import handcalc
import forallpeople as si
 
si.environment("structural")

st.write("##### DESIGN AND DETAILING OF REINFORCED CONCRETE WALLS TO AS 3600:2018")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    df = df.set_index(['Story','Pier'])
    df = df.drop('Unnamed: 0', axis=1)
    pd.set_option('display.max_columns',None)
    #pd.set_option('display.max_rows',None)
    st.dataframe(df)

Ductility_factor = st.selectbox("Select Ductility factor (μ):", options=('1','2','3'))
Sturctural_performance_factor = st.selectbox("Sturctural performance factor (Sp):", options=('0.67','0.77','1'))
Soil_classification = st.selectbox("Site soil classification:", options=('Ae - Strong rock','Be - Rock','Ce - Shallow soil', 'De - Deep or soft soil', 'Ee - Very soft soil'))
unique_stories = df.index.get_level_values('Story').unique()
selected_story = st.selectbox("Select a Story:", unique_stories)
unique_piers = df.index.get_level_values('Pier').unique()
selected_pier = st.selectbox("Select a Pier:", unique_piers)

col1, col2 = st.columns([1,2])

with col2:
    try:
        Pier_forces = df.loc[(selected_story, selected_pier)]
        st.write("Selected Pier forces:")
        st.write(Pier_forces)
    except KeyError:
        st.write("Selected story and pier combination is not available.")

#DESIGN OF WALLS AS A COLUMN

with col1:
    st.write("<u>DESIGN OF WALLS AS A COLUMN</u>",unsafe_allow_html=True)
    st.caption(""" ##### Design Assumptions: 
               
The horizontal cross section of the wall is subject to tension on part of the section, the wall shall be designed for in-plane bending in accordance with one of the following options as appropriate-

(a): if H/L ratio <= 2 design as strut and tie according to section 12. Clause 11.7 still applies; or

(b): if H/L ratio >2 design as a column in accordance with section 10 where verticalreinforcement is provided in each face, except that clause 11.74 may override the requirements of clause 10.7.4. The provisions of clause 10.7.1(b), clause 11.4 and clause 11.7 still apply.""")

    if Soil_classification == "De - Deep or soft soil":
        st.markdown("Simplified design method for compression forces does not apply (cl.11.5.2(c)), design wall as column as per AS3600:2018 Section 10")
    elif Soil_classification == "Ee - Very soft soil":
        st.markdown("Simplified design method for compression forces does not apply (cl.11.5.2(c)), design wall as column as per AS3600:2018 Section 10")
    else:
        st.markdown("Simplified design method for compression forces applies (cl.11.5)")
with col1:
    st.write("<u>Wall section input</u>",unsafe_allow_html=True)
    tw = Pier_forces['b']
    st.write("Width (mm):", tw)
    b = Pier_forces['d']
    st.write("Length (mm):", b)
    reo_bar_size = st.selectbox("Reinforcement Bar Size (mm):",options=('10','12','16','20','24','28','32','36','40'))
    bar_area = (3.14*(float(reo_bar_size))**2)/4
    st.write("Bar area (mm2):", bar_area)
    st.number_input (label="Number of bars on the right:",min_value=2,max_value=100,step=1)
    st.number_input (label="Number of bars on the left:",min_value=2,max_value=100,step=1)
    st.number_input (label="Right cover:",min_value=5,max_value=100,step=5)
    st.number_input (label="Left cover:",min_value=5,max_value=100,step=5)
    st.number_input (label="Top cover:",min_value=5,max_value=100,step=5)
    st.number_input (label="Bottom cover:",min_value=5,max_value=100,step=5)
    st.write("<u>Design Data</u>",unsafe_allow_html=True)
    concrete_strength = st.selectbox("Concrete strength f'c (MPa)",options=('20','25','32','40','50','65','80','100'))
    fsy = 500
    st.write("Yield strength of reinforcing steel (MPa):", fsy)
    
    Lw = Pier_forces['d']

tw = Pier_forces['b'] * si.mm
Hwe = Pier_forces['H'] * si.mm
@handcalc()
def wall_segment(tw: float) -> float:
    """ 
    Calculates division of wall into segements for compression check, (uses tw:Lw ration of 1:4)
    """
    Sg = 4*tw
    return Sg
with col2:
    Sg_latex, Sg_value = wall_segment(tw)
    st.markdown("Length of wall segment:")
    st.latex(Sg_latex)

@handcalc()
def eccentricity(tw: float) -> float:
    """ 
    Calculates the eccentricity of the vertical load in mm
    """
    e = 0.05*tw
    return e
with col2:
    e_latex, e_value = eccentricity(tw)
    st.markdown("Eccentricity of vertical load(cl11.5.4):")
    st.latex(e_latex)

@handcalc()
def additional_eccentricity(tw: float, Hwe: float) -> float:
    """ 
    Calculates the additional eccentricity of the vertical load in mm
    """
    ea = ((Hwe)**2)/(2500*tw)
    return ea
with col2:
    ea_latex, ea_value = additional_eccentricity(tw,Hwe)
    st.markdown("Additonal eccentricity of vertical load(cl11.5.3):")
    st.latex(ea_latex)

fc = float(concrete_strength) * si.MPa
e_latex, e_value = eccentricity(tw)
e = float(e_value) * si.mm
ea_latex, ea_value = additional_eccentricity(tw,Hwe)
ea = float(ea_value) * si.mm
tw = Pier_forces['b'] * si.mm
Sg_latex, Sg_value = wall_segment(tw)
Sg = float(Sg_value) * si.mm
@handcalc()
def ultimate_strength(tw: float, ea: float, e: float, fc: float) -> float:
    """ 
    Calculates the ultimate compression strength of wall segment
    """
    Nu = ((0.65*((tw-1.2*e-2*ea)*0.6*fc))*Sg).prefix('k')
    return Nu
with col2:
    Nu_latex, Nu_value = ultimate_strength(tw,ea,e,fc)
    st.markdown("Compression capacity of wall segment (cl.11.5.3):")
    st.latex(Nu_latex)

s = Pier_forces['Net compression stress'] * si.MPa
Sg_latex, Sg_value = wall_segment(tw)
Sg = float(Sg_value) * si.mm
@handcalc()
def axial_load(tw: float, s: float) -> float:
    """ 
    Calculates the compression force on the wall from net compression stress on wall segment
    """
    P = (tw*s*Sg).prefix('k')
    return P
with col2:
    P_latex, P_value = axial_load(tw,s)
    st.markdown("Compression force on wall segment:")
    st.latex(P_latex)
with col1:
    P_latex, P_value = axial_load(tw,s)
    P = round(float(P_value),1)
    st.write("Compression force on wall segment, P (kN):", P)
    Nu_latex, Nu_value = ultimate_strength(tw,ea,e,fc)
    Nu = round(float(Nu_value),1)
    st.write("Compression capacity of wall segment, Nu (kN)):", Nu)
    if P > Nu:
        st.write('<p style="color: red;">Compression capacity of wall exceeded, NG!!</p>', unsafe_allow_html=True)
    else:
        st.write('<p style="color: green;">Wall segment compression capacity, OKAY!!</p>', unsafe_allow_html=True)

#INPLANE SHEAR CHECK
#1. Shear strength excluding wall reinforcement

with col1:
    st.write("<u>2. IN-PLANE SHEAR CAPACITY CHECK (φVu)</u>",unsafe_allow_html=True)
    V = abs(Pier_forces['V2(Max V2)'])
    st.write("Shear force in wall (kN):", V)
    st.markdown("(a)Shear strength excluding wall reinforcement(cl11.6.3)")

Lw = Pier_forces['d'] * si.mm
Hw = Pier_forces['H'] * si.mm
tw = Pier_forces['b'] * si.mm
fc = float(concrete_strength) * si.MPa
@handcalc()
def Shear_strength_ex_reo1(tw: float, Lw: float, Hw: float, fc: float) -> float:
    """
    Returns the shear strength of the wall excluding wall reinforcement where Hw/Lw <= 1
    """
    Vuc = (((0.66*math.sqrt(fc)*si.MPa)-0.21*(Hw/Lw)*(math.sqrt(fc)*si.MPa))*0.8*Lw*tw).prefix('k')
    return Vuc
with col1:
    if Hw/Lw < 1 or Hw/Lw == 1:
        Vuc_latex, Vuc_value = Shear_strength_ex_reo1(tw,Lw,Hw,fc)
        Vuc = round(float(Vuc_value),2)
        st.write("In-plane capacity excluding wall reinforcement, Vuc (kN)):", Vuc)
with col2:
    if Hw/Lw < 1 or Hw/Lw == 1:
        Vuc_latex, Vuc_value = Shear_strength_ex_reo1(tw,Lw,Hw,fc)
        st.markdown("In-plane capacity excluding wall reinforcement:")
        st.latex(Vuc_latex)

@handcalc()
def Shear_strength_ex_reo2(tw: float, Lw: float, Hw: float, fc: float) -> float:
    """
    Returns the shear strength of the wall excluding wall reinforcement where Hw/Lw > 1
    """
    Vuc = (((0.05*(math.sqrt(fc))*si.MPa)+((0.1*(math.sqrt(fc))*si.MPa)/((Hw/Lw)-1)))*0.8*Lw*tw).prefix('k')
    return Vuc
with col1:
    if Hw/Lw > 1:
        Vuc_latex, Vuc_value = Shear_strength_ex_reo2(tw,Lw,Hw,fc)
        Vuc = round(float(Vuc_value),2)
        st.write("In-plane capacity excluding wall reinforcement, Vuc (kN)):", Vuc)
with col2:
    if Hw/Lw > 1:
        Vuc_latex, Vuc_value = Shear_strength_ex_reo2(tw,Lw,Hw,fc)
        st.markdown("In-plane capacity excluding wall reinforcement:")
        st.latex(Vuc_latex)

#@handcalc()
#def minimum_shear_strength(tw: float, Lw: float, fc: float) -> float:
    #"""
    #Returns the minimum shear strength of wall excluding wall reinforcement
    #"""
    #Vucmin = (0.17*math.sqrt(fc)*(0.8*Lw*tw)).prefix('k')
    #return Vucmin
#Vucmin_latex, Vucmin_value = minimum_shear_strength(tw, Lw, fc)
#Vucmin = round(float(Vucmin_value), 2)
#with col1:
    #if Vuc < Vucmin:
        #Vuc_latex, Vuc_value = minimum_shear_strength(tw,Lw,fc)
        #Vuc = round(float(Vuc_value),2)
        #st.write("Minimum In-plane capacity excluding wall reinforcement, Vuc (kN)):", Vuc)
#with col2:
    #if Vuc < Vucmin:
        #Vuc_latex, Vuc_value = minimum_shear_strength(tw,Lw,fc).prefix('k')
        #st.markdown("Minimum In-plane capacity excluding wall reinforcement, Vuc (kN)):")
        #st.latex(Vuc_latex)


#2. Contribution to shear strength by wall reinforcement
with col1:
    st.markdown("(b) Contribution to shear strength by wall reinforcement(cl11.6.4)")
    pw = 0.0025
    st.write("Minimum reo ratio in horizontal direction(cl11.7.1):", pw)
    
    Horz_bar_dia = st.selectbox("Horizontal bar diameter (mm)",options=('10','12','16','20','24','28','32'))
    Horz_bar_spc = st.selectbox("Horizontal bar spcaing (mm)",options=('100','150','200','250','300','350','400'))
@handcalc()
def hor_reo_ratio(Horz_bar_dia: float, Horz_bar_spc: float,tw: float):
    """
    Returns the reo ratio in the horizontal direction
    """
    pw2 = ((math.pi*float(Horz_bar_dia)**2/4)*((1000/float(Horz_bar_spc))+1)/(1000*float(tw)))
    return pw2
with col1:
    pw2_latex, pw2_value = hor_reo_ratio(Horz_bar_dia,Horz_bar_spc,tw)
    pw2 = round(float(pw2_value),4)
    st.write("reo ratio(pw)", pw2)
    if pw2 < 0.0025:
        st.write('<p style="color: red;">Horizontal reo ratio is less than 0.0025, NG!!</p>', unsafe_allow_html=True)
    #else:
        #st.write('<p style="color: green;">Wall segment compression capacity, OKAY!!</p>', unsafe_allow_html=True)

@handcalc()
def Shear_strength_with_reo(pw: float, Lw: float, fsy: float) -> float:
    """
    Returns the contribution to shear strength by wall reinforcement
    """
    Vus = (max(0.0025,((pw2 * fsy*si.MPa)*0.8*Lw*tw))).prefix('k')
    return Vus
with col1:
    Vus_latex, Vus_value = Shear_strength_with_reo(pw,Lw,fsy)
    Vus = round(float(Vus_value),2)
    st.write("In-plane capacity contribution from wall reinforcement, Vus (kN)):", Vus)
with col2:
    Vus_latex, Vus_value = Shear_strength_with_reo(pw,Lw,fsy)
    st.markdown("In-plane capacity contribution from wall reinforcement:")
    st.latex(Vus_latex)

phi = 0.65
@handcalc()
def strength_in_shear(Vuc: float, Vus: float) -> float:
    """
    Returns the design strength of the wall subjected to in-plane shear forces
    """
    Vu = (phi*(Vuc*si.kN + Vus*si.kN)).prefix('k')
    return Vu
with col1:
    Vu_latex, Vu_value = strength_in_shear(Vuc,Vus)
    Vu = round(float(Vu_value),2)
    st.write("Wall strength in shear, Vu (kN):", Vu)
    if Vu < V:
        st.write('<p style="color: red;">Shear capacity exceeded, NG!!</p>', unsafe_allow_html=True)
    else:
        st.write('<p style="color: green;">Shear demand, OKAY!!</p>', unsafe_allow_html=True)
with col2:
    Vu_latex, Vu_value = strength_in_shear(Vuc,Vus)
    st.markdown("Wall strength in shear:")
    st.latex(Vu_latex)

#3. Detailing
with col1:
    st.write("<u>3. REINFORCEMENT DETAILING</u>",unsafe_allow_html=True)
    st.markdown("-Vertical Reinforcement: Minimum vertical reo is required, assuming vertical reinforcement is not used as compression reinforcement!!")
with col1:
    st.write("Minimum reo ratio in vertical direction(cl11.7.1):", pw)
    fsy = 500
    Vert_bar_dia = st.selectbox("Vertical bar diameter (mm)",options=('10','12','16','20','24','28','32'))
    Vert_bar_spc = st.selectbox("Vertical bar spcaing (mm)",options=('100','150','200','250','300','350','400'))
@handcalc()
def vert_reo_ratio(Vert_bar_dia: float, Vert_bar_spc: float,tw: float):
    """
    Returns the reo ratio in the horizontal direction
    """
    pw3 = ((math.pi*float(Vert_bar_dia)**2/4)*((1000/float(Vert_bar_spc))+1)/(1000*float(tw)))
    return pw3
with col1:
    pw3_latex, pw3_value = vert_reo_ratio(Vert_bar_dia,Vert_bar_spc,tw)
    pw3 = round(float(pw3_value),4)
    st.write("Vertical bars reo ratio(pw)", pw3)
    if pw3 < 0.0025:
        st.write('<p style="color: red;">Vertical reo ratio is less than 0.0025, NG!!</p>', unsafe_allow_html=True)
with col1:
    st.markdown("-Restraint of Vertical Reinforcement (cl11.7.4):")
fc = float(concrete_strength)
with col1:
    if fc<51:
        st.markdown("Restraint not required for vertical bars (cl11.7.4(c))")
    elif fc>51:
        st.markdown("Restraint required for vertical bars (cl11.7.4(d(ii)))")