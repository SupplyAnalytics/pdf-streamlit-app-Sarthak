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
import pikepdf
import os
import time
import re
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

    

def generate_catalogue_pdf(Platform, subcategory, price_range, BijnisExpress, productcount, UTMSource, UTMCampaign, UTMMedium, progress_callback=None):
    
    def compress_pdf(input_pdf_path, output_pdf_path):
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input PDF file '{input_pdf_path}' does not exist.")
        with pikepdf.open(input_pdf_path) as pdf:
            pdf.save(output_pdf_path, compress_streams=True)


    def sort_dataframe_by_variant_count(df):
        print('sorting')
        print(df['SubCategory'])
        subcategory_counts = df.groupby('SubCategory')['variantid'].count().reset_index()
        print(subcategory_counts)
        subcategory_counts.columns = ['SubCategory', 'Count']
        sorted_subcategories = subcategory_counts.sort_values(by='Count', ascending=False)['SubCategory']
        df['SubCategory'] = pd.Categorical(df['SubCategory'], categories=sorted_subcategories, ordered=True)
        df = df.sort_values('SubCategory')
        print('Sorted')
        return df
    
    def parse_colors(color_text):
        color_mapping = {
            'red': '#ff0000',
            'blue': '#0000ff',
            'green': '#008000',
            'yellow': '#ffff00',
            'black': '#000000',
            'white': '#ffffff',
            'brown': '#a52a2a',
            'orange': '#ffa500',
            'pink': '#ffc0cb',
            'purple': '#800080',
            'gray': '#808080',
            'grey': '#808080',
            'multicolor': None,
            'military': '#2e3b4e'
        }
        colors_list = re.findall(r'[a-zA-Z]+', color_text.lower())
        color_codes = [color_mapping.get(color) for color in colors_list if color in color_mapping and color_mapping.get(color) is not None]
        # Use a default color if no valid color is found
        if not color_codes:
            color_codes = ['#0000FF']  # Default color
        return color_codes
    
    def create_pdf_4by5(df, output_file, max_image_width, max_image_height, orientation='portrait'):
        print('Creating PDF')
        if orientation == 'portrait':
            page_width, page_height = portrait(letter)
        elif orientation == 'landscape':
            page_width, page_height = landscape(letter)
        else:
            raise ValueError("Invalid orientation. Please specify 'portrait' or 'landscape'.")

        margin_rows = 10  # Set margin space between rows
        margin_columns = 20  # Set margin space between columns
        increased_page_width = 685  # Set the increased page width
        increased_page_height = 1040  # Set the increased page height

        subcategories = df['SubCategory'].unique()

        num_columns = 4  # Adjust as needed
        num_rows = 5  # Adjust as needed

    # Calculate total width and height including margins
        total_width = (max_image_width + margin_columns) * num_columns + margin_columns * (num_columns - 1) + margin_rows * 2
        total_height = (max_image_height + margin_rows) * num_rows + margin_rows * 2

        x_offset = (increased_page_width - total_width) / 2 + 25
        y_offset = (increased_page_height - total_height) / 2

        c = canvas.Canvas(output_file, pagesize=(increased_page_width, increased_page_height))  # Set page size with increased width and height
        styles = getSampleStyleSheet()

        small_image_path = "BijnisLogo.png"
        small_image_width = 140
        small_image_height = 70

        total_steps = len(subcategories)
        step = 0
        start_time = time.time()

        for subcategory in subcategories:
            subcategory_df = df[df['SubCategory'] == subcategory]
            pages = (len(subcategory_df) + num_columns * num_rows - 1) // (num_columns * num_rows)  # Calculate number of pages needed

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

                sub_df = subcategory_df.iloc[page * num_columns * num_rows:(page + 1) * num_columns * num_rows]  # Limit rows per page
                image_urls = sub_df['App_Image'].tolist()
                product_names = sub_df['ProductName'].tolist()
                price_ranges = sub_df['Price_Range'].tolist()  # Extract price range
                deeplink_urls = sub_df['App_Deeplink'].tolist()  # Extract deeplink URLs

                page_has_content = False  # Flag to track if the page has content
                print('Creating Images')

                for i, (image_url, product_name, price_range, deeplink_url) in enumerate(zip(image_urls, product_names, price_ranges, deeplink_urls)):  # Modify loop to include price range
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
                        img.thumbnail((max_image_width, max_image_height - 30))  # Adjust height for image to fit the title

                    # Draw the image with margin and add hyperlink
                        c.drawImage(ImageReader(img_bytes), x, y, width=max_image_width, height=max_image_height - 30, preserveAspectRatio=True)
                        c.linkURL(deeplink_url, (x, y, x + max_image_width, y + max_image_height - 30))

                        print('Image Drawn')

                    # Draw the outline rectangle
                        hex_yellow = "#FFCA18"  # Hex color code for yellow
                        c.setStrokeColor(colors.HexColor(hex_yellow))  # Set the outline color to yellow
                        c.setLineWidth(4)  # Set the outline thickness
                        c.rect(x, y - 30, max_image_width+10, max_image_height)  # Draw the outline rectangle

                    # Draw product name and price range inside the yellow box below the image
                        product_info = f"{product_name}<br/>Rs:{price_range}"
                        hyperlink = f'<a href="{deeplink_url}">{product_info}</a>'
                        hyperlink_style = styles["BodyText"]
                        hyperlink_style.fontName = "Helvetica-Bold"
                        if len(product_name) <= 21:
                            hyperlink_style.fontSize = 14
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 14)
                        else:
                            hyperlink_style.fontSize = 294 / len(product_name)
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 294 / len(product_name)) 

                        print(len(product_name.split()))
                        print(product_name.split())
                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width)/2) - pwidth/2) , y - 25)
                        page_has_content = True  # Mark the page as having content
                    else:
                        print(f"Failed to download image from {image_url}")

            # Check if the page has content before calling showPage()
                if page_has_content:
                    c.showPage()
                    print('Shown Page')
            
            step += 1
            elapsed_time = time.time() - start_time
            avg_time_per_step = elapsed_time / step
            remaining_steps = total_steps - step
            estimated_time_remaining = avg_time_per_step * remaining_steps
            if progress_callback:
                progress_callback(step / total_steps, estimated_time_remaining)

        c.save()
        print('save')

    def create_pdf(df, output_file, max_image_width, max_image_height, orientation='portrait'):
        if orientation == 'portrait':
            page_width, page_height = portrait(letter)
        elif orientation == 'landscape':
            page_width, page_height = landscape(letter)
        else:
            raise ValueError("Invalid orientation. Please specify 'portrait' or 'landscape'.")

        margin_rows = 100
        margin_columns = 30
        increased_page_width = 685 + 420
        increased_page_height = (1040 + 400) * 1.5

        df['Platform'] = pd.Categorical(df['Platform'], categories=['Production', 'Distribution'], ordered=True)
        df = df.sort_values(by='Platform')

        subcategories = df['SubCategory'].unique()

        num_columns = 2
        num_rows = 3

        total_width = (max_image_width + margin_columns) * num_columns + margin_columns * (num_columns - 1) + margin_rows * 2
        total_height = (max_image_height + margin_rows) * num_rows + margin_rows * 2

        x_offset = (increased_page_width - total_width) / 2 + 25
        y_offset = (increased_page_height - total_height) / 2

        c = canvas.Canvas(output_file, pagesize=(increased_page_width, increased_page_height))
        styles = getSampleStyleSheet()

        small_image_path = "BijnisLogo.png"
        small_image_width = 140
        small_image_height = 70

        #Varaibles for Progress Var
        total_steps = len(subcategories)
        step = 0
        start_time = time.time()

        for subcategory in subcategories:
            subcategory_df = df[df['SubCategory'] == subcategory]
            pages = (len(subcategory_df) + num_columns * num_rows - 1) // (num_columns * num_rows)

            for page in range(pages):
                c.drawImage(small_image_path, (increased_page_width + margin_rows) - small_image_width - 100, increased_page_height - small_image_height, width=small_image_width, height=small_image_height)
                subcategory_upper = f"{subcategory.upper()}"
                c.setFont("Helvetica-Bold", 40)
                text_width = c.stringWidth(subcategory_upper, 'Helvetica-Bold', 40)
                c.drawString((increased_page_width / 2 - text_width / 2), increased_page_height - 40, subcategory_upper)
            
                sub_df = subcategory_df.iloc[page * num_columns * num_rows:(page + 1) * num_columns * num_rows]
                image_urls = sub_df['App_Image'].astype(str).tolist()
                product_names = sub_df['ProductName'].astype(str).tolist()
                price_ranges = sub_df['Price_Range'].astype(str).tolist()
                deeplink_urls = sub_df['App_Deeplink'].astype(str).tolist()
                sizes = sub_df['VariantSize'].astype(str).tolist()
                colors_list = sub_df['Color'].astype(str).tolist()

                page_has_content = False
                for i, (image_url, product_name, price_range, deeplink_url, size, color_text) in enumerate(zip(image_urls, product_names, price_ranges, deeplink_urls, sizes, colors_list)):
                    row_index = i // num_columns
                    col_index = i % num_columns
                    x = x_offset + margin_columns + col_index * (max_image_width + margin_columns) + 50
                    y = y_offset + margin_rows + (num_rows - row_index - 1) * (max_image_height + margin_rows)

                    response = requests.get(image_url)
                    if response.status_code == 200:
                        img_bytes = BytesIO(response.content)
                        img = Image.open(img_bytes)
                        img.thumbnail((max_image_width, max_image_height - 30))
                        c.drawImage(ImageReader(img_bytes), x, y + 60, width=max_image_width, height=max_image_height - 80, preserveAspectRatio=True)
                        c.linkURL(deeplink_url, (x, y + 60, x + max_image_width, y + max_image_height - 80))

                        rect_color = colors.HexColor("#F26522")
                        c.setStrokeColor(rect_color)
                        c.setLineWidth(4)
                        c.roundRect(x, y - 30, max_image_width + 20, max_image_height + 90, radius=10)

                        hyperlink_style = ParagraphStyle('hyperlink', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=24, textColor=colors.black, underline=True)
                        product_info = f'{product_name}<br/><br/><font size="18" color="red" style="text-decoration: underline; text-decoration-thickness: 2px;">CLICK </font><font size="18" color="black" style="text-decoration: underline; text-decoration-thickness: 2px;"> For More Info</font>'
                        hyperlink = f'<a href="{deeplink_url}" color="black">{product_info}</a>'
                        p = Paragraph(hyperlink, hyperlink_style)

                        if len(product_name) <= 20:
                            hyperlink_style.fontSize = 30
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 30)
                        else:
                            hyperlink_style.fontSize = 600 / len(product_name)
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 600 / len(product_name))

                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width) / 2) - (pwidth / 2)), y + 590)

                        c.setStrokeColor('black')
                        c.setLineWidth(2)
                        c.setFillColor('black')
                        c.roundRect(x + (((max_image_width) / 2) - (pwidth / 2)) - 5, y + 565, pwidth + 40, 60, radius=10)
                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width) / 2) - (pwidth / 2)), y + 590)

                        color_codes = parse_colors(color_text)
                        rect_y = y + 30
                        rect_width = 25
                        rect_height = 25
                        rect_spacing = 5
                        c.setFont("Helvetica", 18)

                        for j, color_code in enumerate(color_codes):
                            rect_x = x + j * (rect_width + rect_spacing) + 120
                            c.setFillColor(color_code)
                            c.setLineWidth(0)
                            c.rect(rect_x, rect_y - 40, rect_width, rect_height, fill=1)
                            break

                        if len(size) <= 20:
                            c.setFont("Helvetica", 28)
                            c.setFillColor('black')
                            c.drawString(rect_x + 50, rect_y - 40, f"Size: {size}")
                        else:
                            c.setFont("Helvetica", 12)
                            c.setFillColor('black')
                            c.drawString(rect_x + 50, rect_y - 40, f"Size: {size}")

                        c.setFillColor('yellow')
                        c.circle(x + 500, rect_y + 80, 70, fill=1, stroke=1)
                        c.setFont("Helvetica-Bold", 20)
                        c.setFillColor('black')
                        c.drawString(x + 450, rect_y + 80, 'Price (Rs):')

                        if len(price_range) >= 11:
                            c.setFont("Helvetica-Bold", 22)
                            c.drawString(x + 450, rect_y + 60, f'{price_range}')
                        else:
                            c.setFont("Helvetica-Bold", 24)
                            c.drawString(x + 450, rect_y + 60, f'{price_range}')

                        page_has_content = True
                    else:
                        print(f"Failed to download image from {image_url}")

                if page_has_content:
                    c.showPage()

            step += 1
            elapsed_time = time.time() - start_time
            avg_time_per_step = elapsed_time / step
            remaining_steps = total_steps - step
            estimated_time_remaining = avg_time_per_step * remaining_steps
            if progress_callback:
                progress_callback(step / total_steps, estimated_time_remaining)

        c.save()

    output_file = 'sample_catalogue.pdf'
    compressed_output_file = 'sample_catalogue_compressed.pdf'
    max_image_width = 146 + 400
    max_image_height = 175 + 400

    df = pd.read_csv('PDFReport_174857000100873355.csv')
    df['SubCategory'] = df['SubCategory'].fillna('')


    print(UTMSource)
    print(UTMCampaign)
    print(UTMMedium)
    


    if Platform != "All":
        df = df[df['Platform'] == Platform]

    if supercategory != "All":
        df = df[df['SuperCategory'] == supercategory]

    if subcategory != "All":
        df = df[df['SubCategory'] == subcategory]
       
    if price_range is not None:
        df = df[(df['Avg_Price'] >= price_range[0]) & (df['Avg_Price'] <= price_range[1])]

    if SellerName1 != "All":
        df = df[df['SellerName'] == SellerName1]

    if productcount is not None:
        if Platform == "BijnisExpress":
            df = df[(df['rankBijExp'] <= productcount[1])]
        elif Platform == "Production":
            df = df[(df['rankPP'] <= productcount[1])]
        elif Platform == "Distribution":
            df = df[(df['rankDP'] <= productcount[1])]
        else:
            df = df[(df['rankOverall'] <= productcount[1])]

    df = sort_dataframe_by_variant_count(df)

    # if UTM == "Default":
    #     UTMSource = "BI_Campaign",
    #     UTMCampaign = "BI_Campaign",
    #     UTMMedium = "BI_Campaign"
    #     deeplink(UTMSource,UTMCampaign,UTMMedium,df)
    # else:
        

    

    if UTM != "Default":
        deeplink(UTMSource,UTMCampaign,UTMMedium,df)
        link_df = pd.read_csv('Postman_Deeplink_Final.csv')
        df = df.merge(link_df, how='left', on='variantid')
        df.to_csv('Default.csv')
        df = df.rename(columns={"App_Deeplink_y": "App_Deeplink"})

    
    if Platform == "BijnisExpress":
        df['SubCategory'] = 'Bijnis Express - 3 Hours Delivery'
        df = df.sort_values(by='SuperCategory', ascending=True)
       
    
    if format =='4x5':
        create_pdf_4by5(df, output_file, max_image_width = 146 , max_image_height = 175)
    else:
        create_pdf(df, output_file, max_image_width, max_image_height)
    
    compress_pdf(output_file, compressed_output_file)
    
    return compressed_output_file

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

