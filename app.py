import streamlit as st
import pandas as pd
import numpy as np
import joblib
from math import radians, sin, cos, sqrt, atan2


# ---------------- Page ----------------

st.set_page_config(
    page_title="Restaurant Recommendation System",
    page_icon="🍽️",
    layout="wide"
)


with open("app.css") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )


# ---------------- Load Files ----------------

model = joblib.load("best_model.pkl")

label_encoders = joblib.load("label_encoders.pkl")


excel_file = "Final Project Roaad.xlsx"


restaurants = pd.read_excel(
    excel_file,
    sheet_name="restaurants"
)

restaurant_cuisines = pd.read_excel(
    excel_file,
    sheet_name="restaurant_cuisines"
)

consumers = pd.read_excel(
    excel_file,
    sheet_name="consumers"
)

consumer_preferences = pd.read_excel(
    excel_file,
    sheet_name="consumer_preferences"
)



# ---------------- Header ----------------

st.markdown(
    """
    <div class='header'>
    <h1>🍽️ Restaurant Recommendation System</h1>
    <p>
    Discover the best restaurants based on your preferences.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)



# ---------------- Haversine ----------------

def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        sin(dlat/2)**2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon/2)**2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1-a)
    )

    return R*c



# ---------------- Features ----------------

features = [
    'Consumer_ID',
    'Restaurant_ID',
    'Food_Rating',
    'Service_Rating',
    'City_x',
    'State_x',
    'Country_x',
    'Latitude_x',
    'Longitude_x',
    'Smoker',
    'Drink_Level',
    'Transportation_Method',
    'Marital_Status',
    'Children',
    'Age',
    'Occupation',
    'Budget',
    'Preferred_Cuisine',
    'Name',
    'City_y',
    'State_y',
    'Country_y',
    'Zip_Code',
    'Latitude_y',
    'Longitude_y',
    'Alcohol_Service',
    'Smoking_Allowed',
    'Price',
    'Franchise',
    'Area',
    'Parking',
    'Cuisine',
    'Distance_km',
    'Cuisine_Match',
    'Budget_Match',
    'Lifestyle_Score'
]



# ---------------- User Type ----------------

st.subheader("👤 User Information")


user_type = st.radio(
    "🆔 Do you already have a Customer ID?",
    ["Yes","No"],
    horizontal=True
)



# ---------------- Existing User ----------------
if user_type == "Yes":

    customer_id = st.selectbox(
        "👤 Select Customer ID",
        consumers["Consumer_ID"].unique()
    )


    customer_info = consumers[
        consumers["Consumer_ID"] == customer_id
    ].iloc[0].to_dict()


    customer_cuisines = (
        consumer_preferences[
            consumer_preferences["Consumer_ID"] == customer_id
        ]["Preferred_Cuisine"]
        .tolist()
    )


    # -------- Customer Profile --------

    st.subheader("👤 Customer Profile")


    profile = pd.DataFrame(
        customer_info.items(),
        columns=[
            "Feature",
            "Value"
        ]
    )


    st.dataframe(
        profile,
        use_container_width=True
    )


    # -------- Customer Preferences --------

    st.subheader("🍽️ Preferred Cuisines")


    if len(customer_cuisines) > 0:

        st.write(
            ", ".join(customer_cuisines)
        )

    else:

        st.write(
            "No preferences available"
        )



# ---------------- New User ----------------

else:

    customer_info={}


    col1,col2=st.columns(2)


    with col1:

        customer_info["Smoker"]=st.selectbox(
            "🚬 Smoker",
            ["Yes","No"]
        )


        customer_info["Drink_Level"]=st.selectbox(
            "🍷 Drink Level",
            ["Abstemious","Casual","Social"]
        )


        customer_info["Transportation_Method"]=st.text_input(
            "🚗 Transportation Method"
        )


        customer_info["Marital_Status"]=st.selectbox(
            "💍 Marital Status",
            ["Single","Married"]
        )


        customer_info["Children"]=st.selectbox(
            "👶 Children",
            ["Yes","No"]
        )


    with col2:


        customer_info["Occupation"]=st.text_input(
            "💼 Occupation"
        )


        customer_info["Budget"]=st.selectbox(
            "💰 Budget",
            ["Low","Medium","High"]
        )


        customer_info["Latitude"]=st.number_input(
            "Latitude"
        )


        customer_info["Longitude"]=st.number_input(
            "Longitude"
        )


        cuisine=st.selectbox(
            "🍕 Preferred Cuisine",
            restaurant_cuisines["Cuisine"].dropna().unique()
        )


    customer_cuisines=[cuisine]



# ---------------- Recommendation ----------------

def budget_score(price, budget):

    if price == budget:
        return 1

    elif (
        (price == "Medium" and budget in ["Low", "High"])
        or
        (budget == "Medium" and price in ["Low", "High"])
    ):
        return 0.5

    else:
        return 0



if st.button("🍽️ Get Recommendations"):


    candidate_restaurants = restaurants.copy()


    # Add Cuisine information
    cuisine_mapping = (
        restaurant_cuisines
        .groupby("Restaurant_ID")["Cuisine"]
        .apply(lambda x: ", ".join(x.dropna().astype(str)))
        .reset_index()
    )


    candidate_restaurants = candidate_restaurants.merge(
        cuisine_mapping,
        on="Restaurant_ID",
        how="left"
    )


    customer_lat = customer_info.get(
        "Latitude",
        0
    )

    customer_lon = customer_info.get(
        "Longitude",
        0
    )


    customer_budget = customer_info.get(
        "Budget",
        ""
    )


    # ---------------- Distance ----------------

    candidate_restaurants["Distance_km"] = candidate_restaurants.apply(
        lambda x:
        haversine(
            customer_lat,
            customer_lon,
            x["Latitude"],
            x["Longitude"]
        ),
        axis=1
    )


    # ---------------- Cuisine Match ----------------

    preferred_restaurants = restaurant_cuisines[
        restaurant_cuisines["Cuisine"].isin(
            customer_cuisines
        )
    ]["Restaurant_ID"].unique()


    candidate_restaurants["Cuisine_Match"] = (
        candidate_restaurants["Restaurant_ID"]
        .isin(preferred_restaurants)
        .astype(int)
    )



    # ---------------- Budget Match ----------------

    candidate_restaurants["Budget_Match"] = (
        candidate_restaurants.apply(
            lambda x:
            budget_score(
                x["Price"],
                customer_budget
            ),
            axis=1
        )
    )



    # ---------------- Add Customer Features ----------------

    candidate_restaurants["Preferred_Cuisine"] = (
        customer_cuisines[0]
    )


    for col, value in customer_info.items():

        if col not in candidate_restaurants.columns:

            candidate_restaurants[col] = value



    # ---------------- Prepare Model Input ----------------

    X_rec = candidate_restaurants.copy()


    for col, encoder in label_encoders.items():

        if col in X_rec.columns:

            X_rec[col] = X_rec[col].astype(str)


            X_rec[col] = X_rec[col].apply(
                lambda x:
                x if x in encoder.classes_
                else encoder.classes_[0]
            )


            X_rec[col] = encoder.transform(
                X_rec[col]
            )



    for col in features:

        if col not in X_rec.columns:

            X_rec[col] = 0



    X_rec = X_rec[features]



    # ---------------- Prediction ----------------

    predictions = model.predict(
        X_rec
    )


    candidate_restaurants[
        "Predicted_Rating"
    ] = predictions



    # ---------------- Top 5 ----------------

    top = (
        candidate_restaurants
        .sort_values(
            "Predicted_Rating",
            ascending=False
        )
        .head(5)
    )



    st.subheader(
        "⭐ Top 5 Recommendations"
    )



    for _, row in top.iterrows():

        st.markdown(
            f"""
            <div class='card'>

            <h3>🍴 {row['Name']}</h3>


            ⭐ Predicted Rating:
            {row['Predicted_Rating']:.2f}


            <br><br>


            🍕 Cuisine:
            {row['Cuisine']}


            <br>


            🍕 Cuisine Match:
            {row['Cuisine_Match']}


            <br>


            💰 Price:
            {row['Price']}


            <br>


            💵 Budget Match:
            {row['Budget_Match']}


            <br>


            📍 Distance:
            {row['Distance_km']:.2f} km


            <br>


            🚗 Parking:
            {row['Parking']}


            <br>


            🚬 Smoking Allowed:
            {row['Smoking_Allowed']}


            <br>


            🍷 Alcohol Service:
            {row['Alcohol_Service']}


            <br>


            📌 Area:
            {row['Area']}


            </div>
            """,
            unsafe_allow_html=True
        )