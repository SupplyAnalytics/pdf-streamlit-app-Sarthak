from __future__ import with_statement
from AnalyticsClient import AnalyticsClient
import pandas as pd
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
import subprocess
import platform
import tempfile
import pikepdf
import os
import smtplib
import re

def generate_catalogue_pdf():
    def compress_pdf(input_pdf_path, output_pdf_path):
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input PDF file '{input_pdf_path}' does not exist.")
    
        with pikepdf.open(input_pdf_path) as pdf:
            pdf.save(output_pdf_path, compress_streams=True)

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


        # Extract colors from text
        colors_list = re.findall(r'[a-zA-Z]+', color_text.lower())
        color_codes = [color_mapping.get(color, '#0000FF') for color in colors_list if color in color_mapping or not color.isdigit()]
        return color_codes

    def create_pdf(df, output_file, max_image_width, max_image_height, orientation='portrait'):
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

        click_icon_path = "Click.png"
        click_icon_width = 50
        click_icon_height = 50

        for subcategory in subcategories:
            print(subcategory)
            subcategory_df = df[df['SubCategory'] == subcategory]
            pages = (len(subcategory_df) + num_columns * num_rows - 1) // (num_columns * num_rows)

            for page in range(pages):
                c.drawImage(small_image_path, (increased_page_width + margin_rows) - small_image_width, increased_page_height - small_image_height, width=small_image_width, height=small_image_height)
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

                for i, (image_url, product_name, price_range, deeplink_url, Platform) in enumerate(zip(image_urls, product_names, price_ranges, deeplink_urls, Platforms)):
                    row_index = i // num_columns
                    col_index = i % num_columns
                    x = x_offset + margin_columns + col_index * (max_image_width + margin_columns)
                    y = y_offset + margin_rows + (num_rows - row_index - 1) * (max_image_height + margin_rows)

                    response = requests.get(image_url)
                    if response.status_code == 200:
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

                        p.wrapOn(c, max_image_width, max_image_height)
                        p.drawOn(c, x + (((max_image_width + 10) / 2) - (pwidth / 2)) , y - 25)
                        page_has_content = True
                    else:
                        print(f"Failed to download image from {image_url}")

                if page_has_content:
                    c.showPage()

        c.save()

    output_file = 'sample_catalogue.pdf'
    compressed_output_file = 'sample_catalogue_compressed.pdf'
    max_image_width = 146 
    max_image_height = 175  

    df = pd.read_csv('PDFReport_174857000100873355.csv')
    df = df[df['SuperCategory'] == 'Apparels']

    create_pdf(df, output_file, max_image_width, max_image_height)
    
    compress_pdf(output_file, compressed_output_file)
    
    return compressed_output_file

generate_catalogue_pdf()