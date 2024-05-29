from __future__ import with_statement
from AnalyticsClient import AnalyticsClient
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
from reportlab.lib.pagesizes import landscape, letter, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib import colors
import requests
from PIL import Image
from io import BytesIO
import smtplib
import tempfile

def generate_catalogue_pdf(Platform, subcategory, price_range, BijnisExpress, productcount):

    def resize_image(image, max_width, max_height):
        img = Image.open(image)
        img.thumbnail((max_width, max_height))
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    def sort_dataframe_by_variant_count(df):
        subcategory_counts = df.groupby('SubCategory')['variantid'].count().reset_index()
        subcategory_counts.columns = ['SubCategory', 'Count']
        sorted_subcategories = subcategory_counts.sort_values(by='Count', ascending=False)['SubCategory']
        df['SubCategory'] = pd.Categorical(df['SubCategory'], categories=sorted_subcategories, ordered=True)
        df = df.sort_values('SubCategory')
        return df

    def create_pdf(df, output_file, max_image_width, max_image_height, orientation='portrait'):
        print('Creating PDF')
        if orientation == 'portrait':
            page_width, page_height = portrait(letter)
        elif orientation == 'landscape':
            page_width, page_height = landscape(letter)
        else:
            raise ValueError("Invalid orientation. Please specify 'portrait' or 'landscape'.")

        margin_rows = 10
        margin_columns = 20
        increased_page_width = 685
        increased_page_height = 1040

        df['Platform'] = pd.Categorical(df['Platform'], categories=['Production', 'Distribution'], ordered=True)
        df = df.sort_values(by='Platform')
        subcategories = df['SubCategory'].unique()

        num_columns = 4
        num_rows = 5

        total_width = (max_image_width + margin_columns) * num_columns + margin_columns * (num_columns - 1) + margin_rows * 2
        total_height = (max_image_height + margin_rows) * num_rows + margin_rows * 2

        x_offset = (increased_page_width - total_width) / 2 + 25
        y_offset = (increased_page_height - total_height) / 2

        c = canvas.Canvas(output_file, pagesize=(increased_page_width, increased_page_height))
        styles = getSampleStyleSheet()

        small_image_path = "BijnisLogo.png"
        small_image_width = 140
        small_image_height = 70

        subcategory = None

        for subcategory in subcategories:
            subcategory_df = df[df['SubCategory'] == subcategory]
            pages = (len(subcategory_df) + num_columns * num_rows - 1) // (num_columns * num_rows)

            for page in range(pages):
                print(subcategory)
                print('Creating Logo')
                c.drawImage(small_image_path, (increased_page_width + margin_rows) - small_image_width, increased_page_height - small_image_height, width=small_image_width, height=small_image_height)
                print('Creating Subcatcategory')
                subcategory_upper = subcategory.upper()
                c.setFont("Helvetica-Bold", 25)
                text_width = c.stringWidth(subcategory_upper, 'Helvetica-Bold', 25)
                c.drawString((increased_page_width / 2 - text_width / 2), increased_page_height - 40, subcategory_upper)

                text_var = 'Please click on the below product Image'
                c.setFont("Helvetica", 15)
                text_width1 = c.stringWidth(text_var, 'Helvetica', 15)
                c.setFillColor(colors.HexColor("#FFCA18"))
                c.rect((increased_page_width / 2 - text_width1 / 2) - 5, increased_page_height - 75, text_width1 + 10, 20, fill=True)
                c.setFillColor(colors.black)
                c.drawString((increased_page_width / 2 - text_width1 / 2), increased_page_height - 70, text_var)

                sub_df = subcategory_df.iloc[page * num_columns * num_rows:(page + 1) * num_columns * num_rows]
                image_urls = sub_df['App_Image'].tolist()
                product_names = sub_df['ProductName'].tolist()
                price_ranges = sub_df['Price_Range'].tolist()
                deeplink_urls = sub_df['App_Deeplink'].tolist()
                Platforms = sub_df['Platform'].tolist()

                page_has_content = False
                print('Creating Images')

                for i, (image_url, product_name, price_range, deeplink_url, Platform) in enumerate(zip(image_urls, product_names, price_ranges, deeplink_urls, Platforms)):
                    print('In Image Loop')
                    row_index = i // num_columns
                    col_index = i % num_columns
                    x = x_offset + margin_columns + col_index * (max_image_width + margin_columns)
                    y = y_offset + margin_rows + (num_rows - row_index - 1) * (max_image_height + margin_rows)

                    response = requests.get(image_url)
                    if response.status_code == 200:
                        print('Downloading Images')
                        img_bytes = BytesIO(response.content)
                        img = Image.open(img_bytes)
                        img.thumbnail((max_image_width, max_image_height - 30))

                        c.drawImage(ImageReader(img_bytes), x, y, width=max_image_width, height=max_image_height - 30, preserveAspectRatio=True)
                        c.linkURL(deeplink_url, (x, y, x + max_image_width, y + max_image_height - 30))

                        df['Platform'] = pd.Categorical(df['Platform'], categories=['Production', 'Distribution'], ordered=True)
                        df = df.sort_values(by='Platform')
                        
                        if Platform == 'Production':
                            rect_color = colors.HexColor("#F26522")
                        else:
                            rect_color = colors.HexColor("#FFCA18")
                        hex_yellow = "#FFCA18"
                        c.setStrokeColor(rect_color)
                        c.setLineWidth(4)
                        c.rect(x, y - 30, max_image_width + 10, max_image_height)

                        product_info = f"{product_name}<br/>Rs:{price_range}"
                        hyperlink = f'<a href="{deeplink_url}">{product_info}</a>'
                        hyperlink_style = styles["BodyText"]
                        hyperlink_style.fontName = "Helvetica-Bold"
                        if len(product_name) <= 20:
                            hyperlink_style.fontSize = 14
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 14)
                        else:
                            hyperlink_style.fontSize = 280 / len(product_name)
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 308 / len(product_name)) 

                        print(len(product_name.split()))
                        print(product_name.split())
                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width + 10) / 2) - (pwidth / 2)) , y - 25)
                        page_has_content = True
                    else:
                        print(f"Failed to download image from {image_url}")

                if page_has_content:
                    c.showPage()
                    print('Shown Page')

        c.save()
        print('save')

    # Main execution
    output_file = 'sample_catalogue.pdf'
    max_image_width = 146
    max_image_height = 175

    df = pd.read_csv('PDFReport_174857000100873355.csv')

    if Platform != "All":
        df = df[df['Platform'] == Platform]

    if subcategory != "All":
            df = df[df['SubCategory'] == subcategory]
       
    if price_range is not None:
        df = df[(df['Avg_Price'] >= price_range[0]) & (df['Avg_Price'] <= price_range[1])]

    if BijnisExpress is not None:
        df = df[df['IsBijnisExpress'] == BijnisExpress]
        df['SubCategory'] = 'Bijnis Express - 3 Hours Delivery'
    
    if productcount is not None:
        if Platform == "Production":
            df = df[(df['rankPP'] >= productcount[1])]
        elif Platform == "Distribution":
            df = df[(df['rankDP'] >= productcount[1])]
        else:
            df = df[(df['rankOverall'] >= productcount[1])]

    create_pdf(df, output_file, max_image_width, max_image_height)
    return output_file