def new_variants_pdf( progress_callback=None):
    def compress_pdf(input_pdf_path, output_pdf_path):
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input PDF file '{input_pdf_path}' does not exist.")
        with pikepdf.open(input_pdf_path) as pdf:
            pdf.save(output_pdf_path, compress_streams=True)


    
    def sort_dataframe_by_variant_count(df):
        print('sorting')
        print(df['SubCategory'])
        subcategory_counts = df.groupby('SubCategory')['variantid'].count().reset_index()
        print(subcategory_counts)
        subcategory_counts.columns = ['SubCategory', 'Count']
        sorted_subcategories = subcategory_counts.sort_values(by='Count', ascending=False)['SubCategory']
        df['SubCategory'] = pd.Categorical(df['SubCategory'], categories=sorted_subcategories, ordered=True)
        df = df.sort_values('SubCategory')
        print(sorted_subcategories)
        print('Sorted')
        return df
    
    def parse_colors(color_text):
        color_mapping = {
            'red': '#ff0000',
            'blue': '#0000ff',
            'green': '#008000',
            'yellow': '#ffff00',
            'black': '#000000',
            'white': '#ffffff',
            'brown': '#a52a2a',
            'orange': '#ffa500',
            'pink': '#ffc0cb',
            'purple': '#800080',
            'gray': '#808080',
            'grey': '#808080',
            'multicolor': None,
            'military': '#2e3b4e'
        }
        colors_list = re.findall(r'[a-zA-Z]+', color_text.lower())
        color_codes = [color_mapping.get(color) for color in colors_list if color in color_mapping and color_mapping.get(color) is not None]
        # Use a default color if no valid color is found
        if not color_codes:
            color_codes = ['#0000FF']  # Default color
        return color_codes
    def create_pdf(df, output_file, max_image_width, max_image_height, orientation='portrait'):
        if orientation == 'portrait':
            page_width, page_height = portrait(letter)
        elif orientation == 'landscape':
            page_width, page_height = landscape(letter)
        else:
            raise ValueError("Invalid orientation. Please specify 'portrait' or 'landscape'.")

        margin_rows = 100
        margin_columns = 30
        increased_page_width = 685 + 420
        increased_page_height = (1040 + 400) * 1.5

        df['Platform'] = pd.Categorical(df['Platform'], categories=['Production', 'Distribution'], ordered=True)
        df = df.sort_values(by='Platform')

        subcategories = df['SubCategory'].unique()

        num_columns = 2
        num_rows = 3

        total_width = (max_image_width + margin_columns) * num_columns + margin_columns * (num_columns - 1) + margin_rows * 2
        total_height = (max_image_height + margin_rows) * num_rows + margin_rows * 2

        x_offset = (increased_page_width - total_width) / 2 + 25
        y_offset = (increased_page_height - total_height) / 2

        c = canvas.Canvas(output_file, pagesize=(increased_page_width, increased_page_height))
        styles = getSampleStyleSheet()

        small_image_path = "BijnisLogo.png"
        small_image_width = 140
        small_image_height = 70

        total_steps = len(subcategories)
        step = 0
        start_time = time.time()

        for subcategory in subcategories:
            print(subcategory)
            subcategory_df = df[df['SubCategory'] == subcategory]
            pages = (len(subcategory_df) + num_columns * num_rows - 1) // (num_columns * num_rows)

            for page in range(pages):
                c.drawImage(small_image_path, (increased_page_width + margin_rows) - small_image_width - 100, increased_page_height - small_image_height, width=small_image_width, height=small_image_height)
                subcategory_upper = f"{subcategory.upper()}"
                c.setFont("Helvetica-Bold", 40)
                text_width = c.stringWidth(subcategory_upper, 'Helvetica-Bold', 40)
                c.drawString((increased_page_width / 2 - text_width / 2), increased_page_height - 40, subcategory_upper)



                sub_df = subcategory_df.iloc[page * num_columns * num_rows:(page + 1) * num_columns * num_rows]
                image_urls = sub_df['App_Image'].astype(str).tolist()
                product_names = sub_df['ProductName'].astype(str).tolist()
                price_ranges = sub_df['Price_Range'].astype(str).tolist()
                deeplink_urls = sub_df['App_Deeplink'].astype(str).tolist()
                sizes = sub_df['VariantSize'].astype(str).tolist()
                colors_list = sub_df['Color'].astype(str).tolist()

                page_has_content = False
                for i, (image_url, product_name, price_range, deeplink_url, size, color_text) in enumerate(zip(image_urls, product_names, price_ranges, deeplink_urls, sizes, colors_list)):
                    row_index = i // num_columns
                    col_index = i % num_columns
                    x = x_offset + margin_columns + col_index * (max_image_width + margin_columns) + 50
                    y = y_offset + margin_rows + (num_rows - row_index - 1) * (max_image_height + margin_rows)

                    response = requests.get(image_url)
                    if response.status_code == 200:
                        img_bytes = BytesIO(response.content)
                        img = Image.open(img_bytes)
                        img.thumbnail((max_image_width, max_image_height - 30))
                        c.drawImage(ImageReader(img_bytes), x, y + 60, width=max_image_width, height=max_image_height - 80, preserveAspectRatio=True)
                        c.linkURL(deeplink_url, (x, y + 60, x + max_image_width, y + max_image_height - 80))

                        rect_color = colors.HexColor("#F26522")
                        c.setStrokeColor(rect_color)
                        c.setLineWidth(4)
                        c.roundRect(x, y - 30, max_image_width + 20, max_image_height + 90, radius=10)

                        hyperlink_style = ParagraphStyle('hyperlink', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=24, textColor=colors.black, underline=True)
                        product_info = f'{product_name}<br/><br/><font size="18" color="red" style="text-decoration: underline; text-decoration-thickness: 2px;">CLICK </font><font size="18" color="black" style="text-decoration: underline; text-decoration-thickness: 2px;"> For More Info</font>'
                        hyperlink = f'<a href="{deeplink_url}" color="black">{product_info}</a>'
                        p = Paragraph(hyperlink, hyperlink_style)

                        if len(product_name) <= 20:
                            hyperlink_style.fontSize = 30
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 30)
                        else:
                            hyperlink_style.fontSize = 600 / len(product_name)
                            p = Paragraph(hyperlink, hyperlink_style)
                            pwidth = c.stringWidth(product_name, 'Helvetica-Bold', 600 / len(product_name))

                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width) / 2) - (pwidth / 2)), y + 590)

                        c.setStrokeColor('black')
                        c.setLineWidth(2)
                        c.setFillColor('black')
                        c.roundRect(x + (((max_image_width) / 2) - (pwidth / 2)) - 5, y + 565, pwidth + 40, 60, radius=10)
                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width) / 2) - (pwidth / 2)), y + 590)

                        color_codes = parse_colors(color_text)
                        rect_y = y + 30
                        rect_width = 25
                        rect_height = 25
                        rect_spacing = 5
                        c.setFont("Helvetica", 18)

                        for j, color_code in enumerate(color_codes):
                            rect_x = x + j * (rect_width + rect_spacing) + 120
                            c.setFillColor(color_code)
                            c.setLineWidth(0)
                            c.rect(rect_x, rect_y - 40, rect_width, rect_height, fill=1)
                            break

                        if len(size) <= 20:
                            c.setFont("Helvetica", 28)
                            c.setFillColor('black')
                            c.drawString(rect_x + 50, rect_y - 40, f"Size: {size}")
                        else:
                            c.setFont("Helvetica", 12)
                            c.setFillColor('black')
                            c.drawString(rect_x + 50, rect_y - 40, f"Size: {size}")

                        c.setFillColor('yellow')
                        c.circle(x + 500, rect_y + 80, 70, fill=1, stroke=1)
                        c.setFont("Helvetica-Bold", 20)
                        c.setFillColor('black')
                        c.drawString(x + 450, rect_y + 80, 'Price (Rs):')

                        if len(price_range) >= 11:
                            c.setFont("Helvetica-Bold", 22)
                            c.drawString(x + 450, rect_y + 60, f'{price_range}')
                        else:
                            c.setFont("Helvetica-Bold", 24)
                            c.drawString(x + 450, rect_y + 60, f'{price_range}')

                        page_has_content = True
                    else:
                        print(f"Failed to download image from {image_url}")

                if page_has_content:
                    c.showPage()
        
            step += 1
            elapsed_time = time.time() - start_time
            avg_time_per_step = elapsed_time / step
            remaining_steps = total_steps - step
            estimated_time_remaining = avg_time_per_step * remaining_steps
            if progress_callback:
                progress_callback(step / total_steps, estimated_time_remaining)

        c.save()

    output_file = 'sample_catalogue.pdf'
    compressed_output_file = 'sample_catalogue_compressed.pdf'
    max_image_width = 146 + 400
    max_image_height = 175 + 400
    df = pd.read_csv('PDFReport_174857000103979557.csv')
    df = df[df['Platform']=='Production']
    df = sort_dataframe_by_variant_count(df)
    create_pdf(df, output_file, max_image_width, max_image_height)
    compress_pdf(output_file, compressed_output_file)

    return compressed_output_file

