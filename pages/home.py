import streamlit as st
import pandas as pd
import requests


@st.cache_data(ttl=3600)
def fetch_webcam_data():
    url = "https://tourism.api.opendatahub.com/v1/WebcamInfo?pagesize=2000&removenullvalues=false&getasidarray=false"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


try:
    data = fetch_webcam_data()
    webcams = data.get('Items', [])

    coords = []

    for webcam in webcams:
        gps_info = webcam.get('GpsInfo')
        image_gallery = webcam.get('ImageGallery')
        detail = webcam.get('Detail', {})
        lang_info = next(iter(detail.values()), {})
        language = lang_info.get('Language', 'unknown')

        if gps_info and image_gallery:
            position = gps_info[0]
            lat = position.get('Latitude')
            lon = position.get('Longitude')
            img_url = image_gallery[0].get('ImageUrl') if image_gallery else None
            title = webcam.get('Shortname', 'Unnamed Webcam')

            if lat and lon and img_url:
                coords.append({
                    'title': title,
                    'language': language,
                    'lat': lat,
                    'lon': lon,
                    'image': img_url
                })

    if coords:
        df_coords = pd.DataFrame(coords)

        st.subheader('Webcam Table')

        # --- Search ---
        search_term = st.text_input("Search webcams", "")
        if search_term:
            filtered_df = df_coords[df_coords['title'].str.contains(search_term, case=False)]
        else:
            filtered_df = df_coords

        # --- Pagination Setup ---
        page_size = 9
        total_pages = (len(filtered_df) - 1) // page_size + 1

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        # Clamp page number
        st.session_state.current_page = max(1, min(st.session_state.current_page, total_pages))

        start_idx = (st.session_state.current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(filtered_df))

        # --- Display Table ---
        st.dataframe(
            filtered_df.iloc[start_idx:end_idx][['title', 'language', 'lat', 'lon']],
            hide_index=True,
            use_container_width=True
        )

        st.write(f"Showing {start_idx + 1}-{end_idx} of {len(filtered_df)} webcams")

        # --- Pagination Controls ---
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("← Previous") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1

        with col2:
            st.markdown(
                f"<div style='text-align: center; font-size: 18px;'>Page {st.session_state.current_page} of {total_pages}</div>",
                unsafe_allow_html=True
            )

        with col3:
            if st.button("Next →") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1

        # --- Export as CSV ---
        if st.button("Export as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="webcams.csv",
                mime="text/csv"
            )

        # --- Webcam Preview ---
        if not filtered_df.empty:
            st.subheader("Preview Selected Webcam")
            selected_title = st.selectbox("Choose a webcam", filtered_df['title'])
            selected_row = filtered_df[filtered_df['title'] == selected_title].iloc[0]

            col1, col2 = st.columns([2, 1])
            with col1:
                st.image(selected_row['image'], caption=selected_title, use_container_width=True)
            with col2:
                st.write(f"**Title:** {selected_row['title']}")
                st.write(f"**Language:** {selected_row['language']}")
                st.write(f"**Latitude:** {selected_row['lat']}")
                st.write(f"**Longitude:** {selected_row['lon']}")

        else:
            st.warning('No webcams with coordinates and images found.')

except requests.exceptions.RequestException as e:
    st.error(f"Error fetching data: {e}")