def ExportData():
    class Config:
        CLIENTID = "1000.DQ32DWGNGDO7CV0V1S1CB3QFRAI72K"
        CLIENTSECRET = "92dfbbbe8c2743295e9331286d90da900375b2b66c"
        REFRESHTOKEN = "1000.0cd324af15278b51d3fc85ed80ca5c04.7f4492eb09c6ae494a728cd9213b53ce"
        ORGID = "60006357703"
        VIEWID = "174857000100873355"
        WORKSPACEID = "174857000004732522"

    class sample:
        ac = AnalyticsClient(Config.CLIENTID, Config.CLIENTSECRET, Config.REFRESHTOKEN)

        def export_data(self, ac):
            response_format = "csv"
            file_path_template = "PDFReport_{}.csv"
            bulk = ac.get_bulk_instance(Config.ORGID, Config.WORKSPACEID)

            for view_id in view_ids:
                file_path = file_path_template.format(view_id)
                bulk.export_data(view_id, response_format, file_path)

    try:
        obj = sample()
        view_ids = ["174857000100873355"]
        obj.export_data(obj.ac)

    except Exception as e:
        print(str(e))

    return 'Data Export'

page_bg_img = '''
<style>
@import url('https://fonts.googleapis.com/css2?family=Proxima Nova:wght@700&display=swap');
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #FFCC99, #C2E0FF);
    background-size: cover;
h1 {
    font-family: 'Proxima Nova', sans-serif;
}
}
</style>
'''

st.markdown(page_bg_img, unsafe_allow_html=True)

st.title("The PDF Tool")

# Session state to keep track of submission state
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

option = st.selectbox(
    "Select the required report:",
    ["Top Performing Variants"],
    index=0,
    placeholder="Select report name...",
)

# Handle the Filter button
if st.button('Filter'):
    st.session_state.submitted = True

BijnisExpress = None
Platform = None
subcategory = None
price_range = None
productcount = None


subcategory_list_df = pd.read_csv('SubcategoryList.csv')
subcategory_names = subcategory_list_df['SubCategory'].unique().tolist()
subcategory_names.insert(0, "All")


price_ranges = ["All", "0-500", "501-1000", "1001-1500", "1501-2000"]


if st.session_state.submitted:

    col1, col2, col3, col4, col5 = st.columns([5,5,5,5,5])

    if option == "Top Performing Variants":
        with col1:
            Platform = st.selectbox("Select Platform", ["All", "Production", "Distribution"], index=0)
            st.write(f"You selected: {Platform}")
        with col2:
            subcategory = st.selectbox("Select Subcategory", subcategory_names, index=0)
            st.write(f"You selected: {subcategory}")
        with col3:
            productcount = st.slider("Select Count", 0, 100, (0, 100), step=5)
            st.write(f"Top {productcount} Products")
        with col4:
            price_ranges = st.slider("Select Price Range", 0, 5000, (0, 5000), step=50)
            st.write(f"You selected: {price_ranges}")
        with col5:
            BijnisExpress = st.selectbox("Bijnis Express",[None,"Yes","No"],index=0)
            st.write(f"You selected: {BijnisExpress}")

    # Handle the Download button
    if st.button('Process', key='download_button'):
        ExportData()
        st.write("Exporting From Zoho")
        if option == "Top Performing Variants":
            result = generate_catalogue_pdf(Platform, subcategory, price_range, BijnisExpress, productcount)
            # compress_pdf()
            with open(result, "rb") as pdf_file:
                st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name="TopSellingProducts.pdf",
                mime="application/pdf"
                )

        if result is not None:
            st.write(f"Result: {result}")