def ExportPivotMaster():
    class Config:
        CLIENTID = "1000.DQ32DWGNGDO7CV0V1S1CB3QFRAI72K";
        CLIENTSECRET = "92dfbbbe8c2743295e9331286d90da900375b2b66c";
        REFRESHTOKEN = "1000.0cd324af15278b51d3fc85ed80ca5c04.7f4492eb09c6ae494a728cd9213b53ce";
        ORGID = "60006357703";
        VIEWID = "174857000103979557"
        WORKSPACEID = "174857000004732522";

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
        view_ids = ["174857000103979557"]
        obj.export_data(obj.ac);

    except Exception as e:
        print(str(e))

def deeplink(UTMSource,UTMCampaign,UTMMedium,df):
    print(UTMSource)
    def ExportPivotMaster():
        class Config:
            CLIENTID = "1000.DQ32DWGNGDO7CV0V1S1CB3QFRAI72K"
            CLIENTSECRET = "92dfbbbe8c2743295e9331286d90da900375b2b66c"
            REFRESHTOKEN = "1000.0cd324af15278b51d3fc85ed80ca5c04.7f4492eb09c6ae494a728cd9213b53ce"
            ORGID = "60006357703"
            VIEWID = "174857000104896659"
            WORKSPACEID = "174857000004732522"

        class Sample:
            def __init__(self, ac):
                self.ac = ac

            def export_data(self):
                response_format = "csv"
                file_path_template = "BijnisDeeplinkPDF.csv"
                bulk = self.ac.get_bulk_instance(Config.ORGID, Config.WORKSPACEID)

                for view_id in view_ids:
                    file_path = file_path_template.format(view_id)
                    bulk.export_data(view_id, response_format, file_path)

        try:
            ac = AnalyticsClient(Config.CLIENTID, Config.CLIENTSECRET, Config.REFRESHTOKEN)
            obj = Sample(ac)
            view_ids = ["174857000104896659"]
            obj.export_data()
        except Exception as e:
            print(str(e))

    ExportPivotMaster()

# Verify if the CSV file was created
    df.to_csv('BijnisDeeplinkPDF.csv')
    csv_file = 'BijnisDeeplinkPDF.csv'
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found. Please check the export process.")
        exit(1)

# Read the CSV file
    data = pd.read_csv(csv_file)
    print(data)

# URL and headers for the API request
    url = 'https://api.bijnis.com/g/ba/generate/pdplink/'
    headers = {
    'Content-Type': 'application/json'
    }

# Initialize a list to hold all the responses
    responses = []

# Function to handle individual requests
    def make_request(variant_id):
    # Create the payload as specified in the cURL command
        payload = {
            "nid": [variant_id],
            "utmSource": UTMSource,
            "utmCampaign": UTMCampaign,
            "utmMedium": UTMMedium
        }

    # Make the POST request
        response = requests.post(url, headers=headers, json=payload)

    # Add error handling
        if response.status_code == 200:
            return {'variantid': variant_id, 'response': response.json()}
        else:
            return {'variantid': variant_id, 'error': response.status_code}

# Use ThreadPoolExecutor to make parallel requests
    with ThreadPoolExecutor(max_workers=100) as executor:
    # Submit tasks to the executor
        futures = {executor.submit(make_request, int(row['variantid'])): int(row['variantid']) for _, row in data.iterrows()}

    # Use tqdm to display a progress bar
        for future in tqdm(as_completed(futures), total=len(futures)):
            responses.append(future.result())

# Write all responses to a JSON file
    json_file = 'output.json'
    with open(json_file, 'w') as outfile:
        json.dump(responses, outfile, indent=4)

    print("Data fetching complete. Responses saved to output.json.")

# Verify if the JSON file was created
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found. Please check the path.")
        exit(1)

# Read the JSON file and extract the required data
    final_data = []

    try:
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Iterate through each JSON object in the array
            for item in data:
            # Extract variantId
                variant_id = item['variantid']

            # Check if 'response' and 'url' keys exist
                if 'response' in item and 'url' in item['response']:
                    url = item['response']['url'][str(variant_id)]  # Access URL using variantId as key
                    final_data.append({'variantid': variant_id, 'App_Deeplink': url})
                else:
                    print(f"Warning: Missing 'response' or 'url' key in item with variantid: {variant_id}")

    # Create pandas DataFrame and save to CSV (if data was extracted)
        if final_data:
            df = pd.DataFrame(final_data)
            df.to_csv('Postman_Deeplink_Final.csv', index=False)
            print('Success! CSV file created.')
        else:
            print("Warning: No data extracted due to missing keys in JSON objects.")
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found. Please check the path.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON data from '{json_file}'.")

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
# ExportPivotMaster()

st.title("The PDF Tool")
# ExportData()

# Session state to keep track of submission state
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

option = st.selectbox(
    "Select the required report:",
    ["Top Performing Variants","Yesterday Launched Variants"],
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
supercategory = None
UTMSource = None,
UTMCampaign = None,
UTMMedium = None

subcategory_list_df = pd.read_csv('PDFReport_174857000100873355.csv')
subcategory_names = subcategory_list_df['SubCategory'].unique().tolist()
subcategory_names.insert(0, "All")

SellerName = subcategory_list_df['SellerName'].unique().tolist()
SellerName.insert(0, "All")


price_ranges = ["All", "0-500", "501-1000", "1001-1500", "1501-2000"]

if st.session_state.submitted:
    if option == "Top Performing Variants":
        col1, col2, col3, col4, col5, col6, col7 = st.columns([20, 18, 19, 19, 12, 15, 15])

    
        with col1:
            Platform = st.selectbox("Select Platform", ["All", "Production", "Distribution", "BijnisExpress"], index=0)
            st.write(f"You selected: {Platform}")
        with col1: 
             
            UTM = st.selectbox("Select UTM", ["Default", "Custom"], index=0)
            if UTM == "Custom":
                UTMSource = st.text_input("Input UTM Source")
                st.write(f"You selected: {UTMSource}")
                UTMCampaign = st.text_input("Input UTM Campaign")
                st.write(f"You selected: {UTMCampaign}")
                UTMMedium = st.text_input("Input UTM Medium")
                st.write(f"You selected: {UTMMedium}")
            else: 
                UTMSource = "BI_Campaign"
                UTMCampaign = "BI_Campaign"
                UTMMedium = "BI_Campaign"
        with col2:
            supercategory = st.selectbox("Select SuperCat", ["All","Footwear","Apparels"])
            st.write(f"You selected: {supercategory}")
        with col3:
            if Platform != 'All':
                if supercategory != 'All':
                    subcategory_list_df1 = subcategory_list_df[subcategory_list_df['SuperCategory'] == supercategory]
                    SellerName = subcategory_list_df1['SellerName'].unique().tolist()
                    SellerName.insert(0, "All")
                    SellerName1 = st.selectbox("Select SellerName", SellerName, index=0)
                    st.write(f"You selected: {SellerName1}")
                else:
                    subcategory_list_df1 = subcategory_list_df[subcategory_list_df['Platform'] == Platform]
                    SellerName = subcategory_list_df1['SellerName'].unique().tolist()
                    SellerName.insert(0, "All")
                    SellerName1 = st.selectbox("Select SellerName", SellerName, index=0)
                    st.write(f"You selected: {SellerName1}")
            else:
                SellerName1 = st.selectbox("Select Seller", SellerName, index=0)
                st.write(f"You selected: {SellerName1}")
        with col4:
            if SellerName1 != 'All':
                subcategory_list_df1 = subcategory_list_df[subcategory_list_df['SellerName'] == SellerName1]
                subcategory_names = subcategory_list_df1['SubCategory'].unique().tolist()
                subcategory_names.insert(0, "All")
                subcategory = st.selectbox("Select Subcat", subcategory_names, index=0)
                st.write(f"You selected: {subcategory}")
            elif supercategory != 'All':
                subcategory_list_df1 = subcategory_list_df[subcategory_list_df['SuperCategory'] == supercategory]
                subcategory_names = subcategory_list_df1['SubCategory'].unique().tolist()
                subcategory_names.insert(0, "All")
                subcategory = st.selectbox("Select Subcat", subcategory_names, index=0)
            else:
                subcategory = st.selectbox("Select Subcat", subcategory_names, index=0)
                st.write(f"You selected: {subcategory}")
        with col5:
            productcount = st.slider("Select Count", 0, 20, (0, 24), step=1)
            st.write(f"Top {productcount} Products")
        with col6:
            price_ranges = st.slider("Select Price Range", 0, 5000, (0, 5000), step=50)
            st.write(f"You selected: {price_ranges}")
        with col7:
            format = st.selectbox("Select PDF Format", [ "2x3", "4x5"], index=0)
            st.write(f"You selected: {format}")
    
    
    if st.button('Process', key='download_button'):

        if option == "Yesterday Launched Variants":   
            ExportPivotMaster()
            st.write('Exporting From Zoho')
            progress_bar = st.progress(0)
            progress_text = st.empty()
            def update_progress(progress, estimated_time_remaining):
                    progress_bar.progress(progress)
                    progress_text.text(f"Estimated time remaining: {int(estimated_time_remaining)} seconds")

            result = new_variants_pdf(update_progress)
            with open(result, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_file,
                        file_name="YesterdayLaunchedVariants.pdf",
                        mime="application/pdf"
                )
                    
        if option == "Top Performing Variants":
            ExportData()
            st.write("Exporting From Zoho")
            if option == "Top Performing Variants":
                progress_bar = st.progress(0)
                progress_text = st.empty()

                def update_progress(progress, estimated_time_remaining):
                    progress_bar.progress(progress)
                    progress_text.text(f"Estimated time remaining: {int(estimated_time_remaining)} seconds")

                result = generate_catalogue_pdf(Platform, subcategory, price_range, BijnisExpress, productcount, UTMSource,UTMCampaign,UTMMedium, update_progress)
                with open(result, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_file,
                        file_name="TopSellingProducts.pdf",
                        mime="application/pdf"
                )

            if result is not None:
                st.write(f"Result: {result}")           